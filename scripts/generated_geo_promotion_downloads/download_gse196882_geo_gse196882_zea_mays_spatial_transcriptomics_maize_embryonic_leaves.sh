#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE196882
export SNOWCELL_GEO_DATASET_ID=geo_gse196882_zea_mays_spatial_transcriptomics_maize_embryonic_leaves
export SNOWCELL_GEO_SPECIES='Zea mays'
export SNOWCELL_GEO_TISSUE=leaf
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
