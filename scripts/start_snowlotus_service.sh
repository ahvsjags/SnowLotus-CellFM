#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=${PROJECT_DIR:-/mnt/snowlotus_cellfm}
BACKBONE_CHECKPOINT=${BACKBONE_CHECKPOINT:-$PROJECT_DIR/outputs/remote_joint_scplantdb_pretrain_4090/best.pt}
ANNOTATION_CHECKPOINT=${ANNOTATION_CHECKPOINT:-$PROJECT_DIR/outputs/remote_srp169576_joint_init_hybrid_4090/best.pt}
DATA_ROOT=${DATA_ROOT:-$PROJECT_DIR/data/public/scPlantDB_h5ad}
ADAPTER_REGISTRY=${ADAPTER_REGISTRY:-$PROJECT_DIR/release_metadata/plant_species_adapters.json}
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}
DEVICE=${DEVICE:-cuda}
PYTHON_BIN=${PYTHON_BIN:-/root/miniconda3/envs/myconda/bin/python}

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN=python
fi

cd "$PROJECT_DIR"
export PYTHONPATH=src
exec "$PYTHON_BIN" -X utf8 scripts/serve_snowlotus.py \
  --backbone-checkpoint "$BACKBONE_CHECKPOINT" \
  --annotation-checkpoint "$ANNOTATION_CHECKPOINT" \
  --data-root "$DATA_ROOT" \
  --adapter-registry "$ADAPTER_REGISTRY" \
  --project-root "$PROJECT_DIR" \
  --host "$HOST" \
  --port "$PORT" \
  --device "$DEVICE"
