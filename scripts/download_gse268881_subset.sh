#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/public/GSE268881_10x data/public/GSE268881_npz logs

source .venv/bin/activate 2>/dev/null || true

filelist="data/public/geo_filelists/GSE268881/filelist.txt"

filelist_ready() {
  [ -s "$filelist" ] \
    && grep -Eq "GSM[0-9]+_.*_(barcodes\\.tsv|features\\.tsv|matrix\\.mtx)\\.gz" "$filelist" \
    && ! grep -qiE "<html|access forbidden" "$filelist"
}

if ! filelist_ready; then
  echo "Missing $filelist; fetching GEO supplementary file list for GSE268881."
  SNOWCELL_GEO_ACCESSION=GSE268881 bash scripts/fetch_geo_supplementary_filelist.sh || true
fi
if ! filelist_ready && [ -f scripts/generated_downloads/download_geo_filelists.sh ]; then
  echo "GSE268881 file list still missing; trying generated GEO filelist downloader."
  bash scripts/generated_downloads/download_geo_filelists.sh || true
fi
if ! filelist_ready; then
  echo "Missing $filelist; unable to continue GSE268881 subset download."
  exit 1
fi

download_dir="data/public/GSE268881_10x"
download_list="data/public/GSE268881_download_files.txt"
sample_regex="${SNOWCELL_GSE268881_REGEX:-_(Ath|Esa|Sir|Spa|Csa)_Root_Ctrl_scRNAseq_R1$}"
max_samples="${SNOWCELL_GSE268881_MAX_SAMPLES:-5}"

python - "$filelist" "$download_list" "$sample_regex" "$max_samples" <<'PY'
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

filelist = Path(sys.argv[1])
download_list = Path(sys.argv[2])
sample_regex = re.compile(sys.argv[3])
max_samples = int(sys.argv[4])
names = re.findall(
    r"(GSM\d+_[A-Za-z0-9_]+_(?:barcodes\.tsv|features\.tsv|matrix\.mtx)\.gz)",
    filelist.read_text(encoding="utf-8", errors="ignore"),
)
groups: dict[str, dict[str, str]] = defaultdict(dict)
for name in names:
    if name.endswith("_barcodes.tsv.gz"):
        groups[name.removesuffix("_barcodes.tsv.gz")]["barcodes"] = name
    elif name.endswith("_features.tsv.gz"):
        groups[name.removesuffix("_features.tsv.gz")]["features"] = name
    elif name.endswith("_matrix.mtx.gz"):
        groups[name.removesuffix("_matrix.mtx.gz")]["matrix"] = name
selected = [
    sample for sample in sorted(groups)
    if sample_regex.search(sample) and {"barcodes", "features", "matrix"} <= groups[sample].keys()
][:max_samples]
files = []
for sample in selected:
    files.extend([groups[sample]["barcodes"], groups[sample]["features"], groups[sample]["matrix"]])
download_list.write_text("\n".join(files) + "\n", encoding="utf-8")
print(f"Selected {len(selected)} samples and {len(files)} files")
for sample in selected:
    print(sample)
PY

geo_sample_url() {
  local filename="$1"
  local sample_accession="${filename%%_*}"
  local sample_bucket="${sample_accession%???}nnn"
  printf "https://ftp.ncbi.nlm.nih.gov/geo/samples/%s/%s/suppl/%s" \
    "$sample_bucket" "$sample_accession" "$filename"
}

needs_download() {
  local target="$1"
  if [ ! -s "$target" ]; then
    return 0
  fi
  if gzip -t "$target" >/dev/null 2>&1; then
    return 1
  fi
  if head -c 2 "$target" | grep -q "<"; then
    echo "removing invalid HTML download $target"
    rm -f "$target"
  else
    echo "will resume incomplete download $target"
  fi
  return 0
}

if command -v aria2c >/dev/null 2>&1; then
  aria2_input="data/public/GSE268881_aria2_urls.txt"
  : > "$aria2_input"
  while IFS= read -r filename; do
    [ -n "$filename" ] || continue
    target="$download_dir/$filename"
    if needs_download "$target"; then
      {
        geo_sample_url "$filename"
        printf "\n  dir=%s\n  out=%s\n" "$download_dir" "$filename"
      } >> "$aria2_input"
    else
      echo "exists $target"
    fi
  done < "$download_list"

  if [ -s "$aria2_input" ]; then
    aria2c -c \
      -j "${SNOWCELL_GSE268881_PARALLEL_JOBS:-4}" \
      -x "${SNOWCELL_GSE268881_CONNECTIONS:-8}" \
      -s "${SNOWCELL_GSE268881_CONNECTIONS:-8}" \
      --max-tries=8 --retry-wait=10 --timeout=60 \
      --user-agent="SnowLotus-CellFM/0.1 public-data-collector" \
      -i "$aria2_input"
  fi
else
  while IFS= read -r filename; do
    [ -n "$filename" ] || continue
    target="$download_dir/$filename"
    url="$(geo_sample_url "$filename")"
    resume=0
    if [ -s "$target" ]; then
      if gzip -t "$target" >/dev/null 2>&1; then
        echo "exists $target"
        continue
      fi
      if head -c 2 "$target" | grep -q "<"; then
        echo "removing invalid HTML download $target"
        rm -f "$target"
      else
        echo "resuming incomplete download $target"
        resume=1
      fi
    fi
    echo "downloading $filename"
    if [ "$resume" = "1" ]; then
      curl -L --fail --http1.1 --retry 5 --retry-all-errors --connect-timeout 20 --max-time 7200 -C - \
        -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
        -o "$target" "$url"
    else
      curl -L --fail --http1.1 --retry 5 --retry-all-errors --connect-timeout 20 --max-time 7200 -C - \
        -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
        -o "$target" "$url"
    fi
  done < "$download_list"
fi

while IFS= read -r filename; do
  [ -n "$filename" ] || continue
  target="$download_dir/$filename"
  if [ ! -s "$target" ]; then
    echo "missing selected GSE268881 file after download: $target" >&2
    exit 1
  fi
  gzip -t "$target"
done < "$download_list"

python scripts/geo_10x_to_npz.py \
  --input-dir "$download_dir" \
  --output-dir data/public/GSE268881_npz \
  --dataset-id brassicaceae_multi_species_root_atlas \
  --sample-regex "$sample_regex" \
  --max-samples "$max_samples" \
  --manifest-output data/corpus_manifest.gse268881.tsv

echo "Wrote data/corpus_manifest.gse268881.tsv"
