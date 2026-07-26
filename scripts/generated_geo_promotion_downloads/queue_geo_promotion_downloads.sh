#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs

poll_seconds="${SNOWCELL_GEO_PROMOTION_QUEUE_POLL_SECONDS:-120}"
large_raw_scan_interval="${SNOWCELL_GEO_RAW_TAR_SCAN_INTERVAL_SECONDS:-1800}"
last_large_raw_scan=0

jobs=(
  "snowcell_geo_promotion_gse224928|data/corpus_manifest.gse224928.tsv|bash scripts/generated_geo_promotion_downloads/download_gse224928_geo_gse224928_arabidopsis_thaliana_transcriptome_radially_growing_arabidopsis_wi.sh|logs/geo_promotion_gse224928.log"
  "snowcell_geo_promotion_gse155304|data/corpus_manifest.gse155304.tsv|bash scripts/generated_geo_promotion_downloads/download_gse155304_geo_gse155304_arabidopsis_thaliana_single_cell_level_analysis_arabidopsis.sh|logs/geo_promotion_gse155304.log"
  "snowcell_geo_promotion_gse123013|data/corpus_manifest.gse123013.tsv|bash scripts/generated_geo_promotion_downloads/download_gse123013_geo_gse123013_arabidopsis_thaliana_single_cell_rna_sequencing_analysis.sh|logs/geo_promotion_gse123013.log"
  "snowcell_geo_promotion_gse138526|data/corpus_manifest.gse138526.tsv|bash scripts/generated_geo_promotion_downloads/download_gse138526_geo_gse138526_zea_mays_high_throughput_single_cell_rna.sh|logs/geo_promotion_gse138526.log"
  "snowcell_geo_promotion_gse181999|data/corpus_manifest.gse181999.tsv|bash scripts/generated_geo_promotion_downloads/download_gse181999_geo_gse181999_arabidopsis_thaliana_an_arabidopsis_root_phloem_pole.sh|logs/geo_promotion_gse181999.log"
  "snowcell_geo_promotion_gse182507|data/corpus_manifest.gse182507.tsv|bash scripts/generated_geo_promotion_downloads/download_gse182507_geo_gse182507_medicago_truncatula_single_cell_rna_sequencing_medicago.sh|logs/geo_promotion_gse182507.log"
  "snowcell_geo_promotion_gse196882|data/corpus_manifest.gse196882.tsv|bash scripts/generated_geo_promotion_downloads/download_gse196882_geo_gse196882_zea_mays_spatial_transcriptomics_maize_embryonic_leaves.sh|logs/geo_promotion_gse196882.log"
  "snowcell_geo_promotion_gse210881|data/corpus_manifest.gse210881.tsv|bash scripts/generated_geo_promotion_downloads/download_gse210881_geo_gse210881_medicago_truncatula_gene_expression_profile_at_single.sh|logs/geo_promotion_gse210881.log"
  "snowcell_geo_promotion_gse226149|data/corpus_manifest.gse226149.tsv|bash scripts/generated_geo_promotion_downloads/download_gse226149_geo_gse226149_glycine_max_gene_expression_profile_at_single.sh|logs/geo_promotion_gse226149.log"
  "snowcell_geo_promotion_gse273033|data/corpus_manifest.gse273033.tsv|bash scripts/generated_geo_promotion_downloads/download_gse273033_geo_gse273033_arabidopsis_thaliana_dual_spatially_resolved_drought_responses.sh|logs/geo_promotion_gse273033.log"
  "snowcell_geo_promotion_gse121619|data/corpus_manifest.gse121619.tsv|bash scripts/generated_geo_promotion_downloads/download_gse121619_geo_gse121619_arabidopsis_thaliana_dynamics_gene_expression_single_root.sh|logs/geo_promotion_gse121619.log"
  "snowcell_geo_promotion_gse212403|data/corpus_manifest.gse212403.tsv|bash scripts/generated_geo_promotion_downloads/download_gse212403_geo_gse212403_solanum_lycopersicum_single_cell_data_suberized_exodermis.sh|logs/geo_promotion_gse212403.log"
  "snowcell_geo_promotion_gse214130|data/corpus_manifest.gse214130.tsv|bash scripts/generated_geo_promotion_downloads/download_gse214130_geo_gse214130_oryza_sativa_chromatin_accessibility_map_rice_root.sh|logs/geo_promotion_gse214130.log"
  "snowcell_geo_promotion_gse220277|data/corpus_manifest.gse220277.tsv|bash scripts/generated_geo_promotion_downloads/download_gse220277_geo_gse220277_arabidopsis_drought_recovery_plants_triggers_a.sh|logs/geo_promotion_gse220277.log"
  "snowcell_geo_promotion_gse226218|data/corpus_manifest.gse226218.tsv|bash scripts/generated_geo_promotion_downloads/download_gse226218_geo_gse226218_gossypium_arboreum_transcriptional_landscape_cottont_roots_respons.sh|logs/geo_promotion_gse226218.log"
  "snowcell_geo_promotion_gse235495|data/corpus_manifest.gse235495.tsv|bash scripts/generated_geo_promotion_downloads/download_gse235495_geo_gse235495_arabidopsis_thaliana_multiome_same_cell_revealed_impact.sh|logs/geo_promotion_gse235495.log"
  "snowcell_geo_promotion_gse235509|data/corpus_manifest.gse235509.tsv|bash scripts/generated_geo_promotion_downloads/download_gse235509_geo_gse235509_arabidopsis_thaliana_multiome_same_cell_revealed_impact.sh|logs/geo_promotion_gse235509.log"
  "snowcell_geo_promotion_gse235510|data/corpus_manifest.gse235510.tsv|bash scripts/generated_geo_promotion_downloads/download_gse235510_geo_gse235510_arabidopsis_thaliana_multiome_same_cell_revealed_impact.sh|logs/geo_promotion_gse235510.log"
  "snowcell_geo_promotion_gse267159|data/corpus_manifest.gse267159.tsv|bash scripts/generated_geo_promotion_downloads/download_gse267159_geo_gse267159_populus_trichocarpa_single_cell_spatial_multi_omics.sh|logs/geo_promotion_gse267159.log"
)

