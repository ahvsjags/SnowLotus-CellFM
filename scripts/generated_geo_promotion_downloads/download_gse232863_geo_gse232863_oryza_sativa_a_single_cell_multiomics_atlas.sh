#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE232863
export SNOWCELL_GEO_DATASET_ID=geo_gse232863_oryza_sativa_a_single_cell_multiomics_atlas
export SNOWCELL_GEO_SPECIES='Oryza sativa'
export SNOWCELL_GEO_TISSUE=public_discovery
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
