#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
BACKBONE_CHECKPOINT="${BACKBONE_CHECKPOINT:-${PROJECT_DIR}/outputs/plant_general_foundation_public_plants_v1_4090/best.pt}"
ANNOTATION_CHECKPOINT="${ANNOTATION_CHECKPOINT:-${PROJECT_DIR}/outputs/plant_general_annotation_public_plants_v1_cell_split_4090/best.pt}"
DATA_ROOT="${DATA_ROOT:-${PROJECT_DIR}/data/public/scPlantDB_h5ad}"
ADAPTER_REGISTRY="${ADAPTER_REGISTRY:-${PROJECT_DIR}/release_metadata/plant_species_adapters.json}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
DEVICE="${DEVICE:-cuda}"
INTERVAL_SECONDS="${SNOWCELL_SERVICE_WATCH_INTERVAL_SECONDS:-30}"
LOG="${SNOWCELL_SERVICE_WATCH_LOG:-${PROJECT_DIR}/logs/service_watchdog.log}"
SERVICE_LOG="${SNOWCELL_SERVICE_LOG:-${PROJECT_DIR}/logs/service_watchdog_server.log}"
PID_FILE="${SNOWCELL_SERVICE_PID_FILE:-${PROJECT_DIR}/logs/service_watchdog.pid}"

mkdir -p "${PROJECT_DIR}/logs"
cd "${PROJECT_DIR}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" >> "${LOG}"
}

find_service_pid() {
  pgrep -f "serve_snowlotus.py.*--port ${PORT}" | head -n 1 || true
}

service_is_healthy() {
  curl --connect-timeout 3 --max-time 8 -fsS "http://${HOST}:${PORT}/health" >/dev/null 2>&1
}

remember_existing_service() {
  local pid
  pid="$(find_service_pid)"
  if [ -n "${pid}" ]; then
    printf '%s\n' "${pid}" > "${PID_FILE}"
    log "adopted existing healthy service pid=${pid}"
  fi
}

stop_stale_service() {
  local pid
  pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
  if [ -z "${pid}" ]; then
    pid="$(find_service_pid)"
  fi
  if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
    log "stopping unhealthy service pid=${pid}"
    kill "${pid}" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "${pid}" 2>/dev/null || return 0
      sleep 1
    done
    kill -9 "${pid}" 2>/dev/null || true
  fi
  rm -f "${PID_FILE}"
}

start_service() {
  log "starting Plant-CellFM service on ${HOST}:${PORT}"
  PYTHONPATH=src nohup "${PYTHON_BIN}" -X utf8 scripts/serve_snowlotus.py \
    --backbone-checkpoint "${BACKBONE_CHECKPOINT}" \
    --annotation-checkpoint "${ANNOTATION_CHECKPOINT}" \
    --data-root "${DATA_ROOT}" \
    --adapter-registry "${ADAPTER_REGISTRY}" \
    --project-root "${PROJECT_DIR}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --device "${DEVICE}" > "${SERVICE_LOG}" 2>&1 &
  printf '%s\n' "$!" > "${PID_FILE}"
}

log "watchdog started"
while true; do
  if service_is_healthy; then
    remember_existing_service
  else
    log "health check failed"
    stop_stale_service
    start_service
    sleep 5
    if service_is_healthy; then
      remember_existing_service
      log "service recovered"
    else
      log "service is still unavailable; retrying"
    fi
  fi
  sleep "${INTERVAL_SECONDS}"
done
