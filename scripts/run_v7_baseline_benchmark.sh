#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
V7_ROOT="${SNOWCELL_V7_ROOT:-/root/snowlotus_public_plants_v7}"
CHECKPOINT="${SNOWCELL_V3_CHECKPOINT:-${PROJECT_DIR}/outputs/publication_package/checkpoints/v3_extended_4090/best.pt}"
OUTPUT="${SNOWCELL_V7_BENCHMARK_OUTPUT:-${V7_ROOT}/v3_on_v7_cross_species_benchmark.json}"
LOG="${SNOWCELL_V7_BENCHMARK_LOG:-${V7_ROOT}/v3_on_v7_cross_species_benchmark.log}"

cd "${PROJECT_DIR}"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
  scripts/benchmark_public_plants_v1.py \
  --project-dir "${PROJECT_DIR}" \
  --checkpoint "${CHECKPOINT}" \
  --data "${V7_ROOT}/plant_foundation_corpus_public_plants_v7.h5ad" \
  --manifest "${V7_ROOT}/corpus_manifest_public_plants_v7.tsv" \
  --output "${OUTPUT}" \
  --max-cells-per-dataset 256 \
  --batch-size 64 \
  --min-test-cells 20 \
  --device cuda \
  > "${LOG}" 2>&1

echo "v7 baseline benchmark complete: ${OUTPUT}"
