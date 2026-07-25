#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/root/snowlotus-cellfm}"
session="${SNOWCELL_GSE226097_WATCHDOG_SESSION:-snowcell_gse226097_lifecycle_watchdog}"
log_path="${project_dir}/logs/gse226097_lifecycle_watchdog.log"

cd "$project_dir"
mkdir -p logs

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "GSE226097 lifecycle watchdog already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && bash scripts/watch_gse226097_lifecycle_subset.sh >> '$log_path' 2>&1"

echo "started GSE226097 lifecycle watchdog: $session"
echo "log: $log_path"
