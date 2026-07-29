#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
V4_TRAIN="${SNOWCELL_V4_TRAIN_ROOT:-/root/snowlotus_cellfm_v4_4090}"
V5_ROOT="${SNOWCELL_V5_ROOT:-/root/snowlotus_public_plants_v5}"
V6_ROOT="${SNOWCELL_V6_ROOT:-/root/snowlotus_cellfm_v6_4090}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
MANIFEST="${V5_ROOT}/corpus_manifest_public_plants_v5.tsv"
SUMMARY="${V5_ROOT}/public_plants_v5_summary.json"
CORPUS="${V5_ROOT}/plant_foundation_corpus_public_plants_v5.h5ad"
BENCHMARK="${V6_ROOT}/v6_cross_species_benchmark.json"
COMPARISON="${V6_ROOT}/v6_vs_v4_checkpoint_comparison.json"
COMPARISON_MD="${V6_ROOT}/v6_vs_v4_checkpoint_comparison.md"

mkdir -p "${V6_ROOT}"
while [ ! -s "${SUMMARY}" ] || [ ! -d "${CORPUS}" ]; do
  sleep "${SNOWCELL_V6_POLL_SECONDS:-120}"
done

cd "${PROJECT_DIR}"
if [ ! -s "${V6_ROOT}/test_metrics.json" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u -X utf8 \
    -m snowcell.cli train \
    --config configs/generated/foundation_public_plants_v6_4090.yaml \
    --device cuda \
    > "${V6_ROOT}/train.log" 2>&1
fi

if [ ! -s "${BENCHMARK}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/benchmark_public_plants_v1.py \
    --project-dir "${PROJECT_DIR}" \
    --checkpoint "${V6_ROOT}/best.pt" \
    --data "${CORPUS}" \
    --manifest "${MANIFEST}" \
    --output "${BENCHMARK}" \
    --max-cells-per-dataset 256 \
    --batch-size 64 \
    --device cuda \
    > "${V6_ROOT}/benchmark.log" 2>&1
fi

if [ ! -s "${COMPARISON}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 \
    scripts/compare_all_plant_checkpoint_benchmarks.py \
    --baseline "${V4_TRAIN}/v4_cross_species_benchmark.json" \
    --candidate "${BENCHMARK}" \
    --output-json "${COMPARISON}" \
    --output-md "${COMPARISON_MD}"
fi

PACKAGE="${PROJECT_DIR}/outputs/publication_package"
mkdir -p "${PACKAGE}/benchmarks/v6" \
  "${PACKAGE}/strict_benchmarks/v6" \
  "${PACKAGE}/v6_training" \
  "${PACKAGE}/checkpoints/v6_4090"
cp -f "${MANIFEST}" "${PACKAGE}/benchmarks/v6/v5_public_plants_corpus_manifest.tsv"
cp -f "${SUMMARY}" "${PACKAGE}/benchmarks/v6/v5_public_plants_corpus_summary.json"
cp -f "${BENCHMARK}" "${PACKAGE}/benchmarks/v6/"
cp -f "${COMPARISON}" "${PACKAGE}/benchmarks/v6/"
cp -f "${COMPARISON_MD}" "${PACKAGE}/benchmarks/v6/"
cp -f "${V6_ROOT}/best.pt" "${PACKAGE}/checkpoints/v6_4090/best.pt"
for file in config.resolved.json history.json test_metrics.json preprocessing_stats.json progress_latest.json; do
  [ -f "${V6_ROOT}/${file}" ] && cp -f "${V6_ROOT}/${file}" "${PACKAGE}/strict_benchmarks/v6/v6_${file}"
done
cp -f "${V6_ROOT}/train.log" "${PACKAGE}/v6_training/" 2>/dev/null || true
cp -f "${V6_ROOT}/benchmark.log" "${PACKAGE}/v6_training/" 2>/dev/null || true
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 \
  scripts/write_artifact_checksums.py \
  --project-dir "${PROJECT_DIR}" \
  --output "${PACKAGE}/artifact_checksums.tsv" \
  > "${V6_ROOT}/artifact_checksums.log" 2>&1
touch "${V6_ROOT}/v6_pipeline_complete.marker"
echo "v6 public plants pipeline complete"
