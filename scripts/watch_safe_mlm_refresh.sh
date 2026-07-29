#!/usr/bin/env bash
set -euo pipefail

cd "${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
source .venv/bin/activate 2>/dev/null || true

session="${SNOWCELL_SAFE_MLM_SESSION:-snowcell_mlm_public_late_refresh_safe}"
base_config="${SNOWCELL_SAFE_MLM_CONFIG:-configs/foundation_5090_mlm_public_late_refresh_safe.yaml}"
output_dir="${SNOWCELL_SAFE_MLM_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_late_refresh_safe}"
resume_config="${SNOWCELL_SAFE_MLM_RESUME_CONFIG:-configs/generated/foundation_5090_mlm_public_late_refresh_safe.resume.yaml}"
poll_seconds="${SNOWCELL_SAFE_MLM_WATCHDOG_POLL_SECONDS:-600}"
device="${SNOWCELL_SAFE_MLM_DEVICE:-cuda}"
log_dir="${SNOWCELL_SAFE_MLM_LOG_DIR:-logs}"

mkdir -p "$log_dir" "$(dirname "$resume_config")"

target_epochs() {
  python - "$base_config" <<'PY'
import sys, yaml
cfg = yaml.safe_load(open(sys.argv[1], encoding="utf-8")) or {}
print(int((cfg.get("train") or {}).get("epochs") or 0))
PY
}

completed_epochs() {
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

write_resume_config() {
  local checkpoint="$1"
  python - "$base_config" "$resume_config" "$checkpoint" "$output_dir" <<'PY'
import sys, yaml
base, output, checkpoint, output_dir = sys.argv[1:5]
cfg = yaml.safe_load(open(base, encoding="utf-8")) or {}
train = dict(cfg.get("train") or {})
train["resume_checkpoint"] = checkpoint
train["init_checkpoint"] = None
cfg["train"] = train
out = dict(cfg.get("output") or {})
out["directory"] = output_dir
cfg["output"] = out
with open(output, "w", encoding="utf-8") as handle:
    yaml.safe_dump(cfg, handle, sort_keys=False)
print(output)
PY
}

launch_training() {
  local config_path="$1"
  local stamp
  stamp="$(date +%Y%m%d_%H%M%S)"
  echo "[$(date)] launching $session with $config_path"
  tmux new-session -d -s "$session" \
    "cd $(pwd); source .venv/bin/activate 2>/dev/null || true; snowcell train --config $config_path --device $device 2>&1 | tee $log_dir/mlm_public_late_refresh_safe_watchdog_${stamp}.log; bash scripts/run_strict_benchmark_audits.sh; bash scripts/generate_publication_package.sh"
}

echo "[$(date)] SnowCell safe MLM watchdog started: session=$session"

while true; do
  target="$(target_epochs)"
  done_epochs="$(completed_epochs)"
  if [ "$target" -gt 0 ] && [ "$done_epochs" -ge "$target" ]; then
    echo "[$(date)] safe MLM target complete: epochs=$done_epochs/$target"
    bash scripts/generate_publication_package.sh >/tmp/snowcell_safe_watchdog_package.log 2>&1 || true
    sleep "$poll_seconds"
    continue
  fi

  if tmux has-session -t "=$session" 2>/dev/null; then
    echo "[$(date)] safe MLM training active: epochs=$done_epochs/$target"
    sleep "$poll_seconds"
    continue
  fi

  if [ -s "$output_dir/latest.pt" ]; then
    config_to_run="$(write_resume_config "$output_dir/latest.pt")"
  else
    config_to_run="$base_config"
  fi
  launch_training "$config_to_run"
  sleep "$poll_seconds"
done
