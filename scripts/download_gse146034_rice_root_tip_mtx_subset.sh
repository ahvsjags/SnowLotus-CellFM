#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE146034
export SNOWCELL_GEO_DATASET_ID=rice_root_tip_atlas
export SNOWCELL_GEO_SPECIES="Oryza sativa"
export SNOWCELL_GEO_TISSUE=root_tip
export SNOWCELL_GEO_FEATURE_COLUMN="${SNOWCELL_GSE146034_FEATURE_COLUMN:-0}"
export SNOWCELL_GEO_LABEL="${SNOWCELL_GSE146034_LABEL:-unannotated_root_tip}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GSE146034_COARSE_LABEL:-unannotated_root_tip}"

bash "$(dirname "$0")/download_geo_raw_tar_mtx_subset.sh"
