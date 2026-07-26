#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
SESSION="${SNOWCELL_FULL_ON_DISK_WATCHDOG_SESSION:-snowcell_public_mlm_full_on_disk_corpus}"
LOG="${PROJECT_DIR}/logs/public_mlm_full_on_disk_corpus.log"

cd "${PROJECT_DIR}"
mkdir -p logs
chmod +x scripts/build_public_mlm_corpus_on_disk.py scripts/build_public_mlm_full_on_disk_corpus.sh

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "full on-disk corpus build already running: ${SESSION}"
  exit 0
fi

tmux new-session -d -s "${SESSION}" \
  "cd '${PROJECT_DIR}' && bash scripts/build_public_mlm_full_on_disk_corpus.sh >> '${LOG}' 2>&1"
echo "started ${SESSION}"
tmux ls
