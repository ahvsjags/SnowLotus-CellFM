#!/usr/bin/env bash
set -euo pipefail

PROJECT="${PROJECT:-/root/snowlotus-cellfm}"
RELEASE_LABEL="${RELEASE_LABEL:-editor-v0.3}"
RELEASE_DIR="${PROJECT}/outputs/github_release/SnowLotus-CellFM"
ARCHIVE_DIR="${PROJECT}/outputs/github_release_archives"
STATE_DIR="${PROJECT}/outputs/post_training_release"
FULL="${ARCHIVE_DIR}/snowlotus-cellfm-${RELEASE_LABEL}-full-with-models.tar.gz"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="${STATE_DIR}/editor_v03_full_archive_rebuild_${STAMP}.log"
if [ -z "${PYTHON:-}" ]; then
  if [ -x "${PROJECT}/.venv/bin/python" ]; then
    PYTHON="${PROJECT}/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
  else
    PYTHON="python"
  fi
fi

mkdir -p "${ARCHIVE_DIR}" "${STATE_DIR}"
exec > >(tee "${LOG}") 2>&1

echo "FULL_ARCHIVE_REBUILD_BEGIN $(date -Is)"
cd "${RELEASE_DIR}"
sha256sum -c models/SHA256SUMS.txt
git status -sb
git log --oneline -1
git tag --points-at HEAD

cd "${PROJECT}"
tar --exclude='.git' --exclude='*/__pycache__' --exclude='*/.pytest_cache' --exclude='*.pyc' --exclude='*.bak_*' -czf "${FULL}" -C "$(dirname "${RELEASE_DIR}")" "$(basename "${RELEASE_DIR}")"
sha256sum "${FULL}" > "${FULL}.sha256"

"${PYTHON}" - "${FULL}" "${FULL}.sha256" "${LOG}" > "${STATE_DIR}/editor_v03_full_archive_current.json" <<'PY'
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

full = Path(sys.argv[1])
sha_file = Path(sys.argv[2])
log = Path(sys.argv[3])
sha = hashlib.sha256()
with full.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        sha.update(chunk)
payload = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "archive": full.as_posix(),
    "sha256_file": sha_file.as_posix(),
    "sha256": sha.hexdigest(),
    "bytes": full.stat().st_size,
    "log": log.as_posix(),
}
print(json.dumps(payload, indent=2, sort_keys=True))
PY

ls -lh "${FULL}" "${FULL}.sha256"
cat "${FULL}.sha256"
echo "FULL_ARCHIVE_REBUILD_END $(date -Is)"
echo "LOG=${LOG}"
