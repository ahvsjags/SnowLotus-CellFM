#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE152766
export SNOWCELL_GEO_DATASET_ID=arabidopsis_root_atlas
export SNOWCELL_GEO_SPECIES=Arabidopsis_thaliana
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_SAMPLE_REGEX="${SNOWCELL_GSE152766_REGEX:-_mtx\\.tar\\.gz$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE152766_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_mtx_tar_subset.sh"
