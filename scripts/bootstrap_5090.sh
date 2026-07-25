#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[singlecell,dev]"

python - <<'PY'
import torch

print("torch:", torch.__version__)
print("cuda:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu:", torch.cuda.get_device_name(0))
PY

snowcell make-demo --output data/demo.npz
snowcell train --config configs/smoke.yaml --device cuda
snowcell predict \
  --checkpoint outputs/smoke/best.pt \
  --data data/demo.npz \
  --output outputs/smoke/predictions.csv \
  --device cuda

echo "Smoke run finished: outputs/smoke"
