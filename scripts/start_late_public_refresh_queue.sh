#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
SESSION="${SNOWCELL_LATE_REFRESH_QUEUE_SESSION:-snowcell_late_public_refresh_queue}"

cd "${PROJECT_DIR}"
mkdir -p logs

if tmux has-session -t "=${SESSION}" 2>/dev/null; then
  echo "late refresh queue already running in tmux: ${SESSION}"
  exit 0
fi

tmux new-session -d -s "${SESSION}" \
  "cd '${PROJECT_DIR}' && bash scripts/queue_late_public_mlm_refresh.sh >> logs/late_public_refresh_queue.log 2>&1"
echo "started ${SESSION}"
