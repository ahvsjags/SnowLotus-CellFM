#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

accession="${SNOWCELL_GEO_ACCESSION:?set SNOWCELL_GEO_ACCESSION}"
dataset_id="${SNOWCELL_GEO_DATASET_ID:?set SNOWCELL_GEO_DATASET_ID}"
species="${SNOWCELL_GEO_SPECIES:?set SNOWCELL_GEO_SPECIES}"
tissue="${SNOWCELL_GEO_TISSUE:?set SNOWCELL_GEO_TISSUE}"
feature_column="${SNOWCELL_GEO_FEATURE_COLUMN:-0}"
label="${SNOWCELL_GEO_LABEL:-unannotated}"
coarse_label="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
h5_sample_regex="${SNOWCELL_GEO_H5_SAMPLE_REGEX:-${SNOWCELL_GEO_SAMPLE_REGEX:-filtered_feature_bc_matrix\\.h5$}}"
h5_max_files="${SNOWCELL_GEO_H5_MAX_FILES:-${SNOWCELL_GEO_MAX_FILES:-25}}"
h5_feature_column="${SNOWCELL_GEO_H5_FEATURE_COLUMN:-id}"

raw_dir="data/public/${accession}_raw_tar"
extract_dir="data/public/${accession}_mtx_extracted"
h5_dir="data/public/${accession}_h5"
npz_dir="data/public/${accession}_npz"
raw_tar="${raw_dir}/${accession}_RAW.tar"
raw_tmp="${raw_tar}.download"
manifest_output="data/corpus_manifest.${accession,,}.tsv"
series_bucket="${accession%???}nnn"
raw_url="${SNOWCELL_GEO_RAW_URL:-https://ftp.ncbi.nlm.nih.gov/geo/series/${series_bucket}/${accession}/suppl/${accession}_RAW.tar}"
raw_fallback_url="${SNOWCELL_GEO_RAW_FALLBACK_URL:-https://www.ncbi.nlm.nih.gov/geo/download/?acc=${accession}&format=file}"
downloader="${SNOWCELL_GEO_RAW_TAR_DOWNLOADER:-aria2}"

mkdir -p "$raw_dir" "$extract_dir" "$npz_dir" logs

write_unsupported_report() {
  local reason="$1"
  local error_file="${2:-}"
  local unsupported_report="${raw_dir}/unsupported_single_cell_matrix.json"
  python - "$extract_dir" "$manifest_output" "$unsupported_report" "$accession" "$dataset_id" "$species" "$tissue" "$reason" "$error_file" <<'PY'
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

extract_dir = Path(sys.argv[1])
manifest_output = Path(sys.argv[2])
unsupported_report = Path(sys.argv[3])
accession, dataset_id, species, tissue = sys.argv[4:8]
reason = sys.argv[8]
error_file = Path(sys.argv[9]) if len(sys.argv) > 9 and sys.argv[9] else None

files = sorted(path for path in extract_dir.rglob("*") if path.is_file())
suffix_counts = Counter("".join(path.suffixes) or "<none>" for path in files)
quant_sf = [path for path in files if path.name.endswith("quant.sf") or path.name.endswith("quant.sf.gz")]
mtx_files = [path for path in files if ".mtx" in "".join(path.suffixes).lower() or "matrix" in path.name.lower()]
feature_files = [
    path
    for path in files
    if "features" in path.name.lower()
    or "genes" in path.name.lower()
    or path.name.lower() == "genes.txt"
]

manifest_output.parent.mkdir(parents=True, exist_ok=True)
with manifest_output.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(["path", "dataset_id", "species", "tissue", "layer", "label_key", "coarse_label_key", "sample_key"])

payload = {
    "accession": accession,
    "dataset_id": dataset_id,
    "species": species,
    "tissue": tissue,
    "status": "unsupported_for_single_cell_matrix_corpus",
    "reason": reason,
    "file_count": len(files),
    "matrix_like_file_count": len(mtx_files),
    "feature_like_file_count": len(feature_files),
    "quant_sf_file_count": len(quant_sf),
    "suffix_counts": dict(sorted(suffix_counts.items())),
    "example_files": [path.relative_to(extract_dir).as_posix() for path in files[:25]],
    "corpus_manifest": manifest_output.as_posix(),
    "corpus_manifest_rows": 0,
}
if error_file and error_file.exists():
    error_text = error_file.read_text(encoding="utf-8", errors="replace")
    payload["conversion_error_tail"] = error_text[-4000:]
unsupported_report.parent.mkdir(parents=True, exist_ok=True)
unsupported_report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(unsupported_report)
print(manifest_output)
PY
}

