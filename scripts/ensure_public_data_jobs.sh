#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
cd "${PROJECT_DIR}"
mkdir -p logs
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

start_job() {
  local session="$1"
  local done_file="$2"
  local command="$3"
  if manifest_matrix_ready "$done_file"; then
    echo "[$(date)] public data job complete: $done_file"
    return 0
  fi
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "[$(date)] public data job running: $session"
    return 0
  fi
  if [ -s "$done_file" ]; then
    echo "[$(date)] public data manifest exists but matrix files are missing; restarting: $done_file"
  fi
  echo "[$(date)] starting public data job: $session"
  if tmux new-session -d -s "$session" "$command"; then
    return 0
  fi
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "[$(date)] public data job started by another queue: $session"
    return 0
  fi
  return 1
}

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
missing = []
for row in rows:
    value = row.get("path", "")
    if not value:
        missing.append("<empty>")
        continue
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        missing.append(value)
if missing:
    print("missing matrix paths: " + ";".join(missing[:8]))
    raise SystemExit(1)
raise SystemExit(0)
PY
}

if [ "${SNOWCELL_ENSURE_GSE268881:-1}" = "1" ]; then
  start_job \
    snowcell_gse268881_subset \
    data/corpus_manifest.gse268881.tsv \
    "cd ${PROJECT_DIR} && bash scripts/run_gse268881_subset_background.sh"
fi

if [ "${SNOWCELL_ENSURE_GSE152766:-1}" = "1" ]; then
  start_job \
    snowcell_gse152766_arabidopsis_subset \
    data/corpus_manifest.gse152766.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE152766_MAX_FILES=${SNOWCELL_GSE152766_MAX_FILES:-1} bash scripts/download_gse152766_arabidopsis_mtx_subset.sh 2>&1 | tee -a logs/gse152766_arabidopsis_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE146034:-1}" = "1" ]; then
  start_job \
    snowcell_gse146034_rice_root_tip_subset \
    data/corpus_manifest.gse146034.tsv \
    "cd ${PROJECT_DIR} && bash scripts/download_gse146034_rice_root_tip_mtx_subset.sh 2>&1 | tee -a logs/gse146034_rice_root_tip_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE270342:-1}" = "1" ]; then
  start_job \
    snowcell_gse270342_wheat_subset \
    data/corpus_manifest.gse270342.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE270342_MAX_FILES=${SNOWCELL_GSE270342_MAX_FILES:-1} bash scripts/download_gse270342_wheat_h5_generic.sh 2>&1 | tee -a logs/gse270342_wheat_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE243419:-1}" = "1" ]; then
  start_job \
    snowcell_gse243419_cotton_glandular_subset \
    data/corpus_manifest.gse243419.tsv \
    "cd ${PROJECT_DIR} && bash scripts/download_gse243419_cotton_glandular_mtx_subset.sh 2>&1 | tee -a logs/gse243419_cotton_glandular_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE270140:-1}" = "1" ]; then
  start_job \
    snowcell_gse270140_arabidopsis_secondary_root_subset \
    data/corpus_manifest.gse270140.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE270140_MAX_FILES=${SNOWCELL_GSE270140_MAX_FILES:-1} bash scripts/download_gse270140_arabidopsis_secondary_root_h5_subset.sh 2>&1 | tee -a logs/gse270140_arabidopsis_secondary_root_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE251706:-1}" = "1" ]; then
  start_job \
    snowcell_gse251706_rice_rds_subset \
    data/corpus_manifest.gse251706.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE251706_MAX_FILES=${SNOWCELL_GSE251706_MAX_FILES:-1} bash scripts/download_gse251706_rice_rds_subset.sh 2>&1 | tee -a logs/gse251706_rice_rds_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE338572:-0}" = "1" ]; then
  start_job \
    snowcell_gse338572_maize_easy_multiome_rna_subset \
    data/corpus_manifest.gse338572.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE338572_MAX_FILES=${SNOWCELL_GSE338572_MAX_FILES:-1} bash scripts/download_gse338572_maize_easy_multiome_rna_rds_subset.sh 2>&1 | tee -a logs/gse338572_maize_easy_multiome_rna_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE313726:-0}" = "1" ]; then
  start_job \
    snowcell_gse313726_rice_leaf_stress_subset \
    data/corpus_manifest.gse313726.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE313726_MAX_FILES=${SNOWCELL_GSE313726_MAX_FILES:-1} bash scripts/download_gse313726_rice_leaf_stress_rds_subset.sh 2>&1 | tee -a logs/gse313726_rice_leaf_stress_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE311951:-0}" = "1" ]; then
  start_job \
    snowcell_gse311951_stevia_leaf_subset \
    data/corpus_manifest.gse311951.tsv \
    "cd ${PROJECT_DIR} && bash scripts/download_gse311951_stevia_leaf_mtx_subset.sh 2>&1 | tee -a logs/gse311951_stevia_leaf_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE302041:-0}" = "1" ]; then
  start_job \
    snowcell_gse302041_arabidopsis_lateral_root_subset \
    data/corpus_manifest.gse302041.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE302041_MAX_FILES=${SNOWCELL_GSE302041_MAX_FILES:-1} bash scripts/download_gse302041_arabidopsis_lateral_root_rds_subset.sh 2>&1 | tee -a logs/gse302041_arabidopsis_lateral_root_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE314252:-0}" = "1" ]; then
  start_job \
    snowcell_gse314252_tomato_mycorrhiza_subset \
    data/corpus_manifest.gse314252.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE314252_MAX_FILES=${SNOWCELL_GSE314252_MAX_FILES:-1} bash scripts/download_gse314252_tomato_mycorrhiza_rds_subset.sh 2>&1 | tee -a logs/gse314252_tomato_mycorrhiza_subset.log"
fi

if [ "${SNOWCELL_ENSURE_GSE300264:-0}" = "1" ]; then
  start_job \
    snowcell_gse300264_arabidopsis_method_subset \
    data/corpus_manifest.gse300264.tsv \
    "cd ${PROJECT_DIR} && SNOWCELL_GSE300264_MAX_FILES=${SNOWCELL_GSE300264_MAX_FILES:-1} bash scripts/download_gse300264_arabidopsis_method_rds_subset.sh 2>&1 | tee -a logs/gse300264_arabidopsis_method_subset.log"
fi
