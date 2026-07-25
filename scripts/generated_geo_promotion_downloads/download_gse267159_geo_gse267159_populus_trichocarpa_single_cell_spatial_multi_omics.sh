#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE267159
export SNOWCELL_GEO_DATASET_ID=geo_gse267159_populus_trichocarpa_single_cell_spatial_multi_omics
export SNOWCELL_GEO_SPECIES='Populus trichocarpa'
export SNOWCELL_GEO_TISSUE=stem
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
