#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
input="${project_dir}/data/public/saussurea_genome_reference/GCA_033807775.1_ASM3380777v1_genomic.gbff.gz"
output="${project_dir}/data/public/saussurea_genome_reference/saussurea_gene_catalog.tsv"
summary="${project_dir}/data/public/saussurea_genome_reference/saussurea_gene_catalog_summary.json"

source /root/miniconda3/etc/profile.d/conda.sh
conda activate myconda
while [[ ! -s "${input}" ]]; do
  sleep 60
done

python "${project_dir}/scripts/build_saussurea_gene_catalog.py" \
  --input "${input}" \
  --output "${output}" \
  --summary "${summary}"
