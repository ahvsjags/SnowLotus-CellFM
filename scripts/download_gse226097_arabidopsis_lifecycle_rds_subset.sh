#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE226097
export SNOWCELL_GEO_DATASET_ID=arabidopsis_lifecycle_spatial_atlas
export SNOWCELL_GEO_SPECIES=Arabidopsis_thaliana
export SNOWCELL_GEO_TISSUE=multi_organ
export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GSE226097_PATTERN:-GSE226097_seedling_3d_relaxed_220711\\.rds$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE226097_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_page_rds_subset.sh"
