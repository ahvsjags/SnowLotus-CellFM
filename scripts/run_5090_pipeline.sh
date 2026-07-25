#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p logs data outputs

echo "== SnowLotus-CellFM 5090 pipeline =="
date
hostname
pwd

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "nvidia-smi not found"
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[singlecell,dev]"

python - <<'PY'
import torch

print("torch:", torch.__version__)
print("cuda_available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu:", torch.cuda.get_device_name(0))
    print("capability:", torch.cuda.get_device_capability(0))
PY

echo "== local package checks =="
python -m ruff check src tests
python -m pytest -q

echo "== smoke run =="
snowcell make-demo --output data/demo.npz
snowcell train --config configs/smoke.yaml --device auto
snowcell predict \
  --checkpoint outputs/smoke/best.pt \
  --data data/demo.npz \
  --output outputs/smoke/predictions.csv \
  --device auto

if [ -f data/saussurea_involucrata.h5ad ]; then
  echo "== real Saussurea run =="
  snowcell train --config configs/rtx5090_base.yaml --device cuda
else
  echo "data/saussurea_involucrata.h5ad not found; real training skipped."
  echo "Upload the h5ad and optional ortholog TSV, then run:"
  echo "  snowcell train --config configs/rtx5090_base.yaml --device cuda"
fi

echo "== done =="
date
