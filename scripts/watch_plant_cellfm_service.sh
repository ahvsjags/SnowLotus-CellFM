#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
CHECKPOINT="${SNOWCELL_SERVICE_CHECKPOINT:-/root/snowlotus_cellfm_v8_lora_shared_4090/best.pt}"
DATA_ROOT="${SNOWCELL_SERVICE_DATA_ROOT:-/root/snowlotus_public_plants_v8}"
PORT="${SNOWCELL_SERVICE_PORT:-8000}"
LOG="${SNOWCELL_SERVICE_LOG:-/root/snowlotus_cellfm_v8_lora_shared_4090/service_watchdog.log}"

mkdir -p "$(dirname "${LOG}")"
while true; do
  if curl -fsS "http://127.0.0.1:${PORT}/health" 2>/dev/null | grep -q '"status": "ok"'; then
    sleep 30
    continue
  fi
  if pgrep -f "serve_snowlotus.py.*--port ${PORT}" >/dev/null 2>&1; then
    sleep 15
    continue
  fi
  echo "$(date -Is) restarting Plant-CellFM on port ${PORT}" >> "${LOG}"
  cd "${PROJECT_DIR}"
  nohup env PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u scripts/serve_snowlotus.py \
    --backbone-checkpoint "${CHECKPOINT}" \
    --annotation-checkpoint "${CHECKPOINT}" \
    --data-root "${DATA_ROOT}" \
    --adapter-registry "${PROJECT_DIR}/release_metadata/plant_species_adapters.json" \
    --project-root "${PROJECT_DIR}" \
    --host 127.0.0.1 --port "${PORT}" --device cuda \
    >> "${LOG}" 2>&1 < /dev/null &
  sleep 15
done
