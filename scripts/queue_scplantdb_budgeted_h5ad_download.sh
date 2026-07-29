#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
max_bytes="${SNOWCELL_SCPLANTDB_MAX_BYTES:-500000000}"
max_total_bytes="${SNOWCELL_SCPLANTDB_MAX_TOTAL_BYTES:-3000000000}"
max_datasets="${SNOWCELL_SCPLANTDB_MAX_DATASETS:-32}"
min_cells="${SNOWCELL_SCPLANTDB_MIN_CELLS:-0}"
timeout_seconds="${SNOWCELL_SCPLANTDB_PROBE_TIMEOUT:-15}"
selected_file="${SNOWCELL_SCPLANTDB_SELECTED_FILE:-data/public_discovery/scplantdb_selected_h5ad_datasets.txt}"
manifest="${SNOWCELL_SCPLANTDB_MANIFEST:-data/corpus_manifest.scplantdb.tsv}"
refresh_package="${SNOWCELL_SCPLANTDB_REFRESH_PACKAGE:-1}"

cd "$project_dir"
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs data/public_discovery outputs/publication_package

if ! bash scripts/check_disk_budget.sh "${project_dir}"; then
  echo "[$(date)] scPlantDB queue paused by disk budget"
  exit 0
fi

manifest_rows() {
  if [ -s "$manifest" ]; then
    tail -n +2 "$manifest" | wc -l
  else
    echo 0
  fi
}

before_rows="$(manifest_rows)"
echo "[$(date)] scPlantDB budgeted H5AD queue started"
echo "[$(date)] budgets: max_bytes=${max_bytes} max_total_bytes=${max_total_bytes} max_datasets=${max_datasets} min_cells=${min_cells}"
echo "[$(date)] manifest rows before: ${before_rows}"

python scripts/extract_scplantdb_catalog.py \
  --chunks-dir data/public/source_pages/scplantdb_chunks \
  --output-tsv data/public_discovery/scplantdb_dataset_catalog.tsv \
  --output-json data/public_discovery/scplantdb_dataset_catalog.json \
  --output-md data/public_discovery/scplantdb_acquisition_catalog.md

python scripts/probe_scplantdb_h5ad_sizes.py \
  --catalog-tsv data/public_discovery/scplantdb_dataset_catalog.tsv \
  --output-tsv data/public_discovery/scplantdb_h5ad_size_probe.tsv \
  --output-json data/public_discovery/scplantdb_h5ad_size_probe.json \
  --output-md data/public_discovery/scplantdb_h5ad_size_probe.md \
  --selected-output "$selected_file" \
  --max-bytes "$max_bytes" \
  --max-total-bytes "$max_total_bytes" \
  --max-datasets "$max_datasets" \
  --min-cells "$min_cells" \
  --timeout "$timeout_seconds"

if [ ! -s "$selected_file" ]; then
  echo "[$(date)] no scPlantDB datasets selected; exiting"
  exit 0
fi

echo "[$(date)] selected datasets:"
cat "$selected_file"

SNOWCELL_SCPLANTDB_DATASETS_FILE="$selected_file" \
SNOWCELL_SCPLANTDB_MANIFEST="$manifest" \
bash scripts/download_scplantdb_h5ad_subset.sh

python scripts/write_scplantdb_manifest_audit.py \
  --project-dir . \
  --manifest "$manifest" \
  --output-md outputs/publication_package/scplantdb_manifest_audit.md \
  --output-json outputs/publication_package/scplantdb_manifest_audit.json \
  --output-tsv outputs/publication_package/scplantdb_manifest_audit.tsv

python scripts/audit_data_integrity.py \
  --project-dir . \
  --output-md outputs/publication_package/data_integrity_audit.md \
  --output-json outputs/publication_package/data_integrity_audit.json \
  --output-tsv outputs/publication_package/data_integrity_audit.tsv

python scripts/write_pending_corpus_additions.py \
  --project-dir . \
  --output-md outputs/publication_package/pending_corpus_additions.md \
  --output-json outputs/publication_package/pending_corpus_additions.json

after_rows="$(manifest_rows)"
echo "[$(date)] manifest rows after: ${after_rows}"

if [ "$refresh_package" = "1" ]; then
  bash scripts/generate_publication_package.sh
fi

echo "[$(date)] scPlantDB budgeted H5AD queue complete"
