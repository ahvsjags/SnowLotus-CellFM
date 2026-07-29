#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
V5_ROOT="${SNOWCELL_V5_ROOT:-/root/snowlotus_public_plants_v5}"
V7_ROOT="${SNOWCELL_V7_ROOT:-/root/snowlotus_public_plants_v7}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
MAX_LOADED_ELEMS="${SNOWCELL_V7_MAX_LOADED_ELEMS:-100000000}"
MANIFEST="${V7_ROOT}/corpus_manifest_public_plants_v7.tsv"
SUMMARY="${V7_ROOT}/v7_manifest_audit.json"
CORPUS="${V7_ROOT}/plant_foundation_corpus_public_plants_v7.h5ad"

mkdir -p "${V7_ROOT}"
cd "${PROJECT_DIR}"

if [ ! -s "${MANIFEST}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/prepare_public_plants_expansion_manifest.py \
    --manifest "${V5_ROOT}/corpus_manifest_public_plants_v5.tsv" \
    --manifest "${PROJECT_DIR}/data/corpus_manifest.gse226149.tsv" \
    --manifest "${PROJECT_DIR}/data/corpus_manifest.gse273722.tsv" \
    --output "${MANIFEST}" \
    --summary-output "${SUMMARY}" \
    --project-root "${PROJECT_DIR}" \
    --require-files \
    --fail-on-missing \
    > "${V7_ROOT}/manifest.log" 2>&1
fi

if [ ! -s "${V7_ROOT}/public_plants_v7_summary.json" ] || [ ! -d "${CORPUS}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/build_public_mlm_corpus_on_disk.py \
    --base-manifest "${MANIFEST}" \
    --extra-manifest "${V5_ROOT}/empty_manifest.tsv" \
    --manifest-output "${MANIFEST}" \
    --output "${CORPUS}" \
    --work-dir "${V7_ROOT}/work" \
    --summary-output "${V7_ROOT}/public_plants_v7_summary.json" \
    --max-loaded-elems "${MAX_LOADED_ELEMS}" \
    --reuse-shards \
    > "${V7_ROOT}/build_v7.log" 2>&1
fi

touch "${V7_ROOT}/v7_corpus_complete.marker"
echo "v7 public plants corpus complete"
