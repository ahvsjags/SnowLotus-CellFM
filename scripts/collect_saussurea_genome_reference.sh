#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-.}"
project_dir="$(cd "${project_dir}" && pwd)"
out_dir="${SNOWCELL_SAUSSUREA_REFERENCE_DIR:-${project_dir}/data/public/saussurea_genome_reference}"
base_url="https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/033/807/775/GCA_033807775.1_ASM3380777v1"
structure_url="${base_url}/GCA_033807775.1_ASM3380777v1_assembly_structure/Primary_Assembly"

mkdir -p "${out_dir}"

fetch() {
  local output="$1"
  local url="$2"
  curl -fL --retry 3 --retry-all-errors --connect-timeout 30 -o "${out_dir}/${output}.part" "${url}"
  mv -f "${out_dir}/${output}.part" "${out_dir}/${output}"
}

fetch GCA_033807775.1_ASM3380777v1_assembly_report.txt "${base_url}/GCA_033807775.1_ASM3380777v1_assembly_report.txt"
fetch GCA_033807775.1_ASM3380777v1_assembly_stats.txt "${base_url}/GCA_033807775.1_ASM3380777v1_assembly_stats.txt"
fetch GCA_033807775.1_ASM3380777v1_feature_count.txt "${base_url}/GCA_033807775.1_ASM3380777v1_feature_count.txt"
fetch assembly_status.txt "${base_url}/assembly_status.txt"
fetch annotation_hashes.txt "${base_url}/annotation_hashes.txt"
fetch README.txt "${base_url}/README.txt"
fetch Primary_Assembly_component_localID2acc "${structure_url}/component_localID2acc"
fetch Primary_Assembly_scaffold_localID2acc "${structure_url}/scaffold_localID2acc"

printf '%s\n' \
  "asset_dir=${out_dir}" \
  "assembly=GCA_033807775.1" \
  "taxon=Saussurea_involucrata" \
  "status=latest" \
  "source_root=${base_url}/" \
  "feature_count=43311_protein_coding_genes" \
  "annotation_files=not_present_in_assembly_directory" \
  > "${out_dir}/manifest.tsv"

sha256sum \
  "${out_dir}/GCA_033807775.1_ASM3380777v1_assembly_report.txt" \
  "${out_dir}/GCA_033807775.1_ASM3380777v1_assembly_stats.txt" \
  "${out_dir}/GCA_033807775.1_ASM3380777v1_feature_count.txt" \
  "${out_dir}/Primary_Assembly_component_localID2acc" \
  "${out_dir}/Primary_Assembly_scaffold_localID2acc" \
  "${out_dir}/annotation_hashes.txt" \
  "${out_dir}/assembly_status.txt" \
  "${out_dir}/README.txt" \
  > "${out_dir}/sha256sums.txt"

sha256sum -c "${out_dir}/sha256sums.txt"
echo "Saussurea reference assets collected in ${out_dir}"
