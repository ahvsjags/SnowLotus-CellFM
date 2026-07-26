#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE226218
export SNOWCELL_GEO_DATASET_ID=geo_gse226218_gossypium_arboreum_transcriptional_landscape_cottont_roots_response
export SNOWCELL_GEO_SPECIES='Gossypium arboreum'
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_mtx_component_subset.sh
