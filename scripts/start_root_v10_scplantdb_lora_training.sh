#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/root/snowlotus_cellfm_v10}"
session="${SNOWCELL_ROOT_V10_SCPLANTDB_SESSION:-snowcell_root_v10_scplantdb_lora}"
python_bin="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
config="${SNOWCELL_ROOT_V10_SCPLANTDB_CONFIG:-configs/generated/foundation_public_plants_v10_scplantdb_root_lora_4090.yaml}"
log_dir="${SNOWCELL_ROOT_V10_SCPLANTDB_LOG_DIR:-${project_dir}/logs}"
stamp="$(date +%Y%m%d_%H%M%S)"
log_path="${log_dir}/root_v10_scplantdb_lora_${stamp}.log"

cd "$project_dir"
mkdir -p "$log_dir" /root/snowlotus_cellfm_v10_scplantdb_lora_4090

if [ ! -s "data/plant_foundation_corpus_scplantdb_v10_root.h5ad" ]; then
  echo "missing root v10 scPlantDB corpus: data/plant_foundation_corpus_scplantdb_v10_root.h5ad" >&2
  exit 2
fi

if tmux has-session -t "=${session}" 2>/dev/null; then
  echo "root v10 scPlantDB LoRA training already running: ${session}"
  echo "latest logs:"
  ls -1t "${log_dir}"/root_v10_scplantdb_lora_*.log 2>/dev/null | head -3 || true
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && export PYTHONPATH=src && '$python_bin' -m snowcell.cli train --config '$config' --device cuda >> '$log_path' 2>&1"

echo "started root v10 scPlantDB LoRA training: ${session}"
echo "config: ${config}"
echo "log: ${log_path}"
