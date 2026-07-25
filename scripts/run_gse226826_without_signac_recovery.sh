#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
cd "${PROJECT_DIR}"

mkdir -p logs
source .venv/bin/activate 2>/dev/null || true

rds_path="data/public/GSE226826_rds/GSE226826_AvrRpm1_24h_peak.rds.gz"
inspection_log="logs/gse226826_rds_slots_without_signac.txt"
manifest_output="data/corpus_manifest.gse226826.tsv"
unsupported_report="data/public/GSE226826_rds/unsupported_single_cell_matrix.json"
mtx_dir="data/public/GSE226826_mtx"
npz_dir="data/public/GSE226826_npz"

Rscript scripts/inspect_seurat_slots_without_signac.R "${rds_path}" 40 \
  > "${inspection_log}" 2>&1

set +e
python scripts/write_rds_unsupported_manifest_from_inspection.py \
  --inspection-log "${inspection_log}" \
  --manifest-output "${manifest_output}" \
  --unsupported-report "${unsupported_report}" \
  --accession GSE226826 \
  --dataset-id geo_gse226826_arabidopsis_thaliana_time_resolved_single_cell_spatial \
  --species "Arabidopsis thaliana" \
  --tissue public_discovery \
  --rds-path "${rds_path}" \
  --conversion-error-log logs/geo_promotion_gse226826.log
writer_rc=$?
set -e

if [ "${writer_rc}" -eq 2 ]; then
  rm -rf "${mtx_dir}" "${npz_dir}"
  mkdir -p "${mtx_dir}" "${npz_dir}"
  Rscript scripts/export_seurat_rds_expression_slot_to_mtx.R \
    data/public/GSE226826_rds \
    "${mtx_dir}" \
    RNA \
    counts
  python scripts/build_npz_from_seurat_export.py \
    --export-dir "${mtx_dir}" \
    --output-dir "${npz_dir}" \
    --dataset-id geo_gse226826_arabidopsis_thaliana_time_resolved_single_cell_spatial \
    --species "Arabidopsis thaliana" \
    --tissue public_discovery
  python scripts/write_npz_corpus_manifest.py \
    --npz-dir "${npz_dir}" \
    --output "${manifest_output}" \
    --dataset-id geo_gse226826_arabidopsis_thaliana_time_resolved_single_cell_spatial \
    --species "Arabidopsis thaliana" \
    --tissue public_discovery
  rm -f "${unsupported_report}"
  echo "Wrote ${manifest_output} from direct RNA/counts RDS export"
  writer_rc=0
fi
if [ "${writer_rc}" -ne 0 ]; then
  exit "${writer_rc}"
fi

bash scripts/generate_publication_package.sh
bash scripts/sync_github_release_repo.sh
