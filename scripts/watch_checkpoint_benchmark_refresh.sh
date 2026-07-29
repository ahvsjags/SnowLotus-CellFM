#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
INTERVAL_SECONDS="${SNOWCELL_BENCHMARK_REFRESH_INTERVAL_SECONDS:-21600}"
ONESHOT="${SNOWCELL_BENCHMARK_REFRESH_ONESHOT:-0}"
AUTO_SYNC_RELEASE="${SNOWCELL_BENCHMARK_REFRESH_SYNC_RELEASE:-1}"
RUN_STRICT_AUDITS="${SNOWCELL_BENCHMARK_REFRESH_STRICT_AUDITS:-1}"
RELEASE_LABEL="${SNOWCELL_BENCHMARK_RELEASE_LABEL:-editor-v0.3}"
V03_RUN_ID="${SNOWCELL_EDITOR_V03_RUN_ID:-foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm}"
V03_CHECKPOINT="${SNOWCELL_EDITOR_V03_CHECKPOINT:-outputs/${V03_RUN_ID}/best.pt}"
V04_RUN_ID="${SNOWCELL_MLM_V0_4_RUN_ID:-foundation_5090_mlm_public_expansion_v0_4_plus_latest_seed48_b8_vocabwarm}"
V04_CHECKPOINT="${SNOWCELL_MLM_V0_4_BEST:-outputs/${V04_RUN_ID}/best.pt}"
STATE_DIR="${PROJECT_DIR}/outputs/post_training_release"
SIGNATURE_FILE="${STATE_DIR}/benchmark_refresh_inputs.sha256"
LOCK_DIR="${PROJECT_DIR}/outputs/benchmark_refresh.lock"
LOG_DIR="${PROJECT_DIR}/logs"

cd "${PROJECT_DIR}"
mkdir -p "${STATE_DIR}" "${LOG_DIR}"
source .venv/bin/activate 2>/dev/null || true

if [ -z "${PYTHON:-}" ]; then
  if [ -x "${PROJECT_DIR}/.venv/bin/python" ]; then
    PYTHON="${PROJECT_DIR}/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
  else
    PYTHON="python"
  fi
fi

active_embedding_checkpoint() {
  if [ -s "${V04_CHECKPOINT}" ]; then
    printf '%s\n' "${V04_CHECKPOINT}"
  else
    printf '%s\n' "${V03_CHECKPOINT}"
  fi
}

compute_signature() {
  local checkpoint="$1"
  "${PYTHON}" - "${checkpoint}" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

root = Path(".")
checkpoint = Path(sys.argv[1])
patterns = [
    checkpoint.as_posix(),
    "configs/**/*.yaml",
    "configs/**/*.yml",
    "scripts/run_strict_benchmark_audits.sh",
    "scripts/write_benchmark_gap_audit.py",
    "scripts/write_scplantllm_input_readiness.py",
    "scripts/write_scplantannotate_access_audit.py",
    "scripts/write_scplantannotate_benchmark_package.py",
    "data/plant_foundation_corpus_public_mlm.h5ad",
    "data/plant_foundation_corpus_public_mlm_plus_latest.h5ad",
    "data/corpus_manifest*.tsv",
    "outputs/external_benchmarks/**/*.json",
    "outputs/external_benchmarks/**/*.csv",
    "outputs/strict_benchmarks/**/*.json",
]

seen: set[Path] = set()
files: list[Path] = []
for pattern in patterns:
    for path in root.glob(pattern):
        if path.is_file() and path not in seen:
            seen.add(path)
            files.append(path)

digest = hashlib.sha256()
manifest = []
for path in sorted(files, key=lambda item: item.as_posix()):
    stat = path.stat()
    digest.update(path.as_posix().encode("utf-8") + b"\0")
    digest.update(str(stat.st_size).encode("ascii") + b"\0")
    if stat.st_size <= 32 * 1024 * 1024:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
    manifest.append({"path": path.as_posix(), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})

payload = {"sha256": digest.hexdigest(), "checkpoint": checkpoint.as_posix(), "files": len(files), "manifest": manifest}
print(json.dumps(payload, sort_keys=True))
PY
}

