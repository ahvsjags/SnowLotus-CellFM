#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE308757
export SNOWCELL_GEO_DATASET_ID=rice_node_reproductive_stage_atlas
export SNOWCELL_GEO_SPECIES="Oryza sativa Japonica Group"
export SNOWCELL_GEO_TISSUE="node_I_reproductive_stage"
export SNOWCELL_GEO_FEATURE_COLUMN="${SNOWCELL_GSE308757_FEATURE_COLUMN:-0}"
export SNOWCELL_GEO_LABEL="${SNOWCELL_GSE308757_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GSE308757_COARSE_LABEL:-unannotated}"

bash "$(dirname "$0")/download_geo_raw_tar_mtx_subset.sh"
