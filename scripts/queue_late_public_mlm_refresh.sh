#!/usr/bin/env bash
set -euo pipefail

cd /mnt/snowlotus_cellfm
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs outputs

poll_seconds="${SNOWCELL_LATE_QUEUE_POLL_SECONDS:-600}"
gse_manifest="data/corpus_manifest.gse268881.tsv"
mlm_corpus="${SNOWCELL_MLM_CORPUS_OUTPUT:-data/plant_foundation_corpus_public_mlm.h5ad}"
late_session="${SNOWCELL_LATE_MLM_SESSION:-snowcell_mlm_public_post_gse226097_refresh_safe}"
late_config="${SNOWCELL_LATE_MLM_CONFIG:-configs/foundation_5090_mlm_public_post_gse226097_refresh_safe.yaml}"
late_resume_config="${SNOWCELL_LATE_MLM_RESUME_CONFIG:-configs/generated/foundation_5090_mlm_public_post_gse226097_refresh_safe.resume.yaml}"
late_output_dir="${SNOWCELL_LATE_MLM_OUTPUT_DIR:-outputs/foundation_5090_mlm_public_post_gse226097_refresh_safe}"
late_log_prefix="${SNOWCELL_LATE_MLM_LOG_PREFIX:-mlm_public_post_gse226097_refresh_safe}"
training_sessions=(
  "${SNOWCELL_FOUNDATION_SESSION:-snowcell_foundation_long}"
  "${SNOWCELL_AVAILABLE_MLM_SESSION:-snowcell_mlm_public_available_expansion}"
  "${SNOWCELL_MLM_SESSION:-snowcell_mlm_public_expansion}"
  "${SNOWCELL_MLM_CONTINUATION_SESSION:-snowcell_mlm_public_expansion_continuation}"
  "${SNOWCELL_SAFE_MLM_SESSION:-snowcell_mlm_public_late_refresh_safe}"
  "${SNOWCELL_PUBLIC_SAFE_INIT_SESSION:-snowcell_public_safe_init}"
  "${SNOWCELL_MLM_V0_3_SESSION:-snowcell_mlm_public_expansion_v0_3}"
  "$late_session"
)
training_process_tokens=(
  "configs/foundation_5090_pretrain.yaml"
  "configs/foundation_5090_mlm_public_available_expansion.yaml"
  "configs/foundation_5090_mlm_public_expansion.yaml"
  "configs/generated/foundation_5090_mlm_public_expansion_continuation.yaml"
  "configs/generated/foundation_5090_mlm_public_expansion_continuation.resume.yaml"
  "configs/foundation_5090_mlm_public_late_refresh.yaml"
  "configs/foundation_5090_mlm_public_late_refresh_safe.yaml"
  "configs/foundation_5090_mlm_public_post_gse226097_refresh_safe.yaml"
  "configs/generated/foundation_5090_mlm_public_post_gse226097_refresh_safe.resume.yaml"
  "configs/generated/foundation_5090_mlm_public_late_refresh_safe.resume.yaml"
  "configs/foundation_5090_public_safe_init.yaml"
  "configs/generated/foundation_5090_public_safe_init.resume.yaml"
  "configs/generated/foundation_5090_mlm_public_expansion_continuation_v0_3.yaml"
)

manifest_matrix_ready() {
  local manifest="$1"
  python - "$manifest" <<'PY'
import csv
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
root = Path(".")
if not manifest.exists() or manifest.stat().st_size == 0:
    raise SystemExit(1)
with manifest.open("r", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))
if not rows:
    raise SystemExit(1)
missing = []
for row in rows:
    value = row.get("path", "")
    if not value:
        missing.append("<empty>")
        continue
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        missing.append(value)
if missing:
    print("missing matrix paths: " + ";".join(missing[:8]))
    raise SystemExit(1)
raise SystemExit(0)
PY
}

