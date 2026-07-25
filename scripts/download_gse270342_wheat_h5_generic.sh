#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE270342
export SNOWCELL_GEO_DATASET_ID=wheat_soil_root_atlas
export SNOWCELL_GEO_SPECIES="Triticum aestivum"
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_SAMPLE_REGEX="${SNOWCELL_GSE270342_REGEX:-filtered_feature_bc_matrix\\.h5$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE270342_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_h5_subset.sh"
