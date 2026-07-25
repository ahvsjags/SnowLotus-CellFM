#!/usr/bin/env bash
set -euo pipefail

cd "${SNOWCELL_PROJECT_DIR:-/root/snowlotus-cellfm}"
source .venv/bin/activate 2>/dev/null || true

session="${SNOWCELL_MLM_CONTINUATION_SESSION:-snowcell_mlm_public_expansion_continuation}"
output_dir="${SNOWCELL_MLM_CONTINUATION_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_expansion_continuation}"
poll_seconds="${SNOWCELL_MLM_CONTINUATION_WATCHDOG_POLL_SECONDS:-600}"

mkdir -p logs

latest_progress() {
  python - "$output_dir/progress_latest.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("no_progress")
else:
    payload = json.loads(path.read_text(encoding="utf-8"))
    status = payload.get("status") or "-"
    epoch = payload.get("epoch") or "-"
    step = payload.get("step") or "-"
    total = payload.get("train_batches_per_epoch") or "-"
    print(f"{status} epoch={epoch} step={step}/{total}")
PY
}

echo "[$(date)] SnowCell public MLM continuation watchdog started: session=$session"

while true; do
  if tmux has-session -t "=$session" 2>/dev/null; then
    echo "[$(date)] continuation training active: $(latest_progress)"
  else
    echo "[$(date)] continuation training inactive; invoking resume-aware starter"
    bash scripts/start_public_mlm_continuation_training.sh
  fi
  sleep "$poll_seconds"
done
