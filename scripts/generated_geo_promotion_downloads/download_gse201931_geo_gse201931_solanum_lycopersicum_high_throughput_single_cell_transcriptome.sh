#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE201931
export SNOWCELL_GEO_DATASET_ID=geo_gse201931_solanum_lycopersicum_high_throughput_single_cell_transcriptome
export SNOWCELL_GEO_SPECIES='Solanum lycopersicum'
export SNOWCELL_GEO_TISSUE=leaf
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_mtx_component_subset.sh
