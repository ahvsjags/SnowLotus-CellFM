#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

accession="GSE149217"
dataset_id="tomato_rice_root_tip_celltype_atlas"
species="${SNOWCELL_GSE149217_SPECIES:-Solanum lycopersicum; Oryza sativa}"
tissue="root_tip"
raw_dir="data/public/${accession}_raw_tar"
manifest_output="data/corpus_manifest.gse149217.tsv"
unsupported_report="${raw_dir}/unsupported_single_cell_matrix.json"

mkdir -p "$raw_dir" logs

python - "$manifest_output" "$unsupported_report" "$accession" "$dataset_id" "$species" "$tissue" <<'PY'
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

manifest_output = Path(sys.argv[1])
unsupported_report = Path(sys.argv[2])
accession, dataset_id, species, tissue = sys.argv[3:7]

manifest_output.parent.mkdir(parents=True, exist_ok=True)
with manifest_output.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(["path", "dataset_id", "species", "tissue", "layer", "label_key", "coarse_label_key", "sample_key"])

payload = {
    "accession": accession,
    "dataset_id": dataset_id,
    "species": species,
    "tissue": tissue,
    "status": "unsupported_for_single_cell_matrix_corpus",
    "reason": (
        "GEO GSE149217 is a tomato/rice root cell-type TRAP-seq and ATAC-seq atlas. "
        "The downloadable raw_counts CSV.gz files are gene-by-sample count tables, "
        "not scRNA/snRNA cell-by-gene expression matrices with cell barcodes."
    ),
    "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149217",
    "example_supplementary_files": [
        "GSE149217_Rice_ATLAS_raw_counts.csv.gz",
        "GSE149217_Tomato_ATLAS_raw_counts.csv.gz",
        "GSE149217_Tomato_DWL_raw_counts.csv.gz",
        "GSE149217_Tomato_Field_raw_counts.csv.gz",
    ],
    "corpus_manifest": manifest_output.as_posix(),
    "corpus_manifest_rows": 0,
}
unsupported_report.parent.mkdir(parents=True, exist_ok=True)
unsupported_report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(unsupported_report)
print(manifest_output)
PY

echo "GSE149217 is not a single-cell expression matrix corpus target; wrote unsupported report and header-only ${manifest_output}"
