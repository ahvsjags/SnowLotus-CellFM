#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

accession="${SNOWCELL_GEO_ACCESSION:?set SNOWCELL_GEO_ACCESSION}"
dataset_id="${SNOWCELL_GEO_DATASET_ID:?set SNOWCELL_GEO_DATASET_ID}"
species="${SNOWCELL_GEO_SPECIES:?set SNOWCELL_GEO_SPECIES}"
tissue="${SNOWCELL_GEO_TISSUE:?set SNOWCELL_GEO_TISSUE}"
sample_regex="${SNOWCELL_GEO_SAMPLE_REGEX:-filtered_feature_bc_matrix\\.h5$}"
max_files="${SNOWCELL_GEO_MAX_FILES:-1}"
feature_column="${SNOWCELL_GEO_FEATURE_COLUMN:-id}"

filelist="data/public/geo_filelists/${accession}/filelist.txt"
download_dir="data/public/${accession}_h5"
npz_dir="data/public/${accession}_npz"
download_list="data/public/${accession}_h5_download_files.txt"
manifest_output="data/corpus_manifest.${accession,,}.tsv"

mkdir -p "$download_dir" "$npz_dir" logs

if [ ! -s "$filelist" ]; then
  echo "Missing $filelist; fetching GEO supplementary filelist for $accession"
  bash scripts/fetch_geo_supplementary_filelist.sh
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
names = re.findall(r"(GSM\d+_[A-Za-z0-9_.-]+\.h5)", filelist.read_text(encoding="utf-8", errors="ignore"))
selected = [name for name in names if sample_regex.search(name)][:max_files]
if not selected:
    raise SystemExit("no matching H5 files selected")
download_list.write_text("\n".join(selected) + "\n", encoding="utf-8")
print(f"Selected {len(selected)} H5 files")
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

aria2_input="data/public/${accession}_h5_aria2_urls.txt"
: > "$aria2_input"
while IFS= read -r filename; do
  [ -n "$filename" ] || continue
  target="$download_dir/$filename"
  if [ -s "$target" ]; then
    python - "$target" <<'PY' && { echo "exists $target"; continue; } || true
import h5py
import sys
h5py.File(sys.argv[1], "r").close()
PY
    rm -f "$target"
  fi
  {
    geo_sample_url "$filename"
    printf "\n  dir=%s\n  out=%s\n" "$download_dir" "$filename"
  } >> "$aria2_input"
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
  python - "$download_dir/$filename" <<'PY'
import h5py
import sys
h5py.File(sys.argv[1], "r").close()
PY
done < "$download_list"

python scripts/tenx_h5_to_npz.py \
  --input-dir "$download_dir" \
  --output-dir "$npz_dir" \
  --dataset-id "$dataset_id" \
  --species "$species" \
  --tissue "$tissue" \
  --pattern "*.h5" \
  --sample-regex "$sample_regex" \
  --max-files "$max_files" \
  --min-files 1 \
  --feature-column "$feature_column" \
  --manifest-output "$manifest_output"

echo "Wrote $manifest_output"
