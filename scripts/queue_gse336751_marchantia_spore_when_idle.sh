#!/usr/bin/env bash
set -euo pipefail

cd /mnt/snowlotus_cellfm
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs

poll_seconds="${SNOWCELL_GSE336751_QUEUE_POLL_SECONDS:-900}"
done_file="data/corpus_manifest.gse336751.tsv"
self_session="${SNOWCELL_GSE336751_QUEUE_SESSION:-snowcell_gse336751_marchantia_spore_subset}"

active_transfer_sessions=(
  snowcell_gse270140_arabidopsis_secondary_root_subset
  snowcell_gse338572_maize_easy_multiome_rna_subset
  snowcell_gse313726_rice_leaf_stress_subset
  snowcell_gse311951_stevia_leaf_subset
  snowcell_gse302041_arabidopsis_lateral_root_subset
  snowcell_gse314252_tomato_mycorrhiza_subset
  snowcell_gse300264_arabidopsis_method_subset
)

has_other_active_transfer() {
  local session
  for session in "${active_transfer_sessions[@]}"; do
    if [ "$session" = "$self_session" ]; then
      continue
    fi
    if tmux has-session -t "$session" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

echo "[$(date)] GSE336751 Marchantia outgroup queue started"

while true; do
  if [ -s "$done_file" ]; then
    echo "[$(date)] GSE336751 already complete: $done_file"
    bash scripts/generate_publication_package.sh || true
    exit 0
  fi
  if has_other_active_transfer; then
    echo "[$(date)] another transfer is active; waiting before GSE336751"
    sleep "$poll_seconds"
    continue
  fi
  echo "[$(date)] starting GSE336751 Marchantia RAW MTX download"
  bash scripts/download_gse336751_marchantia_spore_mtx_subset.sh 2>&1 | tee -a logs/gse336751_marchantia_spore_subset.log
  bash scripts/generate_publication_package.sh || true
  exit 0
done
