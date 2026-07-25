#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

accession="${SNOWCELL_GEO_ACCESSION:?set SNOWCELL_GEO_ACCESSION}"
dataset_id="${SNOWCELL_GEO_DATASET_ID:?set SNOWCELL_GEO_DATASET_ID}"
species="${SNOWCELL_GEO_SPECIES:?set SNOWCELL_GEO_SPECIES}"
tissue="${SNOWCELL_GEO_TISSUE:?set SNOWCELL_GEO_TISSUE}"
sample_regex="${SNOWCELL_GEO_SAMPLE_REGEX:-_mtx\\.tar\\.gz$}"
max_files="${SNOWCELL_GEO_MAX_FILES:-1}"
feature_column="${SNOWCELL_GEO_FEATURE_COLUMN:-0}"

filelist="data/public/geo_filelists/${accession}/filelist.txt"
download_dir="data/public/${accession}_mtx_tar"
extract_dir="data/public/${accession}_mtx_extracted"
npz_dir="data/public/${accession}_npz"
download_list="data/public/${accession}_mtx_download_files.txt"
manifest_output="data/corpus_manifest.${accession,,}.tsv"

mkdir -p "$download_dir" "$extract_dir" "$npz_dir" logs

if [ ! -s "$filelist" ]; then
  echo "Missing $filelist. Run scripts/generated_downloads/download_geo_filelists.sh first." >&2
  exit 1
fi

python - "$filelist" "$download_list" "$sample_regex" "$max_files" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

filelist = Path(sys.argv[1])
download_list = Path(sys.argv[2])
sample_regex = re.compile(sys.argv[3])
max_files = int(sys.argv[4])
names = re.findall(r"(GSM\d+_[A-Za-z0-9_.-]+\.tar\.gz)", filelist.read_text(encoding="utf-8", errors="ignore"))
selected = [name for name in names if sample_regex.search(name)][:max_files]
if not selected:
    raise SystemExit("no matching MTX tar files selected")
download_list.write_text("\n".join(selected) + "\n", encoding="utf-8")
print(f"Selected {len(selected)} MTX tar files")
for name in selected:
    print(name)
PY

geo_sample_url() {
  local filename="$1"
  local sample_accession="${filename%%_*}"
  local sample_bucket="${sample_accession%???}nnn"
  printf "https://ftp.ncbi.nlm.nih.gov/geo/samples/%s/%s/suppl/%s" \
    "$sample_bucket" "$sample_accession" "$filename"
}

aria2_input="data/public/${accession}_mtx_aria2_urls.txt"
: > "$aria2_input"
while IFS= read -r filename; do
  [ -n "$filename" ] || continue
  target="$download_dir/$filename"
  if [ ! -s "$target" ] || ! tar -tzf "$target" >/dev/null 2>&1; then
    {
      geo_sample_url "$filename"
      printf "\n  dir=%s\n  out=%s\n" "$download_dir" "$filename"
    } >> "$aria2_input"
  else
    echo "exists $target"
  fi
done < "$download_list"

if [ -s "$aria2_input" ]; then
  if command -v aria2c >/dev/null 2>&1; then
    aria2c -c -j "${SNOWCELL_GEO_PARALLEL_JOBS:-2}" -x 8 -s 8 \
      --max-tries=8 --retry-wait=10 --timeout=60 \
      --user-agent="SnowLotus-CellFM/0.1 public-data-collector" \
      -i "$aria2_input"
  else
    while IFS= read -r filename; do
      [ -n "$filename" ] || continue
      curl -L --fail --retry 5 --connect-timeout 20 --max-time 7200 \
        -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
        -o "$download_dir/$filename" "$(geo_sample_url "$filename")"
    done < "$download_list"
  fi
fi

while IFS= read -r filename; do
  [ -n "$filename" ] || continue
  target="$download_dir/$filename"
  tar -tzf "$target" >/dev/null
  sample_dir="$extract_dir/${filename%.tar.gz}"
  rm -rf "$sample_dir"
  mkdir -p "$sample_dir"
  tar -xzf "$target" -C "$sample_dir"
done < "$download_list"

python scripts/geo_mtx_tar_to_npz.py \
  --input-dir "$extract_dir" \
  --output-dir "$npz_dir" \
  --dataset-id "$dataset_id" \
  --species "$species" \
  --tissue "$tissue" \
  --feature-column "$feature_column" \
  --manifest-output "$manifest_output" \
  --min-samples 1

echo "Wrote $manifest_output"
