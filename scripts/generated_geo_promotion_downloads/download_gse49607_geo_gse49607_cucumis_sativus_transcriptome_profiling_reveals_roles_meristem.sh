#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE49607
export SNOWCELL_GEO_DATASET_ID=geo_gse49607_cucumis_sativus_transcriptome_profiling_reveals_roles_meristem
export SNOWCELL_GEO_SPECIES='Cucumis sativus'
export SNOWCELL_GEO_TISSUE=stem
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
