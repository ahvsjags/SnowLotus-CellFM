#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
CONFIG="${CONFIG:-${PROJECT_DIR}/configs/plant_general_annotation_public_plants_v1_4090.yaml}"
CORPUS="${CORPUS:-${PROJECT_DIR}/data/plant_foundation_corpus_public_plants_v1.h5ad}"
OUTPUT="${OUTPUT:-${PROJECT_DIR}/outputs/plant_general_annotation_public_plants_v1_4090}"
LOG="${LOG:-${PROJECT_DIR}/logs/plant_general_annotation_public_plants_v1_4090.log}"
PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"

cd "${PROJECT_DIR}"
mkdir -p "$(dirname "${LOG}")"
export PYTHONPATH="${PROJECT_DIR}/src:${PYTHONPATH:-}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

while [ ! -s "${CORPUS}" ]; do
  echo "[$(date)] waiting for public plant corpus: ${CORPUS}" >> "${LOG}"
  sleep "${SNOWCELL_ANNOTATION_WAIT_INTERVAL_SECONDS:-120}"
done

if [ -s "${OUTPUT}/best.pt" ]; then
  echo "[$(date)] annotation checkpoint already exists: ${OUTPUT}/best.pt" >> "${LOG}"
  exit 0
fi

echo "[$(date)] starting all-plant annotation-head training" >> "${LOG}"
"${PYTHON_BIN}" -X utf8 -m snowcell.cli train --config "${CONFIG}" --device cuda >> "${LOG}" 2>&1
echo "[$(date)] all-plant annotation-head training completed" >> "${LOG}"
