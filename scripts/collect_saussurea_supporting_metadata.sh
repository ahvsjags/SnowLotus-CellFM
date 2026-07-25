#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

mkdir -p data/public/sra_runinfo data/public/source_pages logs outputs/publication_package

user_agent="SnowLotus-CellFM/0.1 saussurea-supporting-metadata"

download_runinfo() {
  local accession="$1"
  local output="data/public/sra_runinfo/${accession}.runinfo.csv"
  local tmp_output="${output}.part"
  local url="https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=${accession}"
  if [ -s "${output}" ] && [ "${SNOWCELL_FORCE_RUNINFO_REFRESH:-0}" != "1" ]; then
    echo "runinfo_exists ${accession}"
    return 0
  fi
  echo "download_runinfo ${accession}"
  rm -f "${tmp_output}"
  curl -L --retry 2 --retry-all-errors --connect-timeout 20 --max-time "${SNOWCELL_RUNINFO_MAX_TIME_SECONDS:-900}" \
    -H "User-Agent: ${user_agent}" \
    -o "${tmp_output}" "${url}" \
    && mv -f "${tmp_output}" "${output}" || true
  rm -f "${tmp_output}"
}

download_source_page() {
  local dataset_id="$1"
  local url="$2"
  local output="data/public/source_pages/${dataset_id}.html"
  if [ -s "${output}" ] && [ "${SNOWCELL_FORCE_SOURCE_PAGE_REFRESH:-0}" != "1" ]; then
    echo "source_page_exists ${dataset_id}"
    return 0
  fi
  if [[ "${url}" == http://* || "${url}" == https://* ]]; then
    curl -L --retry 5 --connect-timeout 20 --max-time 180 \
      -H "User-Agent: ${user_agent}" \
      -o "${output}" "${url}" || true
  fi
}

for accession in \
  PRJNA169171 SRR516284 SRX156202 \
  PRJNA991078 PRJNA1218246 PRJNA1033840 PRJNA387384 \
  PRJNA1278884 PRJNA1293189 PRJNA1355060; do
  download_runinfo "${accession}"
done

latest_discovery="$(ls -t data/public_discovery/ncbi_discovery_*.tsv 2>/dev/null | head -1 || true)"
if [ -n "$latest_discovery" ]; then
  dynamic_count=0
  dynamic_max="${SNOWCELL_SAUSSUREA_DISCOVERY_MAX_ACCESSIONS:-25}"
  python - "$latest_discovery" <<'PY' | while IFS=$'\t' read -r accession dataset_id url; do
import csv
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
accession_re = re.compile(r"\b(PRJNA\d+|PRJEB\d+|PRJDB\d+|SRP\d+|SRX\d+|SRR\d+)\b", re.I)
saussurea_re = re.compile(r"(saussurea|snow lotus|天山雪莲|雪莲)", re.I)
seen = set()
with path.open("r", encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle, delimiter="\t"):
        priority = (row.get("priority") or "").upper()
        if priority not in {"S", "A", "B"}:
            continue
        text = " ".join(
            row.get(key, "")
            for key in ["accession", "title", "organism", "summary", "matched_queries", "recommended_action", "url"]
        )
        if not saussurea_re.search(text):
            continue
        for accession in accession_re.findall(f"{row.get('accession', '')} {row.get('url', '')}"):
            accession = accession.upper()
            if accession in seen:
                continue
            seen.add(accession)
            dataset_id = f"saussurea_discovered_{accession.lower()}"
            url = row.get("url") or f"https://www.ncbi.nlm.nih.gov/bioproject/{accession}"
            print(f"{accession}\t{dataset_id}\t{url}")
PY
    if [ "$dynamic_count" -ge "$dynamic_max" ]; then
      break
    fi
    dynamic_count=$((dynamic_count + 1))
    download_runinfo "$accession"
    download_source_page "$dataset_id" "$url"
  done
fi

download_source_page saussurea_bulk_transcriptome "https://www.ncbi.nlm.nih.gov/sra/SRX156202%5Baccn%5D"
download_source_page saussurea_genome_reference "https://www.ncbi.nlm.nih.gov/bioproject/PRJNA991078"
download_source_page saussurea_low_pressure "https://pmc.ncbi.nlm.nih.gov/articles/PMC11941927/"
download_source_page saussurea_low_temperature "https://pmc.ncbi.nlm.nih.gov/articles/PMC12470158/"
download_source_page saussurea_raw_sequence_reads "https://www.omicsdi.org/dataset/project/PRJNA387384"
download_source_page saussurea_medusa_wgs "https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1278884"
download_source_page saussurea_hypsipeta_leaf_rna "https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1293189"
download_source_page saussurea_lyrata_hic "https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1355060"
download_source_page saussurea_multicellular_spheroid_single_cell_report "https://advanced.onlinelibrary.wiley.com/doi/10.1002/adhm.202504623"

python scripts/write_saussurea_supporting_evidence.py \
  --project-dir . \
  --output-md outputs/publication_package/saussurea_supporting_evidence.md \
  --output-json outputs/publication_package/saussurea_supporting_evidence.json

echo "Saussurea supporting metadata collection finished."
