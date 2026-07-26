#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/root/snowlotus-cellfm}"
poll_seconds="${SNOWCELL_PUBLIC_DATA_WATCHDOG_POLL_SECONDS:-180}"

cd "$project_dir"
mkdir -p logs
source .venv/bin/activate 2>/dev/null || true

echo "[$(date)] SnowCell public data watchdog started; poll_seconds=$poll_seconds"

while true; do
  echo "[$(date)] public data watchdog ensure pass"
  bash scripts/ensure_public_data_jobs.sh || true
  sleep "$poll_seconds"
done
