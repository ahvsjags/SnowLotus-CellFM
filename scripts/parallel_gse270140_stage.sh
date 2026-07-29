#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
ROOT_STAGE="${SNOWCELL_PUBLIC_DATA_STAGE_ROOT:-/root/snowlotus_public_data_stage}"
h5_path="${ROOT_STAGE}/data/public/GSE270140_h5/GSM8335426_JWE03_filtered_feature_bc_matrix.h5"
mkdir -p "${ROOT_STAGE}/data/public/GSE270140_h5"
/root/miniconda3/envs/myconda/bin/python "${PROJECT_DIR}/scripts/parallel_geo_range_resume.py" \
  --url "https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM8335nnn/GSM8335426/suppl/GSM8335426_JWE03_filtered_feature_bc_matrix.h5" \
  --output "${h5_path}" --expected-bytes 68904043 --chunk-bytes 2000000 --workers 2
exec bash "${PROJECT_DIR}/scripts/start_root_gse270140_staging.sh"
