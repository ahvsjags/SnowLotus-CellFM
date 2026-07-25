#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE270140
export SNOWCELL_GEO_DATASET_ID=arabidopsis_secondary_root_dev_atlas
export SNOWCELL_GEO_SPECIES="Arabidopsis thaliana"
export SNOWCELL_GEO_TISSUE=secondary_root
export SNOWCELL_GEO_SAMPLE_REGEX="${SNOWCELL_GSE270140_REGEX:-\\.h5$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE270140_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_raw_tar_h5_subset.sh"
