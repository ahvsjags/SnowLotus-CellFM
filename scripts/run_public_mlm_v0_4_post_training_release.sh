#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
RELEASE_LABEL="${SNOWCELL_MLM_V0_4_RELEASE_LABEL:-editor-v0.4}"
RUN_ID="${SNOWCELL_MLM_V0_4_RUN_ID:-foundation_5090_mlm_public_expansion_v0_4_plus_latest_seed48_b8_vocabwarm}"
CHECKPOINT="${SNOWCELL_MLM_V0_4_BEST:-outputs/${RUN_ID}/best.pt}"
RELEASE_DIR="${PROJECT_DIR}/outputs/github_release/SnowLotus-CellFM"
ARCHIVE_DIR="${PROJECT_DIR}/outputs/github_release_archives"
LOG_DIR="${PROJECT_DIR}/outputs/post_training_release"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="${LOG_DIR}/editor_v0_4_post_training_release_${STAMP}.log"

cd "${PROJECT_DIR}"
mkdir -p "${ARCHIVE_DIR}" "${LOG_DIR}"
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

exec > >(tee "${LOG}") 2>&1

echo "V0_4_POST_RELEASE_BEGIN $(date -Is)"
if [ ! -s "${CHECKPOINT}" ]; then
  echo "missing v0.4 best checkpoint: ${CHECKPOINT}" >&2
  exit 2
fi

echo "STEP: publication package refresh"
bash scripts/generate_publication_package.sh || true

echo "STEP: v0.4 editor docs"
"${PYTHON}" scripts/write_editor_v04_manuscript_docs.py
if command -v pandoc >/dev/null 2>&1; then
  pandoc github_release_docs/SnowLotus_CellFM_editor_submission_v0_4.md -o github_release_docs/SnowLotus_CellFM_editor_submission_v0_4.docx || true
  pandoc github_release_docs/editor_cover_note_v0_4.md -o github_release_docs/editor_cover_note_v0_4.docx || true
  pandoc github_release_docs/EDITOR_HANDOFF.md -o github_release_docs/EDITOR_HANDOFF.docx || true
else
  echo "WARN: pandoc not available; v0.4 docx files will be absent unless pre-generated"
fi

echo "STEP: release repository sync"
RELEASE_LABEL="${RELEASE_LABEL}" \
  SNOWCELL_RELEASE_EMBEDDING_CHECKPOINT="${CHECKPOINT}" \
  bash scripts/sync_github_release_repo.sh

echo "STEP: release validation"
cd "${RELEASE_DIR}"
PYTHONPATH=src "${PYTHON}" -m pytest -q
sha256sum -c models/SHA256SUMS.txt
git status -sb
git log --oneline -1
git tag --points-at HEAD

echo "STEP: full archive with models"
cd "${PROJECT_DIR}"
FULL="${ARCHIVE_DIR}/snowlotus-cellfm-${RELEASE_LABEL}-full-with-models.tar.gz"
tar --exclude='.git' --exclude='*/__pycache__' --exclude='*/.pytest_cache' --exclude='*.pyc' -czf "${FULL}" -C "$(dirname "${RELEASE_DIR}")" "$(basename "${RELEASE_DIR}")"
sha256sum "${FULL}" > "${FULL}.sha256"
ls -lh "${FULL}" "${FULL}.sha256"
cat "${FULL}.sha256"

echo "STEP: push attempt"
if bash scripts/push_github_release.sh; then
  echo "PUSH_OK"
else
  echo "PUSH_FAILED"
fi

echo "V0_4_POST_RELEASE_END $(date -Is)"
echo "LOG=${LOG}"
