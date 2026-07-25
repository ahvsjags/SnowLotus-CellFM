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
h5_sample_regex="${SNOWCELL_GEO_H5_SAMPLE_REGEX:-${SNOWCELL_GEO_SAMPLE_REGEX:-filtered_feature_bc_matrix.*\\.h5$}}"
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
raw_max_bytes="${SNOWCELL_GEO_RAW_TAR_MAX_BYTES:-21474836480}"
raw_allow_large="${SNOWCELL_GEO_RAW_TAR_ALLOW_LARGE:-0}"

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

remote_content_length() {
  python - "$1" <<'PY'
from __future__ import annotations

import sys
import urllib.request

url = sys.argv[1]
request = urllib.request.Request(
    url,
    method="HEAD",
    headers={"User-Agent": "SnowLotus-CellFM/0.1 public-data-collector"},
)
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        print(response.headers.get("Content-Length", ""))
except Exception:
    print("")
PY
}

curl_common_args=(
  -L
  --fail
  --retry "${SNOWCELL_GEO_RAW_TAR_CURL_RETRIES:-12}"
  --retry-all-errors
  --connect-timeout "${SNOWCELL_GEO_RAW_TAR_CONNECT_TIMEOUT:-20}"
  --speed-limit "${SNOWCELL_GEO_RAW_TAR_MIN_SPEED:-1024}"
  --speed-time "${SNOWCELL_GEO_RAW_TAR_SPEED_TIME:-300}"
  --max-time "${SNOWCELL_GEO_RAW_TAR_MAX_TIME:-86400}"
  -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector"
)

download_with_curl_resume() {
  local url="$1"
  local label="$2"
  echo "curl resume download for ${label}: ${url}"
  curl "${curl_common_args[@]}" -C - -o "$raw_tmp" "$url"
}

download_with_curl_fresh() {
  local url="$1"
  local label="$2"
  local fresh_tmp="${raw_tmp}.fresh"
  rm -f "$fresh_tmp"
  echo "curl fresh download for non-range ${label}: ${url}"
  curl "${curl_common_args[@]}" -o "$fresh_tmp" "$url"
  mv -f "$fresh_tmp" "$raw_tmp"
}

adopt_aria2_partial_for_curl() {
  if [ -s "$raw_tar" ] && [ ! -f "${raw_tar}.aria2" ] && [ ! -s "$raw_tmp" ]; then
    mv -f "$raw_tar" "$raw_tmp"
  else
    rm -f "$raw_tar"
  fi
  rm -f "${raw_tar}.aria2"
}

if [ -s "$raw_tar" ] && [ ! -f "${raw_tar}.aria2" ] && tar -tf "$raw_tar" >/dev/null 2>&1; then
  rm -f "$raw_tmp"
  rm -f "${raw_tar}.aria2"
  echo "exists $raw_tar"
else
  raw_content_length="$(remote_content_length "$raw_url" || true)"
  if [ "$raw_allow_large" != "1" ] && [ -n "$raw_content_length" ] && [ "$raw_content_length" -gt "$raw_max_bytes" ] 2>/dev/null; then
    rm -f "$raw_tar" "${raw_tar}.aria2" "$raw_tmp"
    write_unsupported_report "GEO RAW tar is ${raw_content_length} bytes, which exceeds SNOWCELL_GEO_RAW_TAR_MAX_BYTES=${raw_max_bytes}. Whole-tar retrieval is deferred; use a file-level matrix member retrieval strategy or rerun with SNOWCELL_GEO_RAW_TAR_ALLOW_LARGE=1 after confirming disk/network budget."
    echo "Deferred large GEO RAW tar: $raw_url (${raw_content_length} bytes)"
    exit 0
  fi
  if [ "$downloader" = "aria2" ] && command -v aria2c >/dev/null 2>&1; then
    aria2_input="${raw_dir}/${accession}_RAW.aria2_urls.txt"
    {
      printf "%s\n" "$raw_url"
      printf "  dir=%s\n" "$raw_dir"
      printf "  out=%s\n" "${accession}_RAW.tar"
    } > "$aria2_input"
    if ! aria2c -c -j 1 \
      -x "${SNOWCELL_GEO_RAW_TAR_CONNECTIONS:-1}" -s "${SNOWCELL_GEO_RAW_TAR_SPLITS:-1}" \
      --max-tries=12 --retry-wait=20 --timeout=120 --lowest-speed-limit="${SNOWCELL_GEO_RAW_TAR_ARIA2_LOWEST_SPEED:-1K}" \
      --allow-overwrite=true --auto-file-renaming=false \
      --user-agent="SnowLotus-CellFM/0.1 public-data-collector" \
      -i "$aria2_input"; then
      echo "aria2 raw tar download failed; retrying range-capable raw URL with curl resume"
      adopt_aria2_partial_for_curl
      if ! download_with_curl_resume "$raw_url" "GEO raw tar URL"; then
        echo "curl resume against raw URL failed; retrying GEO download endpoint without resume"
        download_with_curl_fresh "$raw_fallback_url" "GEO download endpoint"
      fi
      mv -f "$raw_tmp" "$raw_tar"
      rm -f "${raw_tar}.aria2"
    fi
  else
    if ! download_with_curl_resume "$raw_url" "GEO raw tar URL"; then
      echo "curl resume against raw URL failed; retrying GEO download endpoint without resume"
      download_with_curl_fresh "$raw_fallback_url" "GEO download endpoint"
    fi
    mv -f "$raw_tmp" "$raw_tar"
    rm -f "${raw_tar}.aria2"
  fi
