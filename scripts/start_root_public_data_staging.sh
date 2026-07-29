#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
stage_root="${SNOWCELL_PUBLIC_DATA_STAGE_ROOT:-/root/snowlotus_public_data_stage}"
accession="${SNOWCELL_ROOT_GEO_ACCESSION:-GSE270342}"
sample_accession="${SNOWCELL_ROOT_GEO_SAMPLE_ACCESSION:-GSM8339904}"
filename="${SNOWCELL_ROOT_GEO_FILENAME:-GSM8339904_rep1_filtered_feature_bc_matrix.h5}"
dataset_id="${SNOWCELL_ROOT_GEO_DATASET_ID:-wheat_soil_root_atlas}"
species="${SNOWCELL_ROOT_GEO_SPECIES:-Triticum aestivum}"
tissue="${SNOWCELL_ROOT_GEO_TISSUE:-root}"

export PATH="/root/miniconda3/envs/myconda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
mkdir -p "${stage_root}/data/public/${accession}_h5" \
  "${stage_root}/data/public/${accession}_npz" \
  "${stage_root}/logs"

if ! bash "${project_dir}/scripts/check_disk_budget.sh" "${stage_root}"; then
  echo "[$(date)] root public data staging paused by disk budget"
  exit 0
fi

sample_bucket="${sample_accession%???}nnn"
url="https://ftp.ncbi.nlm.nih.gov/geo/samples/${sample_bucket}/${sample_accession}/suppl/${filename}"
h5_path="${stage_root}/data/public/${accession}_h5/${filename}"

if [ ! -s "${h5_path}" ] || ! python - "${h5_path}" <<'PY'
import sys
from pathlib import Path

try:
    import h5py
except ImportError:
    raise SystemExit(1)

path = Path(sys.argv[1])
if not path.is_file() or path.stat().st_size == 0:
    raise SystemExit(1)
with h5py.File(path, "r"):
    pass
PY
then
  curl -L --fail --retry 5 --retry-delay 5 --connect-timeout 20 \
    --max-time "${SNOWCELL_ROOT_GEO_MAX_TIME:-7200}" -C - \
    -A "SnowLotus-CellFM/0.1 public-data-collector" \
    -o "${h5_path}" "${url}"
fi

python - "${h5_path}" <<'PY'
import sys
import h5py

with h5py.File(sys.argv[1], "r"):
    pass
print(f"validated_h5={sys.argv[1]}")
PY

python "${project_dir}/scripts/tenx_h5_to_npz.py" \
  --input-dir "${stage_root}/data/public/${accession}_h5" \
  --output-dir "${stage_root}/data/public/${accession}_npz" \
  --dataset-id "${dataset_id}" \
  --species "${species}" \
  --tissue "${tissue}" \
  --pattern "*.h5" \
  --sample-regex "filtered_feature_bc_matrix\\.h5$" \
  --max-files 1 \
  --manifest-output "${stage_root}/data/corpus_manifest.${accession,,}.tsv"

sha256sum "${h5_path}" > "${stage_root}/data/public/${accession}_h5/${filename}.sha256"
printf '%s\t%s\t%s\t%s\n' "${accession}" "${sample_accession}" "${dataset_id}" "${url}" \
  >> "${stage_root}/data/root_staging_sources.tsv"
echo "[$(date)] root public data staging complete: ${h5_path}"
