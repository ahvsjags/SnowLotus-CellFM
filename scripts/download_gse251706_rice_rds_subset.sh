#!/usr/bin/env bash
set -euo pipefail

export SNOWCELL_GEO_ACCESSION=GSE251706
export SNOWCELL_GEO_DATASET_ID=rice_soil_stress_root_atlas
export SNOWCELL_GEO_SPECIES="Oryza sativa"
export SNOWCELL_GEO_TISSUE=root
export SNOWCELL_GEO_SAMPLE_REGEX="${SNOWCELL_GSE251706_PATTERN:-GSM8660509.*\\.rds\\.gz$}"
export SNOWCELL_GEO_MAX_FILES="${SNOWCELL_GSE251706_MAX_FILES:-1}"

bash "$(dirname "$0")/download_geo_rds_subset.sh"
