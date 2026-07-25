#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE311951
export SNOWCELL_GEO_DATASET_ID=stevia_leaf_secondary_metabolism_snuc
export SNOWCELL_GEO_SPECIES="Stevia rebaudiana"
export SNOWCELL_GEO_TISSUE=leaf
export SNOWCELL_GEO_FEATURE_COLUMN="${SNOWCELL_GSE311951_FEATURE_COLUMN:-0}"
export SNOWCELL_GEO_LABEL="${SNOWCELL_GSE311951_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GSE311951_COARSE_LABEL:-unannotated}"

bash "$(dirname "$0")/download_geo_raw_tar_mtx_subset.sh"
