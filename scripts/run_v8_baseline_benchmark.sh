#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
V8_ROOT="${SNOWCELL_V8_ROOT:-/root/snowlotus_public_plants_v8}"
CHECKPOINT="${SNOWCELL_V3_CHECKPOINT:-${PROJECT_DIR}/outputs/publication_package/checkpoints/v3_extended_4090/best.pt}"
SHARED_CORPUS="${SNOWCELL_V8_SHARED_CORPUS:-${V8_ROOT}/plant_foundation_corpus_public_plants_v8_shared_genes.h5ad}"
SUBSET="${SNOWCELL_V8_SHARED_SUBSET:-${V8_ROOT}/v8_benchmark_subset_256_shared_genes.h5ad}"
OUTPUT="${SNOWCELL_V8_BASELINE_BENCHMARK:-${V8_ROOT}/v3_on_v8_shared_subset_cross_species_benchmark.json}"
LOG="${SNOWCELL_V8_BASELINE_BENCHMARK_LOG:-${V8_ROOT}/v3_on_v8_shared_subset_cross_species_benchmark.log}"

cd "${PROJECT_DIR}"
if [ ! -s "${SUBSET}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/materialize_h5ad_benchmark_subset.py \
    --input "${SHARED_CORPUS}" \
    --output "${SUBSET}" \
    --max-cells-per-dataset 256 \
    --seed 20260730 \
    > "${V8_ROOT}/benchmark_subset.log" 2>&1
fi

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 -u \
  scripts/benchmark_public_plants_v1.py \
  --project-dir "${PROJECT_DIR}" \
  --checkpoint "${CHECKPOINT}" \
  --data "${SUBSET}" \
  --manifest "${V8_ROOT}/corpus_manifest_public_plants_v8.tsv" \
  --output "${OUTPUT}" \
  --max-cells-per-dataset 256 \
  --batch-size 64 \
  --min-test-cells 20 \
  --device cuda \
  > "${LOG}" 2>&1

echo "v8 baseline benchmark complete: ${OUTPUT}"
