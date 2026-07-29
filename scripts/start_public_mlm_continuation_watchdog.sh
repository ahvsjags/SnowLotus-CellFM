#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_MLM_CONTINUATION_WATCHDOG_SESSION:-snowcell_mlm_public_expansion_continuation_watchdog}"
poll_seconds="${SNOWCELL_MLM_CONTINUATION_WATCHDOG_POLL_SECONDS:-600}"
log_dir="${SNOWCELL_MLM_CONTINUATION_LOG_DIR:-logs}"
log_path="${project_dir}/${log_dir}/mlm_public_expansion_continuation_watchdog.log"

cd "$project_dir"
mkdir -p "$log_dir"

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "public MLM continuation watchdog already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && SNOWCELL_MLM_CONTINUATION_WATCHDOG_POLL_SECONDS='$poll_seconds' bash scripts/watch_public_mlm_continuation.sh >> '$log_path' 2>&1"

echo "started public MLM continuation watchdog: $session"
echo "log: $log_path"
