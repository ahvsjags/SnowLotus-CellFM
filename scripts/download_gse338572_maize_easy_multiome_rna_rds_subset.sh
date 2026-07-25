#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE338572
export SNOWCELL_GEO_DATASET_ID=maize_easy_multiome_seedling
export SNOWCELL_GEO_SPECIES="Zea mays"
export SNOWCELL_GEO_TISSUE=seedling
export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GSE338572_PATTERN:-(?i)eMultiRNA.*\\.rds$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE338572_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_page_rds_subset.sh"
