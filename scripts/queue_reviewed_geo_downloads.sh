#!/usr/bin/env bash
set -euo pipefail

cd /mnt/snowlotus_cellfm
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs

if ! bash scripts/check_disk_budget.sh "${PWD}"; then
  echo "[$(date)] reviewed GEO queue paused by disk budget"
  exit 0
fi

poll_seconds="${SNOWCELL_REVIEWED_GEO_QUEUE_POLL_SECONDS:-900}"

jobs=(
  "snowcell_gse226097_arabidopsis_lifecycle_subset|data/corpus_manifest.gse226097.tsv|bash scripts/download_gse226097_arabidopsis_lifecycle_rds_subset.sh|logs/gse226097_arabidopsis_lifecycle_subset.log"
  "snowcell_gse338572_maize_easy_multiome_rna_subset|data/corpus_manifest.gse338572.tsv|bash scripts/download_gse338572_maize_easy_multiome_rna_rds_subset.sh|logs/gse338572_maize_easy_multiome_rna_subset.log"
  "snowcell_gse313726_rice_leaf_stress_subset|data/corpus_manifest.gse313726.tsv|bash scripts/download_gse313726_rice_leaf_stress_rds_subset.sh|logs/gse313726_rice_leaf_stress_subset.log"
  "snowcell_gse308757_rice_node_subset|data/corpus_manifest.gse308757.tsv|bash scripts/download_gse308757_rice_node_mtx_subset.sh|logs/gse308757_rice_node_subset.log"
  "snowcell_gse311951_stevia_leaf_subset|data/corpus_manifest.gse311951.tsv|bash scripts/download_gse311951_stevia_leaf_mtx_subset.sh|logs/gse311951_stevia_leaf_subset.log"
  "snowcell_gse302041_arabidopsis_lateral_root_subset|data/corpus_manifest.gse302041.tsv|bash scripts/download_gse302041_arabidopsis_lateral_root_rds_subset.sh|logs/gse302041_arabidopsis_lateral_root_subset.log"
  "snowcell_gse314252_tomato_mycorrhiza_subset|data/corpus_manifest.gse314252.tsv|bash scripts/download_gse314252_tomato_mycorrhiza_rds_subset.sh|logs/gse314252_tomato_mycorrhiza_subset.log"
  "snowcell_gse325371_tomato_salt_idioblast_subset|data/corpus_manifest.gse325371.tsv|bash scripts/download_gse325371_tomato_salt_idioblast_mtx_subset.sh|logs/gse325371_tomato_salt_idioblast_subset.log"
  "snowcell_gse234192_arabidopsis_callus_subset|data/corpus_manifest.gse234192.tsv|bash scripts/download_gse234192_plant_callus_rds_subset.sh|logs/gse234192_arabidopsis_callus_subset.log"
  "snowcell_gse149217_tomato_rice_root_tip_subset|data/corpus_manifest.gse149217.tsv|bash scripts/download_gse149217_tomato_rice_root_tip_mtx_subset.sh|logs/gse149217_tomato_rice_root_tip_subset.log"
  "snowcell_gse300264_arabidopsis_method_subset|data/corpus_manifest.gse300264.tsv|bash scripts/download_gse300264_arabidopsis_method_rds_subset.sh|logs/gse300264_arabidopsis_method_subset.log"
  "snowcell_gse336751_marchantia_spore_subset|data/corpus_manifest.gse336751.tsv|bash scripts/download_gse336751_marchantia_spore_mtx_subset.sh|logs/gse336751_marchantia_spore_subset.log"
)

other_transfer_sessions=(
  snowcell_gse270140_arabidopsis_secondary_root_subset
)

manifest_matrix_status() {
  local manifest="$1"
  python - "$manifest" <<'PY'
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
root = Path(".")
if not path.exists() or path.stat().st_size == 0:
    print("missing_manifest")
    raise SystemExit(0)
with path.open("r", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))
if not rows:
    print("empty_manifest")
    raise SystemExit(0)
