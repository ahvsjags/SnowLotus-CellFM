#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

available_manifest="data/corpus_manifest.gse268881.available.tsv"
available_corpus="data/plant_foundation_corpus_public_mlm_available.h5ad"
merged_manifest="data/corpus_manifest_public_mlm_available.tsv"

manifest_matrix_ready() {
  local manifest="$1"
  python - "$manifest" <<'PY'
import csv
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
root = Path(".")
if not manifest.exists() or manifest.stat().st_size == 0:
    raise SystemExit(1)
with manifest.open("r", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))
if not rows:
    raise SystemExit(1)
missing = []
for row in rows:
    value = row.get("path", "")
    if not value:
        missing.append("<empty>")
        continue
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        missing.append(value)
if missing:
    print("missing matrix paths: " + ";".join(missing[:8]))
    raise SystemExit(1)
raise SystemExit(0)
PY
}

if ! manifest_matrix_ready "$available_manifest"; then
  echo "No available GSE268881 manifest yet: $available_manifest"
  exit 0
fi

extra_manifests="$available_manifest"
for optional_manifest in \
  data/corpus_manifest.gse146034.tsv \
  data/corpus_manifest.gse152766.tsv \
  data/corpus_manifest.gse226097.tsv \
  data/corpus_manifest.gse251706.tsv \
  data/corpus_manifest.gse270140.tsv \
  data/corpus_manifest.gse270342.tsv; do
  if manifest_matrix_ready "$optional_manifest" >/dev/null 2>&1; then
    extra_manifests="$extra_manifests $optional_manifest"
  else
    echo "Skipping non-ready optional manifest: $optional_manifest"
  fi
done

if [ -s "$available_corpus" ]; then
  needs_rebuild=0
  for manifest in $extra_manifests; do
    if [ "$manifest" -nt "$available_corpus" ]; then
      needs_rebuild=1
    fi
    first_path="$(awk -F '\t' 'NR==2 {print $1}' "$manifest")"
    if [ -n "$first_path" ] && ! grep -Fq "$first_path" "$merged_manifest" 2>/dev/null; then
      needs_rebuild=1
    fi
  done
  if [ "$needs_rebuild" = "0" ]; then
    echo "Available public MLM corpus is current: $available_corpus"
    exit 0
  fi
fi

SNOWCELL_EXTRA_CORPUS_MANIFESTS="$extra_manifests" \
SNOWCELL_MLM_CORPUS_MANIFEST="$merged_manifest" \
SNOWCELL_MLM_CORPUS_OUTPUT="$available_corpus" \
  bash scripts/build_public_mlm_corpus.sh

echo "$available_corpus"
