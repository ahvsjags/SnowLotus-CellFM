#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_PUBLIC_DATA_WATCHDOG_SESSION:-snowcell_public_data_watchdog}"
log_path="${SNOWCELL_PUBLIC_DATA_WATCHDOG_LOG:-${project_dir}/logs/public_data_watchdog.log}"
poll_seconds="${SNOWCELL_PUBLIC_DATA_WATCHDOG_POLL_SECONDS:-180}"

cd "$project_dir"
mkdir -p logs

if tmux has-session -t "$session" 2>/dev/null; then
  echo "public data watchdog already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && SNOWCELL_PUBLIC_DATA_WATCHDOG_POLL_SECONDS='$poll_seconds' bash scripts/queue_public_data_watchdog.sh >> '$log_path' 2>&1"

echo "started public data watchdog: $session"
echo "log: $log_path"
echo "poll_seconds=$poll_seconds"
