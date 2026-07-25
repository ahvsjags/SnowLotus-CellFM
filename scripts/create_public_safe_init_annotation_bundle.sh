#!/usr/bin/env bash
set -euo pipefail

cd "${SNOWCELL_PROJECT_DIR:-/root/snowlotus-cellfm}"
source .venv/bin/activate 2>/dev/null || true

checkpoint="${SNOWCELL_PUBLIC_SAFE_INIT_CHECKPOINT:-outputs/foundation_5090_public_safe_init/best.pt}"
data_path="${SNOWCELL_PUBLIC_SAFE_INIT_BUNDLE_DATA:-data/public/scplantllm_srp169576_npz/SRX5025983_seurat0.npz}"
output_dir="${SNOWCELL_PUBLIC_SAFE_INIT_BUNDLE_OUTPUT:-outputs/annotation_bundles/scplantllm_srp169576_public_safe_init}"
device="${SNOWCELL_PUBLIC_SAFE_INIT_BUNDLE_DEVICE:-cuda}"
batch_size="${SNOWCELL_PUBLIC_SAFE_INIT_BUNDLE_BATCH_SIZE:-64}"

if [ ! -s "$checkpoint" ]; then
  echo "Missing safe-init checkpoint: $checkpoint" >&2
  exit 2
fi

if [ ! -s "$data_path" ]; then
  echo "Missing bundle input data: $data_path" >&2
  exit 3
fi

snowcell annotate-bundle \
  --checkpoint "$checkpoint" \
  --data "$data_path" \
  --output-dir "$output_dir" \
  --batch-size "$batch_size" \
  --device "$device"

python scripts/write_annotation_bundle_index.py \
  --project-dir . \
  --output-md outputs/publication_package/annotation_bundle_index.md \
  --output-json outputs/publication_package/annotation_bundle_index.json

echo "public safe-init annotation bundle: $output_dir"
