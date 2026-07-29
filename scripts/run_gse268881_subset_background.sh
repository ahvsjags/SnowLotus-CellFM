#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
cd "${PROJECT_DIR}"
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs

stamp="$(date +%Y%m%d_%H%M%S)"
bash scripts/download_gse268881_subset.sh 2>&1 | tee -a "logs/gse268881_subset_${stamp}.log"
