#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE302041
export SNOWCELL_GEO_DATASET_ID=arabidopsis_lateral_root_founder_atlas
export SNOWCELL_GEO_SPECIES="Arabidopsis thaliana"
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GSE302041_PATTERN:-(?i)LRFC.*\\.rds$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE302041_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_page_rds_subset.sh"
