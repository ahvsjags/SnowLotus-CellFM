#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

accession="${SNOWCELL_GEO_ACCESSION:?set SNOWCELL_GEO_ACCESSION}"
out_dir="data/public/geo_filelists/${accession}"
index_html="${out_dir}/index.html"
filelist="${out_dir}/filelist.txt"

mkdir -p "$out_dir" logs

curl -L --fail --retry 5 --connect-timeout 20 --max-time 1200 \
  -H "User-Agent: SnowLotus-CellFM/0.1 public-data-collector" \
  -o "$index_html" \
  "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=${accession}"

python - "$index_html" "$filelist" <<'PY'
from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote

index_html = Path(sys.argv[1])
filelist = Path(sys.argv[2])
text = html.unescape(index_html.read_text(encoding="utf-8", errors="ignore"))
names = set()
for raw in re.findall(r"GSM\d+_[A-Za-z0-9_.%+\-()]+", text):
    name = unquote(raw).strip().rstrip(".,;)")
    if any(name.endswith(suffix) for suffix in (".h5", ".h5ad", ".rds", ".rds.gz", ".tar.gz", ".mtx.gz")):
        names.add(name)

if not names:
    raise SystemExit(f"no GEO supplementary filenames found in {index_html}")

filelist.write_text("\n".join(sorted(names)) + "\n", encoding="utf-8")
print(filelist)
for name in sorted(names):
    print(name)
PY
