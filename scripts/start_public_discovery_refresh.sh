#!/usr/bin/env bash
set -euo pipefail

project_dir="${1:-/root/snowlotus-cellfm}"
session="${SNOWCELL_PUBLIC_DISCOVERY_SESSION:-snowcell_public_discovery_refresh}"
retmax="${SNOWCELL_NCBI_DISCOVERY_RETMAX:-200}"
stamp="$(date +%Y%m%d_%H%M%S)"
log_path="${project_dir}/logs/public_discovery_refresh_${stamp}.log"

mkdir -p "${project_dir}/logs"

if tmux has-session -t "${session}" 2>/dev/null; then
  echo "public discovery refresh already running: ${session}"
  exit 0
fi

tmux new-session -d -s "${session}" \
  "cd '${project_dir}' && SNOWCELL_NCBI_DISCOVERY_RETMAX='${retmax}' bash scripts/discover_public_ncbi_data.sh 2>&1 | tee '${log_path}'; bash scripts/review_geo_supplementary_candidates.sh 2>&1 | tee -a '${log_path}'; bash scripts/generate_publication_package.sh 2>&1 | tee -a '${log_path}'; SNOWCELL_GEO_PROMOTION_QUEUE_RESTART=1 bash scripts/generated_geo_promotion_downloads/start_geo_promotion_queue.sh 2>&1 | tee -a '${log_path}'"

echo "public discovery refresh started: ${session}"
echo "retmax: ${retmax}"
echo "log: ${log_path}"
