#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
WRAPPER="scripts/generated_geo_promotion_downloads/download_gse226826_geo_gse226826_arabidopsis_thaliana_time_resolved_single_cell_spatial.sh"
LOG="logs/geo_promotion_gse226826.log"

cd "${PROJECT_DIR}"
mkdir -p logs
source .venv/bin/activate 2>/dev/null || true

set +e
bash "${WRAPPER}" 2>&1 | tee -a "${LOG}"
wrapper_rc=${PIPESTATUS[0]}
set -e

bash scripts/generate_publication_package.sh || true
bash scripts/sync_github_release_repo.sh || true

exit "${wrapper_rc}"
