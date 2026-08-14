#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
CONFIG="${SNOWCELL_V19_CONFIG:-${PROJECT_DIR}/configs/revision_v19_cross_species_contrastive_4090.yaml}"
OUTPUT_DIR="${SNOWCELL_V19_OUTPUT:-/root/snowlotus_cellfm_v19_contrastive_4090}"
LOG_DIR="${SNOWCELL_V19_LOG_DIR:-${OUTPUT_DIR}/logs}"
REPLAY_DATA="${SNOWCELL_V19_REPLAY_DATA:-}"
REPLAY_OUTPUT="${SNOWCELL_V19_REPLAY_OUTPUT:-${OUTPUT_DIR}/strict_replay}"

mkdir -p "${LOG_DIR}"
cd "${PROJECT_DIR}"
export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

SNOWCELL_PROJECT_DIR="${PROJECT_DIR}" \
SNOWCELL_PYTHON_BIN="${PYTHON_BIN}" \
SNOWCELL_V19_CONFIG="${CONFIG}" \
SNOWCELL_V19_OUTPUT="${OUTPUT_DIR}" \
SNOWCELL_V19_REPLAY_DATA="${REPLAY_DATA}" \
bash "${PROJECT_DIR}/scripts/preflight_revision_v19_4090.sh"

echo "[v19] project=${PROJECT_DIR}"
echo "[v19] config=${CONFIG}"
echo "[v19] output=${OUTPUT_DIR}"
"${PYTHON_BIN}" -u -m snowcell.cli train \
  --config "${CONFIG}" \
  --device cuda \
  2>&1 | tee "${LOG_DIR}/train_v19.log"

test -s "${OUTPUT_DIR}/best.pt"
test -s "${OUTPUT_DIR}/history.json"
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${OUTPUT_DIR}/training_complete.marker"
echo "[v19] training complete: ${OUTPUT_DIR}/best.pt"

if [[ -n "${REPLAY_DATA}" ]]; then
  test -s "${REPLAY_DATA}"
  "${PYTHON_BIN}" -u "${PROJECT_DIR}/scripts/evaluate_revision_v19_strict_replay.py" \
    --checkpoint "${OUTPUT_DIR}/best.pt" \
    --data "${REPLAY_DATA}" \
    --output-dir "${REPLAY_OUTPUT}" \
    --device cuda \
    2>&1 | tee "${LOG_DIR}/strict_replay_v19.log"
  test -s "${REPLAY_OUTPUT}/strict_replay.json"
  echo "[v19] strict replay complete: ${REPLAY_OUTPUT}/strict_replay.json"
else
  echo "[v19] strict replay skipped: set SNOWCELL_V19_REPLAY_DATA to the locked raw H5AD"
fi
