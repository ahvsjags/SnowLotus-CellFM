#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs outputs data external

bash scripts/install_server_dependencies.sh
bash scripts/collect_public_data.sh

source .venv/bin/activate

echo "== code quality and tests =="
python -m ruff check src tests
python -m pytest -q

echo "== smoke validation =="
snowcell make-demo --output data/demo.npz
snowcell baseline-centroid --config configs/smoke.yaml --output outputs/smoke/centroid_baseline.json
snowcell train --config configs/smoke.yaml --device auto
snowcell predict \
  --checkpoint outputs/smoke/best.pt \
  --data data/demo.npz \
  --output outputs/smoke/predictions.csv

if [ -f data/corpus_manifest.tsv ]; then
  echo "== build foundation corpus =="
  snowcell build-corpus \
    --manifest data/corpus_manifest.tsv \
    --output data/plant_foundation_corpus.h5ad
else
  echo "data/corpus_manifest.tsv not found; copy data/corpus_manifest.template.tsv and fill paths."
fi

if [ -f data/plant_foundation_corpus.h5ad ]; then
  echo "== foundation pretraining =="
  snowcell baseline-centroid \
    --config configs/foundation_5090_pretrain.yaml \
    --output outputs/foundation_5090_pretrain/centroid_baseline.json || true
  snowcell train --config configs/foundation_5090_pretrain.yaml --device cuda
fi

if [ -f data/saussurea_involucrata.h5ad ]; then
  echo "== Saussurea LoRA fine-tuning =="
  snowcell baseline-centroid \
    --config configs/saussurea_lora_finetune.yaml \
    --output outputs/saussurea_lora_finetune/centroid_baseline.json || true
  snowcell train --config configs/saussurea_lora_finetune.yaml --device cuda
fi

bash scripts/generate_publication_package.sh

echo "Top-journal pipeline reached all currently available stages."
