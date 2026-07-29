#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

accession="${SNOWCELL_GEO_ACCESSION:?set SNOWCELL_GEO_ACCESSION}"
dataset_id="${SNOWCELL_GEO_DATASET_ID:?set SNOWCELL_GEO_DATASET_ID}"
species="${SNOWCELL_GEO_SPECIES:?set SNOWCELL_GEO_SPECIES}"
tissue="${SNOWCELL_GEO_TISSUE:?set SNOWCELL_GEO_TISSUE}"
sample_regex="${SNOWCELL_GEO_SAMPLE_REGEX:-\\.h5$}"
max_files="${SNOWCELL_GEO_MAX_FILES:-1}"
feature_column="${SNOWCELL_GEO_FEATURE_COLUMN:-id}"

raw_dir="data/public/${accession}_raw_tar"
download_dir="data/public/${accession}_h5"
npz_dir="data/public/${accession}_npz"
raw_tar="${raw_dir}/${accession}_RAW.tar"
raw_tmp="${raw_tar}.download"
tar_list="${raw_dir}/${accession}_RAW.members.txt"
selected_members="${raw_dir}/${accession}_RAW.selected_h5.txt"
manifest_output="data/corpus_manifest.${accession,,}.tsv"
series_bucket="${accession%???}nnn"
raw_url="${SNOWCELL_GEO_RAW_URL:-https://ftp.ncbi.nlm.nih.gov/geo/series/${series_bucket}/${accession}/suppl/${accession}_RAW.tar}"
raw_fallback_url="${SNOWCELL_GEO_RAW_FALLBACK_URL:-https://www.ncbi.nlm.nih.gov/geo/download/?acc=${accession}&format=file}"
downloader="${SNOWCELL_GEO_RAW_TAR_DOWNLOADER:-aria2}"

mkdir -p "$raw_dir" "$download_dir" "$npz_dir" logs

if [ -s "$raw_tar" ] && [ ! -f "${raw_tar}.aria2" ] && tar -tf "$raw_tar" >/dev/null 2>&1; then
  echo "exists $raw_tar"
else
  if [ -s "$raw_tar" ] && ! tar -tf "$raw_tar" >/dev/null 2>&1; then
    if [ ! -s "$raw_tmp" ] || [ "$(stat -c %s "$raw_tar")" -gt "$(stat -c %s "$raw_tmp")" ]; then
      mv -f "$raw_tar" "$raw_tmp"
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
    aria2c -c -j 1 \
      -x "${SNOWCELL_GEO_RAW_TAR_CONNECTIONS:-1}" -s "${SNOWCELL_GEO_RAW_TAR_SPLITS:-1}" \
      --max-tries=12 --retry-wait=20 --timeout=120 --allow-overwrite=true --auto-file-renaming=false \
      --user-agent="SnowLotus-CellFM/0.1 public-data-collector" \
      -i "$aria2_input"
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
  tar -tf "$raw_tar" >/dev/null
fi

tar -tf "$raw_tar" > "$tar_list"

python - "$tar_list" "$selected_members" "$sample_regex" "$max_files" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

tar_list = Path(sys.argv[1])
selected_members = Path(sys.argv[2])
sample_regex = re.compile(sys.argv[3])
max_files = int(sys.argv[4])
members = [line.strip() for line in tar_list.read_text(encoding="utf-8", errors="ignore").splitlines()]
selected = [
    member
    for member in members
    if member
    and not member.endswith("/")
    and member.lower().endswith(".h5")
    and sample_regex.search(Path(member).name)
][:max_files]
if not selected:
    raise SystemExit("no matching H5 files selected from GEO RAW tar")
selected_members.write_text("\n".join(selected) + "\n", encoding="utf-8")
print(f"Selected {len(selected)} H5 files")
for member in selected:
    print(member)
PY

tar -xf "$raw_tar" -C "$download_dir" -T "$selected_members"

while IFS= read -r member; do
  [ -n "$member" ] || continue
  extracted="$download_dir/$member"
  target="$download_dir/$(basename "$member")"
  if [ -f "$extracted" ] && [ "$(readlink -f "$extracted")" != "$(readlink -f "$target" 2>/dev/null || printf '%s' "$target")" ]; then
    cp -f "$extracted" "$target"
  fi
done < "$selected_members"

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

rm -f "${raw_dir}/unsupported_single_cell_matrix.json"
echo "Wrote $manifest_output"
