#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
cd "${PROJECT_DIR}"

manifest="data/corpus_manifest.gse268881.tsv"
marker="outputs/data_audits/gse268881_refresh_complete.marker"
mkdir -p outputs/data_audits logs

while [ ! -s "${manifest}" ]; do
  sleep "${SNOWCELL_REFRESH_WAIT_SECONDS:-120}"
done

if [ ! -s "data/corpus_manifest.gse268881.available.tsv" ]; then
  bash scripts/convert_gse268881_available.sh 2>&1 | tee -a logs/gse268881_available_conversion.log
fi

python scripts/audit_data_integrity.py \
  --project-dir "${PROJECT_DIR}" \
  --manifest "${manifest}" \
  --manifest data/corpus_manifest.gse268881.available.tsv \
  --output-md outputs/data_audits/gse268881_integrity.md \
  --output-json outputs/data_audits/gse268881_integrity.json \
  --output-tsv outputs/data_audits/gse268881_integrity.tsv

printf '%s\n' "$(date -Iseconds)" > "${marker}"
echo "GSE268881 refresh is ready: ${marker}"
