#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE325371
export SNOWCELL_GEO_DATASET_ID=tomato_salt_idioblast_atlas
export SNOWCELL_GEO_SPECIES="Solanum lycopersicum"
export SNOWCELL_GEO_TISSUE="leaf_salt_stress_idioblast"
export SNOWCELL_GEO_FEATURE_COLUMN="${SNOWCELL_GSE325371_FEATURE_COLUMN:-0}"
export SNOWCELL_GEO_LABEL="${SNOWCELL_GSE325371_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GSE325371_COARSE_LABEL:-unannotated}"

bash "$(dirname "$0")/download_geo_raw_tar_mtx_subset.sh"
