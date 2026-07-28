#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/snowlotus_cellfm
OUT="$ROOT/data/public/GSE146034_raw_tar/GSE146034_RAW.tar.download"
FINAL="$ROOT/data/public/GSE146034_raw_tar/GSE146034_RAW.tar"
PART_DIR="$ROOT/data/public/GSE146034_raw_tar/parallel_suffix_parts"
LOG="$ROOT/logs/gse146034_parallel_ranges.log"
URL='https://ftp.ncbi.nlm.nih.gov/geo/series/GSE146nnn/GSE146034/suppl/GSE146034_RAW.tar'

# The local, validated copy reports this exact byte length.
TOTAL_BYTES=${GSE146034_TOTAL_BYTES:-206387200}
PARTS=${GSE146034_PARTS:-8}
mkdir -p "$PART_DIR" "$(dirname "$LOG")"

prefix_bytes=0
if [ -s "$OUT" ]; then
    prefix_bytes=$(stat -c %s "$OUT")
fi
if [ "$prefix_bytes" -ge "$TOTAL_BYTES" ]; then
    prefix_bytes=0
fi
remaining=$((TOTAL_BYTES - prefix_bytes))
chunk=$(( (remaining + PARTS - 1) / PARTS ))
pids=()
for ((index = 0; index < PARTS; index++)); do
    start=$((prefix_bytes + index * chunk))
    end=$((start + chunk - 1))
    if [ "$end" -ge "$TOTAL_BYTES" ]; then
        end=$((TOTAL_BYTES - 1))
    fi
    part="$PART_DIR/part_$(printf '%02d' "$index").bin"
    expected=$((end - start + 1))
    if [ -s "$part" ] && [ "$(stat -c %s "$part")" -eq "$expected" ]; then
        printf '%s REUSE part=%s bytes=%s\n' "$(date -Is)" "$index" "$expected" >> "$LOG"
        continue
    fi
    (
        while true; do
            rm -f "$part"
            printf '%s START part=%s range=%s-%s\n' "$(date -Is)" "$index" "$start" "$end" >> "$LOG"
            if curl -L --fail --http1.1 --connect-timeout 20 --max-time 3600 \
                -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' \
                --range "$start-$end" -o "$part" "$URL" >> "$LOG" 2>&1; then
                actual=$(stat -c %s "$part")
                if [ "$actual" -eq "$expected" ]; then
                    printf '%s DONE part=%s bytes=%s\n' "$(date -Is)" "$index" "$actual" >> "$LOG"
                    break
                fi
                printf '%s BAD_SIZE part=%s actual=%s expected=%s\n' "$(date -Is)" "$index" "$actual" "$expected" >> "$LOG"
            else
                printf '%s RETRY part=%s\n' "$(date -Is)" "$index" >> "$LOG"
            fi
            sleep 10
        done
    ) &
    pids+=("$!")
done

for pid in "${pids[@]}"; do
    wait "$pid"
done

assembled="$OUT.parallel"
rm -f "$assembled"
if [ "$prefix_bytes" -gt 0 ]; then
    cat "$OUT" >> "$assembled"
fi
for ((index = 0; index < PARTS; index++)); do
    cat "$PART_DIR/part_$(printf '%02d' "$index").bin" >> "$assembled"
done
[ "$(stat -c %s "$assembled")" -eq "$TOTAL_BYTES" ]
tar -tf "$assembled" >/dev/null
mv -f "$assembled" "$OUT"
mv -f "$OUT" "$FINAL"
printf '%s COMPLETE bytes=%s\n' "$(date -Is)" "$(stat -c %s "$FINAL")" >> "$LOG"
