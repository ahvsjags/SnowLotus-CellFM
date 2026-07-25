#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE336751
export SNOWCELL_GEO_DATASET_ID=marchantia_spore_asymmetry_single_cell
export SNOWCELL_GEO_SPECIES="Marchantia polymorpha"
export SNOWCELL_GEO_TISSUE="spore"
export SNOWCELL_GEO_FEATURE_COLUMN="${SNOWCELL_GSE336751_FEATURE_COLUMN:-0}"
export SNOWCELL_GEO_LABEL="${SNOWCELL_GSE336751_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GSE336751_COARSE_LABEL:-unannotated}"

bash "$(dirname "$0")/download_geo_raw_tar_mtx_subset.sh"
