#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
SESSION="${SNOWCELL_GSE226826_WATCHDOG_SESSION:-snowcell_geo_promotion_gse226826_watchdog}"
LOG="${PROJECT_DIR}/logs/geo_promotion_gse226826_watchdog.log"

cd "${PROJECT_DIR}"
mkdir -p logs

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session already running: ${SESSION}"
else
  tmux new-session -d -s "${SESSION}" "cd '${PROJECT_DIR}' && bash scripts/watch_geo_promotion_gse226826.sh"
  echo "started tmux session: ${SESSION}"
fi

tmux ls | grep "${SESSION}" || true
tail -60 "${LOG}" 2>/dev/null || true
