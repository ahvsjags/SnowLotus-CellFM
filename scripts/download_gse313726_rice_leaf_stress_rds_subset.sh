#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE313726
export SNOWCELL_GEO_DATASET_ID=rice_leaf_stress_snuc_atlas
export SNOWCELL_GEO_SPECIES="Oryza sativa"
export SNOWCELL_GEO_TISSUE=leaf
export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GSE313726_PATTERN:-(?i)OsLeafStressIntegrated.*\\.rds$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE313726_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_page_rds_subset.sh"
