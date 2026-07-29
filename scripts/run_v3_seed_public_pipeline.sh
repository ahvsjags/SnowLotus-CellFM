#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
SEED_ROOT="${SNOWCELL_V3_SEED_ROOT:-/root/snowlotus_public_plants_v3_seed}"
SEED_TRAIN="/root/snowlotus_cellfm_v3_seed_4090"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
export PATH="$(dirname "${PYTHON_BIN}"):${PATH}"
LOG_DIR="${SEED_ROOT}/logs"
mkdir -p "${SEED_ROOT}" "${SEED_TRAIN}" "${LOG_DIR}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "${LOG_DIR}/pipeline.log"
}

seed_manifest="${SEED_ROOT}/corpus_manifest_public_plants_v3_seed.tsv"
seed_corpus="${SEED_ROOT}/plant_foundation_corpus_public_plants_v3_seed.h5ad"
seed_summary="${SEED_ROOT}/public_plants_v3_seed_summary.json"
extra_manifest="${PROJECT_DIR}/data/corpus_manifest.gse268881.available.tsv"

if [ ! -s "${seed_summary}" ]; then
  log "building v3 seed corpus from v2 plus available GSE268881"
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    "${PROJECT_DIR}/scripts/build_public_mlm_corpus_on_disk.py" \
    --base-manifest /root/snowlotus_public_plants_v2/corpus_manifest_public_plants_v2_fixed.tsv \
    --extra-manifest "${extra_manifest}" \
    --manifest-output "${seed_manifest}" \
    --output "${seed_corpus}" \
    --work-dir "${SEED_ROOT}/work" \
    --summary-output "${seed_summary}" \
    --skip-errors --keep-shards >> "${LOG_DIR}/build_seed.log" 2>&1
fi

if [ -s "${seed_summary}" ] && ! tmux has-session -t snowcell_public_plants_v3_seed_train 2>/dev/null; then
  log "starting v3 seed training"
  tmux new-session -d -s snowcell_public_plants_v3_seed_train \
    "cd ${PROJECT_DIR} && PYTHONPATH=src ${PYTHON_BIN} -u -X utf8 -m snowcell.cli train --config configs/generated/foundation_public_plants_v3_seed_4090.yaml --device cuda > ${SEED_TRAIN}/train.log 2>&1"
fi

while [ ! -s "${SEED_TRAIN}/test_metrics.json" ]; do
  log "waiting for v3 seed training test metrics"
  sleep "${SNOWCELL_V3_SEED_POLL_SECONDS:-120}"
done

benchmark="${SEED_TRAIN}/v3_seed_cross_species_benchmark.json"
if [ ! -s "${benchmark}" ] && ! tmux has-session -t snowcell_public_plants_v3_seed_benchmark 2>/dev/null; then
  log "starting v3 seed cross-species benchmark"
  tmux new-session -d -s snowcell_public_plants_v3_seed_benchmark \
    "cd ${PROJECT_DIR} && PYTHONPATH=src ${PYTHON_BIN} -u scripts/benchmark_public_plants_v1.py --project-dir ${PROJECT_DIR} --checkpoint ${SEED_TRAIN}/best.pt --data ${seed_corpus} --manifest ${seed_manifest} --output ${benchmark} --max-cells-per-dataset 256 --batch-size 64 --device cuda > ${SEED_TRAIN}/benchmark.log 2>&1"
fi

while [ ! -s "${benchmark}" ]; do
  log "waiting for v3 seed benchmark"
  sleep "${SNOWCELL_V3_SEED_POLL_SECONDS:-120}"
done

comparison_json="${SEED_TRAIN}/v3_seed_vs_v1_checkpoint_comparison.json"
comparison_md="${SEED_TRAIN}/v3_seed_vs_v1_checkpoint_comparison.md"
if [ ! -s "${comparison_json}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 \
    "${PROJECT_DIR}/scripts/compare_all_plant_checkpoint_benchmarks.py" \
    --baseline "${PROJECT_DIR}/outputs/benchmarks/public_plants_v1_continuation_checkpoint.json" \
    --candidate "${benchmark}" --output-json "${comparison_json}" --output-md "${comparison_md}"
fi

package="${PROJECT_DIR}/outputs/publication_package"
mkdir -p "${package}/benchmarks/v3_seed" "${package}/strict_benchmarks/v3_seed" "${package}/v3_seed_training"
cp -f "${seed_manifest}" "${package}/benchmarks/v3_seed/v3_seed_public_plants_corpus_manifest.tsv"
cp -f "${seed_summary}" "${package}/benchmarks/v3_seed/v3_seed_public_plants_corpus_summary.json"
cp -f "${benchmark}" "${package}/benchmarks/v3_seed/v3_seed_public_plants_cross_species.json"
cp -f "${comparison_json}" "${package}/benchmarks/v3_seed/v3_seed_vs_v1_checkpoint_comparison.json"
cp -f "${comparison_md}" "${package}/benchmarks/v3_seed/v3_seed_vs_v1_checkpoint_comparison.md"
for file in config.resolved.json history.json test_metrics.json preprocessing_stats.json progress_latest.json; do
  [ -f "${SEED_TRAIN}/${file}" ] && cp -f "${SEED_TRAIN}/${file}" "${package}/strict_benchmarks/v3_seed/v3_seed_${file}"
done
cp -f "${SEED_TRAIN}/train.log" "${package}/v3_seed_training/v3_seed_train.log" 2>/dev/null || true
cp -f "${SEED_TRAIN}/benchmark.log" "${package}/v3_seed_training/v3_seed_benchmark.log" 2>/dev/null || true
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 \
  "${PROJECT_DIR}/scripts/write_artifact_checksums.py" \
  --output "${package}/artifact_checksums.tsv" >> "${LOG_DIR}/pipeline.log" 2>&1 || true
log "v3 seed pipeline complete"
