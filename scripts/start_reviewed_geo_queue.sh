#!/usr/bin/env bash
set -euo pipefail

cd /root/snowlotus-cellfm
session="${SNOWCELL_REVIEWED_GEO_QUEUE_SESSION:-snowcell_reviewed_geo_download_queue}"
log_path="${SNOWCELL_REVIEWED_GEO_QUEUE_LOG:-logs/reviewed_geo_download_queue.log}"

mkdir -p logs

if tmux has-session -t "$session" 2>/dev/null; then
  echo "reviewed GEO queue already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd /root/snowlotus-cellfm && bash scripts/queue_reviewed_geo_downloads.sh >> '$log_path' 2>&1"
echo "reviewed GEO queue started: $session"
echo "log: $log_path"
