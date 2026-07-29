#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
ROOT_STAGE="${SNOWCELL_PUBLIC_DATA_STAGE_ROOT:-/root/snowlotus_public_data_stage}"
STAGE_PROJECT="${SNOWCELL_PUBLIC_DATA_STAGE_PROJECT:-/root/snowlotus_public_data_stage_project}"
SEED_ROOT="${SNOWCELL_V3_SEED_ROOT:-/root/snowlotus_public_plants_v3_seed}"
LOG="${ROOT_STAGE}/logs/root_pipeline_watchdog.log"
mkdir -p "${ROOT_STAGE}/logs"
mkdir -p "${SEED_ROOT}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "${LOG}"
}

ensure_session() {
  local session="$1"
  local done_file="$2"
  local command="$3"
  if [ -s "${done_file}" ]; then
    return 0
  fi
  if tmux has-session -t "${session}" 2>/dev/null; then
    return 0
  fi
  log "restarting missing session ${session}"
  tmux new-session -d -s "${session}" "${command}" || true
}

while true; do
  ensure_session \
    snowcell_root_gse243419 \
    "${STAGE_PROJECT}/data/corpus_manifest.gse243419.tsv" \
    "cd ${STAGE_PROJECT} && bash scripts/download_gse243419_cotton_glandular_mtx_subset.sh > logs/gse243419.log 2>&1"
  ensure_session \
    snowcell_root_gse270140 \
    "${ROOT_STAGE}/data/corpus_manifest.gse270140.tsv" \
    "bash ${PROJECT_DIR}/scripts/start_root_gse270140_staging.sh > ${ROOT_STAGE}/logs/gse270140_root.log 2>&1"
  ensure_session \
    snowcell_root_v3_pipeline \
    "${ROOT_STAGE}/../snowlotus_public_plants_v3/public_plants_v3_summary.json" \
    "bash ${PROJECT_DIR}/scripts/run_root_v3_public_pipeline.sh > /root/snowlotus_public_plants_v3/pipeline_tmux.log 2>&1"
  ensure_session \
    snowcell_root_v3_seed_pipeline \
    "${SEED_ROOT}/public_plants_v3_seed_summary.json" \
    "bash ${PROJECT_DIR}/scripts/run_v3_seed_public_pipeline.sh > ${SEED_ROOT}/pipeline_tmux.log 2>&1"
  sleep "${SNOWCELL_WATCHDOG_POLL_SECONDS:-300}"
done
