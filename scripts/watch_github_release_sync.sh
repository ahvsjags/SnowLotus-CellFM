#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
INTERVAL_SECONDS="${SNOWCELL_RELEASE_SYNC_INTERVAL_SECONDS:-3600}"
LOCK_DIR="${PROJECT_DIR}/outputs/github_release_sync.lock"

cd "${PROJECT_DIR}"
mkdir -p logs outputs

while true; do
  date -Is
  if mkdir "${LOCK_DIR}" 2>/dev/null; then
    trap 'rmdir "${LOCK_DIR}" 2>/dev/null || true' EXIT
    if bash scripts/generate_publication_package.sh; then
      bash scripts/sync_github_release_repo.sh
    else
      echo "publication package refresh failed; skipping release sync for this cycle" >&2
    fi
    rmdir "${LOCK_DIR}" 2>/dev/null || true
    trap - EXIT
  else
    echo "release sync already running; skipping this cycle"
  fi
  sleep "${INTERVAL_SECONDS}"
done