reviewed_manifests=(
  "data/corpus_manifest.gse226097.tsv"
  "data/corpus_manifest.gse338572.tsv"
  "data/corpus_manifest.gse313726.tsv"
  "data/corpus_manifest.gse308757.tsv"
  "data/corpus_manifest.gse311951.tsv"
  "data/corpus_manifest.gse302041.tsv"
  "data/corpus_manifest.gse314252.tsv"
  "data/corpus_manifest.gse325371.tsv"
  "data/corpus_manifest.gse234192.tsv"
  "data/corpus_manifest.gse149217.tsv"
  "data/corpus_manifest.gse300264.tsv"
  "data/corpus_manifest.gse336751.tsv"
)

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
  find_transfer_file_for_manifest "$manifest" "unsupported_single_cell_matrix.json"
}

partial_download_for_manifest() {
  local manifest="$1"
  find_transfer_file_for_manifest "$manifest" "*.aria2"
}

find_transfer_file_for_manifest() {
  local manifest="$1"
  local pattern="$2"
  local filename accession
  filename="$(basename "$manifest")"
  accession="${filename#corpus_manifest.}"
  accession="${accession%.tsv}"
  accession="${accession^^}"
  local suffix dir hit
  for suffix in 10x h5 h5ad mtx_tar mtx_components raw_tar rds; do
    dir="data/public/${accession}_${suffix}"
    hit="$(find "$dir" \
      -maxdepth 1 \
      -type f \
      -name "$pattern" \
      -print \
      -quit 2>/dev/null || true)"
    if [ -n "$hit" ]; then
      echo "$hit"
      return 0
    fi
  done
}

reviewed_manifest_done() {
  local manifest="$1"
  local rows partial unsupported
  rows="$(manifest_row_count "$manifest")"
  if [ "$rows" -gt 0 ]; then
    return 0
  fi
  partial="$(partial_download_for_manifest "$manifest")"
  if [ -n "$partial" ]; then
    return 1
  fi
  unsupported="$(unsupported_report_for_manifest "$manifest")"
  if [ -n "$unsupported" ]; then
    return 0
  fi
  return 1
}

promotion_manifest_done() {
  local manifest="$1"
  local rows unsupported
  rows="$(manifest_row_count "$manifest")"
  if [ "$rows" -gt 0 ]; then
    echo "[$(date)] promotion GEO job complete: $manifest"
    return 0
  fi
  unsupported="$(unsupported_report_for_manifest "$manifest")"
  if [ -n "$unsupported" ]; then
    echo "[$(date)] promotion GEO job unsupported: $manifest ($unsupported)"
    return 0
  fi
  return 1
}

