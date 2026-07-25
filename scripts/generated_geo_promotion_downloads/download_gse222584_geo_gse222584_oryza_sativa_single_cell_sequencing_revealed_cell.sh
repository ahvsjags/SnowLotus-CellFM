#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE222584
export SNOWCELL_GEO_DATASET_ID=geo_gse222584_oryza_sativa_single_cell_sequencing_revealed_cell
export SNOWCELL_GEO_SPECIES='Oryza sativa'
export SNOWCELL_GEO_TISSUE=public_discovery
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
