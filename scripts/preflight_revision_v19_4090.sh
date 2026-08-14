#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
PYTHON_BIN="${SNOWCELL_PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}"
CONFIG="${SNOWCELL_V19_CONFIG:-${PROJECT_DIR}/configs/revision_v19_cross_species_contrastive_4090.yaml}"
REPORT_DIR="${SNOWCELL_V19_OUTPUT:-/root/snowlotus_cellfm_v19_contrastive_4090}"
REPORT_PATH="${REPORT_DIR}/preflight_v19.json"

mkdir -p "${REPORT_DIR}"
cd "${PROJECT_DIR}"
export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

command -v nvidia-smi >/dev/null
test -x "${PYTHON_BIN}"
test -s "${CONFIG}"

GPU_INFO="$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | head -n 1)"
test -n "${GPU_INFO}"

"${PYTHON_BIN}" - "${CONFIG}" "${REPORT_PATH}" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import torch
import yaml

config_path = Path(sys.argv[1])
report_path = Path(sys.argv[2])
payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
data = payload.get("data", {})
architecture = payload.get("architecture", {})
train = payload.get("train", {})

required = {
    "data_path": Path(str(data.get("path", ""))),
    "ontology_contract": Path(str(data.get("ontology_contract", ""))),
}
if train.get("init_checkpoint"):
    required["init_checkpoint"] = Path(str(train["init_checkpoint"]))
missing = {name: str(path) for name, path in required.items() if not path.is_file()}
if missing:
    raise SystemExit(f"v19 preflight missing files: {missing}")

if not torch.cuda.is_available():
    raise SystemExit("v19 preflight requires CUDA, but torch.cuda.is_available() is false")
gpu_name = torch.cuda.get_device_name(0)
if "4090" not in gpu_name:
    raise SystemExit(f"v19 preflight expected an RTX 4090, found {gpu_name!r}")

if float(train.get("cross_species_contrastive_loss_weight", 0.0)) <= 0:
    raise SystemExit("v19 config must enable cross_species_contrastive_loss_weight")
if train.get("validation_metric") != "species_macro_f1":
    raise SystemExit("v19 config must select validation_metric=species_macro_f1")
alpha = float(train.get("unknown_calibration_alpha", -1.0))
if not 0.0 <= alpha <= 1.0:
    raise SystemExit("v19 config unknown_calibration_alpha must be in [0, 1]")
if not data.get("ontology_contract"):
    raise SystemExit("v19 config must declare a source-only ontology contract")

report = {
    "schema_version": "plant_cellfm_revision_v19_preflight_v1",
    "config": str(config_path),
    "project_dir": os.getcwd(),
    "gpu": {"name": gpu_name, "count": torch.cuda.device_count()},
    "required_files": {name: str(path) for name, path in required.items()},
    "model": {
        "contrastive_dim": int(architecture.get("contrastive_dim", 0)),
        "marker_prior_weight": float(architecture.get("marker_prior_weight", 0.0)),
        "cross_species_contrastive_loss_weight": float(
            train.get("cross_species_contrastive_loss_weight", 0.0)
        ),
        "species_balance": bool(train.get("species_balance", False)),
    },
    "status": "ready",
}
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
PY

echo "[v19] preflight passed: ${REPORT_PATH}"
