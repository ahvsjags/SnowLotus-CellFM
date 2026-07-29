#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_MLM_V0_3_WATCHDOG_SESSION:-snowcell_mlm_public_expansion_v0_3_watchdog}"

cd "$project_dir"
chmod +x scripts/watch_public_mlm_v0_3.sh scripts/start_public_mlm_v0_3_training.sh

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "SnowLotus v0.3 watchdog already running: $session"
else
  tmux new-session -d -s "$session" "cd '$project_dir' && bash scripts/watch_public_mlm_v0_3.sh >> logs/mlm_public_expansion_v0_3_watchdog.log 2>&1"
  echo "started SnowLotus v0.3 watchdog: $session"
fi
tmux ls
