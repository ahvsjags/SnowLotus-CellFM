#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
CHECKPOINT="${PROJECT_DIR}/outputs/plant_general_foundation_public_plants_v1_4090/best.pt"
MARKER="${PROJECT_DIR}/outputs/plant_general_foundation_public_plants_v1_4090/service_promoted.marker"
LOG="${PROJECT_DIR}/logs/plant_general_v1_service_promotion.log"
INTERVAL_SECONDS="${SNOWCELL_SERVICE_WAIT_INTERVAL_SECONDS:-120}"

cd "${PROJECT_DIR}"
mkdir -p "$(dirname "${LOG}")"

while [ ! -s "${CHECKPOINT}" ]; do
  echo "[$(date)] waiting for new backbone: ${CHECKPOINT}" >> "${LOG}"
  sleep "${INTERVAL_SECONDS}"
done

if [ -f "${MARKER}" ]; then
  exit 0
fi

echo "[$(date)] promoting new backbone to Plant-CellFM service" >> "${LOG}"
tmux kill-session -t snowcell_service_final 2>/dev/null || true
tmux new-session -d -s snowcell_service_final "cd ${PROJECT_DIR} && BACKBONE_CHECKPOINT=${CHECKPOINT} bash scripts/start_snowlotus_service.sh > logs/service_final.log 2>&1"
printf '%s\n' "$(date -Is)" > "${MARKER}"
