#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
SESSION="${SNOWCELL_BENCHMARK_REFRESH_SESSION:-snowcell_checkpoint_benchmark_refresh_watchdog}"
LOG="${PROJECT_DIR}/logs/checkpoint_benchmark_refresh_watchdog.log"

cd "${PROJECT_DIR}"
mkdir -p logs

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "watchdog already running: ${SESSION}"
  exit 0
fi

tmux new-session -d -s "${SESSION}" \
  "cd '${PROJECT_DIR}' && bash scripts/watch_checkpoint_benchmark_refresh.sh >> '${LOG}' 2>&1"
echo "started ${SESSION}"
