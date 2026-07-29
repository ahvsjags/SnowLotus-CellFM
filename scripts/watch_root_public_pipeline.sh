#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
ROOT_STAGE="${SNOWCELL_PUBLIC_DATA_STAGE_ROOT:-/root/snowlotus_public_data_stage}"
STAGE_PROJECT="${SNOWCELL_PUBLIC_DATA_STAGE_PROJECT:-/root/snowlotus_public_data_stage_project}"
SEED_ROOT="${SNOWCELL_V3_SEED_ROOT:-/root/snowlotus_public_plants_v3_seed_fixed}"
INTERIM_ROOT="${SNOWCELL_INTERIM_TRAIN_ROOT:-/root/snowlotus_cellfm_interim_gpu_4090}"
LOG="${ROOT_STAGE}/logs/root_pipeline_watchdog.log"
mkdir -p "${ROOT_STAGE}/logs"
mkdir -p "${SEED_ROOT}"
mkdir -p "${STAGE_PROJECT}/logs"
mkdir -p "${INTERIM_ROOT}"

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
    local pane_dead
    pane_dead="$(tmux list-panes -t "${session}" -F '#{pane_dead}' 2>/dev/null | head -n 1 || true)"
    if [ "${pane_dead}" = "0" ]; then
      return 0
    fi
    tmux kill-session -t "${session}" 2>/dev/null || true
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
  ensure_session \
    snowcell_interim_gpu_train \
    "${INTERIM_ROOT}/test_metrics.json" \
    "cd ${PROJECT_DIR} && PYTHONPATH=src /root/miniconda3/envs/myconda/bin/python -u -X utf8 -m snowcell.cli train --config configs/generated/foundation_public_plants_interim_gpu_4090.yaml --device cuda > ${INTERIM_ROOT}/train.log 2>&1"
  sleep "${SNOWCELL_WATCHDOG_POLL_SECONDS:-300}"
done