if [ -s "$raw_tar" ] && [ ! -f "${raw_tar}.aria2" ] && tar -tf "$raw_tar" >/dev/null 2>&1; then
  rm -f "$raw_tmp"
  rm -f "${raw_tar}.aria2"
  echo "exists $raw_tar"
else
  if [ -s "$raw_tmp" ] && { [ ! -s "$raw_tar" ] || ! tar -tf "$raw_tar" >/dev/null 2>&1; }; then
    if [ ! -s "$raw_tar" ] || [ "$(stat -c %s "$raw_tmp")" -gt "$(stat -c %s "$raw_tar" 2>/dev/null || echo 0)" ]; then
      mv -f "$raw_tmp" "$raw_tar"
      rm -f "${raw_tar}.aria2"
    fi
  fi
  if [ "$downloader" = "aria2" ] && command -v aria2c >/dev/null 2>&1; then
    aria2_input="${raw_dir}/${accession}_RAW.aria2_urls.txt"
    {
      if [ "$raw_fallback_url" != "$raw_url" ]; then
        printf "%s\t%s\n" "$raw_url" "$raw_fallback_url"
      else
        printf "%s\n" "$raw_url"
      fi
      printf "  dir=%s\n" "$raw_dir"
      printf "  out=%s\n" "${accession}_RAW.tar"
    } > "$aria2_input"
    if ! aria2c -c -j 1 \
      -x "${SNOWCELL_GEO_RAW_TAR_CONNECTIONS:-1}" -s "${SNOWCELL_GEO_RAW_TAR_SPLITS:-1}" \
      --max-tries=12 --retry-wait=20 --timeout=120 --allow-overwrite=true --auto-file-renaming=false \
      --user-agent="SnowLotus-CellFM/0.1 public-data-collector" \
      -i "$aria2_input"; then
      echo "aria2 raw tar download failed; retrying GEO fallback download with curl resume"
      curl -L --fail --http1.1 --retry 12 --retry-all-errors --connect-timeout 20 --max-time 86400 \
        -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
        -C - -o "$raw_tmp" "$raw_fallback_url"
      mv -f "$raw_tmp" "$raw_tar"
      rm -f "${raw_tar}.aria2"
    fi
  else
    curl -L --fail --http1.1 --retry 12 --retry-all-errors --connect-timeout 20 --max-time 86400 \
      -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
      -C - -o "$raw_tmp" "$raw_fallback_url" \
      || curl -L --fail --http1.1 --retry 12 --retry-all-errors --connect-timeout 20 --max-time 86400 \
        -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
        -C - -o "$raw_tmp" "$raw_url"
    mv -f "$raw_tmp" "$raw_tar"
    rm -f "${raw_tar}.aria2"
  fi
fi

rm -rf "$extract_dir"
mkdir -p "$extract_dir"
tar -xf "$raw_tar" -C "$extract_dir"

gzip_validation_log="${raw_dir}/${accession}_gzip_validation_error.log"
if find "$extract_dir" -type f -iname '*.gz' -print -quit | grep -q .; then
  if ! find "$extract_dir" -type f -iname '*.gz' -print0 | xargs -0 gzip -t > "$gzip_validation_log" 2>&1; then
    corrupt_target="${raw_tar}.corrupt.$(date +%Y%m%d_%H%M%S)"
    mv -f "$raw_tar" "$corrupt_target"
    rm -f "${raw_tar}.aria2"
    rm -rf "$extract_dir"
    echo "Extracted gzip member validation failed; moved corrupt RAW tar to $corrupt_target" >&2
    cat "$gzip_validation_log" >&2
    exit 75
  fi
  rm -f "$gzip_validation_log"
fi

