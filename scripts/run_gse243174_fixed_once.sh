#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs

{
  echo "$(date -Is) GSE243174 fixed MTX run started"
  bash scripts/generated_geo_promotion_downloads/download_gse243174_geo_gse243174_glycine_max_single_cell_multiomic_profiling_soybean.sh
  echo "$(date -Is) GSE243174 fixed MTX conversion finished"
  bash scripts/generate_publication_package.sh
  echo "$(date -Is) GSE243174 publication package refresh finished"
} 2>&1 | tee -a logs/geo_promotion_gse243174.log
