#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE314252
export SNOWCELL_GEO_DATASET_ID=tomato_mycorrhiza_snuc_atlas
export SNOWCELL_GEO_SPECIES="Solanum lycopersicum"
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GSE314252_PATTERN:-(?i)seuratObj.*\\.rds$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE314252_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_page_rds_subset.sh"
