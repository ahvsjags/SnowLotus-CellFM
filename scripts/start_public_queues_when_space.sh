#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_PUBLIC_QUEUE_SPACE_SESSION:-snowcell_public_queues_when_space}"
min_free_bytes="${SNOWCELL_MIN_FREE_BYTES:-21474836480}"
poll_seconds="${SNOWCELL_SPACE_QUEUE_POLL_SECONDS:-600}"
log_path="${SNOWCELL_SPACE_QUEUE_LOG:-${project_dir}/logs/public_queues_when_space.log}"

mkdir -p "${project_dir}/logs"

if tmux has-session -t "=${session}" 2>/dev/null; then
  echo "public queue space watcher already running: ${session}"
  echo "log: ${log_path}"
  exit 0
fi

tmux new-session -d -s "${session}" \
  "cd '${project_dir}' && mkdir -p logs; while true; do echo \"[\$(date)] checking disk before public queues\"; if SNOWCELL_MIN_FREE_BYTES='${min_free_bytes}' bash scripts/check_disk_budget.sh '${project_dir}'; then echo \"[\$(date)] disk budget satisfied; starting public queues\"; SNOWCELL_MIN_FREE_BYTES='${min_free_bytes}' bash scripts/start_public_queues.sh; exit 0; fi; df -h '${project_dir}' /root 2>/dev/null || true; echo \"[\$(date)] disk budget not met; sleeping ${poll_seconds}s\"; sleep '${poll_seconds}'; done >> '${log_path}' 2>&1"

echo "started public queue space watcher: ${session}"
echo "min_free_bytes: ${min_free_bytes}"
echo "poll_seconds: ${poll_seconds}"
echo "log: ${log_path}"
