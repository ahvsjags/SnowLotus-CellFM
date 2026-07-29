#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
SESSION="${SNOWCELL_MLM_V0_4_WATCHDOG_SESSION:-snowcell_mlm_public_expansion_v0_4_after_v0_3_watchdog}"

cd "${PROJECT_DIR}"
mkdir -p logs
chmod +x scripts/watch_public_mlm_v0_4_after_v0_3.sh scripts/build_public_mlm_plus_corpus.sh

if tmux has-session -t "=${SESSION}" 2>/dev/null; then
  echo "SnowLotus v0.4 after-v0.3 watchdog already running: ${SESSION}"
else
  tmux new-session -d -s "${SESSION}" \
    "cd '${PROJECT_DIR}' && bash scripts/watch_public_mlm_v0_4_after_v0_3.sh >> logs/mlm_public_expansion_v0_4_after_v0_3_watchdog.log 2>&1"
  echo "started SnowLotus v0.4 after-v0.3 watchdog: ${SESSION}"
fi
tmux ls
