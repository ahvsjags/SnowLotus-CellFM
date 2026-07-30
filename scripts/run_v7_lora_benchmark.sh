#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
V7_ROOT="${SNOWCELL_V7_ROOT:-/root/snowlotus_public_plants_v7}"
TRAIN_ROOT="${SNOWCELL_V7_TRAIN_ROOT:-/root/snowlotus_cellfm_v7_lora_shared_4090}"
SHARED_CORPUS="${SNOWCELL_V7_SHARED_CORPUS:-${V7_ROOT}/plant_foundation_corpus_public_plants_v7_shared_genes.h5ad}"
SUBSET="${SNOWCELL_V7_SHARED_SUBSET:-${V7_ROOT}/v7_benchmark_subset_256_shared_genes.h5ad}"
CHECKPOINT="${SNOWCELL_V7_CHECKPOINT:-${TRAIN_ROOT}/best.pt}"
OUTPUT="${SNOWCELL_V7_CANDIDATE_BENCHMARK:-${TRAIN_ROOT}/v7_lora_cross_species_benchmark.json}"
LOG="${SNOWCELL_V7_CANDIDATE_BENCHMARK_LOG:-${TRAIN_ROOT}/benchmark.log}"

cd "${PROJECT_DIR}"
if [ ! -s "${SUBSET}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/materialize_h5ad_benchmark_subset.py \
    --input "${SHARED_CORPUS}" \
    --output "${SUBSET}" \
    --max-cells-per-dataset 256 \
    --seed 20260729 \
    > "${TRAIN_ROOT}/benchmark_subset.log" 2>&1
fi

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
  scripts/benchmark_public_plants_v1.py \
  --project-dir "${PROJECT_DIR}" \
  --checkpoint "${CHECKPOINT}" \
  --data "${SUBSET}" \
  --manifest "${V7_ROOT}/corpus_manifest_public_plants_v7.tsv" \
  --output "${OUTPUT}" \
  --max-cells-per-dataset 256 \
  --batch-size 64 \
  --min-test-cells 20 \
  --device cuda \
  > "${LOG}" 2>&1

echo "v7 LoRA benchmark complete: ${OUTPUT}"
