#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
public_session="${SNOWCELL_PUBLIC_QUEUE_SESSION:-snowcell_public_mlm_queue}"
late_session="${SNOWCELL_LATE_QUEUE_SESSION:-snowcell_late_public_refresh_queue}"
scplantdb_session="${SNOWCELL_SCPLANTDB_QUEUE_SESSION:-snowcell_scplantdb_budgeted_h5ad_queue}"
queue_poll="${SNOWCELL_QUEUE_POLL_SECONDS:-300}"
late_poll="${SNOWCELL_LATE_QUEUE_POLL_SECONDS:-600}"
enable_scplantdb="${SNOWCELL_ENABLE_SCPLANTDB_QUEUE:-1}"

cd "$project_dir"
mkdir -p logs

if [ "${SNOWCELL_RESTART_PUBLIC_QUEUES:-0}" = "1" ]; then
  tmux kill-session -t "$public_session" 2>/dev/null || true
  tmux kill-session -t "$late_session" 2>/dev/null || true
  tmux kill-session -t "$scplantdb_session" 2>/dev/null || true
fi

if tmux has-session -t "$public_session" 2>/dev/null; then
  echo "public queue already running: $public_session"
else
  tmux new-session -d -s "$public_session" \
    "cd '$project_dir' && SNOWCELL_QUEUE_POLL_SECONDS='$queue_poll' bash scripts/queue_public_mlm_expansion.sh >> logs/public_mlm_queue.log 2>&1"
  echo "started public queue: $public_session"
fi

if tmux has-session -t "$late_session" 2>/dev/null; then
  echo "late queue already running: $late_session"
else
  tmux new-session -d -s "$late_session" \
    "cd '$project_dir' && SNOWCELL_LATE_QUEUE_POLL_SECONDS='$late_poll' bash scripts/queue_late_public_mlm_refresh.sh >> logs/late_public_refresh_queue.log 2>&1"
  echo "started late queue: $late_session"
fi

if [ "$enable_scplantdb" = "1" ]; then
  SNOWCELL_SCPLANTDB_QUEUE_SESSION="$scplantdb_session" \
    bash scripts/start_scplantdb_budgeted_h5ad_queue.sh
else
  echo "scPlantDB budgeted queue disabled: SNOWCELL_ENABLE_SCPLANTDB_QUEUE=$enable_scplantdb"
fi

tmux ls
