#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
INTERVAL_SECONDS="${SNOWCELL_QUEUE_INTERVAL_SECONDS:-300}"
cd "${PROJECT_DIR}"

while true; do
  bash scripts/start_plant_public_data_queue.sh
  sleep "${INTERVAL_SECONDS}"
done
