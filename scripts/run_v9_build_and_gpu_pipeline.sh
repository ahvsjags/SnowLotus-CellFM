#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
V8_ROOT="/root/snowlotus_public_plants_v8"
V9_ROOT="${SNOWCELL_V9_ROOT:-/root/snowlotus_public_plants_v9}"
V9_DATA="${SNOWCELL_V9_DATA_ROOT:-/root/snowlotus_v9_public_data}"
TRAIN_ROOT="${SNOWCELL_V9_TRAIN_ROOT:-/root/snowlotus_cellfm_v9_lora_shared_4090}"
V9_MANIFEST="${V9_ROOT}/corpus_manifest_public_plants_v9.tsv"

cd "${PROJECT_DIR}"
mkdir -p "${V9_ROOT}/work" "${TRAIN_ROOT}"
echo "Waiting for v9 GEO manifests under ${V9_DATA}"
while [ ! -s "${V9_DATA}/corpus_manifest.gse157757.tsv" ] \
   || [ ! -s "${V9_DATA}/corpus_manifest.gse182507.tsv" ] \
   || [ ! -s "${V9_DATA}/corpus_manifest.gse180121.tsv" ]; do
  sleep 60
done

if [ ! -s "${V9_ROOT}/v9_manifest_audit.json" ]; then
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/prepare_public_plants_expansion_manifest.py \
    --manifest "${V8_ROOT}/corpus_manifest_public_plants_v8.tsv" \
    --manifest "${V9_DATA}/corpus_manifest.gse157757.tsv" \
    --manifest "${V9_DATA}/corpus_manifest.gse182507.tsv" \
    --manifest "${V9_DATA}/corpus_manifest.gse180121.tsv" \
    --output "${V9_MANIFEST}" \
    --summary-output "${V9_ROOT}/v9_manifest_audit.json" \
    --project-root "${PROJECT_DIR}" \
    --require-files --fail-on-missing
fi

if [ ! -s "${V9_ROOT}/plant_foundation_corpus_public_plants_v9.h5ad" ]; then
  if [ ! -d "${V9_ROOT}/work/shards" ]; then
    cp -al "${V8_ROOT}/work/shards" "${V9_ROOT}/work/shards"
  fi
  PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
    scripts/build_public_mlm_corpus_on_disk.py \
    --base-manifest "${V9_MANIFEST}" \
    --extra-manifest "${V8_ROOT}/../snowlotus_public_plants_v5/empty_manifest.tsv" \
    --manifest-output "${V9_MANIFEST}" \
    --output "${V9_ROOT}/plant_foundation_corpus_public_plants_v9.h5ad" \
    --work-dir "${V9_ROOT}/work" \
    --summary-output "${V9_ROOT}/public_plants_v9_summary.json" \
    --max-loaded-elems 100000000 --reuse-shards \
    > "${V9_ROOT}/build_v9.log" 2>&1
fi

export SNOWCELL_V8_CONFIG="${PROJECT_DIR}/configs/generated/foundation_public_plants_v9_lora_4090.yaml"
export SNOWCELL_V8_ROOT="${V9_ROOT}"
export SNOWCELL_V8_TRAIN_ROOT="${TRAIN_ROOT}"
export SNOWCELL_V8_FULL_CORPUS="${V9_ROOT}/plant_foundation_corpus_public_plants_v9.h5ad"
export SNOWCELL_V8_SHARED_CORPUS="${V9_ROOT}/plant_foundation_corpus_public_plants_v9_shared_genes.h5ad"
export SNOWCELL_V8_SHARED_SUBSET="${V9_ROOT}/v9_benchmark_subset_256_shared_genes.h5ad"
export SNOWCELL_V8_BASELINE_BENCHMARK="${V9_ROOT}/v3_on_v9_shared_subset_cross_species_benchmark.json"
export SNOWCELL_V8_CANDIDATE_BENCHMARK="${TRAIN_ROOT}/v9_lora_cross_species_benchmark.json"

if [ ! -s "${TRAIN_ROOT}/training_complete.marker" ] || [ ! -s "${TRAIN_ROOT}/best.pt" ]; then
  bash scripts/run_v8_lora_training.sh
fi
bash scripts/run_v8_baseline_benchmark.sh
bash scripts/run_v8_lora_benchmark.sh

PYTHONPATH="${PROJECT_DIR}/src" "${PYTHON_BIN}" -u \
  scripts/compare_all_plant_checkpoint_benchmarks.py \
  --baseline "${V9_ROOT}/v3_on_v9_shared_subset_cross_species_benchmark.json" \
  --candidate "${TRAIN_ROOT}/v9_lora_cross_species_benchmark.json" \
  --output-json "${TRAIN_ROOT}/v9_lora_vs_v3_shared_comparison.json" \
  --output-md "${TRAIN_ROOT}/v9_lora_vs_v3_shared_comparison.md"

touch "${TRAIN_ROOT}/pipeline_complete.marker"
echo "v9 build and GPU pipeline complete: ${TRAIN_ROOT}"
