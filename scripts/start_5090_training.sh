#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs

stamp="$(date +%Y%m%d_%H%M%S)"
log="logs/snowcell_top_journal_${stamp}.log"
session="snowcell_5090"
cmd="bash scripts/top_journal_pipeline.sh 2>&1 | tee ${log}"

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "${session}" 2>/dev/null; then
    echo "tmux session already exists: ${session}"
    echo "Attach with: tmux attach -t ${session}"
    exit 0
  fi
  tmux new-session -d -s "${session}" "${cmd}"
  echo "Started tmux session: ${session}"
  echo "Attach: tmux attach -t ${session}"
  echo "Log: ${log}"
else
  nohup bash -lc "${cmd}" >/dev/null 2>&1 &
  echo "tmux not found; started background job with nohup"
  echo "PID: $!"
  echo "Log: ${log}"
fi
