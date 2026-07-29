#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
STAGE_PROJECT="${SNOWCELL_PUBLIC_DATA_STAGE_PROJECT:-/root/snowlotus_public_data_stage_project}"
cd "${STAGE_PROJECT}"

raw_dir="${STAGE_PROJECT}/data/public/GSE243419_raw_tar"
raw_tmp="${raw_dir}/GSE243419_RAW.tar.download"
mkdir -p "${raw_dir}"
python "${PROJECT_DIR}/scripts/parallel_geo_range_resume.py" \
  --url "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE243nnn/GSE243419/suppl/GSE243419_RAW.tar" \
  --output "${raw_tmp}" --expected-bytes 150824960 --workers 8
mv -f "${raw_tmp}" "${raw_dir}/GSE243419_RAW.tar"
exec bash scripts/download_gse243419_cotton_glandular_mtx_subset.sh
