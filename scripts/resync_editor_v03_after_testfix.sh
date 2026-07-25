#!/usr/bin/env bash
set -euo pipefail

PROJECT=/root/snowlotus-cellfm
RELEASE_LABEL=editor-v0.3
RUN_ID=foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm
EMBEDDING=outputs/${RUN_ID}/best.pt
RELEASE_DIR=${PROJECT}/outputs/github_release/SnowLotus-CellFM
ARCHIVE_DIR=${PROJECT}/outputs/github_release_archives
LOG_DIR=${PROJECT}/outputs/post_training_release
LOG=${LOG_DIR}/editor_v03_testfix_resync_$(date -u +%Y%m%dT%H%M%SZ).log

mkdir -p "${LOG_DIR}" "${ARCHIVE_DIR}"
exec > >(tee "${LOG}") 2>&1

echo "RESYNC_BEGIN $(date -Is)"
cd "${PROJECT}"
source .venv/bin/activate 2>/dev/null || true

echo "STEP: sync release repository"
RELEASE_LABEL="${RELEASE_LABEL}" SNOWCELL_RELEASE_EMBEDDING_CHECKPOINT="${EMBEDDING}" bash scripts/sync_github_release_repo.sh

echo "STEP: full release tests"
cd "${RELEASE_DIR}"
PYTHONPATH=src "${PROJECT}/.venv/bin/python" -m pytest -q
sha256sum -c models/SHA256SUMS.txt
git status -sb
git log --oneline -1
git tag --points-at HEAD

echo "STEP: full archive with models"
cd "${PROJECT}"
FULL=${ARCHIVE_DIR}/snowlotus-cellfm-${RELEASE_LABEL}-full-with-models.tar.gz
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

echo "RESYNC_END $(date -Is)"
echo "LOG=${LOG}"
