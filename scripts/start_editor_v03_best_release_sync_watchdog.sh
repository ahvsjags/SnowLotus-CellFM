#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
SESSION="${SNOWCELL_EDITOR_V03_RELEASE_SESSION:-snowcell_editor_v03_best_release_watchdog}"
LOG="${PROJECT_DIR}/logs/editor_v03_best_release_watchdog.log"

cd "${PROJECT_DIR}"
mkdir -p logs

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "watchdog already running: ${SESSION}"
  exit 0
fi

tmux new-session -d -s "${SESSION}" \
  "cd '${PROJECT_DIR}' && bash scripts/watch_editor_v03_best_release_sync.sh >> '${LOG}' 2>&1"
echo "started ${SESSION}"
