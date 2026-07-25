#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

accession="${SNOWCELL_GEO_ACCESSION:?set SNOWCELL_GEO_ACCESSION}"
dataset_id="${SNOWCELL_GEO_DATASET_ID:?set SNOWCELL_GEO_DATASET_ID}"
species="${SNOWCELL_GEO_SPECIES:?set SNOWCELL_GEO_SPECIES}"
tissue="${SNOWCELL_GEO_TISSUE:?set SNOWCELL_GEO_TISSUE}"
sample_regex="${SNOWCELL_GEO_SAMPLE_REGEX:-\\.rds(\\.gz)?$}"
max_files="${SNOWCELL_GEO_MAX_FILES:-1}"

filelist="data/public/geo_filelists/${accession}/filelist.txt"
download_dir="data/public/${accession}_rds"
mtx_dir="data/public/${accession}_mtx"
npz_dir="data/public/${accession}_npz"
download_list="data/public/${accession}_rds_download_files.txt"
manifest_output="data/corpus_manifest.${accession,,}.tsv"

mkdir -p "$download_dir" "$mtx_dir" "$npz_dir" logs

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
names = re.findall(r"(GSM\d+_[A-Za-z0-9_.-]+\.rds(?:\.gz)?)", filelist.read_text(encoding="utf-8", errors="ignore"))
selected = [name for name in names if sample_regex.search(name)][:max_files]
if not selected:
    raise SystemExit("no matching RDS files selected")
download_list.write_text("\n".join(selected) + "\n", encoding="utf-8")
print(f"Selected {len(selected)} RDS files")
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

verify_download() {
  local path="$1"
  [ -s "$path" ] || return 1
  case "$path" in
    *.gz)
      gzip -t "$path" >/dev/null 2>&1
      ;;
    *)
      return 0
      ;;
  esac
}

curl_download_file() {
  local filename="$1"
  local target="$download_dir/$filename"
  local tmp="${target}.curltmp"
  rm -f "$tmp"
  if curl --http1.1 -L --fail --retry 24 --retry-all-errors --connect-timeout 20 --max-time 14400 \
    -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
    -o "$tmp" "$(geo_sample_url "$filename")" && verify_download "$tmp"; then
    mv "$tmp" "$target"
    rm -f "${target}.aria2"
    return 0
  fi
  rm -f "$tmp"
  return 1
}

aria2_input="data/public/${accession}_rds_aria2_urls.txt"
: > "$aria2_input"
while IFS= read -r filename; do
  [ -n "$filename" ] || continue
  target="$download_dir/$filename"
  if ! verify_download "$target" || [ -f "${target}.aria2" ]; then
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
    if ! aria2c -c -j "${SNOWCELL_GEO_PARALLEL_JOBS:-1}" -x 4 -s 4 \
      --max-tries=8 --retry-wait=10 --timeout=60 \
      --user-agent="SnowLotus-CellFM/0.1 public-data-collector" \
      -i "$aria2_input"; then
      echo "aria2 reported failure; validating partial outputs and falling back to curl where needed." >&2
    fi
  fi
  while IFS= read -r filename; do
    [ -n "$filename" ] || continue
    target="$download_dir/$filename"
    if verify_download "$target"; then
      rm -f "${target}.aria2"
      echo "verified $target"
      continue
    fi
    rm -f "$target" "${target}.aria2"
    curl_download_file "$filename"
  done < "$download_list"
fi

if ! command -v Rscript >/dev/null 2>&1; then
  echo "Rscript not found. Run scripts/install_r_singlecell_tools.sh first." >&2
  exit 2
fi

Rscript scripts/export_seurat_rds_to_mtx.R "$download_dir" "$mtx_dir"
python scripts/build_npz_from_seurat_export.py \
  --export-dir "$mtx_dir" \
  --output-dir "$npz_dir" \
  --dataset-id "$dataset_id" \
  --species "$species" \
  --tissue "$tissue"

python - "$npz_dir" "$manifest_output" "$dataset_id" "$species" "$tissue" <<'PY'
from __future__ import annotations

import csv
import sys
from pathlib import Path

npz_dir = Path(sys.argv[1])
manifest = Path(sys.argv[2])
dataset_id, species, tissue = sys.argv[3:6]
paths = sorted(npz_dir.glob("*.npz"))
if not paths:
    raise SystemExit("no NPZ outputs were produced")
with manifest.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(["path", "dataset_id", "species", "tissue", "layer", "label_key", "coarse_label_key", "sample_key"])
    for path in paths:
        writer.writerow([str(path), dataset_id, species, tissue, "", "cell_type", "cell_type_coarse", "sample_id"])
print(manifest)
PY

echo "Wrote $manifest_output"
