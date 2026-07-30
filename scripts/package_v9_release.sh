#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
V9_ROOT="${SNOWCELL_V9_ROOT:-/root/snowlotus_public_plants_v9}"
TRAIN_ROOT="${SNOWCELL_V9_TRAIN_ROOT:-/root/snowlotus_cellfm_v9_lora_shared_4090}"
PACKAGE="${SNOWCELL_V9_PACKAGE:-${PROJECT_DIR}/outputs/publication_package/v9_lora_shared_4090}"

mkdir -p "${PACKAGE}/benchmarks" "${PACKAGE}/checkpoints" "${PACKAGE}/configs" "${PACKAGE}/scripts" "${PACKAGE}/training"

cp -f "${TRAIN_ROOT}/best.pt" "${PACKAGE}/checkpoints/best.pt"
cp -f "${V9_ROOT}/corpus_manifest_public_plants_v9.tsv" "${PACKAGE}/benchmarks/"
cp -f "${V9_ROOT}/public_plants_v9_summary.json" "${PACKAGE}/benchmarks/"
cp -f "${V9_ROOT}/v9_manifest_audit.json" "${PACKAGE}/benchmarks/"
cp -f "${V9_ROOT}/v3_on_v9_shared_subset_cross_species_benchmark.json" "${PACKAGE}/benchmarks/"
cp -f "${TRAIN_ROOT}/v9_lora_cross_species_benchmark.json" "${PACKAGE}/benchmarks/"
cp -f "${TRAIN_ROOT}/v9_lora_vs_v3_shared_comparison.json" "${PACKAGE}/benchmarks/"
cp -f "${TRAIN_ROOT}/v9_lora_vs_v3_shared_comparison.md" "${PACKAGE}/benchmarks/"
cp -f "${V9_ROOT}/v9_benchmark_subset_256_shared_genes.h5ad" "${PACKAGE}/benchmarks/"
cp -f "${PROJECT_DIR}/configs/generated/foundation_public_plants_v9_lora_4090.yaml" "${PACKAGE}/configs/"

for script in \
  run_v9_build_and_gpu_pipeline.sh \
  run_v8_lora_training.sh \
  run_v8_baseline_benchmark.sh \
  run_v8_lora_benchmark.sh \
  filter_h5ad_to_checkpoint_genes.py \
  materialize_h5ad_benchmark_subset.py \
  compare_all_plant_checkpoint_benchmarks.py \
  serve_snowlotus.py \
  watch_plant_cellfm_service.sh \
  download_geo_raw_tar_mtx_subset.sh; do
  cp -f "${PROJECT_DIR}/scripts/${script}" "${PACKAGE}/scripts/"
done
cp -f "${PROJECT_DIR}/release_metadata/plant_species_adapters.json" "${PACKAGE}/scripts/"

for artifact in config.resolved.json preprocessing_stats.json progress.jsonl progress_latest.json train.log test_metrics.json history.json; do
  if [ -f "${TRAIN_ROOT}/${artifact}" ]; then
    cp -f "${TRAIN_ROOT}/${artifact}" "${PACKAGE}/training/"
  fi
done

cat > "${PACKAGE}/README.paths.txt" <<EOF
SnowLotus-CellFM v9 all-plant release package

Checkpoint: ${PACKAGE}/checkpoints/best.pt
Full corpus: ${V9_ROOT}/plant_foundation_corpus_public_plants_v9.h5ad
Shared-gene corpus: ${V9_ROOT}/plant_foundation_corpus_public_plants_v9_shared_genes.h5ad
Benchmark subset: ${V9_ROOT}/v9_benchmark_subset_256_shared_genes.h5ad
Training output: ${TRAIN_ROOT}
Service: http://127.0.0.1:8000
Model scope: general plant single-cell embedding and annotation transfer
EOF

cat > "${PACKAGE}/MODEL_CARD.md" <<'EOF'
# SnowLotus-CellFM v9

SnowLotus-CellFM v9 is a general plant single-cell foundation checkpoint with a shared-gene representation, hierarchical annotation heads, species-aware runtime adapters, embedding export, and annotation transfer.

## Training corpus

- 56 manifest rows and approximately 13.78 million cells.
- Approximately 1.53 million source genes before shared-gene filtering.
- 21 plant species represented in the v9 corpus manifest.
- The model checkpoint uses the 280,747-gene shared vocabulary inherited from the reproducible checkpoint-gene gate.

## Evaluation

The same v9 shared-gene subset was used for baseline and candidate comparison. Candidate fine-label macro-F1 was 0.3485 for leave-dataset-out, 0.4902 for leave-sample-out, and 0.2897 for leave-species-out. The corresponding baseline values were 0.1203, 0.2372, and 0.1290.

## Reproduction

Use the included configuration and scripts. The full corpus is kept at the server path recorded in `README.paths.txt`; the release package contains the benchmark subset and all training/evaluation metadata.
EOF

touch "${PACKAGE}/release_complete.marker"
(cd "${PACKAGE}" && find . -type f ! -name release_sha256sums.txt -print0 | sort -z | xargs -0 sha256sum > release_sha256sums.txt)
(cd "${PACKAGE}" && sha256sum -c release_sha256sums.txt)
echo "v9 release package complete: ${PACKAGE}"
