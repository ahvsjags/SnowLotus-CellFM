#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE155304
export SNOWCELL_GEO_DATASET_ID=geo_gse155304_arabidopsis_thaliana_single_cell_level_analysis_arabidopsis
export SNOWCELL_GEO_SPECIES='Arabidopsis thaliana'
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
