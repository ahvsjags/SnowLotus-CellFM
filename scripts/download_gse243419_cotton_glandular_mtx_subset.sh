#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE243419
export SNOWCELL_GEO_DATASET_ID=cotton_glandular_terpenoid_atlas
export SNOWCELL_GEO_SPECIES="Gossypium hirsutum"
export SNOWCELL_GEO_TISSUE=leaf_glandular_cells
export SNOWCELL_GEO_FEATURE_COLUMN="${SNOWCELL_GSE243419_FEATURE_COLUMN:-0}"
export SNOWCELL_GEO_LABEL="${SNOWCELL_GSE243419_LABEL:-unannotated_leaf_glandular}"
export SNOWCELL_GEO_COARSE_LABEL="${SNOWCELL_GSE243419_COARSE_LABEL:-secretory_or_epidermal}"
export SNOWCELL_GEO_RAW_TAR_DOWNLOADER="${SNOWCELL_GEO_RAW_TAR_DOWNLOADER:-curl}"
export SNOWCELL_GEO_RAW_EXPECTED_BYTES="${SNOWCELL_GEO_RAW_EXPECTED_BYTES:-150824960}"

bash "$(dirname "$0")/download_geo_raw_tar_mtx_subset.sh"
