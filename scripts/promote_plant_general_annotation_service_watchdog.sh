#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
CHECKPOINT="${CHECKPOINT:-${PROJECT_DIR}/outputs/plant_general_annotation_public_plants_v1_sample_split_4090/best.pt}"
MARKER="${MARKER:-${PROJECT_DIR}/outputs/plant_general_annotation_public_plants_v1_sample_split_4090/service_promoted.marker}"
DONE_MARKER="${DONE_MARKER:-${PROJECT_DIR}/outputs/plant_general_annotation_public_plants_v1_sample_split_4090/training_complete.marker}"
LOG="${LOG:-${PROJECT_DIR}/logs/plant_general_annotation_service_promotion.log}"
INTERVAL_SECONDS="${SNOWCELL_SERVICE_WAIT_INTERVAL_SECONDS:-120}"

cd "${PROJECT_DIR}"
mkdir -p "$(dirname "${LOG}")"

while [ ! -s "${CHECKPOINT}" ] || [ ! -s "${DONE_MARKER}" ]; do
  echo "[$(date)] waiting for completed all-plant annotation head: ${CHECKPOINT}" >> "${LOG}"
  sleep "${INTERVAL_SECONDS}"
done

while [ ! -f "${MARKER}" ]; do
  echo "[$(date)] promoting all-plant annotation head" >> "${LOG}"
  tmux kill-session -t snowcell_service_final 2>/dev/null || true
  tmux new-session -d -s snowcell_service_final "cd ${PROJECT_DIR} && BACKBONE_CHECKPOINT=${PROJECT_DIR}/outputs/plant_general_foundation_public_plants_v1_4090/best.pt ANNOTATION_CHECKPOINT=${CHECKPOINT} bash scripts/start_snowlotus_service.sh > logs/service_final.log 2>&1"
  for _ in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
      printf '%s\n' "$(date -Is)" > "${MARKER}"
      exit 0
    fi
    sleep 5
  done
  echo "[$(date)] service health check failed; retrying" >> "${LOG}"
  sleep "${INTERVAL_SECONDS}"
done
