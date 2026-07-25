#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE243174
export SNOWCELL_GEO_DATASET_ID=geo_gse243174_glycine_max_single_cell_multiomic_profiling_soybean
export SNOWCELL_GEO_SPECIES='Glycine max'
export SNOWCELL_GEO_TISSUE=seed
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
