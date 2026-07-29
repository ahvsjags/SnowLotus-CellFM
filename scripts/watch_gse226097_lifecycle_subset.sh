#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
poll_seconds="${SNOWCELL_GSE226097_WATCH_POLL_SECONDS:-300}"

cd "$project_dir"

echo "[$(date)] GSE226097 lifecycle subset watchdog started"

while true; do
  if [ -s data/corpus_manifest.gse226097.tsv ]; then
    echo "[$(date)] GSE226097 manifest ready: data/corpus_manifest.gse226097.tsv"
  else
    bash scripts/start_gse226097_lifecycle_subset.sh || true
  fi
  sleep "$poll_seconds"
done
