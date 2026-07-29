#!/usr/bin/env bash
set -euo pipefail

project_dir="${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
session="${SNOWCELL_MLM_CONTINUATION_SESSION:-snowcell_mlm_public_expansion_continuation}"
base_config="${SNOWCELL_MLM_CONTINUATION_CONFIG:-configs/generated/foundation_5090_mlm_public_expansion_continuation.yaml}"
output_dir="${SNOWCELL_MLM_CONTINUATION_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_expansion_continuation}"
resume_config="${SNOWCELL_MLM_CONTINUATION_RESUME_CONFIG:-configs/generated/foundation_5090_mlm_public_expansion_continuation.resume.yaml}"
final_marker="${SNOWCELL_MLM_CONTINUATION_FINALIZED_MARKER:-${output_dir}/finalized_after_training.stamp}"
device="${SNOWCELL_MLM_CONTINUATION_DEVICE:-cuda}"
log_dir="${SNOWCELL_MLM_CONTINUATION_LOG_DIR:-logs}"

cd "$project_dir"
source .venv/bin/activate 2>/dev/null || true
mkdir -p "$log_dir" outputs "$(dirname "$resume_config")"

target_epochs() {
  python - "$base_config" <<'PY'
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

write_resume_config() {
  local checkpoint="$1"
  python - "$base_config" "$resume_config" "$checkpoint" "$output_dir" <<'PY'
import sys
import yaml

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

finalization_needed() {
  local path
  if [ ! -s "$final_marker" ]; then
    return 0
  fi
  for path in "$base_config" "$output_dir/history.json" "$output_dir/latest.pt" "$output_dir/best.pt"; do
    if [ -e "$path" ] && [ "$path" -nt "$final_marker" ]; then
      return 0
    fi
  done
  return 1
}

finalize_training_outputs() {
  mkdir -p "$(dirname "$final_marker")"
  echo "public MLM continuation finalization running: $final_marker"
  bash scripts/run_strict_benchmark_audits.sh || true
  bash scripts/generate_publication_package.sh || true
  touch "$final_marker"
  echo "public MLM continuation finalization complete: $final_marker"
}

target="$(target_epochs)"
done_epochs="$(completed_epochs)"

if tmux has-session -t "=$session" 2>/dev/null; then
  echo "public MLM continuation already running: $session epochs=$done_epochs/$target"
  tmux ls
  exit 0
fi

if [ "$target" -gt 0 ] && [ "$done_epochs" -ge "$target" ]; then
  echo "public MLM continuation target complete: epochs=$done_epochs/$target"
  if finalization_needed; then
    finalize_training_outputs
  else
    echo "public MLM continuation already finalized: $final_marker"
  fi
  exit 0
fi

config_to_run="$base_config"
if [ -s "$output_dir/latest.pt" ]; then
  config_to_run="$(write_resume_config "$output_dir/latest.pt")"
fi

stamp="$(date +%Y%m%d_%H%M%S)"
log_path="$log_dir/mlm_public_expansion_continuation_${stamp}.log"

tmux new-session -d -s "$session" \
  "cd '$project_dir' && source .venv/bin/activate 2>/dev/null || true; PYTHONPATH=src /root/miniconda3/envs/myconda/bin/python -m snowcell.cli train --config '$config_to_run' --device '$device' 2>&1 | tee '$log_path'; bash scripts/run_strict_benchmark_audits.sh 2>&1 | tee -a '$log_path'; bash scripts/generate_publication_package.sh 2>&1 | tee -a '$log_path'; touch '$final_marker'"

echo "started public MLM continuation: $session"
echo "log: $log_path"
echo "config: $config_to_run"
tmux ls
