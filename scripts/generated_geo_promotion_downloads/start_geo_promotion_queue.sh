#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
session="${SNOWCELL_GEO_PROMOTION_QUEUE_SESSION:-snowcell_geo_promotion_download_queue}"
log_path="${SNOWCELL_GEO_PROMOTION_QUEUE_LOG:-logs/geo_promotion_download_queue.log}"
restart="${SNOWCELL_GEO_PROMOTION_QUEUE_RESTART:-0}"

mkdir -p logs

if tmux has-session -t "$session" 2>/dev/null; then
  if [ "$restart" = "1" ]; then
    echo "GEO promotion queue restarting supervisor: $session"
    tmux kill-session -t "$session"
  else
  echo "GEO promotion queue already running: $session"
  exit 0
  fi
fi

tmux new-session -d -s "$session" \
  "cd /root/snowlotus-cellfm && bash scripts/generated_geo_promotion_downloads/queue_geo_promotion_downloads.sh >> '$log_path' 2>&1"
echo "GEO promotion queue started: $session"
echo "log: $log_path"
