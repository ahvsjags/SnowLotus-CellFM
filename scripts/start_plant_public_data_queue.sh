#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
cd "${PROJECT_DIR}"
source /root/miniconda3/etc/profile.d/conda.sh
conda activate myconda

export SNOWCELL_ENSURE_GSE268881="${SNOWCELL_ENSURE_GSE268881:-1}"
export SNOWCELL_ENSURE_GSE152766="${SNOWCELL_ENSURE_GSE152766:-1}"
export SNOWCELL_ENSURE_GSE146034="${SNOWCELL_ENSURE_GSE146034:-1}"
export SNOWCELL_ENSURE_GSE270342="${SNOWCELL_ENSURE_GSE270342:-1}"
export SNOWCELL_ENSURE_GSE243419="${SNOWCELL_ENSURE_GSE243419:-1}"
export SNOWCELL_ENSURE_GSE270140="${SNOWCELL_ENSURE_GSE270140:-1}"
export SNOWCELL_ENSURE_GSE251706="${SNOWCELL_ENSURE_GSE251706:-1}"
export SNOWCELL_ENSURE_GSE338572="${SNOWCELL_ENSURE_GSE338572:-1}"
export SNOWCELL_ENSURE_GSE313726="${SNOWCELL_ENSURE_GSE313726:-1}"
export SNOWCELL_ENSURE_GSE311951="${SNOWCELL_ENSURE_GSE311951:-1}"
export SNOWCELL_ENSURE_GSE302041="${SNOWCELL_ENSURE_GSE302041:-1}"
export SNOWCELL_ENSURE_GSE314252="${SNOWCELL_ENSURE_GSE314252:-1}"
export SNOWCELL_ENSURE_GSE300264="${SNOWCELL_ENSURE_GSE300264:-1}"

if [ "${SNOWCELL_REFRESH_GEO_FILELISTS:-1}" = "1" ]; then
  missing_filelist=0
  for accession in GSE146034 GSE149217 GSE152766 GSE172280 GSE226097 GSE243419 GSE251706 GSE268881 GSE270140 GSE270342; do
    if [ ! -s "data/public/geo_filelists/${accession}/filelist.txt" ]; then
      missing_filelist=1
      break
    fi
  done
  if [ "${missing_filelist}" = "1" ]; then
    bash scripts/generated_downloads/download_geo_filelists.sh >> logs/geo_filelists.log 2>&1 || true
  fi
fi

exec bash scripts/ensure_public_data_jobs.sh
