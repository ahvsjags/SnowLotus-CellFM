#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
V4_ROOT="${SNOWCELL_V4_ROOT:-/root/snowlotus_public_plants_v4}"
V4_TRAIN="${SNOWCELL_V4_TRAIN_ROOT:-/root/snowlotus_cellfm_v4_4090}"
V5_ROOT="${SNOWCELL_V5_ROOT:-/root/snowlotus_public_plants_v5}"
V5_TRAIN="${SNOWCELL_V5_TRAIN_ROOT:-/root/snowlotus_cellfm_v5_4090}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
V5_MANIFEST="${V5_ROOT}/corpus_manifest_public_plants_v5.tsv"
V5_SUMMARY="${V5_ROOT}/public_plants_v5_summary.json"
V5_CORPUS="${V5_ROOT}/plant_foundation_corpus_public_plants_v5.h5ad"
V5_BENCHMARK="${V5_TRAIN}/v5_cross_species_benchmark.json"
V5_COMPARISON="${V5_TRAIN}/v5_vs_v4_checkpoint_comparison.json"
V5_COMPARISON_MD="${V5_TRAIN}/v5_vs_v4_checkpoint_comparison.md"

mkdir -p "${V5_ROOT}" "${V5_TRAIN}"
while [ ! -s "${V4_TRAIN}/v4_vs_v3_extended_checkpoint_comparison.json" ]; do
  sleep "${SNOWCELL_V5_POLL_SECONDS:-120}"
done
while [ ! -s "${PROJECT_DIR}/data/corpus_manifest.gse325371.tsv" ]; do
  sleep "${SNOWCELL_V5_POLL_SECONDS:-120}"
done

cd "${PROJECT_DIR}"
if [ ! -s "${V5_MANIFEST}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/prepare_public_plants_expansion_manifest.py \
    --manifest "${V4_ROOT}/corpus_manifest_public_plants_v4.tsv" \
    --manifest "${PROJECT_DIR}/data/corpus_manifest.gse234192.tsv" \
    --manifest "${PROJECT_DIR}/data/corpus_manifest.gse325371.tsv" \
    --output "${V5_MANIFEST}" \
    --summary-output "${V5_ROOT}/v5_manifest_audit.json" \
    --project-root "${PROJECT_DIR}" \
    --require-files \
    --fail-on-missing
fi

if [ ! -s "${V5_SUMMARY}" ] || [ ! -d "${V5_CORPUS}" ]; then
  EMPTY_MANIFEST="${V5_ROOT}/empty_manifest.tsv"
  printf 'path\tdataset_id\tspecies\ttissue\tlayer\tlabel_key\tcoarse_label_key\tsample_key\n' > "${EMPTY_MANIFEST}"
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/build_public_mlm_corpus_on_disk.py \
    --base-manifest "${V5_MANIFEST}" \
    --extra-manifest "${EMPTY_MANIFEST}" \
    --manifest-output "${V5_MANIFEST}" \
    --output "${V5_CORPUS}" \
    --work-dir "${V5_ROOT}/work" \
    --summary-output "${V5_SUMMARY}" \
    > "${V5_ROOT}/build_v5.log" 2>&1
fi

if [ ! -s "${V5_TRAIN}/test_metrics.json" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u -X utf8 \
    -m snowcell.cli train \
    --config configs/generated/foundation_public_plants_v5_4090.yaml \
    --device cuda \
    > "${V5_TRAIN}/train.log" 2>&1
fi

if [ ! -s "${V5_BENCHMARK}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/benchmark_public_plants_v1.py \
    --project-dir "${PROJECT_DIR}" \
    --checkpoint "${V5_TRAIN}/best.pt" \
    --data "${V5_CORPUS}" \
    --manifest "${V5_MANIFEST}" \
    --output "${V5_BENCHMARK}" \
    --max-cells-per-dataset 256 \
    --batch-size 64 \
    --device cuda \
    > "${V5_TRAIN}/benchmark.log" 2>&1
fi

if [ ! -s "${V5_COMPARISON}" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 \
    scripts/compare_all_plant_checkpoint_benchmarks.py \
    --baseline "${V4_TRAIN}/v4_cross_species_benchmark.json" \
    --candidate "${V5_BENCHMARK}" \
    --output-json "${V5_COMPARISON}" \
    --output-md "${V5_COMPARISON_MD}"
fi

PACKAGE="${PROJECT_DIR}/outputs/publication_package"
mkdir -p "${PACKAGE}/benchmarks/v5" \
  "${PACKAGE}/strict_benchmarks/v5" \
  "${PACKAGE}/v5_training" \
  "${PACKAGE}/checkpoints/v5_4090"
cp -f "${V5_MANIFEST}" "${PACKAGE}/benchmarks/v5/v5_public_plants_corpus_manifest.tsv"
cp -f "${V5_SUMMARY}" "${PACKAGE}/benchmarks/v5/v5_public_plants_corpus_summary.json"
cp -f "${V5_ROOT}/v5_manifest_audit.json" "${PACKAGE}/benchmarks/v5/"
cp -f "${V5_BENCHMARK}" "${PACKAGE}/benchmarks/v5/"
cp -f "${V5_COMPARISON}" "${PACKAGE}/benchmarks/v5/"
cp -f "${V5_COMPARISON_MD}" "${PACKAGE}/benchmarks/v5/"
cp -f "${V5_TRAIN}/best.pt" "${PACKAGE}/checkpoints/v5_4090/best.pt"
for file in config.resolved.json history.json test_metrics.json preprocessing_stats.json progress_latest.json; do
  [ -f "${V5_TRAIN}/${file}" ] && cp -f "${V5_TRAIN}/${file}" "${PACKAGE}/strict_benchmarks/v5/v5_${file}"
done
cp -f "${V5_TRAIN}/train.log" "${PACKAGE}/v5_training/" 2>/dev/null || true
cp -f "${V5_TRAIN}/benchmark.log" "${PACKAGE}/v5_training/" 2>/dev/null || true
PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -X utf8 \
  scripts/write_artifact_checksums.py \
  --project-dir "${PROJECT_DIR}" \
  --output "${PACKAGE}/artifact_checksums.tsv" \
  > "${V5_TRAIN}/artifact_checksums.log" 2>&1
touch "${V5_TRAIN}/v5_pipeline_complete.marker"
echo "v5 public plants pipeline complete"
