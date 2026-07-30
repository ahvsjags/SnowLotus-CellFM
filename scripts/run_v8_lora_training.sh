#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
CONFIG="${SNOWCELL_V8_CONFIG:-${PROJECT_DIR}/configs/generated/foundation_public_plants_v8_lora_4090.yaml}"
OUTPUT="${SNOWCELL_V8_TRAIN_ROOT:-/root/snowlotus_cellfm_v8_lora_shared_4090}"
FULL_CORPUS="${SNOWCELL_V8_FULL_CORPUS:-/root/snowlotus_public_plants_v8/plant_foundation_corpus_public_plants_v8.h5ad}"
SHARED_CORPUS="${SNOWCELL_V8_SHARED_CORPUS:-/root/snowlotus_public_plants_v8/plant_foundation_corpus_public_plants_v8_shared_genes.h5ad}"
BASE_CHECKPOINT="${SNOWCELL_V3_CHECKPOINT:-${PROJECT_DIR}/outputs/publication_package/checkpoints/v3_extended_4090/best.pt}"

mkdir -p "${OUTPUT}"
cd "${PROJECT_DIR}"
if [ ! -s "${FULL_CORPUS}" ]; then
  echo "missing v8 corpus: ${FULL_CORPUS}" >&2
  exit 2
fi
if [ ! -s "${SHARED_CORPUS}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/filter_h5ad_to_checkpoint_genes.py \
    --input "${FULL_CORPUS}" \
    --output "${SHARED_CORPUS}" \
    --checkpoint "${BASE_CHECKPOINT}" \
    > "${OUTPUT}/shared_gene_filter.log" 2>&1
fi

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" \
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 -u \
  -m snowcell.cli train \
  --config "${CONFIG}" \
  --device cuda \
  > "${OUTPUT}/train.log" 2>&1

touch "${OUTPUT}/training_complete.marker"
echo "v8 LoRA training complete: ${OUTPUT}"
