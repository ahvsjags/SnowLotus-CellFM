#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE157757
export SNOWCELL_GEO_DATASET_ID=geo_gse157757_zea_mays_single_cell_sequencing_reveals_phloem
export SNOWCELL_GEO_SPECIES='Zea mays'
export SNOWCELL_GEO_TISSUE=leaf
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
