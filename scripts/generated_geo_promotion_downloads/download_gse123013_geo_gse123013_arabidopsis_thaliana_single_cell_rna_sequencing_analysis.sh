#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE123013
export SNOWCELL_GEO_DATASET_ID=geo_gse123013_arabidopsis_thaliana_single_cell_rna_sequencing_analysis
export SNOWCELL_GEO_SPECIES='Arabidopsis thaliana'
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