signature_sha() {
  "${PYTHON}" -c 'import json,sys; print(json.loads(sys.stdin.read())["sha256"])'
}

refresh_benchmarks() {
  local stamp="$1"
  local checkpoint="$2"
  local signature_json="$3"

  if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
    echo "benchmark refresh lock held; skipping"
    return 0
  fi
  trap 'rmdir "${LOCK_DIR}" 2>/dev/null || true' RETURN

  echo "${signature_json}" > "${STATE_DIR}/benchmark_refresh_inputs.before.json"
  echo "benchmark refresh started: stamp=${stamp} checkpoint=${checkpoint}"

  if [ "${RUN_STRICT_AUDITS}" = "1" ]; then
    bash scripts/run_strict_benchmark_audits.sh > "${LOG_DIR}/benchmark_refresh_strict_${stamp}.log" 2>&1 || true
  else
    bash scripts/generate_publication_package.sh > "${LOG_DIR}/benchmark_refresh_package_${stamp}.log" 2>&1 || true
  fi

  "${PYTHON}" scripts/write_benchmark_gap_audit.py \
    --status-summary outputs/publication_package/status_summary.json \
    --project-dir . \
    --output-md outputs/publication_package/benchmark_gap_audit.md \
    --output-json outputs/publication_package/benchmark_gap_audit.json || true
  "${PYTHON}" scripts/write_scplantllm_input_readiness.py \
    --project-dir . \
    --input-dir outputs/external_benchmarks/scplantllm_public_sprint_input \
    --output-md outputs/publication_package/scplantllm_input_readiness.md \
    --output-json outputs/publication_package/scplantllm_input_readiness.json || true
  "${PYTHON}" scripts/write_scplantannotate_access_audit.py \
    --timeout 5 \
    --max-bytes 500000 \
    --max-assets 8 \
    --max-endpoints 6 \
    --output-md outputs/publication_package/scplantannotate_access_audit.md \
    --output-json outputs/publication_package/scplantannotate_access_audit.json || true

  if [ "${AUTO_SYNC_RELEASE}" = "1" ]; then
    RELEASE_LABEL="${RELEASE_LABEL}" \
      SNOWCELL_RELEASE_EMBEDDING_CHECKPOINT="${checkpoint}" \
      bash scripts/sync_github_release_repo.sh || true
  fi

  local after_signature_json
  after_signature_json="$(compute_signature "${checkpoint}")"
  echo "${after_signature_json}" > "${STATE_DIR}/benchmark_refresh_inputs.after.json"
  echo "${after_signature_json}" | signature_sha > "${SIGNATURE_FILE}"
  echo "benchmark refresh finished: stamp=${stamp}"
}

echo "SnowCell checkpoint benchmark refresh watchdog started: interval=${INTERVAL_SECONDS}s"
while true; do
  checkpoint="$(active_embedding_checkpoint)"
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  if [ ! -s "${checkpoint}" ]; then
    echo "waiting for checkpoint: ${checkpoint}"
  else
    signature_json="$(compute_signature "${checkpoint}")"
    current_sha="$(echo "${signature_json}" | signature_sha)"
    previous_sha=""
    if [ -s "${SIGNATURE_FILE}" ]; then
      previous_sha="$(cat "${SIGNATURE_FILE}")"
    fi
    echo "$(date -Is) benchmark_input_sha=${current_sha} previous=${previous_sha:-missing} checkpoint=${checkpoint}"
    if [ "${current_sha}" != "${previous_sha}" ]; then
      refresh_benchmarks "${stamp}" "${checkpoint}" "${signature_json}"
    else
      echo "benchmark evidence already current"
    fi
  fi

  if [ "${ONESHOT}" = "1" ]; then
    exit 0
  fi
  sleep "${INTERVAL_SECONDS}"
done
