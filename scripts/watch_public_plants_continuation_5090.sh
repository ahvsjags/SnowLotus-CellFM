#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
output_dir="${SNOWCELL_PUBLIC_PLANTS_CONTINUATION_OUTPUT_DIR:-outputs/plant_general_public_plants_continuation_5090}"
pid_file="${output_dir}/training.pid"
final_marker="${output_dir}/training_complete.marker"
poll_seconds="${SNOWCELL_PUBLIC_PLANTS_CONTINUATION_POLL_SECONDS:-600}"

cd "$project_dir"
export PATH="/root/miniconda3/envs/myconda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "[$(date)] public plants continuation watchdog started"
while true; do
  if [ -e "$final_marker" ]; then
    echo "[$(date)] continuation complete: $final_marker"
    exit 0
  fi

  running=0
  if [ -s "$pid_file" ]; then
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      running=1
      echo "[$(date)] continuation active: pid=$pid"
    fi
  fi

  if [ "$running" = "0" ]; then
    echo "[$(date)] continuation inactive; restarting"
    SNOWCELL_PROJECT_DIR="$project_dir" /bin/bash scripts/start_public_plants_continuation_5090.sh || true
  fi
  /bin/sleep "$poll_seconds"
done
