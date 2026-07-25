#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/snowlotus-cellfm}"
cd "${PROJECT_DIR}"
source .venv/bin/activate 2>/dev/null || true

merged_manifest="${SNOWCELL_PLUS_MLM_CORPUS_MANIFEST:-data/corpus_manifest_public_mlm_plus_latest.tsv}"
output="${SNOWCELL_PLUS_MLM_CORPUS_OUTPUT:-data/plant_foundation_corpus_public_mlm_plus_latest.h5ad}"
active_output="data/plant_foundation_corpus_public_mlm.h5ad"

if [ "${output}" = "${active_output}" ]; then
  echo "Refusing to overwrite active v0.3 corpus: ${active_output}" >&2
  exit 2
fi

extra_manifests="${SNOWCELL_PLUS_EXTRA_CORPUS_MANIFESTS:-}"
if [ -z "${extra_manifests}" ]; then
  extra_manifests="$(find data -maxdepth 1 -type f \( -name 'corpus_manifest.gse*.tsv' -o -name 'corpus_manifest.scplantdb*.tsv' \) ! -name '*.available.tsv' | sort | tr '\n' ' ')"
fi

SNOWCELL_EXTRA_CORPUS_MANIFESTS="${extra_manifests}" \
SNOWCELL_MLM_CORPUS_MANIFEST="${merged_manifest}" \
SNOWCELL_MLM_CORPUS_OUTPUT="${output}" \
  bash scripts/build_public_mlm_corpus.sh

python - "${merged_manifest}" "${output}" "outputs/publication_package/public_mlm_plus_latest_manifest_summary.json" <<'PY'
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

manifest = Path(sys.argv[1])
corpus = Path(sys.argv[2])
output = Path(sys.argv[3])
rows = []
with manifest.open("r", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))
datasets = Counter(row.get("dataset_id", "") for row in rows if row.get("dataset_id"))
species = Counter(row.get("species", "") for row in rows if row.get("species"))
payload = {
    "manifest": manifest.as_posix(),
    "corpus": corpus.as_posix(),
    "manifest_rows": len(rows),
    "dataset_count": len(datasets),
    "species_count": len(species),
    "top_datasets": datasets.most_common(20),
    "top_species": species.most_common(20),
    "corpus_bytes": corpus.stat().st_size if corpus.exists() else 0,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(output)
PY
