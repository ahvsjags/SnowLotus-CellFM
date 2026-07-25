#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE300264
export SNOWCELL_GEO_DATASET_ID=arabidopsis_scrna_method_benchmark
export SNOWCELL_GEO_SPECIES="Arabidopsis thaliana"
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GSE300264_PATTERN:-(?i)merged_seurat.*\\.rds$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE300264_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_page_rds_subset.sh"
