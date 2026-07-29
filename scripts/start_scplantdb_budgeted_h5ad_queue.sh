#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_SCPLANTDB_QUEUE_SESSION:-snowcell_scplantdb_budgeted_h5ad_queue}"
log_path="${SNOWCELL_SCPLANTDB_QUEUE_LOG:-${project_dir}/logs/scplantdb_budgeted_h5ad_queue.log}"
max_bytes="${SNOWCELL_SCPLANTDB_MAX_BYTES:-500000000}"
max_total_bytes="${SNOWCELL_SCPLANTDB_MAX_TOTAL_BYTES:-3000000000}"
max_datasets="${SNOWCELL_SCPLANTDB_MAX_DATASETS:-32}"
min_cells="${SNOWCELL_SCPLANTDB_MIN_CELLS:-0}"
probe_timeout="${SNOWCELL_SCPLANTDB_PROBE_TIMEOUT:-15}"
refresh_package="${SNOWCELL_SCPLANTDB_REFRESH_PACKAGE:-1}"

cd "$project_dir"
mkdir -p logs

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "scPlantDB budgeted H5AD queue already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && SNOWCELL_SCPLANTDB_MAX_BYTES='$max_bytes' SNOWCELL_SCPLANTDB_MAX_TOTAL_BYTES='$max_total_bytes' SNOWCELL_SCPLANTDB_MAX_DATASETS='$max_datasets' SNOWCELL_SCPLANTDB_MIN_CELLS='$min_cells' SNOWCELL_SCPLANTDB_PROBE_TIMEOUT='$probe_timeout' SNOWCELL_SCPLANTDB_REFRESH_PACKAGE='$refresh_package' bash scripts/queue_scplantdb_budgeted_h5ad_download.sh >> '$log_path' 2>&1"

echo "started scPlantDB budgeted H5AD queue: $session"
echo "log: $log_path"
echo "budgets: max_bytes=$max_bytes max_total_bytes=$max_total_bytes max_datasets=$max_datasets min_cells=$min_cells"