collect_public_extra_manifests() {
  local manifest
  while IFS= read -r manifest; do
    if manifest_matrix_ready "$manifest" >/dev/null 2>&1; then
      printf "%s " "$manifest"
    else
      echo "[$(date)] skipping non-ready extra manifest: $manifest" >&2
    fi
  done < <(find data -maxdepth 1 -type f \( -name "corpus_manifest.gse*.tsv" -o -name "corpus_manifest.scplantdb*.tsv" \) ! -name "*.available.tsv" | sort)
}

has_running_training_session() {
  local session
  local token
  local running_train_processes

  running_train_processes="$(ps -eo pid,args 2>/dev/null | grep -F "snowcell train" | grep -F -- "--config" | grep -v grep || true)"
  if [ -n "$running_train_processes" ]; then
    echo "[$(date)] detected active snowcell training process"
    printf '%s\n' "$running_train_processes" | head -5
    return 0
  fi
  for token in "${training_process_tokens[@]}"; do
    if printf '%s\n' "$running_train_processes" | grep -Fq "$token"; then
      echo "[$(date)] detected active training process for $token"
      return 0
    fi
  done

  for session in "${training_sessions[@]}"; do
    if tmux has-session -t "=$session" 2>/dev/null; then
      echo "[$(date)] observed training tmux session without matched train process: $session"
    fi
  done
  return 1
}

has_new_optional_manifest() {
  local manifest
  while IFS= read -r manifest; do
    if manifest_matrix_ready "$manifest" >/dev/null 2>&1 && { [ ! -s "$mlm_corpus" ] || [ "$manifest" -nt "$mlm_corpus" ]; }; then
      return 0
    fi
  done < <(find data -maxdepth 1 -type f \( -name "corpus_manifest.gse*.tsv" -o -name "corpus_manifest.scplantdb*.tsv" \) ! -name "*.available.tsv" | sort)
  return 1
}

needs_late_training() {
  if [ ! -s "$mlm_corpus" ]; then
    return 1
  fi
  if [ ! -s "$late_output_dir/best.pt" ]; then
    return 0
  fi
  if [ "$mlm_corpus" -nt "$late_output_dir/best.pt" ]; then
    return 0
  fi
  return 1
}