fi

rm -rf "$extract_dir"
mkdir -p "$extract_dir"
tar -xf "$raw_tar" -C "$extract_dir"

gzip_validation_log="${raw_dir}/${accession}_gzip_validation_error.log"
gzip_quarantine_report="${raw_dir}/${accession}_gzip_quarantine.json"
if find "$extract_dir" -type f -iname '*.gz' -print -quit | grep -q .; then
  python - "$extract_dir" "$raw_dir" "$gzip_validation_log" "$gzip_quarantine_report" <<'PY'
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

extract_dir = Path(sys.argv[1])
raw_dir = Path(sys.argv[2])
log_path = Path(sys.argv[3])
report_path = Path(sys.argv[4])
quarantine_dir = raw_dir / "quarantined_gzip_members"

suffixes = [
    "_matrix.mtx.gz",
    "_features.tsv.gz",
    "_genes.tsv.gz",
    "_barcodes.tsv.gz",
]


def sample_prefix(path: Path) -> str | None:
    for suffix in suffixes:
        if path.name.endswith(suffix):
            return path.name[: -len(suffix)]
    return None


corrupt: list[dict[str, str]] = []
for path in sorted(extract_dir.rglob("*.gz")):
    result = subprocess.run(["gzip", "-t", str(path)], capture_output=True, text=True)
    if result.returncode:
        corrupt.append(
            {
                "path": path.relative_to(extract_dir).as_posix(),
                "stderr": result.stderr.strip(),
                "sample_prefix": sample_prefix(path) or "",
            }
        )

if not corrupt:
    log_path.unlink(missing_ok=True)
    report_path.unlink(missing_ok=True)
    raise SystemExit(0)

log_path.write_text("\n".join(item["stderr"] for item in corrupt if item["stderr"]) + "\n", encoding="utf-8")

quarantined: list[str] = []
for item in corrupt:
    bad_path = extract_dir / item["path"]
    prefix = item["sample_prefix"]
    if prefix:
        candidates = sorted(bad_path.parent.glob(f"{prefix}_*"))
    else:
        candidates = [bad_path]
    for source in candidates:
        if not source.exists() or not source.is_file():
            continue
        rel = source.relative_to(extract_dir)
        target = quarantine_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        quarantined.append(rel.as_posix())

payload = {
    "status": "partial_gzip_member_quarantine",
    "corrupt_members": corrupt,
    "quarantined_files": quarantined,
}
report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"Quarantined {len(quarantined)} files with corrupt gzip members; continuing with valid samples")
PY
fi

python - "$extract_dir" "${raw_dir}/${accession}_flat_mtx_triplets.json" <<'PY'
from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

extract_dir = Path(sys.argv[1])
report_path = Path(sys.argv[2])

role_suffixes = {
    "matrix": ["_matrix.mtx.gz", "_matrix.mtx"],
    "features": ["_features.tsv.gz", "_features.tsv", "_genes.tsv.gz", "_genes.tsv"],
    "barcodes": ["_barcodes.tsv.gz", "_barcodes.tsv"],
}


def split_role(path: Path) -> tuple[str, str] | None:
    for role, suffixes in role_suffixes.items():
        for suffix in suffixes:
            if path.name.endswith(suffix):
                return path.name[: -len(suffix)], role
    return None


organized: list[dict[str, str]] = []
for parent in [extract_dir, *sorted(path for path in extract_dir.rglob("*") if path.is_dir())]:
    groups: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for path in sorted(parent.iterdir()):
        if not path.is_file():
            continue
        parsed = split_role(path)
        if not parsed:
            continue
        prefix, role = parsed
        groups[prefix][role].append(path)
    for prefix, roles in groups.items():
        if not {"matrix", "features", "barcodes"}.issubset(roles):
            continue
        target_dir = parent / prefix
        if parent.name == prefix:
            continue
        target_dir.mkdir(exist_ok=True)
        for paths in roles.values():
            for source in paths:
                target = target_dir / source.name
                if source.resolve() == target.resolve():
                    continue
                shutil.move(str(source), str(target))
                organized.append({"source": source.relative_to(extract_dir).as_posix(), "target": target.relative_to(extract_dir).as_posix()})

if organized:
    report_path.write_text(json.dumps({"status": "organized_flat_mtx_triplets", "files": organized}, indent=2) + "\n", encoding="utf-8")
    print(f"Organized {len(organized)} flat MTX triplet files into sample directories")
else:
    report_path.unlink(missing_ok=True)
PY

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
