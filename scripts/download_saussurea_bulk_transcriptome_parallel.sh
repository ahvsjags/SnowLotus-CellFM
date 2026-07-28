#!/usr/bin/env bash
set -euo pipefail

out_dir="${SNOWCELL_SAUSSUREA_REFERENCE_DIR:-/mnt/snowlotus_cellfm/data/public/saussurea_genome_reference}"
url="https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR516/SRR516284/SRR516284.fastq.gz"
size=267339249
chunk_bytes="${SNOWCELL_RANGE_CHUNK_BYTES:-33554432}"
workers="${SNOWCELL_RANGE_WORKERS:-8}"
work="${out_dir}/.range_SRR516284.fastq.gz"

mkdir -p "${work}"
total=$(( (size + chunk_bytes - 1) / chunk_bytes ))
pids=()
for ((index = 0; index < total; index++)); do
  start=$((index * chunk_bytes))
  end=$((start + chunk_bytes - 1))
  if ((end >= size)); then end=$((size - 1)); fi
  expected=$((end - start + 1))
  chunk="${work}/$(printf '%06d' "${index}")"
  if [[ -f "${chunk}" ]] && [[ "$(stat -c %s "${chunk}")" -eq "${expected}" ]]; then continue; fi
  rm -f "${chunk}" "${chunk}.part"
  curl -fsSL --retry 8 --retry-all-errors --connect-timeout 30 \
    --range "${start}-${end}" -o "${chunk}.part" "${url}" &
  pids+=("$!")
  if ((${#pids[@]} >= workers)); then
    for pid in "${pids[@]}"; do wait "${pid}"; done
    pids=()
  fi
done
for pid in "${pids[@]}"; do wait "${pid}"; done

for ((index = 0; index < total; index++)); do
  start=$((index * chunk_bytes))
  end=$((start + chunk_bytes - 1))
  if ((end >= size)); then end=$((size - 1)); fi
  expected=$((end - start + 1))
  chunk="${work}/$(printf '%06d' "${index}")"
  if [[ ! -f "${chunk}" ]] && [[ -f "${chunk}.part" ]]; then mv -f "${chunk}.part" "${chunk}"; fi
  [[ -f "${chunk}" ]]
  [[ "$(stat -c %s "${chunk}")" -eq "${expected}" ]]
done

cat "${work}"/* > "${out_dir}/SRR516284.fastq.gz.part"
[[ "$(stat -c %s "${out_dir}/SRR516284.fastq.gz.part")" -eq "${size}" ]]
gzip -t "${out_dir}/SRR516284.fastq.gz.part"
mv -f "${out_dir}/SRR516284.fastq.gz.part" "${out_dir}/SRR516284.fastq.gz"
sha256sum "${out_dir}/SRR516284.fastq.gz" > "${out_dir}/SRR516284.fastq.gz.sha256"
printf '%s\n' \
  "accession=SRR516284" \
  "species=Saussurea_involucrata" \
  "modality=bulk_RNA_seq" \
  "read_count=6666667" \
  "bytes=${size}" \
  "source=${url}" \
  > "${out_dir}/SRR516284.metadata.tsv"
rm -rf "${work}"
echo "Saussurea bulk transcriptome downloaded and verified."
