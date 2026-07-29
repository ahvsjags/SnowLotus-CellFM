#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/mnt/snowlotus_cellfm}"
RELEASE_DIR="${RELEASE_DIR:-${PROJECT_DIR}/outputs/github_release/SnowLotus-CellFM}"
GITHUB_KEY="${GITHUB_KEY:-/root/.ssh/snowlotus_cellfm_github_ed25519}"

cd "${RELEASE_DIR}"

export GIT_SSH_COMMAND="ssh -i ${GITHUB_KEY} -o IdentitiesOnly=yes -o BatchMode=yes"
git push origin main --tags
