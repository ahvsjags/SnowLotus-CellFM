#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
RUN_ID="${SNOWCELL_EDITOR_V03_RUN_ID:-foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm}"
CHECKPOINT="${SNOWCELL_EDITOR_V03_CHECKPOINT:-outputs/${RUN_ID}/best.pt}"
RELEASE_MODEL="${SNOWCELL_EDITOR_V03_RELEASE_MODEL:-outputs/github_release/SnowLotus-CellFM/models/SnowLotus_CellFM_best_embedding.pt}"
INTERVAL_SECONDS="${SNOWCELL_EDITOR_V03_RELEASE_INTERVAL_SECONDS:-1800}"
AUTO_PUSH="${SNOWCELL_EDITOR_V03_AUTO_PUSH:-1}"
LOCK_DIR="${PROJECT_DIR}/outputs/editor_v03_best_release_sync.lock"

cd "${PROJECT_DIR}"
mkdir -p logs outputs/post_training_release

while true; do
  date -Is
  if [ ! -s "${CHECKPOINT}" ]; then
    echo "waiting for checkpoint: ${CHECKPOINT}"
    sleep "${INTERVAL_SECONDS}"
    continue
  fi

  best_sha="$(sha256sum "${CHECKPOINT}" | awk '{print $1}')"
  release_sha=""
  if [ -s "${RELEASE_MODEL}" ]; then
    release_sha="$(sha256sum "${RELEASE_MODEL}" | awk '{print $1}')"
  fi

  echo "best_sha=${best_sha} release_sha=${release_sha:-missing}"
  if [ "${best_sha}" != "${release_sha}" ]; then
    if mkdir "${LOCK_DIR}" 2>/dev/null; then
      trap 'rmdir "${LOCK_DIR}" 2>/dev/null || true' EXIT
      .venv/bin/python scripts/write_editor_v03_current_best_docs.py
      if command -v pandoc >/dev/null 2>&1; then
        pandoc github_release_docs/EDITOR_HANDOFF.md -o github_release_docs/EDITOR_HANDOFF.docx || true
      fi
      RELEASE_LABEL=editor-v0.3 \
        SNOWCELL_RELEASE_EMBEDDING_CHECKPOINT="${CHECKPOINT}" \
        bash scripts/sync_github_release_repo.sh
      tar --exclude='.git' --exclude='*/__pycache__' --exclude='*/.pytest_cache' --exclude='*.pyc' --exclude='*.bak_*' -czf outputs/github_release_archives/snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz \
        -C outputs/github_release SnowLotus-CellFM
      sha256sum outputs/github_release_archives/snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz \
        > outputs/github_release_archives/snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz.sha256
      if [ "${AUTO_PUSH}" = "1" ]; then
        bash scripts/push_github_release.sh || true
      fi
      rmdir "${LOCK_DIR}" 2>/dev/null || true
      trap - EXIT
    else
      echo "release sync lock held; skipping"
    fi
  else
    echo "release already matches current best"
  fi
  sleep "${INTERVAL_SECONDS}"
done
