#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
BASE_ROOT="/root/snowlotus_public_plants_v9"
V10_ROOT="${SNOWCELL_V10_ROOT:-/root/snowlotus_public_plants_v10}"
V10_DATA="${SNOWCELL_V10_DATA_ROOT:-/root/snowlotus_v10_public_data}"
TRAIN_ROOT="${SNOWCELL_V10_TRAIN_ROOT:-/root/snowlotus_cellfm_v10_lora_shared_4090}"
V10_MANIFEST="${V10_ROOT}/corpus_manifest_public_plants_v10.tsv"

cd "${PROJECT_DIR}"
mkdir -p "${V10_ROOT}/work" "${TRAIN_ROOT}"
echo "Waiting for v10 GEO manifests under ${V10_DATA}"
while [ ! -s "${V10_DATA}/corpus_manifest.gse273033.tsv" ] \
   || [ ! -s "${V10_DATA}/corpus_manifest.gse308672.tsv" ] \
   || [ ! -s "${V10_DATA}/corpus_manifest.gse336751.tsv" ]; do
  sleep 60
done

if [ ! -s "${V10_ROOT}/v10_manifest_audit.json" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/prepare_public_plants_expansion_manifest.py \
    --manifest "${BASE_ROOT}/corpus_manifest_public_plants_v9.tsv" \
    --manifest "${V10_DATA}/corpus_manifest.gse273033.tsv" \
    --manifest "${V10_DATA}/corpus_manifest.gse308672.tsv" \
    --manifest "${V10_DATA}/corpus_manifest.gse336751.tsv" \
    --output "${V10_MANIFEST}" \
    --summary-output "${V10_ROOT}/v10_manifest_audit.json" \
    --project-root "${PROJECT_DIR}" \
    --require-files --fail-on-missing
fi

if [ ! -s "${V10_ROOT}/plant_foundation_corpus_public_plants_v10.h5ad" ]; then
  if [ ! -d "${V10_ROOT}/work/shards" ] && [ -d "${BASE_ROOT}/work/shards" ]; then
    cp -al "${BASE_ROOT}/work/shards" "${V10_ROOT}/work/shards"
  fi
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/build_public_mlm_corpus_on_disk.py \
    --base-manifest "${V10_MANIFEST}" \
    --extra-manifest "${BASE_ROOT}/../snowlotus_public_plants_v5/empty_manifest.tsv" \
    --manifest-output "${V10_MANIFEST}" \
    --output "${V10_ROOT}/plant_foundation_corpus_public_plants_v10.h5ad" \
    --work-dir "${V10_ROOT}/work" \
    --summary-output "${V10_ROOT}/public_plants_v10_summary.json" \
    --max-loaded-elems 100000000 --reuse-shards \
    > "${V10_ROOT}/build_v10.log" 2>&1
fi

export SNOWCELL_V8_CONFIG="${PROJECT_DIR}/configs/generated/foundation_public_plants_v10_lora_4090.yaml"
export SNOWCELL_V8_ROOT="${V10_ROOT}"
export SNOWCELL_V8_MANIFEST="${V10_MANIFEST}"
export SNOWCELL_V8_TRAIN_ROOT="${TRAIN_ROOT}"
export SNOWCELL_V8_FULL_CORPUS="${V10_ROOT}/plant_foundation_corpus_public_plants_v10.h5ad"
export SNOWCELL_V8_SHARED_CORPUS="${V10_ROOT}/plant_foundation_corpus_public_plants_v10_shared_genes.h5ad"
export SNOWCELL_V8_SHARED_SUBSET="${V10_ROOT}/v10_benchmark_subset_256_shared_genes.h5ad"
export SNOWCELL_V8_BASELINE_BENCHMARK="${V10_ROOT}/v9_on_v10_shared_subset_cross_species_benchmark.json"
export SNOWCELL_V8_CANDIDATE_BENCHMARK="${TRAIN_ROOT}/v10_lora_cross_species_benchmark.json"

if [ ! -s "${TRAIN_ROOT}/training_complete.marker" ] || [ ! -s "${TRAIN_ROOT}/best.pt" ]; then
  bash scripts/run_v8_lora_training.sh
fi
bash scripts/run_v8_baseline_benchmark.sh
bash scripts/run_v8_lora_benchmark.sh

PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
  scripts/compare_all_plant_checkpoint_benchmarks.py \
  --baseline "${V10_ROOT}/v9_on_v10_shared_subset_cross_species_benchmark.json" \
  --candidate "${TRAIN_ROOT}/v10_lora_cross_species_benchmark.json" \
  --output-json "${TRAIN_ROOT}/v10_lora_vs_v9_shared_comparison.json" \
  --output-md "${TRAIN_ROOT}/v10_lora_vs_v9_shared_comparison.md"

touch "${TRAIN_ROOT}/pipeline_complete.marker"
echo "v10 build and GPU pipeline complete: ${TRAIN_ROOT}"
