#!/usr/bin/env bash
set -euo pipefail

out_dir="${SNOWCELL_SAUSSUREA_REFERENCE_DIR:-/mnt/snowlotus_cellfm/data/public/saussurea_genome_reference}"
base_url="https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/033/807/775/GCA_033807775.1_ASM3380777v1"

mkdir -p "${out_dir}"
cd "${out_dir}"

curl -fL --retry 5 --retry-all-errors -C - \
  -o GCA_033807775.1_ASM3380777v1_genomic.fna.gz.part \
  "${base_url}/GCA_033807775.1_ASM3380777v1_genomic.fna.gz"
mv -f GCA_033807775.1_ASM3380777v1_genomic.fna.gz.part \
  GCA_033807775.1_ASM3380777v1_genomic.fna.gz

curl -fL --retry 5 --retry-all-errors -C - \
  -o GCA_033807775.1_ASM3380777v1_genomic.gbff.gz.part \
  "${base_url}/GCA_033807775.1_ASM3380777v1_genomic.gbff.gz"
mv -f GCA_033807775.1_ASM3380777v1_genomic.gbff.gz.part \
  GCA_033807775.1_ASM3380777v1_genomic.gbff.gz

sha256sum \
  GCA_033807775.1_ASM3380777v1_genomic.fna.gz \
  GCA_033807775.1_ASM3380777v1_genomic.gbff.gz \
  > sequence_sha256sums.txt
echo "Saussurea genome sequence assets downloaded and verified."