missing = []
for row in rows:
    value = row.get("path", "")
    if not value:
        missing.append("<empty>")
        continue
    matrix = Path(value)
    if not matrix.is_absolute():
        matrix = root / matrix
    if not matrix.is_file():
        missing.append(value)
if missing:
    print("missing_files")
else:
    print("ready")
PY
}

manifest_row_count() {
  local manifest="$1"
  python - "$manifest" <<'PY'
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print(0)
else:
    with path.open("r", encoding="utf-8", newline="") as handle:
        print(sum(1 for _ in csv.DictReader(handle, delimiter="\t")))
PY
}

unsupported_report_for_manifest() {
  local manifest="$1"
  local filename accession
  filename="$(basename "$manifest")"
  accession="${filename#corpus_manifest.}"
  accession="${accession%.tsv}"
  accession="${accession^^}"
  find "data/public/${accession}_raw_tar" \
    -maxdepth 1 \
    -type f \
    -name "unsupported_single_cell_matrix.json" \
    -print \
    -quit 2>/dev/null
}

partial_download_for_manifest() {
  local manifest="$1"
  local filename accession
  filename="$(basename "$manifest")"
  accession="${filename#corpus_manifest.}"
  accession="${accession%.tsv}"
  accession="${accession^^}"
  find "data/public/${accession}_raw_tar" \
    -maxdepth 1 \
    -type f \
    -name "*.aria2" \
    -print \
    -quit 2>/dev/null
}

job_done_status() {
  local session="$1"
  local manifest="$2"
  local status partial unsupported
  status="$(manifest_matrix_status "$manifest")"
  if [ "$status" = "ready" ]; then
    echo "complete"
    return 0
  fi
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "running"
    return 0
  fi
  partial="$(partial_download_for_manifest "$manifest")"
  if [ -n "$partial" ]; then
    echo "partial"
    return 0
  fi
  unsupported="$(unsupported_report_for_manifest "$manifest")"
  if [ -n "$unsupported" ]; then
    echo "unsupported"
    return 0
  fi
  if [ "$status" = "missing_files" ]; then
    echo "stale_manifest"
    return 0
  fi
  echo "missing"
  return 0
}

has_active_transfer() {
  local entry session
  for entry in "${jobs[@]}"; do
    IFS='|' read -r session _ _ _ <<< "$entry"
    if tmux has-session -t "$session" 2>/dev/null; then
      return 0
    fi
  done
  for session in "${other_transfer_sessions[@]}"; do
    if tmux has-session -t "$session" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

echo "[$(date)] reviewed GEO download queue started"

while true; do
  launched=0
  all_done=1
  for entry in "${jobs[@]}"; do
    IFS='|' read -r session done_file command log_file <<< "$entry"
    done_status="$(job_done_status "$session" "$done_file")"
    if [ "$done_status" = "complete" ]; then
      echo "[$(date)] reviewed GEO job complete: $done_file"
      continue
    fi
    if [ "$done_status" = "running" ]; then
      all_done=0
      echo "[$(date)] reviewed GEO job running: $session"
      launched=1
      break
    fi
    if [ "$done_status" = "unsupported" ]; then
      echo "[$(date)] reviewed GEO job unsupported for expression corpus: $done_file"
      continue
    fi
    all_done=0
    if tmux has-session -t "$session" 2>/dev/null; then
      echo "[$(date)] reviewed GEO job running: $session"
      launched=1
      break
    fi
    if has_active_transfer; then
      echo "[$(date)] transfer already active; waiting before starting $session"
      break
    fi
    echo "[$(date)] starting reviewed GEO job: $session"
    tmux new-session -d -s "$session" \
      "cd /mnt/snowlotus_cellfm && source .venv/bin/activate 2>/dev/null || true; $command 2>&1 | tee -a $log_file; bash scripts/generate_publication_package.sh || true"
    launched=1
    break
  done
  if [ "$all_done" = "1" ]; then
    echo "[$(date)] all reviewed GEO jobs complete"
  elif [ "$launched" = "0" ]; then
    echo "[$(date)] no reviewed GEO job launched this cycle"
  fi
  sleep "$poll_seconds"
done
