#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export PATH="/root/miniconda3/envs/myconda/bin:$PATH"

mkdir -p data/public_discovery logs
stamp="$(date +%Y%m%d_%H%M%S)"
retmax="${SNOWCELL_NCBI_DISCOVERY_RETMAX:-50}"
tsv_output="data/public_discovery/ncbi_discovery_${stamp}.tsv"
json_output="data/public_discovery/ncbi_discovery_${stamp}.json"
log_output="logs/ncbi_public_discovery_${stamp}.log"

python scripts/discover_ncbi_public_datasets.py \
  --retmax "$retmax" \
  --output-tsv "$tsv_output" \
  --output-json "$json_output" \
  2>&1 | tee -a "$log_output"

echo "$tsv_output"
echo "$json_output"
