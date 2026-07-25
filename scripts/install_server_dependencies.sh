#!/usr/bin/env bash
set -euo pipefail

echo "== install system dependencies =="
if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    curl \
    git \
    gzip \
    htop \
    jq \
    pigz \
    python3-pip \
    python3-venv \
    tmux \
    unzip \
    wget
fi

echo "== python environment =="
cd "$(dirname "$0")/.."
if [ -d .venv ] && [ ! -f .venv/bin/activate ]; then
  echo "Removing incomplete .venv"
  rm -rf .venv
fi
if [ ! -f .venv/bin/activate ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
python -m pip config set global.trusted-host mirrors.aliyun.com
python -m pip config set global.timeout 120
python -m pip config set global.retries 10
python -m pip install wheel setuptools
python -m pip install -e ".[pipeline,dev]"

python - <<'PY'
import importlib
import torch

for name in ["numpy", "pandas", "scipy", "anndata", "yaml", "torch"]:
    importlib.import_module(name)
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY
