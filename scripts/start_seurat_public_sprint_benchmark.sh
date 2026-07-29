#!/usr/bin/env bash
set -euo pipefail

project_dir="${1:-/mnt/snowlotus_cellfm}"
config="${SNOWCELL_SEURAT_CONFIG:-configs/foundation_5090_public_sprint.yaml}"
name="${SNOWCELL_SEURAT_BENCHMARK_NAME:-seurat_public_sprint}"
session="${SNOWCELL_SEURAT_SESSION:-snowcell_seurat_public_sprint}"
export_dir="outputs/external_benchmarks/${name}_split"
output_json="outputs/external_benchmarks/${name}.json"
stamp="$(date +%Y%m%d_%H%M%S)"
log_path="${project_dir}/logs/${name}_${stamp}.log"

mkdir -p "${project_dir}/logs"

if tmux has-session -t "${session}" 2>/dev/null; then
  echo "tmux session already running: ${session}"
  exit 0
fi

tmux new-session -d -s "${session}" \
  "cd '${project_dir}' && source .venv/bin/activate 2>/dev/null || true; mkdir -p outputs/external_benchmarks; python scripts/export_seurat_benchmark_split.py --config '${config}' --output-dir '${export_dir}' 2>&1 | tee '${log_path}'; Rscript scripts/run_seurat_label_transfer_benchmark.R --input-dir '${export_dir}' --output-json '${output_json}' 2>&1 | tee -a '${log_path}'; bash scripts/generate_publication_package.sh 2>&1 | tee -a '${log_path}'"

echo "started ${session}"
echo "${log_path}"