mtx_count="$(find "$extract_dir" -type f \( -iname '*matrix*.mtx*' -o -iname '*.mtx*' \) | wc -l | tr -d ' ')"
if [ "$mtx_count" = "0" ]; then
  h5_list="${raw_dir}/${accession}_RAW.detected_h5.txt"
  find "$extract_dir" -type f -iname '*.h5' | sort > "$h5_list"
  h5_count="$(wc -l < "$h5_list" | tr -d ' ')"
  if [ "$h5_count" != "0" ]; then
    rm -rf "$h5_dir"
    mkdir -p "$h5_dir"
    python - "$h5_list" "$h5_dir" "$h5_sample_regex" "$h5_max_files" <<'PY'
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

h5_list = Path(sys.argv[1])
h5_dir = Path(sys.argv[2])
sample_regex = re.compile(sys.argv[3])
max_files = int(sys.argv[4])
paths = [
    Path(line.strip())
    for line in h5_list.read_text(encoding="utf-8", errors="ignore").splitlines()
    if line.strip()
]
selected = [path for path in paths if sample_regex.search(path.name)][:max_files]
if not selected:
    raise SystemExit("H5 files were found, but none matched SNOWCELL_GEO_H5_SAMPLE_REGEX")
h5_dir.mkdir(parents=True, exist_ok=True)
used_names: set[str] = set()
for index, source in enumerate(selected, start=1):
    target_name = source.name
    if target_name in used_names or (h5_dir / target_name).exists():
        target_name = f"{index:03d}_{target_name}"
    used_names.add(target_name)
    shutil.copy2(source, h5_dir / target_name)
print(f"Selected {len(selected)} H5 files from RAW tar")
for source in selected:
    print(source)
PY
    h5_conversion_log="${raw_dir}/${accession}_h5_conversion_error.log"
    if ! python scripts/tenx_h5_to_npz.py \
      --input-dir "$h5_dir" \
      --output-dir "$npz_dir" \
      --dataset-id "$dataset_id" \
      --species "$species" \
      --tissue "$tissue" \
      --pattern "*.h5" \
      --sample-regex "$h5_sample_regex" \
      --max-files "$h5_max_files" \
      --min-files 1 \
      --feature-column "$h5_feature_column" \
      --manifest-output "$manifest_output" \
      2> "$h5_conversion_log"; then
      cat "$h5_conversion_log" >&2
      write_unsupported_report "GEO RAW tar contained H5 files, but conversion to a cell-by-gene expression corpus failed." "$h5_conversion_log"
      echo "H5 conversion failed; wrote unsupported report and header-only $manifest_output"
      exit 0
    fi
    rm -f "${raw_dir}/unsupported_single_cell_matrix.json"
    echo "Wrote $manifest_output from 10x H5 files embedded in $raw_tar"
    exit 0
  fi
  write_unsupported_report "No Matrix Market/10x matrix files were found after extracting the GEO RAW tar archive."
  echo "No MTX matrix files found under $extract_dir; wrote unsupported report and header-only $manifest_output"
  exit 0
fi

feature_count="$(find "$extract_dir" -type f \( -iname '*features*.tsv*' -o -iname '*genes*.tsv*' -o -iname 'genes.txt' \) | wc -l | tr -d ' ')"
if [ "$feature_count" = "0" ]; then
  write_unsupported_report "Matrix files were present, but no gene/features TSV files were found; this is likely a non-RNA modality matrix such as ATAC peaks rather than a cell-by-gene expression matrix."
  echo "MTX files were present but no gene/features files were found under $extract_dir; wrote unsupported report and header-only $manifest_output"
  exit 0
fi

conversion_log="${raw_dir}/${accession}_conversion_error.log"
if ! python scripts/geo_mtx_tar_to_npz.py \
  --input-dir "$extract_dir" \
  --output-dir "$npz_dir" \
  --dataset-id "$dataset_id" \
  --species "$species" \
  --tissue "$tissue" \
  --feature-column "$feature_column" \
  --label "$label" \
  --coarse-label "$coarse_label" \
  --manifest-output "$manifest_output" \
  --min-samples 1 2> "$conversion_log"; then
  cat "$conversion_log" >&2
  write_unsupported_report "GEO RAW tar contained matrix-like files, but conversion to a cell-by-gene expression corpus failed." "$conversion_log"
  echo "MTX conversion failed; wrote unsupported report and header-only $manifest_output"
  exit 0
fi

rm -f "${raw_dir}/unsupported_single_cell_matrix.json"
echo "Wrote $manifest_output"
