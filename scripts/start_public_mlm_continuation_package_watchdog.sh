#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/root/snowlotus-cellfm}"
session="${SNOWCELL_MLM_CONTINUATION_PACKAGE_SESSION:-snowcell_publication_package_watchdog_continuation}"
run_id="${SNOWCELL_MLM_CONTINUATION_PACKAGE_RUN_ID:-foundation_5090_mlm_public_expansion_continuation}"
output_dir="${SNOWCELL_MLM_CONTINUATION_PACKAGE_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_expansion_continuation}"
poll_seconds="${SNOWCELL_MLM_CONTINUATION_PACKAGE_POLL_SECONDS:-300}"
log_dir="${SNOWCELL_MLM_CONTINUATION_LOG_DIR:-logs}"
log_path="${project_dir}/${log_dir}/publication_package_watchdog_continuation.log"

cd "$project_dir"
mkdir -p "$log_dir"

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "continuation package watchdog already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && SNOWCELL_PACKAGE_REFRESH_SESSION='$session' SNOWCELL_PACKAGE_REFRESH_RUN_ID='$run_id' SNOWCELL_PACKAGE_REFRESH_OUTPUT_DIR='$output_dir' SNOWCELL_PACKAGE_REFRESH_POLL_SECONDS='$poll_seconds' bash scripts/watch_publication_package_refresh.sh >> '$log_path' 2>&1"

echo "started continuation package watchdog: $session"
echo "log: $log_path"
