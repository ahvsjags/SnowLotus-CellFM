#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
SESSION="${SNOWCELL_RELEASE_SYNC_SESSION:-snowcell_github_release_sync_watchdog}"
LOG="${PROJECT_DIR}/logs/github_release_sync_watchdog.log"

cd "${PROJECT_DIR}"
mkdir -p logs

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session already running: ${SESSION}"
else
  tmux new-session -d -s "${SESSION}" "cd '${PROJECT_DIR}' && bash scripts/watch_github_release_sync.sh >> '${LOG}' 2>&1"
  echo "started tmux session: ${SESSION}"
fi

tmux ls | grep "${SESSION}" || true
tail -40 "${LOG}" 2>/dev/null || true
