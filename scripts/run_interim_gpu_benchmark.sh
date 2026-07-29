#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/mnt/snowlotus_cellfm"
PYTHON_BIN="/root/miniconda3/envs/myconda/bin/python"
TRAIN_DIR="/root/snowlotus_cellfm_interim_gpu_4090"
DATA="/root/snowlotus_public_plants_v3_seed_fixed/plant_foundation_corpus_public_plants_v3_seed.h5ad"
MANIFEST="/root/snowlotus_public_plants_v3_seed_fixed/corpus_manifest_public_plants_v3_seed.tsv"

mkdir -p "${TRAIN_DIR}"
cd "${PROJECT_DIR}"
export PATH="$(dirname "${PYTHON_BIN}"):${PATH}"
export PYTHONPATH=src

exec "${PYTHON_BIN}" -u scripts/benchmark_public_plants_v1.py \
  --project-dir "${PROJECT_DIR}" \
  --checkpoint "${TRAIN_DIR}/best.pt" \
  --data "${DATA}" \
  --manifest "${MANIFEST}" \
  --output "${TRAIN_DIR}/interim_cross_species_benchmark.json" \
  --max-cells-per-dataset 256 \
  --batch-size 64 \
  --device cuda \
  >> "${TRAIN_DIR}/benchmark.log" 2>&1
