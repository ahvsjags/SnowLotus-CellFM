#!/usr/bin/env bash
set -euo pipefail

source_dir="${SNOWCELL_SOURCE_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
stage_dir="${SNOWCELL_ROOT_STAGE_DIR:-/root/snowlotus_cellfm_v10}"

if [ ! -d "$source_dir" ]; then
  echo "source project does not exist: $source_dir" >&2
  exit 2
fi

mkdir -p "$stage_dir"

copy_if_exists() {
  local item="$1"
  if [ -e "${source_dir}/${item}" ]; then
    mkdir -p "${stage_dir}/$(dirname "$item")"
    tar -C "$source_dir" --ignore-failed-read --warning=no-file-changed -cf - "$item" | tar -C "$stage_dir" -xf -
  fi
}

for item in \
  README.md \
  pyproject.toml \
  setup.cfg \
  setup.py \
  configs \
  docs \
  manuscript \
  release_metadata \
  scripts \
  src \
  tests; do
  copy_if_exists "$item"
done

mkdir -p \
  "$stage_dir/data/public/source_pages" \
  "$stage_dir/data/public_discovery" \
  "$stage_dir/data/public" \
  "$stage_dir/logs" \
  "$stage_dir/outputs/editor_submission_v9" \
  "$stage_dir/outputs/publication_package"

for item in \
  data/public/source_pages/scplantdb_chunks \
  data/public_discovery/scplantdb_dataset_catalog.tsv \
  data/public_discovery/scplantdb_dataset_catalog.json \
  data/public_discovery/scplantdb_acquisition_catalog.md \
  data/public_discovery/scplantdb_h5ad_size_probe.tsv \
  data/public_discovery/scplantdb_h5ad_size_probe.json \
  data/public_discovery/scplantdb_h5ad_size_probe.md \
  data/public_discovery/scplantdb_selected_h5ad_datasets.txt \
  outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.status.json \
  outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.status.md \
  outputs/editor_submission_v9/server_release_verification_v9.json \
  outputs/editor_submission_v9/server_release_verification_v9.md \
  outputs/editor_submission_v9/release_gate_completion_audit_v9.json \
  outputs/editor_submission_v9/release_gate_completion_audit_v9.md; do
  copy_if_exists "$item"
done

cat > "$stage_dir/ROOT_STAGING_README.md" <<EOF
# Plant-CellFM v10 root staging workspace

Source project: \`$source_dir\`

This staging directory is for post-v9 continuation work when \`/mnt\` is full.
It intentionally excludes large matrices, checkpoints and historical output folders.
Use it for lightweight public discovery and budgeted downloads only.

Example:

\`\`\`bash
cd "$stage_dir"
SNOWCELL_PROJECT_DIR="$stage_dir" \\
SNOWCELL_MIN_FREE_BYTES=10737418240 \\
SNOWCELL_SCPLANTDB_MAX_TOTAL_BYTES=2147483648 \\
SNOWCELL_SCPLANTDB_MAX_DATASETS=4 \\
bash scripts/start_scplantdb_budgeted_h5ad_queue.sh
\`\`\`
EOF

echo "$stage_dir"
du -sh "$stage_dir" 2>/dev/null || true
