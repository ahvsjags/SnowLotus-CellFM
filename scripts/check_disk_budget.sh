#!/usr/bin/env bash
set -euo pipefail

path="${1:-/mnt/snowlotus_cellfm}"
min_free_bytes="${SNOWCELL_MIN_FREE_BYTES:-10737418240}"

free_bytes="$(df -PB1 "${path}" | awk 'NR == 2 {print $4}')"
if [ -z "${free_bytes}" ]; then
  echo "disk budget check failed: cannot read free bytes for ${path}" >&2
  exit 2
fi

if [ "${free_bytes}" -lt "${min_free_bytes}" ]; then
  echo "disk budget pause: path=${path} free_bytes=${free_bytes} required_bytes=${min_free_bytes}" >&2
  exit 75
fi

echo "disk budget ok: path=${path} free_bytes=${free_bytes} required_bytes=${min_free_bytes}"
