#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/root/snowlotus-cellfm}"
session="${SNOWCELL_GSE226097_SESSION:-snowcell_gse226097_arabidopsis_lifecycle_subset}"
log_path="${project_dir}/logs/gse226097_arabidopsis_lifecycle_subset.log"

cd "$project_dir"
mkdir -p logs

if [ -s data/corpus_manifest.gse226097.tsv ]; then
  echo "GSE226097 manifest already exists: data/corpus_manifest.gse226097.tsv"
  exit 0
fi

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "GSE226097 lifecycle subset already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && source .venv/bin/activate 2>/dev/null || true; bash scripts/download_gse226097_arabidopsis_lifecycle_rds_subset.sh 2>&1 | tee -a '$log_path'; bash scripts/generate_publication_package.sh || true"

echo "started GSE226097 lifecycle subset: $session"
echo "log: $log_path"
