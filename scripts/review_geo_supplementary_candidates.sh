#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

mkdir -p data/public_discovery logs
stamp="$(date +%Y%m%d_%H%M%S)"
tsv_output="data/public_discovery/geo_supplementary_review_${stamp}.tsv"
json_output="data/public_discovery/geo_supplementary_review_${stamp}.json"
file_tsv_output="data/public_discovery/geo_supplementary_files_${stamp}.tsv"
file_json_output="data/public_discovery/geo_supplementary_files_${stamp}.json"
log_output="logs/geo_supplementary_review_${stamp}.log"
latest_discovery="$(ls -t data/public_discovery/ncbi_discovery_*.tsv 2>/dev/null | head -1 || true)"
discovery_args=()
if [ -n "$latest_discovery" ]; then
  discovery_args=(
    --discovery-tsv "$latest_discovery"
    --max-discovery-gse "${SNOWCELL_GEO_REVIEW_MAX_DISCOVERY_GSE:-25}"
  )
fi

python scripts/review_geo_supplementary_candidates.py \
  --manifest data/public_dataset_manifest.tsv \
  --status discovery_candidate \
  --status download_candidate \
  "${discovery_args[@]}" \
  --output-tsv "$tsv_output" \
  --output-json "$json_output" \
  --file-output-tsv "$file_tsv_output" \
  --file-output-json "$file_json_output" \
  2>&1 | tee -a "$log_output"

echo "$tsv_output"
echo "$json_output"
echo "$file_tsv_output"
echo "$file_json_output"
