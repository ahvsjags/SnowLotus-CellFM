#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/public data/raw logs

source .venv/bin/activate 2>/dev/null || true

echo "== public data manifest =="
column -t -s $'\t' data/public_dataset_manifest.tsv || cat data/public_dataset_manifest.tsv

echo "== discover scPlantLLM reference code =="
clone_target="external/scPlantLLM"
if git -C "$clone_target" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  && [ -f "$clone_target/README.md" ] \
  && [ -f "$clone_target/scplantllm/model.py" ]; then
  git -C "$clone_target" rev-parse --short HEAD || true
elif [ "${SNOWCELL_CLONE_REFERENCES:-0}" != "1" ]; then
  echo "Set SNOWCELL_CLONE_REFERENCES=1 to clone scPlantLLM reference code."
else
  mkdir -p external
  if [ -e "$clone_target" ]; then
    backup="${clone_target}.incomplete_$(date +%Y%m%d_%H%M%S)"
    mv "$clone_target" "$backup"
    echo "Moved incomplete scPlantLLM checkout to $backup"
  fi
  timeout 180 git clone --depth 1 https://github.com/compbioNJU/scPlantLLM "$clone_target" \
    || echo "scPlantLLM clone skipped after timeout/network failure; continuing pipeline."
fi

echo "== generate Figshare download scripts when API is reachable =="
python -m snowcell.collect manifest-scripts \
  --manifest data/public_dataset_manifest.tsv \
  --output-dir scripts/generated_downloads || true
chmod +x scripts/generated_downloads/*.sh 2>/dev/null || true

echo "== lightweight provenance and accession metadata =="
if [ "${SNOWCELL_FETCH_PUBLIC_METADATA:-1}" = "1" ]; then
  for script in \
    scripts/generated_downloads/download_source_pages.sh \
    scripts/generated_downloads/download_sra_runinfo.sh \
    scripts/generated_downloads/download_geo_filelists.sh; do
    [ -f "$script" ] || continue
    echo "running $script"
    bash "$script" || true
  done
else
  echo "Set SNOWCELL_FETCH_PUBLIC_METADATA=1 to fetch source pages, SRA runinfo, and GEO filelists."
fi

echo "== optional public data downloads =="
if [ "${SNOWCELL_DOWNLOAD_PUBLIC_DATA:-0}" = "1" ]; then
  for script in scripts/generated_downloads/*.sh; do
    [ -f "$script" ] || continue
    case "$(basename "$script")" in
      download_source_pages.sh|download_sra_runinfo.sh|download_geo_filelists.sh)
        continue
        ;;
    esac
    echo "running $script"
    bash "$script" || true
  done
else
  echo "Set SNOWCELL_DOWNLOAD_PUBLIC_DATA=1 to run generated download scripts."
fi

echo "== accession checklist =="
cat > data/public/DATA_COLLECTION_TODO.md <<'EOF'
# Public Data Collection TODO

1. Use scPlantDB as the discovery index and download processed matrices/accessions for high-quality plant scRNA datasets.
2. Add each processed `.h5ad` or `.npz` to `data/corpus_manifest.tsv`.
3. Minimum first corpus:
   - Arabidopsis root atlas
   - Arabidopsis leaf atlas
   - rice seedling atlas
   - one maize or tomato root atlas
   - Catharanthus roseus medicinal plant single-cell multi-omics
   - Saussurea involucrata user sc/snRNA data
4. Keep raw data provenance in `data/public_dataset_manifest.tsv`.
5. Inspect `data/public/geo_filelists/*/filelist.txt` before full GEO downloads; some processed matrices are tens of GB.
6. Build merged corpus:

```bash
cp data/corpus_manifest.template.tsv data/corpus_manifest.tsv
snowcell build-corpus --manifest data/corpus_manifest.tsv --output data/plant_foundation_corpus.h5ad
```
EOF

echo "Collection helper finished. See data/public/DATA_COLLECTION_TODO.md"
