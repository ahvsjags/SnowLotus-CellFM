#!/usr/bin/env bash
set -euo pipefail

out_dir="${SNOWCELL_SAUSSUREA_REFERENCE_DIR:-/mnt/snowlotus_cellfm/data/public/saussurea_genome_reference}"
url="https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR516/SRR516284/SRR516284.fastq.gz"
expected_bytes=267339249

mkdir -p "${out_dir}"
cd "${out_dir}"
curl -fL --retry 8 --retry-all-errors -C - -o SRR516284.fastq.gz.part "${url}"
[[ "$(stat -c %s SRR516284.fastq.gz.part)" -eq "${expected_bytes}" ]]
gzip -t SRR516284.fastq.gz.part
mv -f SRR516284.fastq.gz.part SRR516284.fastq.gz
sha256sum SRR516284.fastq.gz > SRR516284.fastq.gz.sha256
printf '%s\n' \
  "accession=SRR516284" \
  "species=Saussurea_involucrata" \
  "modality=bulk_RNA_seq" \
  "read_count=6666667" \
  "bytes=${expected_bytes}" \
  "source=${url}" \
  > SRR516284.metadata.tsv
echo "Saussurea bulk transcriptome downloaded and verified."
