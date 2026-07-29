#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
V3_ROOT="${SNOWCELL_V3_ROOT:-/root/snowlotus_public_plants_v3}"
TRAIN_ROOT="${SNOWCELL_V3_EXTENDED_ROOT:-/root/snowlotus_cellfm_v3_extended_4090}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
CORPUS="${V3_ROOT}/plant_foundation_corpus_public_plants_v3.h5ad"
MANIFEST="${V3_ROOT}/corpus_manifest_public_plants_v3.tsv"
BENCHMARK="${TRAIN_ROOT}/v3_extended_cross_species_benchmark.json"
COMPARISON="${TRAIN_ROOT}/v3_extended_vs_v3_checkpoint_comparison.json"
COMPARISON_MD="${TRAIN_ROOT}/v3_extended_vs_v3_checkpoint_comparison.md"

mkdir -p "${TRAIN_ROOT}"
while [ ! -s "${TRAIN_ROOT}/test_metrics.json" ]; do
  sleep "${SNOWCELL_V3_EXTENDED_POLL_SECONDS:-120}"
done

cd "${PROJECT_DIR}"
if [ ! -s "${BENCHMARK}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/benchmark_public_plants_v1.py \
    --project-dir "${PROJECT_DIR}" \
    --checkpoint "${TRAIN_ROOT}/best.pt" \
    --data "${CORPUS}" \
    --manifest "${MANIFEST}" \
    --output "${BENCHMARK}" \
    --max-cells-per-dataset 256 \
    --batch-size 64 \
    --device cuda > "${TRAIN_ROOT}/benchmark.log" 2>&1
fi

if [ ! -s "${COMPARISON}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 \
    scripts/compare_all_plant_checkpoint_benchmarks.py \
    --baseline "/root/snowlotus_cellfm_v3_4090/v3_cross_species_benchmark.json" \
    --candidate "${BENCHMARK}" \
    --output-json "${COMPARISON}" \
    --output-md "${COMPARISON_MD}"
fi

PACKAGE="${PROJECT_DIR}/outputs/publication_package"
mkdir -p "${PACKAGE}/benchmarks/v3_extended" \
  "${PACKAGE}/strict_benchmarks/v3_extended" \
  "${PACKAGE}/v3_extended_training" \
  "${PACKAGE}/checkpoints/v3_extended_4090"
cp -f "${MANIFEST}" "${PACKAGE}/benchmarks/v3_extended/v3_extended_public_plants_corpus_manifest.tsv"
cp -f "${V3_ROOT}/public_plants_v3_summary.json" "${PACKAGE}/benchmarks/v3_extended/v3_extended_public_plants_corpus_summary.json"
cp -f "${BENCHMARK}" "${PACKAGE}/benchmarks/v3_extended/"
cp -f "${COMPARISON}" "${PACKAGE}/benchmarks/v3_extended/"
cp -f "${COMPARISON_MD}" "${PACKAGE}/benchmarks/v3_extended/"
cp -f "${TRAIN_ROOT}/best.pt" "${PACKAGE}/checkpoints/v3_extended_4090/best.pt"
for file in config.resolved.json history.json test_metrics.json preprocessing_stats.json progress_latest.json; do
  [ -f "${TRAIN_ROOT}/${file}" ] && cp -f "${TRAIN_ROOT}/${file}" "${PACKAGE}/strict_benchmarks/v3_extended/v3_extended_${file}"
done
cp -f "${TRAIN_ROOT}/train.log" "${PACKAGE}/v3_extended_training/" 2>/dev/null || true
cp -f "${TRAIN_ROOT}/benchmark.log" "${PACKAGE}/v3_extended_training/" 2>/dev/null || true
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 \
  scripts/write_artifact_checksums.py \
  --project-dir "${PROJECT_DIR}" \
  --output "${PACKAGE}/artifact_checksums.tsv" \
  > "${TRAIN_ROOT}/artifact_checksums.log" 2>&1
echo "v3 extended evaluation and package complete"
