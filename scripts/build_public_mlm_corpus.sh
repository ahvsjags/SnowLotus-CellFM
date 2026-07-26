#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

base_manifest="${SNOWCELL_BASE_CORPUS_MANIFEST:-data/corpus_manifest.tsv}"
extra_manifests="${SNOWCELL_EXTRA_CORPUS_MANIFESTS:-${SNOWCELL_EXTRA_CORPUS_MANIFEST:-}}"
merged_manifest="${SNOWCELL_MLM_CORPUS_MANIFEST:-data/corpus_manifest_public_mlm.tsv}"
output="${SNOWCELL_MLM_CORPUS_OUTPUT:-data/plant_foundation_corpus_public_mlm.h5ad}"
tmp_manifest_dir="$(dirname "$merged_manifest")"
tmp_output_dir="$(dirname "$output")"
tmp_manifest="${tmp_manifest_dir}/.$(basename "$merged_manifest").tmp.$$"
tmp_filtered_manifest="${tmp_manifest_dir}/.$(basename "$merged_manifest").filtered.tmp.$$"
missing_report="${SNOWCELL_MLM_MISSING_ROWS_REPORT:-${tmp_manifest_dir}/$(basename "$merged_manifest" .tsv).missing_paths.tsv}"
tmp_output="${tmp_output_dir}/.$(basename "$output").tmp.$$"

cleanup_tmp() {
  rm -f "$tmp_manifest" "$tmp_filtered_manifest" "$tmp_output"
}
trap cleanup_tmp EXIT

if [ ! -s "$base_manifest" ]; then
  echo "Missing base manifest: $base_manifest"
  exit 1
fi

if [ -z "$extra_manifests" ]; then
  extra_manifests="$(find data -maxdepth 1 -type f \( -name 'corpus_manifest.gse*.tsv' -o -name 'corpus_manifest.scplantdb*.tsv' \) ! -name '*.available.tsv' | sort | tr '\n' ' ')"
fi

mkdir -p "$tmp_manifest_dir" "$tmp_output_dir"

head -n 1 "$base_manifest" > "$tmp_manifest"
tail -n +2 "$base_manifest" >> "$tmp_manifest"

for extra_manifest in $extra_manifests; do
  if [ ! -s "$extra_manifest" ]; then
    echo "Missing extra manifest: $extra_manifest"
    exit 1
  fi
  tail -n +2 "$extra_manifest" >> "$tmp_manifest"
done

python - "$tmp_manifest" "$tmp_filtered_manifest" "$missing_report" <<'PY'
import csv
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
missing_report = Path(sys.argv[3])
root = Path(".")

with source.open("r", encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    fieldnames = list(reader.fieldnames or [])
    rows = list(reader)

if "path" not in fieldnames:
    raise SystemExit("merged manifest is missing required path column")

ready_rows = []
missing_rows = []
for row in rows:
    value = row.get("path", "")
    matrix = Path(value)
    if value and not matrix.is_absolute():
        matrix = root / matrix
    if value and matrix.is_file():
        ready_rows.append(row)
    else:
        missing_rows.append(row)

with target.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(ready_rows)

missing_report.parent.mkdir(parents=True, exist_ok=True)
with missing_report.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(missing_rows)

print(f"ready_rows={len(ready_rows)} missing_rows={len(missing_rows)} missing_report={missing_report}")
if not ready_rows:
    raise SystemExit("no ready matrix rows remain after filtering missing manifest paths")
PY

snowcell build-corpus --manifest "$tmp_filtered_manifest" --output "$tmp_output"
mv -f "$tmp_output" "$output"
mv -f "$tmp_filtered_manifest" "$merged_manifest"
echo "$output"
