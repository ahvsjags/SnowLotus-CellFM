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
expected_bytes="${SNOWCELL_ROOT_GEO_EXPECTED_BYTES:-}"
chunk_bytes="${SNOWCELL_ROOT_GEO_CHUNK_BYTES:-1000000}"

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
ftp_url="ftp://ftp.ncbi.nlm.nih.gov/geo/samples/${sample_bucket}/${sample_accession}/suppl/${filename}"
h5_path="${stage_root}/data/public/${accession}_h5/${filename}"

download_full_file() {
  local full_tmp="${h5_path}.full_download"
  local attempt_tmp="${full_tmp}.attempt"
  # Keep the previous partial and the current attempt separate so a watchdog
  # restart never destroys the only local copy of a large public file.
  local curl_status=0
  if [ -s "${attempt_tmp}" ]; then
    curl -4 -L --fail --http1.1 --retry 12 --retry-all-errors --retry-delay 10 \
      --connect-timeout 20 \
      --max-time "${SNOWCELL_ROOT_GEO_MAX_TIME:-86400}" \
      -e "https://www.ncbi.nlm.nih.gov/geo/" \
      -A "SnowLotus-CellFM/0.1 public-data-collector" \
      -C - -o "${attempt_tmp}" "${url}" || curl_status=$?
  else
    curl -4 -L --fail --http1.1 --retry 12 --retry-all-errors --retry-delay 10 \
      --connect-timeout 20 \
      --max-time "${SNOWCELL_ROOT_GEO_MAX_TIME:-86400}" \
      -e "https://www.ncbi.nlm.nih.gov/geo/" \
      -A "SnowLotus-CellFM/0.1 public-data-collector" \
      -o "${attempt_tmp}" "${url}" || curl_status=$?
  fi
  if [ "${curl_status}" -ne 0 ]; then
    # Preserve a failed resume attempt for postmortem, then retry from a
    # fresh file so a server-side Range policy cannot poison the next run.
    mv -f "${attempt_tmp}" "${attempt_tmp}.resume_failed.$(date +%s)" 2>/dev/null || true
    curl -4 -L --fail --http1.1 --retry 12 --retry-all-errors --retry-delay 10 \
      --connect-timeout 20 \
      --max-time "${SNOWCELL_ROOT_GEO_MAX_TIME:-86400}" \
      -e "https://www.ncbi.nlm.nih.gov/geo/" \
      -A "SnowLotus-CellFM/0.1 public-data-collector" \
      -o "${attempt_tmp}" "${url}"
  fi
  if [ -n "${expected_bytes}" ] && [ "$(wc -c < "${attempt_tmp}")" -ne "${expected_bytes}" ]; then
    echo "full GEO download has unexpected size: expected=${expected_bytes} received=$(wc -c < "${attempt_tmp}")" >&2
    return 1
  fi
  mv -f "${attempt_tmp}" "${full_tmp}"
  mv -f "${full_tmp}" "${h5_path}"
}

download_ftp_ranges() {
  local current_bytes="$1"
  local remainder_path="${h5_path}.remainder"
  mkdir -p "$(dirname "${remainder_path}")"
  while [ "${current_bytes}" -lt "${expected_bytes}" ]; do
    local end_bytes=$((current_bytes + chunk_bytes - 1))
    if [ "${end_bytes}" -ge "${expected_bytes}" ]; then
      end_bytes=$((expected_bytes - 1))
    fi
    rm -f "${remainder_path}"
    local curl_status=0
    curl -4 --ftp-pasv --fail \
      --connect-timeout 20 --max-time "${SNOWCELL_ROOT_GEO_MAX_TIME:-7200}" \
      -r "${current_bytes}-${end_bytes}" \
      -o "${remainder_path}" "${ftp_url}" || curl_status=$?
    local received_chunk_bytes="$(wc -c < "${remainder_path}" 2>/dev/null || echo 0)"
    local expected_chunk_bytes=$((end_bytes - current_bytes + 1))
    if [ "${received_chunk_bytes}" -le 0 ] || [ "${received_chunk_bytes}" -gt "${expected_chunk_bytes}" ]; then
      echo "short or invalid FTP range: start=${current_bytes} end=${end_bytes} expected=${expected_chunk_bytes} received=${received_chunk_bytes} curl_status=${curl_status}" >&2
      rm -f "${remainder_path}"
      return 1
    fi
    cat "${remainder_path}" >> "${h5_path}"
    rm -f "${remainder_path}"
    current_bytes=$((current_bytes + received_chunk_bytes))
    echo "FTP range progress ${current_bytes}/${expected_bytes}"
  done
}

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
  if [ -n "${expected_bytes}" ] && [ -s "${h5_path}" ]; then
    current_bytes="$(wc -c < "${h5_path}")"
    download_ftp_ranges "${current_bytes}" || download_full_file
  else
    if [ -n "${expected_bytes}" ]; then
      : > "${h5_path}"
      download_ftp_ranges 0 || download_full_file
    else
      download_full_file
    fi
  fi
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
