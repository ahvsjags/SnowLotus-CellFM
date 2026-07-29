#!/usr/bin/env bash
set -euo pipefail

cd /mnt/snowlotus_cellfm
source .venv/bin/activate 2>/dev/null || true

export SNOWCELL_GEO_ACCESSION=GSE155304
export SNOWCELL_GEO_DATASET_ID=geo_gse155304_arabidopsis_thaliana_single_cell_level_analysis_arabidopsis
export SNOWCELL_GEO_SPECIES="Arabidopsis thaliana"
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_PAGE_PATTERN='rnaseq_integration[.]rds[.]gz$'
export SNOWCELL_GEO_MAX_FILES=1
export SNOWCELL_GEO_PARALLEL_JOBS=1
export SNOWCELL_GEO_CONNECTIONS=2
export SNOWCELL_GEO_SPLITS=2

bash scripts/download_geo_page_rds_subset.sh
