#!/usr/bin/env bash
set -euo pipefail

cd "${SNOWCELL_PROJECT_DIR:-/root/snowlotus-cellfm}"
source .venv/bin/activate 2>/dev/null || true

session="${SNOWCELL_PUBLIC_SAFE_INIT_SESSION:-snowcell_public_safe_init}"
base_config="${SNOWCELL_PUBLIC_SAFE_INIT_CONFIG:-configs/foundation_5090_public_safe_init.yaml}"
output_dir="${SNOWCELL_PUBLIC_SAFE_INIT_OUTPUT_DIR:-outputs/foundation_5090_public_safe_init}"
resume_config="${SNOWCELL_PUBLIC_SAFE_INIT_RESUME_CONFIG:-configs/generated/foundation_5090_public_safe_init.resume.yaml}"
device="${SNOWCELL_PUBLIC_SAFE_INIT_DEVICE:-cuda}"
log_dir="${SNOWCELL_PUBLIC_SAFE_INIT_LOG_DIR:-logs}"

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

target="$(target_epochs)"
done_epochs="$(completed_epochs)"
if [ "$target" -gt 0 ] && [ "$done_epochs" -ge "$target" ]; then
  echo "public safe-init target complete: epochs=$done_epochs/$target"
  bash scripts/generate_publication_package.sh
  exit 0
fi

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "public safe-init training already running: $session epochs=$done_epochs/$target"
  exit 0
fi

config_to_run="$base_config"
if [ -s "$output_dir/latest.pt" ]; then
  config_to_run="$(write_resume_config "$output_dir/latest.pt")"
fi

stamp="$(date +%Y%m%d_%H%M%S)"
log_path="$log_dir/public_safe_init_${stamp}.log"
tmux new-session -d -s "$session" \
  "cd $(pwd); source .venv/bin/activate 2>/dev/null || true; snowcell train --config $config_to_run --device $device 2>&1 | tee $log_path; bash scripts/generate_publication_package.sh 2>&1 | tee -a $log_path"
echo "public safe-init training started: session=$session log=$log_path config=$config_to_run"