reviewed_queue_pending() {
  local manifest
  for manifest in "${reviewed_manifests[@]}"; do
    if ! reviewed_manifest_done "$manifest"; then
      return 0
    fi
  done
  return 1
}

has_active_reviewed_transfer() {
  tmux ls 2>/dev/null | cut -d: -f1 | grep -E '^snowcell_gse[0-9].*_subset$' >/dev/null 2>&1
}

has_active_unfinished_promotion_transfer() {
  local current_session="${1:-}"
  local active_session active_accession active_manifest
  while IFS= read -r active_session; do
    if [ "$active_session" = "$current_session" ]; then
      continue
    fi
    case "$active_session" in
      snowcell_geo_promotion_gse[0-9]*)
        active_accession="${active_session#snowcell_geo_promotion_}"
        active_manifest="data/corpus_manifest.${active_accession}.tsv"
        if promotion_manifest_done "$active_manifest" >/dev/null; then
          continue
        fi
        echo "[$(date)] another promotion GEO job is already active: $active_session"
        return 0
        ;;
    esac
  done < <(tmux ls 2>/dev/null | cut -d: -f1)

  local entry session manifest command log_file
  for entry in "${jobs[@]}"; do
    IFS='|' read -r session manifest command log_file <<< "$entry"
    if [ "$session" = "$current_session" ]; then
      continue
    fi
    if promotion_manifest_done "$manifest" >/dev/null; then
      continue
    fi
    if tmux has-session -t "$session" 2>/dev/null; then
      echo "[$(date)] another promotion GEO job is already active: $session"
      return 0
    fi
  done
  return 1
}

run_large_raw_tar_defer_scan() {
  local now
  if [ "${SNOWCELL_GEO_PROMOTION_SKIP_LARGE_RAW_SCAN:-0}" = "1" ]; then
    return 0
  fi
  if [ ! -f scripts/defer_large_geo_raw_tar_candidates.py ]; then
    return 0
  fi
  now="$(date +%s)"
  if [ "$last_large_raw_scan" -ne 0 ] && [ $((now - last_large_raw_scan)) -lt "$large_raw_scan_interval" ]; then
    return 0
  fi
  last_large_raw_scan="$now"
  echo "[$(date)] scanning GEO candidates for oversized RAW tar before launch"
  SNOWCELL_GEO_RAW_TAR_QUEUE_MAX_BYTES="${SNOWCELL_GEO_RAW_TAR_QUEUE_MAX_BYTES:-5368709120}" \
    .venv/bin/python scripts/defer_large_geo_raw_tar_candidates.py || true
}

echo "[$(date)] GEO promotion download queue started"

while true; do
  run_large_raw_tar_defer_scan
  launched=0
  all_done=1
  for entry in "${jobs[@]}"; do
    IFS='|' read -r session manifest command log_file <<< "$entry"
    if promotion_manifest_done "$manifest"; then
      continue
    fi
    all_done=0
    if tmux has-session -t "$session" 2>/dev/null; then
      echo "[$(date)] promotion GEO job running: $session"
      launched=1
      break
    fi
    if reviewed_queue_pending; then
      echo "[$(date)] reviewed GEO queue still has pending static jobs; waiting before starting $session"
      break
    fi
    if has_active_reviewed_transfer; then
      echo "[$(date)] reviewed GEO transfer active; waiting before starting $session"
      break
    fi
    if has_active_unfinished_promotion_transfer "$session"; then
      echo "[$(date)] promotion GEO transfer active; waiting before starting $session"
      break
    fi
    echo "[$(date)] starting promotion GEO job: $session"
    tmux new-session -d -s "$session" \
      "cd /root/snowlotus-cellfm && source .venv/bin/activate 2>/dev/null || true; $command 2>&1 | tee -a $log_file; bash scripts/generate_publication_package.sh || true"
    launched=1
    break
  done
  if [ "$all_done" = "1" ]; then
    echo "[$(date)] all promotion GEO jobs complete"
  elif [ "$launched" = "0" ]; then
    echo "[$(date)] no promotion GEO job launched this cycle"
  fi
  sleep "$poll_seconds"
done
