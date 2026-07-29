#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_GSE226097_SESSION:-snowcell_gse226097_arabidopsis_lifecycle_subset}"
log_path="${project_dir}/logs/gse226097_arabidopsis_lifecycle_subset.log"

cd "$project_dir"
mkdir -p logs

manifest_matrix_ready() {
  local manifest="$1"
  python - "$manifest" <<'PY'
import csv
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
root = Path(".")
if not manifest.exists() or manifest.stat().st_size == 0:
    raise SystemExit(1)
with manifest.open("r", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))
if not rows:
    raise SystemExit(1)
for row in rows:
    value = row.get("path", "")
    if not value:
        raise SystemExit(1)
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        raise SystemExit(1)
raise SystemExit(0)
PY
}

if manifest_matrix_ready data/corpus_manifest.gse226097.tsv; then
  echo "GSE226097 manifest already exists: data/corpus_manifest.gse226097.tsv"
  exit 0
fi
if [ -s data/corpus_manifest.gse226097.tsv ]; then
  echo "GSE226097 manifest exists but matrix files are missing; restarting download."
fi

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "GSE226097 lifecycle subset already running: $session"
  exit 0
fi

tmux new-session -d -s "$session" \
  "cd '$project_dir' && source .venv/bin/activate 2>/dev/null || true; bash scripts/download_gse226097_arabidopsis_lifecycle_rds_subset.sh 2>&1 | tee -a '$log_path'; bash scripts/generate_publication_package.sh || true"

echo "started GSE226097 lifecycle subset: $session"
echo "log: $log_path"
