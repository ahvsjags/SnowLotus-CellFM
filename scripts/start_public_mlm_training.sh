#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_MLM_SESSION:-snowcell_mlm_public_expansion}"
config="${SNOWCELL_MLM_CONFIG:-configs/foundation_5090_mlm_public_expansion.yaml}"
stamp="$(date +%Y%m%d_%H%M%S)"
log_path="logs/mlm_public_expansion_${stamp}.log"

cd "$project_dir"
mkdir -p logs outputs

if tmux has-session -t "$session" 2>/dev/null; then
  echo "public MLM training already running: $session"
  tmux ls
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && . .venv/bin/activate && snowcell train --config '$config' --device cuda >> '$log_path' 2>&1; bash scripts/run_strict_benchmark_audits.sh >> '$log_path' 2>&1; bash scripts/generate_publication_package.sh >> '$log_path' 2>&1"

echo "started public MLM training: $session"
echo "log: $log_path"
tmux ls
