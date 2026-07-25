#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

accession="${SNOWCELL_GEO_ACCESSION:?set SNOWCELL_GEO_ACCESSION}"
dataset_id="${SNOWCELL_GEO_DATASET_ID:?set SNOWCELL_GEO_DATASET_ID}"
species="${SNOWCELL_GEO_SPECIES:?set SNOWCELL_GEO_SPECIES}"
tissue="${SNOWCELL_GEO_TISSUE:?set SNOWCELL_GEO_TISSUE}"
feature_column="${SNOWCELL_GEO_FEATURE_COLUMN:-0}"
label="${SNOWCELL_GEO_LABEL:-unannotated}"
coarse_label="${SNOWCELL_GEO_COARSE_LABEL:-unannotated}"
max_sets="${SNOWCELL_GEO_MAX_SETS:-4}"

file_index="${SNOWCELL_GEO_FILE_INDEX:-$(ls -t data/public_discovery/geo_supplementary_files_*.tsv 2>/dev/null | head -1 || true)}"
download_dir="data/public/${accession}_mtx_components"
extract_dir="data/public/${accession}_mtx_extracted"
npz_dir="data/public/${accession}_npz"
plan_tsv="data/public/${accession}_mtx_component_download_plan.tsv"
aria2_input="data/public/${accession}_mtx_component_aria2_urls.txt"
manifest_output="data/corpus_manifest.${accession,,}.tsv"
unsupported_report="${download_dir}/unsupported_single_cell_matrix.json"

mkdir -p "$download_dir" "$extract_dir" "$npz_dir" logs

if [ -z "$file_index" ] || [ ! -s "$file_index" ]; then
  echo "Missing GEO supplementary file index for $accession" >&2
  exit 1
fi

python - "$file_index" "$accession" "$plan_tsv" "$max_sets" "$manifest_output" "$unsupported_report" <<'PY'
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

file_index = Path(sys.argv[1])
accession = sys.argv[2].upper()
plan_tsv = Path(sys.argv[3])
max_sets = int(sys.argv[4])
manifest_output = Path(sys.argv[5])
unsupported_report = Path(sys.argv[6])

suffixes = {
    "matrix": re.compile(r"(.+?)(?:_matrix)?\.mtx(?:\.gz)?$", re.IGNORECASE),
    "features": re.compile(r"(.+?)_(?:features|genes)\.tsv(?:\.gz)?$", re.IGNORECASE),
    "barcodes": re.compile(r"(.+?)_barcodes\.tsv(?:\.gz)?$", re.IGNORECASE),
}
sets: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
with file_index.open("r", encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle, delimiter="\t"):
        if (row.get("accession") or "").upper() != accession:
            continue
        filename = row.get("filename", "")
        url = row.get("url", "")
        if not filename or not url:
            continue
        for kind, pattern in suffixes.items():
            match = pattern.fullmatch(filename)
            if match:
                prefix = match.group(1)
                sets[prefix][kind] = {"filename": filename, "url": url}
                break

complete = [
    (prefix, values)
    for prefix, values in sorted(sets.items())
    if {"matrix", "features", "barcodes"}.issubset(values)
][:max_sets]

