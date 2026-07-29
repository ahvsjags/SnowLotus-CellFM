#!/usr/bin/env bash
set -euo pipefail

project_dir="${1:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_SAUSSUREA_METADATA_SESSION:-snowcell_saussurea_metadata}"
stamp="$(date +%Y%m%d_%H%M%S)"
log_path="${project_dir}/logs/saussurea_metadata_${stamp}.log"

mkdir -p "${project_dir}/logs"

if tmux has-session -t "${session}" 2>/dev/null; then
  echo "tmux session already running: ${session}"
  exit 0
fi

tmux new-session -d -s "${session}" \
  "cd '${project_dir}' && bash scripts/collect_saussurea_supporting_metadata.sh 2>&1 | tee '${log_path}'; bash scripts/generate_publication_package.sh 2>&1 | tee -a '${log_path}'"

echo "started ${session}"
echo "${log_path}"
