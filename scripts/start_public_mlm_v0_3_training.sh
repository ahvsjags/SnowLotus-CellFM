#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_MLM_V0_3_SESSION:-snowcell_mlm_public_expansion_v0_3}"
config="${SNOWCELL_MLM_V0_3_CONFIG:-configs/generated/foundation_5090_mlm_public_expansion_continuation_v0_3.yaml}"
device="${SNOWCELL_MLM_V0_3_DEVICE:-cuda}"
log_dir="${SNOWCELL_MLM_V0_3_LOG_DIR:-logs}"

cd "$project_dir"
source .venv/bin/activate 2>/dev/null || true
mkdir -p "$log_dir"

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "SnowLotus v0.3 MLM training already running: $session"
  tmux ls
  exit 0
fi

stamp="$(date +%Y%m%d_%H%M%S)"
log_path="$log_dir/mlm_public_expansion_v0_3_${stamp}.log"

tmux new-session -d -s "$session" \
  "cd '$project_dir' && source .venv/bin/activate 2>/dev/null || true; snowcell train --config '$config' --device '$device' 2>&1 | tee '$log_path'; bash scripts/generate_publication_package.sh 2>&1 | tee -a '$log_path'"

echo "started SnowLotus v0.3 MLM training: $session"
echo "config: $config"
echo "log: $log_path"
tmux ls