transfer_queues_pending() {
  python - <<'PY'
import csv
import re
import sys
from pathlib import Path

root = Path(".")
job_re = re.compile(r'"([^"|]+)\|(data/corpus_manifest\.[^"|]+\.tsv)\|([^"|]+)\|([^"|]+)"')
queue_scripts = [
    root / "scripts" / "queue_reviewed_geo_downloads.sh",
    root / "scripts" / "generated_geo_promotion_downloads" / "queue_geo_promotion_downloads.sh",
]


def accession_from_manifest(manifest: str) -> str:
    name = Path(manifest).name
    return name.removeprefix("corpus_manifest.").removesuffix(".tsv").upper()


def manifest_ready(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        return False
    missing = []
    for row in rows:
        value = row.get("path", "")
        if not value:
            missing.append(value)
            continue
        matrix = Path(value)
        if not matrix.is_absolute():
            matrix = root / matrix
        if not matrix.is_file():
            missing.append(value)
    return not missing


def unsupported_report(manifest: str) -> bool:
    accession = accession_from_manifest(manifest)
    suffixes = (
        "10x",
        "h5",
        "h5ad",
        "mtx",
        "mtx_tar",
        "mtx_components",
        "raw_tar",
        "rds",
    )
    return any(
        (root / "data" / "public" / f"{accession}_{suffix}" / "unsupported_single_cell_matrix.json").exists()
        for suffix in suffixes
    )


pending = []
for script in queue_scripts:
    if not script.exists():
        continue
    for _session, manifest, _command, _log_path in job_re.findall(script.read_text(encoding="utf-8")):
        if manifest_ready(root / manifest) or unsupported_report(manifest):
            continue
        pending.append(manifest)

if pending:
    print(";".join(pending[:20]))
    sys.exit(0)
sys.exit(1)
PY
}

build_full_public_mlm_corpus() {
  local extra_manifests
  extra_manifests="$(collect_public_extra_manifests)"
  SNOWCELL_EXTRA_CORPUS_MANIFESTS="$extra_manifests" bash scripts/build_public_mlm_corpus.sh
}

write_late_resume_config() {
  local checkpoint="$1"
  python - "$late_config" "$late_resume_config" "$checkpoint" "$late_output_dir" <<'PY'
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

echo "[$(date)] SnowCell late public MLM refresh queue started"
mkdir -p "$(dirname "$late_resume_config")"

while true; do
  bash scripts/ensure_public_data_jobs.sh || true
  if ! manifest_matrix_ready "$gse_manifest" >/dev/null 2>&1; then
    echo "[$(date)] waiting for base public manifest before late refresh: $gse_manifest"
    sleep "$poll_seconds"
    continue
  fi

  if pending_transfers="$(transfer_queues_pending)"; then
    echo "[$(date)] transfer queues still pending; delaying late public refresh: $pending_transfers"
    sleep "$poll_seconds"
    continue
  fi

  needs_rebuild=0
  if has_new_optional_manifest; then
    needs_rebuild=1
  fi
  needs_training=0
  if needs_late_training; then
    needs_training=1
  fi

  if [ "$needs_rebuild" = "0" ] && [ "$needs_training" = "0" ]; then
    echo "[$(date)] no optional manifest newer than $mlm_corpus and late refresh checkpoint is current"
    sleep "$poll_seconds"
    continue
  fi

  if has_running_training_session; then
    echo "[$(date)] late public refresh needed, but GPU training is still active"
    sleep "$poll_seconds"
    continue
  fi

  if [ "$needs_rebuild" = "1" ]; then
    echo "[$(date)] rebuilding full public corpus for late optional manifests"
    build_full_public_mlm_corpus
    bash scripts/run_strict_benchmark_audits.sh || true
    bash scripts/generate_publication_package.sh || true
  else
    echo "[$(date)] late refresh checkpoint missing or older than current corpus; reusing $mlm_corpus"
  fi

  if [ -f "$late_output_dir/best.pt" ] && [ "$late_output_dir/best.pt" -nt "$mlm_corpus" ]; then
    echo "[$(date)] late refresh checkpoint is newer than corpus: $late_output_dir/best.pt"
    sleep "$poll_seconds"
    continue
  fi

  if tmux has-session -t "=$late_session" 2>/dev/null; then
    echo "[$(date)] late refresh tmux session already exists without matched training process: $late_session"
    sleep "$poll_seconds"
    continue
  fi

  config_to_run="$late_config"
  if [ -s "$late_output_dir/latest.pt" ] && [ "$late_output_dir/latest.pt" -nt "$mlm_corpus" ]; then
    config_to_run="$(write_late_resume_config "$late_output_dir/latest.pt")"
    echo "[$(date)] resuming late public MLM refresh from $late_output_dir/latest.pt"
  fi

  stamp="$(date +%Y%m%d_%H%M%S)"
  echo "[$(date)] launching late public MLM refresh in tmux: $late_session"
  tmux new-session -d -s "$late_session" \
    "cd /mnt/snowlotus_cellfm && source .venv/bin/activate 2>/dev/null || true; .venv/bin/snowcell train --config '$config_to_run' --device cuda 2>&1 | tee logs/${late_log_prefix}_${stamp}.log; bash scripts/run_strict_benchmark_audits.sh; SNOWCELL_RELEASE_RUN_ID='$(basename "$late_output_dir")' SNOWCELL_RELEASE_CONFIG='$config_to_run' SNOWCELL_RELEASE_CHECKPOINT='$late_output_dir/best.pt' bash scripts/run_post_training_release_artifacts.sh || bash scripts/generate_publication_package.sh"
  sleep "$poll_seconds"
done
