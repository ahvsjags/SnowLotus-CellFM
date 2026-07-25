#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE273875
export SNOWCELL_GEO_DATASET_ID=geo_gse273875_oryza_sativa_a_single_cell_multiomics_atlas
export SNOWCELL_GEO_SPECIES='Oryza sativa'
export SNOWCELL_GEO_TISSUE=public_discovery
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GEO_MAX_FILES:-1}"
export SNOWCELL_GEO_PAGE_PATTERN="${SNOWCELL_GEO_PAGE_PATTERN:-\.rds(\.gz)?$}"
bash scripts/download_geo_page_rds_subset.sh
