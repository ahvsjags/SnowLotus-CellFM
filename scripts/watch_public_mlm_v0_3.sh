#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_MLM_V0_3_SESSION:-snowcell_mlm_public_expansion_v0_3}"
output_dir="${SNOWCELL_MLM_V0_3_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm}"
poll_seconds="${SNOWCELL_MLM_V0_3_WATCHDOG_POLL_SECONDS:-900}"

cd "$project_dir"
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs

target_epochs() {
  python - "$project_dir/configs/generated/foundation_5090_mlm_public_expansion_continuation_v0_3.yaml" <<'PY'
import sys
import yaml
cfg = yaml.safe_load(open(sys.argv[1], encoding="utf-8")) or {}
print(int((cfg.get("train") or {}).get("epochs") or 0))
PY
}

completed_epochs() {
  python - "$output_dir/history.json" <<'PY'
import json
import sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.exists():
    print(0)
else:
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(len(payload.get("epochs") or []))
PY
}

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

echo "[$(date)] SnowLotus v0.3 MLM watchdog started: session=$session"

while true; do
  target="$(target_epochs)"
  done_epochs="$(completed_epochs)"
  if [ "$target" -gt 0 ] && [ "$done_epochs" -ge "$target" ]; then
    echo "[$(date)] SnowLotus v0.3 target complete: epochs=$done_epochs/$target"
    bash scripts/generate_publication_package.sh || true
    sleep "$poll_seconds"
    continue
  fi
  if tmux has-session -t "=$session" 2>/dev/null; then
    echo "[$(date)] SnowLotus v0.3 active: $(latest_progress)"
  else
    echo "[$(date)] SnowLotus v0.3 inactive; starting"
    bash scripts/start_public_mlm_v0_3_training.sh
  fi
  sleep "$poll_seconds"
done
