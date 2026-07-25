#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/public/GSE270342_h5 data/public/GSE270342_npz logs
source .venv/bin/activate 2>/dev/null || true

filelist="data/public/geo_filelists/GSE270342/filelist.txt"
download_dir="data/public/GSE270342_h5"
download_list="data/public/GSE270342_download_files.txt"
sample_regex="${SNOWCELL_GSE270342_REGEX:-filtered_feature_bc_matrix\\.h5$}"
max_files="${SNOWCELL_GSE270342_MAX_FILES:-3}"

if [ ! -s "$filelist" ]; then
  echo "Missing $filelist; run scripts/generated_downloads/download_geo_filelists.sh first."
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
names = re.findall(r"(GSM\d+_[A-Za-z0-9_.-]+\.h5)", filelist.read_text(encoding="utf-8", errors="ignore"))
selected = [name for name in names if sample_regex.search(name)][:max_files]
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

aria2_input="data/public/GSE270342_aria2_urls.txt"
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
    aria2c -c -j "${SNOWCELL_GSE270342_PARALLEL_JOBS:-3}" -x 8 -s 8 \
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

python scripts/tenx_h5_to_npz.py \
  --input-dir "$download_dir" \
  --output-dir data/public/GSE270342_npz \
  --dataset-id wheat_soil_root_atlas \
  --species "Triticum aestivum" \
  --tissue root \
  --pattern "*.h5" \
  --sample-regex "$sample_regex" \
  --max-files "$max_files" \
  --manifest-output data/corpus_manifest.gse270342.tsv

echo "Wrote data/corpus_manifest.gse270342.tsv"
