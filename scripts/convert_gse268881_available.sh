#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
mkdir -p data/public/GSE268881_npz logs

sample_regex="${SNOWCELL_GSE268881_REGEX:-_(Ath|Esa|Sir|Spa|Csa)_Root_Ctrl_scRNAseq_R1$}"
max_samples="${SNOWCELL_GSE268881_MAX_SAMPLES:-5}"
min_samples="${SNOWCELL_GSE268881_AVAILABLE_MIN_SAMPLES:-1}"

python scripts/geo_10x_to_npz.py \
  --input-dir data/public/GSE268881_10x \
  --output-dir data/public/GSE268881_npz \
  --dataset-id brassicaceae_multi_species_root_atlas \
  --sample-regex "$sample_regex" \
  --max-samples "$max_samples" \
  --min-samples 0 \
  --require-valid-gzip \
  --manifest-output logs/corpus_manifest.gse268881.converted.tsv || true

python scripts/build_gse268881_manifest_from_npz.py \
  --input-dir data/public/GSE268881_npz \
  --output data/corpus_manifest.gse268881.available.tsv \
  --dataset-id brassicaceae_multi_species_root_atlas \
  --sample-regex "$sample_regex" \
  --min-samples "$min_samples"

python - <<'PY'
from __future__ import annotations

from pathlib import Path

import pandas as pd

manifest = Path("data/corpus_manifest.gse268881.available.tsv")
table = pd.read_csv(manifest, sep="\t")
print(f"available_gse268881_samples={len(table)}")
print(table[["path", "species", "tissue"]].to_string(index=False))
PY
