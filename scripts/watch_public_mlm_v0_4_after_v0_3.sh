#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
cd "${PROJECT_DIR}"
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs configs/generated

poll_seconds="${SNOWCELL_MLM_V0_4_POLL_SECONDS:-600}"
v03_session="${SNOWCELL_MLM_V0_3_SESSION:-snowcell_mlm_public_expansion_v0_3}"
v03_config="${SNOWCELL_MLM_V0_3_CONFIG:-configs/generated/foundation_5090_mlm_public_expansion_continuation_v0_3.yaml}"
v03_output_dir="${SNOWCELL_MLM_V0_3_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm}"
v03_best="${SNOWCELL_MLM_V0_3_BEST:-${v03_output_dir}/best.pt}"

v04_session="${SNOWCELL_MLM_V0_4_SESSION:-snowcell_mlm_public_expansion_v0_4_plus_latest}"
v04_config="${SNOWCELL_MLM_V0_4_CONFIG:-configs/generated/foundation_5090_mlm_public_expansion_v0_4_plus_latest.yaml}"
v04_output_dir="${SNOWCELL_MLM_V0_4_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_expansion_v0_4_plus_latest_seed48_b8_vocabwarm}"
plus_manifest="${SNOWCELL_PLUS_MLM_CORPUS_MANIFEST:-data/corpus_manifest_public_mlm_plus_latest.tsv}"
plus_corpus="${SNOWCELL_PLUS_MLM_CORPUS_OUTPUT:-data/plant_foundation_corpus_public_mlm_plus_latest.h5ad}"
device="${SNOWCELL_MLM_V0_4_DEVICE:-cuda}"
post_release_script="${SNOWCELL_MLM_V0_4_POST_RELEASE_SCRIPT:-scripts/run_public_mlm_v0_4_post_training_release.sh}"

active_train_processes() {
  pgrep -af "[s]nowcell train --config" 2>/dev/null || true
}

v03_is_active() {
  if tmux has-session -t "=${v03_session}" 2>/dev/null; then
    return 0
  fi
  if active_train_processes | grep -Fq "${v03_config}"; then
    return 0
  fi
  return 1
}

v04_already_done() {
  [ -s "${v04_output_dir}/best.pt" ] || [ -s "${v04_output_dir}/test_metrics.json" ]
}

needs_plus_rebuild() {
  if [ ! -s "${plus_corpus}" ] || [ ! -s "${plus_manifest}" ]; then
    return 0
  fi
  find data -maxdepth 1 -type f \( -name "corpus_manifest.gse*.tsv" -o -name "corpus_manifest.scplantdb*.tsv" \) ! -name "*.available.tsv" -newer "${plus_corpus}" | grep -q .
}

echo "[$(date)] SnowLotus v0.4 after-v0.3 watcher started"
while true; do
  if v04_already_done; then
    echo "[$(date)] v0.4 output already exists: ${v04_output_dir}"
    if [ -s "${post_release_script}" ]; then
      echo "[$(date)] running v0.4 post-training release hook"
      bash "${post_release_script}" || true
    fi
    exit 0
  fi

  if tmux has-session -t "=${v04_session}" 2>/dev/null; then
    echo "[$(date)] v0.4 training session already running: ${v04_session}"
    sleep "${poll_seconds}"
    continue
  fi

  if v03_is_active; then
    echo "[$(date)] v0.3 still active; waiting before plus-corpus/v0.4 launch"
    sleep "${poll_seconds}"
    continue
  fi

  if [ ! -s "${v03_best}" ]; then
    echo "[$(date)] waiting for v0.3 best checkpoint: ${v03_best}"
    sleep "${poll_seconds}"
    continue
  fi

  running="$(active_train_processes)"
  if [ -n "${running}" ]; then
    echo "[$(date)] another SnowLotus training process is active; waiting"
    printf '%s\n' "${running}" | head -5
    sleep "${poll_seconds}"
    continue
  fi

  if needs_plus_rebuild; then
    echo "[$(date)] building plus public MLM corpus: ${plus_corpus}"
    bash scripts/build_public_mlm_plus_corpus.sh
  else
    echo "[$(date)] plus public MLM corpus already current: ${plus_corpus}"
  fi

  python scripts/write_public_mlm_v0_4_config.py \
    --base-config "${v03_config}" \
    --output "${v04_config}" \
    --corpus "${plus_corpus}" \
    --init-checkpoint "${v03_best}" \
    --output-dir "${v04_output_dir}"

  stamp="$(date +%Y%m%d_%H%M%S)"
  log_path="logs/mlm_public_expansion_v0_4_plus_latest_${stamp}.log"
  echo "[$(date)] launching v0.4 public MLM training: ${v04_session}"
  tmux new-session -d -s "${v04_session}" \
    "cd '${PROJECT_DIR}' && source .venv/bin/activate 2>/dev/null || true; snowcell train --config '${v04_config}' --device '${device}' 2>&1 | tee '${log_path}'; bash '${post_release_script}' 2>&1 | tee -a '${log_path}'"
  exit 0
done
