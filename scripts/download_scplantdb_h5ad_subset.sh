#!/usr/bin/env bash
set -euo pipefail

cd "${SNOWCELL_PROJECT_DIR:-/mnt/snowlotus_cellfm}"
export PATH="/root/miniconda3/envs/myconda/bin:$PATH"
source .venv/bin/activate 2>/dev/null || true

datasets="${SNOWCELL_SCPLANTDB_DATASETS:-SRP169576}"
datasets_file="${SNOWCELL_SCPLANTDB_DATASETS_FILE:-}"
chunks_dir="${SNOWCELL_SCPLANTDB_CHUNKS_DIR:-data/public/source_pages/scplantdb_chunks}"
catalog_tsv="${SNOWCELL_SCPLANTDB_CATALOG_TSV:-data/public_discovery/scplantdb_dataset_catalog.tsv}"
catalog_json="${SNOWCELL_SCPLANTDB_CATALOG_JSON:-data/public_discovery/scplantdb_dataset_catalog.json}"
catalog_md="${SNOWCELL_SCPLANTDB_CATALOG_MD:-data/public_discovery/scplantdb_acquisition_catalog.md}"
gz_dir="${SNOWCELL_SCPLANTDB_GZ_DIR:-data/public/scPlantDB_h5ad_gz}"
h5ad_dir="${SNOWCELL_SCPLANTDB_H5AD_DIR:-data/public/scPlantDB_h5ad}"
manifest="${SNOWCELL_SCPLANTDB_MANIFEST:-data/corpus_manifest.scplantdb.tsv}"

mkdir -p "$(dirname "$catalog_tsv")" "$gz_dir" "$h5ad_dir" "$(dirname "$manifest")"

if find "$chunks_dir" -type f -name "*.js" -print -quit 2>/dev/null | grep -q .; then
  python scripts/extract_scplantdb_catalog.py \
    --chunks-dir "$chunks_dir" \
    --output-tsv "$catalog_tsv" \
    --output-json "$catalog_json" \
    --output-md "$catalog_md"
elif [ -s "$catalog_tsv" ]; then
  echo "[$(date)] reusing existing scPlantDB catalog because cached frontend chunks are unavailable"
else
  echo "[$(date)] missing scPlantDB frontend chunks and existing catalog" >&2
  exit 2
fi

if [ -n "$datasets_file" ] && [ -s "$datasets_file" ]; then
  datasets="$(python - "$datasets_file" <<'PY'
import sys
from pathlib import Path

items = []
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    items.append(line.split()[0])
print(" ".join(items))
PY
)"
fi

download_one() {
  local dataset="$1"
  local url="https://biobigdata.nju.edu.cn/scplantdb/datasets/${dataset}.h5ad.gz"
  local gz="${gz_dir}/${dataset}.h5ad.gz"
  local h5ad="${h5ad_dir}/${dataset}.h5ad"
  local tmp="${h5ad}.tmp.$$"

  if [ ! -s "$gz" ]; then
    if command -v aria2c >/dev/null 2>&1; then
      aria2c -c -x 4 -s 4 --summary-interval=30 -d "$gz_dir" -o "${dataset}.h5ad.gz" "$url"
    else
      curl -L -C - --retry 5 --retry-delay 10 -o "$gz" "$url"
    fi
  fi
  gzip -t "$gz"
  if [ ! -s "$h5ad" ] || [ "$gz" -nt "$h5ad" ]; then
    gzip -cd "$gz" > "$tmp"
    mv -f "$tmp" "$h5ad"
  fi
}

for dataset in $datasets; do
  download_one "$dataset"
done

SNOWCELL_SCPLANTDB_INCLUDE_EXISTING="${SNOWCELL_SCPLANTDB_INCLUDE_EXISTING:-1}" \
python - "$catalog_tsv" "$manifest" "$h5ad_dir" $datasets <<'PY'
import csv
import os
import sys
from pathlib import Path

catalog = Path(sys.argv[1])
manifest = Path(sys.argv[2])
h5ad_dir = Path(sys.argv[3])
datasets = sys.argv[4:]
if os.environ.get("SNOWCELL_SCPLANTDB_INCLUDE_EXISTING", "1") == "1":
    seen = set(datasets)
    for path in sorted(h5ad_dir.glob("*.h5ad")):
        dataset = path.stem
        if dataset not in seen:
            datasets.append(dataset)
            seen.add(dataset)
by_id = {}
with catalog.open("r", encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle, delimiter="\t"):
        by_id[row["dataset"]] = row
manifest.parent.mkdir(parents=True, exist_ok=True)
with manifest.open("w", encoding="utf-8", newline="") as handle:
    fieldnames = [
        "path",
        "dataset_id",
        "species",
        "tissue",
        "layer",
        "label_key",
        "coarse_label_key",
        "sample_key",
    ]
    writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
    writer.writeheader()
    for dataset in datasets:
        row = by_id.get(dataset, {})
        h5ad = h5ad_dir / f"{dataset}.h5ad"
        if not h5ad.exists():
            continue
        writer.writerow(
            {
                "path": h5ad.as_posix(),
                "dataset_id": f"scplantdb_{dataset}",
                "species": row.get("species") or "unknown_species",
                "tissue": row.get("tissue") or "unknown_tissue",
                "layer": "",
                "label_key": "Celltype",
                "coarse_label_key": "Celltype",
                "sample_key": "Orig.ident",
            }
        )
print(manifest)
PY