if not complete:
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    with manifest_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["path", "dataset_id", "species", "tissue", "layer", "label_key", "coarse_label_key", "sample_key"])
    unsupported_report.parent.mkdir(parents=True, exist_ok=True)
    unsupported_report.write_text(
        json.dumps(
            {
                "accession": accession,
                "status": "unsupported_for_single_cell_matrix_corpus",
                "reason": "No complete matrix/features/barcodes component set was found in the GEO supplementary file index.",
                "file_index": file_index.as_posix(),
                "corpus_manifest": manifest_output.as_posix(),
                "corpus_manifest_rows": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(unsupported_report)
    print(manifest_output)
    raise SystemExit(0)

plan_tsv.parent.mkdir(parents=True, exist_ok=True)
with plan_tsv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, delimiter="\t", fieldnames=["prefix", "kind", "filename", "url"])
    writer.writeheader()
    for prefix, values in complete:
        for kind in ["matrix", "features", "barcodes"]:
            writer.writerow({"prefix": prefix, "kind": kind, **values[kind]})
print(plan_tsv)
for prefix, values in complete:
    print(prefix, ",".join(values[kind]["filename"] for kind in ["matrix", "features", "barcodes"]))
PY

if [ -s "$unsupported_report" ] && [ "$(wc -l < "$manifest_output" | tr -d ' ')" = "1" ]; then
  exit 0
fi

python - "$plan_tsv" "$download_dir" "$aria2_input" <<'PY'
from __future__ import annotations

import csv
import sys
from pathlib import Path

plan_tsv = Path(sys.argv[1])
download_dir = Path(sys.argv[2])
aria2_input = Path(sys.argv[3])
download_dir.mkdir(parents=True, exist_ok=True)
lines: list[str] = []
with plan_tsv.open("r", encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle, delimiter="\t"):
        filename = row["filename"]
        target = download_dir / filename
        if target.exists() and target.stat().st_size > 0:
            print(f"exists {target}")
            continue
        lines.extend([row["url"], f"  dir={download_dir.as_posix()}", f"  out={filename}"])
aria2_input.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
print(aria2_input)
PY

if [ -s "$aria2_input" ]; then
  if command -v aria2c >/dev/null 2>&1; then
    aria2c -c -j "${SNOWCELL_GEO_PARALLEL_JOBS:-2}" -x 1 -s 1 \
      --max-tries=8 --retry-wait=10 --timeout=120 --allow-overwrite=true --auto-file-renaming=false \
      --user-agent="SnowLotus-CellFM/0.1 public-data-collector" \
      -i "$aria2_input"
  else
    python - "$plan_tsv" "$download_dir" <<'PY'
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

plan_tsv = Path(sys.argv[1])
download_dir = Path(sys.argv[2])
with plan_tsv.open("r", encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle, delimiter="\t"):
        target = download_dir / row["filename"]
        if target.exists() and target.stat().st_size > 0:
            continue
        subprocess.check_call(
            [
                "curl",
                "-L",
                "--fail",
                "--retry",
                "8",
                "--connect-timeout",
                "20",
                "--max-time",
                "7200",
                "-H",
                "User-Agent: SnowLotus-CellFM/0.1 public-data-collector",
                "-o",
                str(target),
                row["url"],
            ]
        )
PY
  fi
fi

rm -rf "$extract_dir"
mkdir -p "$extract_dir"
python - "$plan_tsv" "$download_dir" "$extract_dir" <<'PY'
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

plan_tsv = Path(sys.argv[1])
download_dir = Path(sys.argv[2])
extract_dir = Path(sys.argv[3])
with plan_tsv.open("r", encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle, delimiter="\t"):
        sample_dir = extract_dir / row["prefix"]
        sample_dir.mkdir(parents=True, exist_ok=True)
        source = download_dir / row["filename"]
        shutil.copy2(source, sample_dir / row["filename"])
        print(sample_dir / row["filename"])
PY

conversion_log="${download_dir}/${accession}_component_conversion_error.log"
if ! python scripts/geo_mtx_tar_to_npz.py \
  --input-dir "$extract_dir" \
  --output-dir "$npz_dir" \
  --dataset-id "$dataset_id" \
  --species "$species" \
  --tissue "$tissue" \
  --feature-column "$feature_column" \
  --label "$label" \
  --coarse-label "$coarse_label" \
  --manifest-output "$manifest_output" \
  --min-samples 1 2> "$conversion_log"; then
  cat "$conversion_log" >&2
  python - "$manifest_output" "$unsupported_report" "$accession" "$conversion_log" <<'PY'
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

manifest_output = Path(sys.argv[1])
unsupported_report = Path(sys.argv[2])
accession = sys.argv[3]
conversion_log = Path(sys.argv[4])
manifest_output.parent.mkdir(parents=True, exist_ok=True)
with manifest_output.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t")
    writer.writerow(["path", "dataset_id", "species", "tissue", "layer", "label_key", "coarse_label_key", "sample_key"])
unsupported_report.parent.mkdir(parents=True, exist_ok=True)
unsupported_report.write_text(
    json.dumps(
        {
            "accession": accession,
            "status": "unsupported_for_single_cell_matrix_corpus",
            "reason": "GEO component files were downloaded, but conversion failed.",
            "conversion_error_tail": conversion_log.read_text(encoding="utf-8", errors="replace")[-4000:],
            "corpus_manifest": manifest_output.as_posix(),
            "corpus_manifest_rows": 0,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(unsupported_report)
PY
  exit 0
fi

rm -f "$unsupported_report"
echo "Wrote $manifest_output"
