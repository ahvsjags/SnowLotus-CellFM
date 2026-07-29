#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
cd "${PROJECT_DIR}"
source .venv/bin/activate 2>/dev/null || true

manifest="${SNOWCELL_FULL_ON_DISK_MANIFEST:-data/corpus_manifest_public_mlm_full_on_disk.tsv}"
output="${SNOWCELL_FULL_ON_DISK_OUTPUT:-data/plant_foundation_corpus_public_mlm_full_on_disk.h5ad}"
summary="${SNOWCELL_FULL_ON_DISK_SUMMARY:-outputs/publication_package/public_mlm_full_on_disk_manifest_summary.json}"
work_dir="${SNOWCELL_FULL_ON_DISK_WORK_DIR:-outputs/on_disk_corpus/public_mlm_full}"
max_loaded_elems="${SNOWCELL_FULL_ON_DISK_MAX_LOADED_ELEMS:-25000000}"

python scripts/build_public_mlm_corpus_on_disk.py \
  --base-manifest data/corpus_manifest_public_mlm.tsv \
  --manifest-output "${manifest}" \
  --output "${output}" \
  --summary-output "${summary}" \
  --work-dir "${work_dir}" \
  --max-loaded-elems "${max_loaded_elems}" \
  --reuse-shards \
  --keep-shards
