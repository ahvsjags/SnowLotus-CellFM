#!/usr/bin/env bash
set -euo pipefail

cd "${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
source .venv/bin/activate 2>/dev/null || true

session="${SNOWCELL_PACKAGE_REFRESH_SESSION:-snowcell_publication_package_watchdog}"
run_id="${SNOWCELL_PACKAGE_REFRESH_RUN_ID:-foundation_5090_mlm_public_late_refresh_safe}"
output_dir="${SNOWCELL_PACKAGE_REFRESH_OUTPUT_DIR:-outputs/${run_id}}"
package_json="${SNOWCELL_PACKAGE_REFRESH_JSON:-outputs/publication_package/training_curve_summary.json}"
poll_seconds="${SNOWCELL_PACKAGE_REFRESH_POLL_SECONDS:-300}"
log_dir="${SNOWCELL_PACKAGE_REFRESH_LOG_DIR:-logs}"
lock_dir="${SNOWCELL_PACKAGE_REFRESH_LOCK_DIR:-/tmp/snowcell_publication_package_refresh.lock}"

mkdir -p "$log_dir" outputs/publication_package

history_epochs() {
  python - "$output_dir/history.json" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.exists():
    print(0)
else:
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(len(payload.get("epochs") or []))
PY
}

packaged_epochs() {
  python - "$package_json" "$run_id" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
run_id = sys.argv[2]
if not path.exists():
    print(-1)
else:
    payload = json.loads(path.read_text(encoding="utf-8"))
    matched = [
        int(run.get("epochs_recorded") or 0)
        for run in payload.get("runs", [])
        if run.get("run_id") == run_id
    ]
    print(matched[0] if matched else -1)
PY
}

refresh_package() {
  local history_count="$1"
  local package_count="$2"
  local stamp
  stamp="$(date +%Y%m%d_%H%M%S)"
  if ! mkdir "$lock_dir" 2>/dev/null; then
    echo "[$(date)] package refresh already locked: history=$history_count packaged=$package_count"
    return 0
  fi
  trap 'rmdir "$lock_dir" 2>/dev/null || true' RETURN
  echo "[$(date)] refreshing publication package: history=$history_count packaged=$package_count"
  bash scripts/generate_publication_package.sh > "$log_dir/publication_package_refresh_${stamp}.log" 2>&1 || true
  echo "[$(date)] publication package refresh finished: log=$log_dir/publication_package_refresh_${stamp}.log"
}

echo "[$(date)] SnowCell publication package refresh watchdog started: session=$session run_id=$run_id"

while true; do
  history_count="$(history_epochs)"
  package_count="$(packaged_epochs)"
  if [ "$history_count" -gt "$package_count" ]; then
    refresh_package "$history_count" "$package_count"
  else
    echo "[$(date)] publication package current: history=$history_count packaged=$package_count"
  fi
  sleep "$poll_seconds"
done
