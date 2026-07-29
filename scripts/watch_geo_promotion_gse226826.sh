#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
ACCESSION="${SNOWCELL_GEO_ACCESSION:-GSE226826}"
DOWNLOAD_SESSION="${SNOWCELL_GSE226826_SESSION:-snowcell_geo_promotion_gse226826}"
WRAPPER="${SNOWCELL_GSE226826_WRAPPER:-scripts/generated_geo_promotion_downloads/download_gse226826_geo_gse226826_arabidopsis_thaliana_time_resolved_single_cell_spatial.sh}"
MANIFEST="${SNOWCELL_GSE226826_MANIFEST:-data/corpus_manifest.gse226826.tsv}"
LOG="${SNOWCELL_GSE226826_LOG:-logs/geo_promotion_gse226826.log}"
WATCHDOG_LOG="${SNOWCELL_GSE226826_WATCHDOG_LOG:-logs/geo_promotion_gse226826_watchdog.log}"
SLEEP_SECONDS="${SNOWCELL_GSE226826_WATCHDOG_INTERVAL_SECONDS:-900}"

cd "${PROJECT_DIR}"
mkdir -p logs

manifest_ready() {
  [ -s "${MANIFEST}" ] && [ "$(wc -l < "${MANIFEST}")" -gt 1 ]
}

download_session_active() {
  tmux has-session -t "${DOWNLOAD_SESSION}" 2>/dev/null
}

download_process_active() {
  pgrep -f "${WRAPPER}" >/dev/null 2>&1 || pgrep -f "download_geo_page_rds_subset.sh" >/dev/null 2>&1 || pgrep -f "aria2c .*${ACCESSION}" >/dev/null 2>&1
}

start_download_session() {
  tmux new-session -d -s "${DOWNLOAD_SESSION}" \
    "bash -lc \"cd '${PROJECT_DIR}' && source .venv/bin/activate 2>/dev/null || true; bash '${WRAPPER}' 2>&1 | tee -a '${LOG}'; rc=\\\${PIPESTATUS[0]}; bash scripts/generate_publication_package.sh || true; bash scripts/sync_github_release_repo.sh || true; exit \\\${rc}\""
}

while true; do
  {
    echo "=== $(date -Is) ${ACCESSION} watchdog ==="
    if manifest_ready; then
      echo "manifest ready: ${MANIFEST}"
      bash scripts/generate_publication_package.sh || true
      bash scripts/sync_github_release_repo.sh || true
      echo "completed ${ACCESSION} lifecycle"
      exit 0
    fi

    if download_session_active || download_process_active; then
      echo "download still active; waiting ${SLEEP_SECONDS}s"
    else
      echo "download inactive and manifest missing; restarting ${DOWNLOAD_SESSION}"
      start_download_session
    fi
  } >> "${WATCHDOG_LOG}" 2>&1
  sleep "${SLEEP_SECONDS}"
done
