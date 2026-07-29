#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_PUBLIC_DATA_STAGE_ROOT="${SNOWCELL_PUBLIC_DATA_STAGE_ROOT:-/root/snowlotus_public_data_stage}"
export SNOWCELL_ROOT_GEO_ACCESSION=GSE270140
export SNOWCELL_ROOT_GEO_SAMPLE_ACCESSION=GSM8335426
export SNOWCELL_ROOT_GEO_FILENAME=GSM8335426_JWE03_filtered_feature_bc_matrix.h5
export SNOWCELL_ROOT_GEO_EXPECTED_BYTES=68904043
export SNOWCELL_ROOT_GEO_DATASET_ID=arabidopsis_secondary_root_dev_atlas
export SNOWCELL_ROOT_GEO_SPECIES="Arabidopsis thaliana"
export SNOWCELL_ROOT_GEO_TISSUE=secondary_root

exec bash "$(dirname "$0")/start_root_public_data_staging.sh"
