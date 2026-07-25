#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

archive="data/public/direct_downloads/scplantllm_srp169576_benchmark.download"
extract_dir="data/public/scplantllm_srp169576"
raw_dir="${extract_dir}/SRP169576_RAW"
mtx_dir="data/public/scplantllm_srp169576_mtx"
npz_dir="data/public/scplantllm_srp169576_npz"

if [ ! -f "$archive" ]; then
  echo "Missing $archive. Run scripts/generated_downloads/download_direct_reference_data.sh first." >&2
  exit 1
fi

mkdir -p "$extract_dir" "$mtx_dir" "$npz_dir"
if [ ! -d "$raw_dir" ]; then
  tar -xzf "$archive" -C "$extract_dir" --strip-components=0
fi

if ! command -v Rscript >/dev/null 2>&1; then
  echo "Rscript not found. Run scripts/install_r_singlecell_tools.sh first." >&2
  exit 2
fi

Rscript scripts/export_seurat_rds_to_mtx.R "$raw_dir" "$mtx_dir"
python scripts/build_npz_from_seurat_export.py \
  --export-dir "$mtx_dir" \
  --output-dir "$npz_dir" \
  --dataset-id scplantllm_srp169576 \
  --species Arabidopsis_thaliana \
  --tissue root

manifest="data/corpus_manifest.tsv"

python - <<'PY'
from pathlib import Path

manifest = Path("data/corpus_manifest.tsv")
template = Path("data/corpus_manifest.template.tsv")
header = template.read_text(encoding="utf-8").splitlines()[0]
existing = manifest.read_text(encoding="utf-8").splitlines() if manifest.exists() else [header]
kept = [line for line in existing[1:] if line.strip() and Path(line.split("\t", 1)[0]).exists()]
seen = {line.split("\t", 1)[0] for line in kept}
rows = []
for path in sorted(Path("data/public/scplantllm_srp169576_npz").glob("*.npz")):
    p = str(path)
    if p in seen:
        continue
    sample = path.stem
    rows.append(
        "\t".join(
            [
                p,
                f"scplantllm_srp169576_{sample}",
                "Arabidopsis_thaliana",
                "root",
                "",
                "cell_type",
                "cell_type_coarse",
                "sample_id",
            ]
        )
    )
manifest.write_text(header + "\n" + "\n".join(kept + rows) + "\n", encoding="utf-8")
print(manifest)
PY
