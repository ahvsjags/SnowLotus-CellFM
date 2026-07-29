#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_PACKAGE_REFRESH_SESSION:-snowcell_publication_package_watchdog}"
poll_seconds="${SNOWCELL_PACKAGE_REFRESH_POLL_SECONDS:-300}"
log_dir="${SNOWCELL_PACKAGE_REFRESH_LOG_DIR:-logs}"
log_path="${project_dir}/${log_dir}/publication_package_watchdog.log"

cd "$project_dir"
mkdir -p "$log_dir"

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "publication package watchdog already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && SNOWCELL_PACKAGE_REFRESH_POLL_SECONDS='$poll_seconds' bash scripts/watch_publication_package_refresh.sh >> '$log_path' 2>&1"

echo "started publication package watchdog: $session"
