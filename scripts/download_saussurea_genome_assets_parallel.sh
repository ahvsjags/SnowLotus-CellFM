#!/usr/bin/env bash
set -euo pipefail

out_dir="${SNOWCELL_SAUSSUREA_REFERENCE_DIR:-/mnt/snowlotus_cellfm/data/public/saussurea_genome_reference}"
base_url="https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/033/807/775/GCA_033807775.1_ASM3380777v1"
chunk_bytes="${SNOWCELL_RANGE_CHUNK_BYTES:-67108864}"
workers="${SNOWCELL_RANGE_WORKERS:-8}"

mkdir -p "${out_dir}"

download_range_file() {
  local name="$1"
  local size="$2"
  local url="${base_url}/${name}"
  local final="${out_dir}/${name}"
  local work="${out_dir}/.range_${name}"
  local total=$(( (size + chunk_bytes - 1) / chunk_bytes ))
  local -a pids=()

  mkdir -p "${work}"
  for ((index = 0; index < total; index++)); do
    local start=$((index * chunk_bytes))
    local end=$((start + chunk_bytes - 1))
    if ((end >= size)); then
      end=$((size - 1))
    fi
    local expected=$((end - start + 1))
    local chunk="${work}/$(printf '%06d' "${index}")"
    if [[ -f "${chunk}" ]] && [[ "$(stat -c %s "${chunk}")" -eq "${expected}" ]]; then
      continue
    fi
    rm -f "${chunk}" "${chunk}.part"
    curl -fL --retry 8 --retry-all-errors --connect-timeout 30 \
      --range "${start}-${end}" -o "${chunk}.part" "${url}" &
    pids+=("$!")
    if ((${#pids[@]} >= workers)); then
      for pid in "${pids[@]}"; do
        wait "${pid}"
      done
      pids=()
    fi
  done
  for pid in "${pids[@]}"; do
    wait "${pid}"
  done

  for ((index = 0; index < total; index++)); do
    local start=$((index * chunk_bytes))
    local end=$((start + chunk_bytes - 1))
    if ((end >= size)); then
      end=$((size - 1))
    fi
    local expected=$((end - start + 1))
    local chunk="${work}/$(printf '%06d' "${index}")"
    if [[ ! -f "${chunk}" ]] && [[ -f "${chunk}.part" ]]; then
      mv -f "${chunk}.part" "${chunk}"
    fi
    [[ -f "${chunk}" ]]
    [[ "$(stat -c %s "${chunk}")" -eq "${expected}" ]]
  done

  cat "${work}"/* > "${final}.part"
  [[ "$(stat -c %s "${final}.part")" -eq "${size}" ]]
  gzip -t "${final}.part"
  mv -f "${final}.part" "${final}"
  sha256sum "${final}" >> "${out_dir}/sequence_sha256sums.txt"
  rm -rf "${work}"
  echo "verified ${name} ${size} bytes"
}

: > "${out_dir}/sequence_sha256sums.txt"
download_range_file GCA_033807775.1_ASM3380777v1_genomic.fna.gz 718280295
download_range_file GCA_033807775.1_ASM3380777v1_genomic.gbff.gz 997439085
echo "Saussurea genome sequence assets downloaded and verified."
