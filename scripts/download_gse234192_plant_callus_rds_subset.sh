#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE234192
export SNOWCELL_GEO_DATASET_ID=arabidopsis_callus_regeneration_scrna
export SNOWCELL_GEO_SPECIES="${SNOWCELL_GSE234192_SPECIES:-Arabidopsis thaliana}"
export SNOWCELL_GEO_TISSUE="callus_regeneration"
export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GSE234192_PATTERN:-processed\\.rds$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE234192_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_page_rds_subset.sh"
