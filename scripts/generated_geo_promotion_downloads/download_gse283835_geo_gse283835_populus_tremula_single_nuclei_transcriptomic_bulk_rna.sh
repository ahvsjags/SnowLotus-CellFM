#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
export SNOWCELL_GEO_ACCESSION=GSE283835
export SNOWCELL_GEO_DATASET_ID=geo_gse283835_populus_tremula_single_nuclei_transcriptomic_bulk_rna
export SNOWCELL_GEO_SPECIES='Populus tremula x Populus alba'
export SNOWCELL_GEO_TISSUE=stem
export SNOWCELL_GEO_LABEL="${SNOWCELL_GEO_LABEL:-unannotated}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
bash scripts/download_geo_raw_tar_mtx_subset.sh
