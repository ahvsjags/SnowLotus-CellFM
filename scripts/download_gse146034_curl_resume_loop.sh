#!/usr/bin/env bash
set -u

ROOT=/mnt/snowlotus_cellfm
OUT="$ROOT/data/public/GSE146034_raw_tar/GSE146034_RAW.tar.download"
FINAL="$ROOT/data/public/GSE146034_raw_tar/GSE146034_RAW.tar"
LOG="$ROOT/logs/gse146034_resume_loop.log"
# The GEO download endpoint does not advertise byte ranges; the official FTP mirror does.
URL='https://ftp.ncbi.nlm.nih.gov/geo/series/GSE146nnn/GSE146034/suppl/GSE146034_RAW.tar'
mkdir -p "$(dirname "$OUT")" "$(dirname "$LOG")"

while true; do
    if [ -s "$OUT" ] && tar -tf "$OUT" >/dev/null 2>&1; then
        mv -f "$OUT" "$FINAL"
        printf '%s COMPLETE %s bytes\n' "$(date -Is)" "$(stat -c %s "$FINAL")" >> "$LOG"
        break
    fi
    printf '%s RESUME %s bytes\n' "$(date -Is)" "$(stat -c %s "$OUT" 2>/dev/null || echo 0)" >> "$LOG"
    curl -L --fail --http1.1 --connect-timeout 20 --max-time 3600 \
        -H 'User-Agent: SnowLotus-CellFM/0.1 public-data-collector' \
        -C - -o "$OUT" "$URL" >> "$LOG" 2>&1 || true
    sleep 10
done
