#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
RUN_ID="${SNOWCELL_EDITOR_V03_RUN_ID:-foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm}"
CHECKPOINT="${SNOWCELL_EDITOR_V03_CHECKPOINT:-outputs/${RUN_ID}/best.pt}"
RELEASE_MODEL="${SNOWCELL_EDITOR_V03_RELEASE_MODEL:-outputs/github_release/SnowLotus-CellFM/models/SnowLotus_CellFM_best_embedding.pt}"
RELEASE_DIR="${PROJECT_DIR}/outputs/github_release/SnowLotus-CellFM"
INTERVAL_SECONDS="${SNOWCELL_EDITOR_V03_METADATA_INTERVAL_SECONDS:-1800}"
AUTO_PUSH="${SNOWCELL_EDITOR_V03_METADATA_AUTO_PUSH:-1}"
RUN_TESTS="${SNOWCELL_EDITOR_V03_METADATA_RUN_TESTS:-0}"
ONESHOT="${SNOWCELL_EDITOR_V03_METADATA_ONESHOT:-0}"
LOCK_DIR="${PROJECT_DIR}/outputs/editor_v03_best_release_sync.lock"
STATE_DIR="${PROJECT_DIR}/outputs/post_training_release"
SIGNATURE_FILE="${STATE_DIR}/editor_v03_release_metadata_inputs.sha256"
LOG_DIR="${PROJECT_DIR}/logs"

cd "${PROJECT_DIR}"
mkdir -p "${STATE_DIR}" "${LOG_DIR}" outputs/github_release_archives
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

compute_signature() {
  "${PYTHON}" - "${RUN_ID}" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

root = Path(".")
run_id = sys.argv[1]

patterns = [
    "pyproject.toml",
    ".gitignore",
    "README.md",
    "src/**/*.py",
    "configs/**/*.yaml",
    "configs/**/*.yml",
    "scripts/**/*.py",
    "scripts/**/*.sh",
    "tests/**/*.py",
    "docs/**/*.md",
    "data/public_dataset_manifest.tsv",
    "data/corpus_manifest*.tsv",
    "data/public_discovery/**/*.md",
    "data/public_discovery/**/*.json",
    "data/public_discovery/**/*.tsv",
    "data/public_discovery/**/*.txt",
    f"outputs/{run_id}/history.json",
    "outputs/foundation_5090_pretrain/history.json",
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
    if stat.st_size <= 50 * 1024 * 1024:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
    manifest.append(
        {
            "path": path.as_posix(),
            "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
    )

payload = {
    "sha256": digest.hexdigest(),
    "files": len(manifest),
    "manifest": manifest,
}
print(json.dumps(payload, sort_keys=True))
PY
}

signature_sha() {
  "${PYTHON}" -c 'import json,sys; print(json.loads(sys.stdin.read())["sha256"])'
}

model_release_pending() {
  if [ ! -s "${CHECKPOINT}" ] || [ ! -s "${RELEASE_MODEL}" ]; then
    return 1
  fi
  local best_sha release_sha
  best_sha="$(sha256sum "${CHECKPOINT}" | awk '{print $1}')"
  release_sha="$(sha256sum "${RELEASE_MODEL}" | awk '{print $1}')"
  if [ "${best_sha}" != "${release_sha}" ]; then
    echo "model checkpoint is newer than release; defer to best-model watchdog: best=${best_sha} release=${release_sha}"
    return 0
  fi
  return 1
}

convert_editor_docx() {
  if ! command -v pandoc >/dev/null 2>&1; then
    echo "pandoc not available; keeping existing docx files if present"
    return 0
  fi
  pandoc github_release_docs/SnowLotus_CellFM_editor_submission_v0_3.md -o github_release_docs/SnowLotus_CellFM_editor_submission_v0_3.docx || true
  pandoc github_release_docs/SnowLotus_CellFM_editor_submission_v0_2.md -o github_release_docs/SnowLotus_CellFM_editor_submission_v0_2.docx || true
  pandoc github_release_docs/editor_cover_note_v0_3.md -o github_release_docs/editor_cover_note_v0_3.docx || true
  pandoc github_release_docs/editor_cover_note_v0_2.md -o github_release_docs/editor_cover_note_v0_2.docx || true
  pandoc github_release_docs/EDITOR_HANDOFF.md -o github_release_docs/EDITOR_HANDOFF.docx || true
}

refresh_release_metadata() {
  local stamp="$1"
  local before_signature_json="$2"

  if model_release_pending; then
    return 0
  fi

  if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
    echo "release sync lock held; skipping metadata refresh"
    return 0
  fi
  trap 'rmdir "${LOCK_DIR}" 2>/dev/null || true' RETURN

  echo "metadata refresh started: ${stamp}"
  echo "${before_signature_json}" > "${STATE_DIR}/editor_v03_release_metadata_inputs.before.json"

  bash scripts/generate_publication_package.sh > "${LOG_DIR}/editor_v03_metadata_package_${stamp}.log" 2>&1 || {
    echo "publication package refresh had non-zero exit; continuing with available artifacts"
  }

  "${PYTHON}" scripts/write_editor_v03_current_best_docs.py || true
  "${PYTHON}" scripts/write_editor_v03_manuscript_docs.py || true
  convert_editor_docx

  if model_release_pending; then
    echo "model changed during metadata refresh; leaving release update to best-model watchdog"
    return 0
  fi

  RELEASE_LABEL=editor-v0.3 \
    SNOWCELL_RELEASE_EMBEDDING_CHECKPOINT="${CHECKPOINT}" \
    bash scripts/sync_github_release_repo.sh

  (
    cd "${RELEASE_DIR}"
    sha256sum -c models/SHA256SUMS.txt
    if [ "${RUN_TESTS}" = "1" ]; then
      PYTHONPATH=src "${PYTHON}" -m pytest -q
    fi
    git status -sb
    git log --oneline -1
    git tag --points-at HEAD
  )

  local after_signature_json
  after_signature_json="$(compute_signature)"
  echo "${after_signature_json}" > "${STATE_DIR}/editor_v03_release_metadata_inputs.after.json"
  echo "${after_signature_json}" | signature_sha > "${SIGNATURE_FILE}"

  if [ "${AUTO_PUSH}" = "1" ]; then
    bash scripts/push_github_release.sh || true
  fi

  echo "metadata refresh finished: ${stamp}"
}

echo "SnowCell editor-v0.3 release metadata watchdog started: interval=${INTERVAL_SECONDS}s run_id=${RUN_ID}"

while true; do
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  now="$(date -Is)"
  signature_json="$(compute_signature)"
  current_sha="$(echo "${signature_json}" | signature_sha)"
  previous_sha=""
  if [ -s "${SIGNATURE_FILE}" ]; then
    previous_sha="$(cat "${SIGNATURE_FILE}")"
  fi

  echo "${now} current_metadata_sha=${current_sha} previous_metadata_sha=${previous_sha:-missing}"
  if [ "${current_sha}" != "${previous_sha}" ]; then
    refresh_release_metadata "${stamp}" "${signature_json}"
  else
    echo "release metadata already current"
  fi

  if [ "${ONESHOT}" = "1" ]; then
    exit 0
  fi
  sleep "${INTERVAL_SECONDS}"
done
