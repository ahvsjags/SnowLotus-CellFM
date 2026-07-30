#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
V8_ROOT="${SNOWCELL_V8_ROOT:-/root/snowlotus_public_plants_v8}"
TRAIN_ROOT="${SNOWCELL_V8_TRAIN_ROOT:-/root/snowlotus_cellfm_v8_lora_shared_4090}"
BUILD_PID_PATTERN="build_public_mlm_corpus_on_disk.py.*public_plants_v8"

cd "${PROJECT_DIR}"
mkdir -p "${TRAIN_ROOT}"

echo "Waiting for v8 corpus build: ${V8_ROOT}"
while [ ! -s "${V8_ROOT}/public_plants_v8_summary.json" ]; do
  if ! pgrep -f "${BUILD_PID_PATTERN}" >/dev/null 2>&1; then
    echo "v8 corpus build exited before writing its summary" >&2
    tail -80 "${V8_ROOT}/build_v8.log" >&2 || true
    exit 3
  fi
  sleep 30
done

if [ ! -s "${TRAIN_ROOT}/training_complete.marker" ] || [ ! -s "${TRAIN_ROOT}/best.pt" ]; then
  bash scripts/run_v8_lora_training.sh
fi

bash scripts/run_v8_baseline_benchmark.sh
bash scripts/run_v8_lora_benchmark.sh

PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
  scripts/compare_all_plant_checkpoint_benchmarks.py \
  --baseline "${V8_ROOT}/v3_on_v8_shared_subset_cross_species_benchmark.json" \
  --candidate "${TRAIN_ROOT}/v8_lora_cross_species_benchmark.json" \
  --output-json "${TRAIN_ROOT}/v8_lora_vs_v3_shared_comparison.json" \
  --output-md "${TRAIN_ROOT}/v8_lora_vs_v3_shared_comparison.md"

touch "${TRAIN_ROOT}/pipeline_complete.marker"
echo "v8 GPU pipeline complete: ${TRAIN_ROOT}"
