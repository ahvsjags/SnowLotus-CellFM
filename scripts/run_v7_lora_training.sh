#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
CONFIG="${SNOWCELL_V7_CONFIG:-${PROJECT_DIR}/configs/generated/foundation_public_plants_v7_lora_4090.yaml}"
OUTPUT="${SNOWCELL_V7_TRAIN_ROOT:-/root/snowlotus_cellfm_v7_lora_4090}"

mkdir -p "${OUTPUT}"
cd "${PROJECT_DIR}"
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u -X utf8 \
  -m snowcell.cli train \
  --config "${CONFIG}" \
  --device cuda \
  > "${OUTPUT}/train.log" 2>&1

touch "${OUTPUT}/training_complete.marker"
echo "v7 LoRA training complete: ${OUTPUT}"
