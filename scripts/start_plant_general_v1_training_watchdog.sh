#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
CORPUS="${PROJECT_DIR}/data/plant_foundation_corpus_public_plants_v1.h5ad"
CONFIG="${PROJECT_DIR}/configs/plant_general_foundation_public_plants_v1_4090.yaml"
OUTPUT="${PROJECT_DIR}/outputs/plant_general_foundation_public_plants_v1_4090"
LOG="${PROJECT_DIR}/logs/plant_general_foundation_public_plants_v1_4090.log"
PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
INTERVAL_SECONDS="${SNOWCELL_TRAIN_WAIT_INTERVAL_SECONDS:-120}"

cd "${PROJECT_DIR}"
mkdir -p "$(dirname "${LOG}")"
export PYTHONPATH="${PROJECT_DIR}/src:${PYTHONPATH:-}"

while [ ! -s "${CORPUS}" ]; do
  echo "[$(date)] waiting for completed corpus: ${CORPUS}" >> "${LOG}"
  sleep "${INTERVAL_SECONDS}"
done

if [ -s "${OUTPUT}/best.pt" ]; then
  echo "[$(date)] training already complete: ${OUTPUT}/best.pt" >> "${LOG}"
  exit 0
fi

echo "[$(date)] starting Plant-CellFM public-plants v1 training" >> "${LOG}"
"${PYTHON_BIN}" -m snowcell.cli train --config "${CONFIG}" --device cuda 2>&1 | tee -a "${LOG}"
