#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE270866
export SNOWCELL_GEO_DATASET_ID=geo_gse270866_zea_mays_kil_transcription_factors_facilitate_embryo
export SNOWCELL_GEO_SPECIES='Zea mays'
export SNOWCELL_GEO_TISSUE=embryo
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
