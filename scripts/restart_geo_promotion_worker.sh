#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: restart_geo_promotion_worker.sh <GSE_ACCESSION>" >&2
  exit 2
fi

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
accession_upper="$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')"
accession_lower="$(printf '%s' "$accession_upper" | tr '[:upper:]' '[:lower:]')"
session="${SNOWCELL_GEO_PROMOTION_SESSION:-snowcell_geo_promotion_${accession_lower}}"
log_path="${SNOWCELL_GEO_PROMOTION_LOG:-logs/geo_promotion_${accession_lower}.log}"

cd "${PROJECT_DIR}"
mkdir -p logs

mapfile -t wrappers < <(find scripts/generated_geo_promotion_downloads -maxdepth 1 -type f -name "download_${accession_lower}_*.sh" | sort)
if [ "${#wrappers[@]}" -eq 0 ]; then
  echo "No generated GEO promotion wrapper found for ${accession_upper}" >&2
  exit 1
fi
wrapper="${wrappers[0]}"

tmux kill-session -t "${session}" 2>/dev/null || true
tmux new-session -d -s "${session}" \
  "cd '${PROJECT_DIR}' && source .venv/bin/activate 2>/dev/null || true; export SNOWCELL_GEO_RAW_TAR_CONNECTIONS='${SNOWCELL_GEO_RAW_TAR_CONNECTIONS:-1}'; export SNOWCELL_GEO_RAW_TAR_SPLITS='${SNOWCELL_GEO_RAW_TAR_SPLITS:-1}'; bash '${wrapper}' 2>&1 | tee -a '${log_path}'; bash scripts/generate_publication_package.sh || true"
echo "restarted ${session}"
echo "wrapper: ${wrapper}"
echo "log: ${log_path}"
