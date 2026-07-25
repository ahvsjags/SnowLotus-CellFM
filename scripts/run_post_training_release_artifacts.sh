#!/usr/bin/env bash
set -euo pipefail

cd "${SNOWCELL_PROJECT_DIR:-/root/snowlotus-cellfm}"
source .venv/bin/activate 2>/dev/null || true

run_id="${SNOWCELL_RELEASE_RUN_ID:-foundation_5090_mlm_public_post_gse226097_refresh_safe}"
config="${SNOWCELL_RELEASE_CONFIG:-configs/foundation_5090_mlm_public_post_gse226097_refresh_safe.yaml}"
checkpoint="${SNOWCELL_RELEASE_CHECKPOINT:-outputs/${run_id}/best.pt}"
eval_output="${SNOWCELL_RELEASE_EVAL_OUTPUT:-outputs/detailed_evaluations/${run_id}_test}"
eval_split="${SNOWCELL_RELEASE_EVAL_SPLIT:-test}"
eval_max_batches="${SNOWCELL_RELEASE_EVAL_MAX_BATCHES:-500}"
eval_batch_size="${SNOWCELL_RELEASE_EVAL_BATCH_SIZE:-}"
bundle_data="${SNOWCELL_RELEASE_BUNDLE_DATA:-data/public/scplantllm_srp169576_npz/SRX5025983_seurat0.npz}"
bundle_output="${SNOWCELL_RELEASE_BUNDLE_OUTPUT:-outputs/annotation_bundles/${run_id}_public_probe}"
bundle_batch_size="${SNOWCELL_RELEASE_BUNDLE_BATCH_SIZE:-64}"
device="${SNOWCELL_RELEASE_DEVICE:-cuda}"

mkdir -p outputs/detailed_evaluations outputs/annotation_bundles outputs/post_training_release logs
summary="outputs/post_training_release/${run_id}.json"

if [ ! -s "$config" ]; then
  echo "Missing release config: $config" >&2
  exit 2
fi

if [ ! -s "$checkpoint" ]; then
  echo "Missing release checkpoint: $checkpoint" >&2
  exit 3
fi

eval_args=(
  --config "$config"
  --checkpoint "$checkpoint"
  --split "$eval_split"
  --output-dir "$eval_output"
  --device "$device"
  --max-batches "$eval_max_batches"
)
if [ -n "$eval_batch_size" ]; then
  eval_args+=(--batch-size "$eval_batch_size")
fi

python scripts/evaluate_checkpoint_detailed.py "${eval_args[@]}"

bundle_status="skipped_missing_input"
if [ -s "$bundle_data" ]; then
  snowcell annotate-bundle \
    --checkpoint "$checkpoint" \
    --data "$bundle_data" \
    --output-dir "$bundle_output" \
    --batch-size "$bundle_batch_size" \
    --device "$device"
  bundle_status="created"
else
  echo "Skipping annotation bundle; missing bundle input: $bundle_data" >&2
fi

python scripts/write_annotation_bundle_index.py \
  --project-dir . \
  --output-md outputs/publication_package/annotation_bundle_index.md \
  --output-json outputs/publication_package/annotation_bundle_index.json || true

python - "$summary" "$run_id" "$config" "$checkpoint" "$eval_output" "$eval_split" "$eval_max_batches" "$bundle_status" "$bundle_data" "$bundle_output" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

(
    summary_path,
    run_id,
    config,
    checkpoint,
    eval_output,
    eval_split,
    eval_max_batches,
    bundle_status,
    bundle_data,
    bundle_output,
) = sys.argv[1:11]

metrics_path = Path(eval_output) / "detailed_metrics.json"
metrics = {}
if metrics_path.exists():
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

payload = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "run_id": run_id,
    "config": config,
    "checkpoint": checkpoint,
    "detailed_evaluation": {
        "status": "created" if metrics_path.exists() else "missing",
        "output_dir": eval_output,
        "split": eval_split,
        "max_batches": int(eval_max_batches),
        "metrics_json": str(metrics_path),
        "evaluated_cells": metrics.get("summary", {}).get("evaluated_cells"),
        "fine_macro_f1": metrics.get("summary", {}).get("fine", {}).get("macro_f1"),
        "coarse_macro_f1": metrics.get("summary", {}).get("coarse", {}).get("macro_f1"),
    },
    "annotation_bundle": {
        "status": bundle_status,
        "input_data": bundle_data,
        "output_dir": bundle_output,
    },
}
Path(summary_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(summary_path)
PY

bash scripts/generate_publication_package.sh

echo "post-training release artifacts: $summary"
