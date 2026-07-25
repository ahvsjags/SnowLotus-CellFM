#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

accession="${SNOWCELL_GEO_ACCESSION:?set SNOWCELL_GEO_ACCESSION}"
dataset_id="${SNOWCELL_GEO_DATASET_ID:?set SNOWCELL_GEO_DATASET_ID}"
species="${SNOWCELL_GEO_SPECIES:?set SNOWCELL_GEO_SPECIES}"
tissue="${SNOWCELL_GEO_TISSUE:?set SNOWCELL_GEO_TISSUE}"
pattern="${SNOWCELL_GEO_PAGE_PATTERN:-\\.rds(\\.gz)?$}"
max_files="${SNOWCELL_GEO_MAX_FILES:-1}"

download_dir="data/public/${accession}_rds"
mtx_dir="data/public/${accession}_mtx"
npz_dir="data/public/${accession}_npz"
url_list="data/public/${accession}_page_download_urls.tsv"
manifest_output="data/corpus_manifest.${accession,,}.tsv"

mkdir -p "$download_dir" "$mtx_dir" "$npz_dir" logs

python scripts/geo_page_download_urls.py \
  --accession "$accession" \
  --pattern "$pattern" \
  --max-files "$max_files" \
  --output "$url_list"

geo_download_fallback_url() {
  python - "$accession" "$1" <<'PY'
from __future__ import annotations

import sys
import urllib.parse

accession, filename = sys.argv[1:3]
encoded = urllib.parse.quote(filename, safe="")
print(f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={accession}&format=file&file={encoded}")
PY
}

should_add_geo_fallback() {
  local url="$1"
  case "$url" in
    *"/geo/series/"*"/${accession}/suppl/"*|*"geo/download/?acc=${accession}"*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
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

aria2_input="data/public/${accession}_page_aria2_urls.txt"
: > "$aria2_input"
while IFS=$'\t' read -r url filename; do
  [ -n "$url" ] || continue
  target="$download_dir/$filename"
  if ! verify_download "$target" || [ -f "${target}.aria2" ]; then
    fallback_url=""
    if should_add_geo_fallback "$url"; then
      fallback_url="$(geo_download_fallback_url "$filename")"
    fi
    {
      if [ -n "$fallback_url" ] && [ "$fallback_url" != "$url" ]; then
        printf "%s\t%s\n" "$url" "$fallback_url"
      else
        printf "%s\n" "$url"
      fi
      printf "  dir=%s\n  out=%s\n" "$download_dir" "$filename"
    } >> "$aria2_input"
  else
    echo "exists $target"
  fi
done < "$url_list"

curl_download_with_fallback() {
  local url="$1"
  local filename="$2"
  local target="$download_dir/$filename"
  local tmp="${target}.curltmp"
  local fallback_url=""
  if should_add_geo_fallback "$url"; then
    fallback_url="$(geo_download_fallback_url "$filename")"
  fi
  rm -f "$tmp"
  if curl --http1.1 -L --fail --retry 24 --retry-all-errors --connect-timeout 20 --max-time 14400 \
    -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
    -o "$tmp" "$url" && verify_download "$tmp"; then
    mv "$tmp" "$target"
    rm -f "${target}.aria2"
    return 0
  fi
  rm -f "$tmp"
  if [ -n "$fallback_url" ] && [ "$fallback_url" != "$url" ]; then
    if curl --http1.1 -L --fail --retry 24 --retry-all-errors --connect-timeout 20 --max-time 14400 \
      -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
      -o "$tmp" "$fallback_url" && verify_download "$tmp"; then
      mv "$tmp" "$target"
      rm -f "${target}.aria2"
      return 0
    fi
  fi
  rm -f "$tmp"
  return 1
}

if [ -s "$aria2_input" ]; then
  if command -v aria2c >/dev/null 2>&1; then
    if ! aria2c -c -j "${SNOWCELL_GEO_PARALLEL_JOBS:-1}" \
      -x "${SNOWCELL_GEO_CONNECTIONS:-1}" -s "${SNOWCELL_GEO_SPLITS:-1}" \
      --max-tries=8 --retry-wait=10 --timeout=60 \
      --user-agent="SnowLotus-CellFM/0.1 public-data-collector" \
      -i "$aria2_input"; then
      echo "aria2 reported failure; validating partial outputs and falling back to curl where needed." >&2
    fi
  fi
  while IFS=$'\t' read -r url filename; do
    [ -n "$url" ] || continue
    target="$download_dir/$filename"
    if verify_download "$target"; then
      rm -f "${target}.aria2"
      echo "verified $target"
      continue
    fi
    rm -f "$target" "${target}.aria2"
    curl_download_with_fallback "$url" "$filename"
  done < "$url_list"
fi

if ! command -v Rscript >/dev/null 2>&1; then
  echo "Rscript not found. Run scripts/install_r_singlecell_tools.sh first." >&2
  exit 2
fi

if ! Rscript scripts/export_seurat_rds_to_mtx.R "$download_dir" "$mtx_dir"; then
  echo "Seurat RDS export failed; trying direct expression slot export." >&2
  Rscript scripts/export_seurat_rds_expression_slot_to_mtx.R "$download_dir" "$mtx_dir"
fi
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
manifest.parent.mkdir(parents=True, exist_ok=True)
with manifest.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(["path", "dataset_id", "species", "tissue", "layer", "label_key", "coarse_label_key", "sample_key"])
    for path in paths:
        writer.writerow([str(path), dataset_id, species, tissue, "", "cell_type", "cell_type_coarse", "sample_id"])
print(manifest)
PY

echo "Wrote $manifest_output"
