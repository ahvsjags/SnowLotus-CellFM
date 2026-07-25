#!/usr/bin/env bash
set -euo pipefail

cd /root/snowlotus-cellfm
source .venv/bin/activate 2>/dev/null || true

mkdir -p configs/generated outputs/strict_benchmarks

base_config="${SNOWCELL_BENCHMARK_BASE_CONFIG:-configs/foundation_5090_public_sprint.yaml}"
public_corpus="${SNOWCELL_BENCHMARK_CORPUS:-data/plant_foundation_corpus_public_mlm.h5ad}"
available_corpus="${SNOWCELL_AVAILABLE_BENCHMARK_CORPUS:-data/plant_foundation_corpus_public_mlm_available.h5ad}"

run_audit_and_optional_baseline() {
  local name="$1"
  local config="$2"
  local audit="outputs/strict_benchmarks/${name}.split_audit.json"
  local baseline="outputs/strict_benchmarks/${name}.centroid_baseline.json"

  python scripts/audit_leaveout_splits.py --config "$config" --output "$audit"
  if python - "$audit" <<'PY'
import json
import sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
raise SystemExit(0 if payload.get("supervised_benchmark_ready") else 1)
PY
  then
    snowcell baseline-centroid --config "$config" --output "$baseline"
  else
    echo "Skipping centroid baseline for $name; split audit says supervised_benchmark_ready=false"
  fi
}

if [ -s "data/plant_foundation_corpus.h5ad" ]; then
  run_audit_and_optional_baseline \
    public_sprint_group_random \
    "$base_config"
  snowcell marker-candidates \
    --config "$base_config" \
    --output outputs/strict_benchmarks/public_sprint.marker_candidates.tsv \
    --summary-output outputs/strict_benchmarks/public_sprint.marker_candidates.json \
    --top-n 20 \
    --min-cells 20 || true
fi

if [ -s "$public_corpus" ]; then
  python scripts/create_leaveout_config.py \
    --base-config "$base_config" \
    --output configs/generated/leaveout_brassicaceae_dataset.yaml \
    --data-path "$public_corpus" \
    --leaveout-key dataset_id \
    --test-value brassicaceae_multi_species_root_atlas \
    --output-dir outputs/strict_benchmarks/leaveout_brassicaceae_dataset_train
  run_audit_and_optional_baseline \
    leaveout_brassicaceae_dataset \
    configs/generated/leaveout_brassicaceae_dataset.yaml

  python scripts/create_leaveout_config.py \
    --base-config "$base_config" \
    --output configs/generated/leaveout_eutrema_species.yaml \
    --data-path "$public_corpus" \
    --leaveout-key species \
    --test-value "Eutrema salsugineum" \
    --validation-value "Sisymbrium irio" \
    --output-dir outputs/strict_benchmarks/leaveout_eutrema_species_train
  run_audit_and_optional_baseline \
    leaveout_eutrema_species \
    configs/generated/leaveout_eutrema_species.yaml
else
  echo "Public MLM corpus not found yet: $public_corpus"
fi

if [ -s "$available_corpus" ]; then
  python scripts/create_leaveout_config.py \
    --base-config "$base_config" \
    --output configs/generated/leaveout_brassicaceae_dataset_available.yaml \
    --data-path "$available_corpus" \
    --leaveout-key dataset_id \
    --test-value brassicaceae_multi_species_root_atlas \
    --output-dir outputs/strict_benchmarks/leaveout_brassicaceae_dataset_available_train
  run_audit_and_optional_baseline \
    leaveout_brassicaceae_dataset_available \
    configs/generated/leaveout_brassicaceae_dataset_available.yaml
fi

bash scripts/generate_publication_package.sh
