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
tmp_output="${tmp_output_dir}/.$(basename "$output").tmp.$$"

cleanup_tmp() {
  rm -f "$tmp_manifest" "$tmp_output"
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

snowcell build-corpus --manifest "$tmp_manifest" --output "$tmp_output"
mv -f "$tmp_output" "$output"
mv -f "$tmp_manifest" "$merged_manifest"
echo "$output"
