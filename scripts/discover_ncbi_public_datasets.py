from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "SnowLotus-CellFM/0.1 public-data-discovery"

ACCESSION_RE = re.compile(
    r"\b(GSE\d+|GSM\d+|GDS\d+|SRP\d+|SRA\d+|SRX\d+|SRR\d+|PRJNA\d+|PRJEB\d+|PRJDB\d+)\b"
)

PLANT_TERMS = [
    "plant",
    "plants",
    "viridiplantae",
    "arabidopsis",
    "oryza",
    "rice",
    "maize",
    "zea",
    "wheat",
    "triticum",
    "tomato",
    "solanum",
    "cotton",
    "gossypium",
    "brassicaceae",
    "asteraceae",
    "helianthus",
    "lactuca",
    "chrysanthemum",
    "catharanthus",
    "artemisia",
    "stevia",
    "rebaudiana",
    "marchantia",
    "medicago",
    "populus",
    "soybean",
    "glycine",
    "cucumber",
    "cucumis",
    "sorghum",
    "barley",
    "hordeum",
    "millet",
    "setaria",
    "moss",
    "physcomitrium",
    "physcomitrella",
    "saussurea",
    "snow lotus",
    "involucrata",
    "dolomiaea",
    "costus",
]

NAMED_PLANT_TERMS = [
    term for term in PLANT_TERMS if term not in {"plant", "plants", "viridiplantae"}
]

NON_PLANT_ORGANISM_TERMS = [
    "homo sapiens",
    "mus musculus",
    "rattus norvegicus",
    "sus scrofa",
    "porcine",
    "mouse",
    "mice",
    "murine",
    "human",
    "rabbit",
    "fly",
    "drosophila",
    "beetle",
    "azoarcus",
]

PRIORITY_RANK = {"S": 0, "A": 1, "B": 2, "C": 3}


@dataclass(frozen=True)
class QuerySpec:
    label: str
    db: str
    term: str


@dataclass
class DiscoveryRecord:
    query_label: str
    db: str
    uid: str
    accession: str
    title: str
    organism: str
    sample_count: str
    publication_date: str
    url: str
    priority: str
    score: int
    recommended_action: str
    matched_queries: str
    summary: str


DEFAULT_QUERIES = [
    QuerySpec(
        label="saussurea_single_cell_gds",
        db="gds",
        term=(
            '(Saussurea[All Fields] OR "Saussurea involucrata"[All Fields] OR '
            '"snow lotus"[All Fields]) AND ("single cell"[All Fields] OR '
            'single-cell[All Fields] OR scRNA[All Fields] OR snRNA[All Fields] OR '
            '"single nucleus"[All Fields] OR "10x"[All Fields])'
        ),
    ),
    QuerySpec(
        label="saussurea_transcriptome_sra",
        db="sra",
        term=(
            '("Saussurea involucrata"[All Fields] OR Saussurea[All Fields] OR '
            '"snow lotus"[All Fields]) AND (RNA[All Fields] OR transcriptome[All Fields] '
            'OR "RNA-Seq"[All Fields] OR stress[All Fields] OR genome[All Fields])'
        ),
    ),
    QuerySpec(
        label="plant_single_cell_gds",
        db="gds",
        term=(
            '(plant[All Fields] OR Arabidopsis[All Fields] OR Oryza[All Fields] OR '
            'rice[All Fields] OR maize[All Fields] OR wheat[All Fields] OR tomato[All Fields] '
            'OR cotton[All Fields] OR Brassicaceae[All Fields]) AND '
            '("single cell"[All Fields] OR single-cell[All Fields] OR scRNA[All Fields] OR '
            'snRNA[All Fields] OR "single nucleus"[All Fields] OR "10x"[All Fields])'
        ),
    ),
    QuerySpec(
        label="plant_single_cell_sra",
        db="sra",
        term=(
            '(plant[All Fields] OR Arabidopsis[All Fields] OR Oryza[All Fields] OR '
            'rice[All Fields] OR maize[All Fields] OR wheat[All Fields] OR tomato[All Fields] '
            'OR cotton[All Fields] OR Brassicaceae[All Fields]) AND '
            '("single cell"[All Fields] OR single-cell[All Fields] OR scRNA[All Fields] OR '
            'snRNA[All Fields] OR "single nucleus"[All Fields] OR "10x"[All Fields])'
        ),
    ),
    QuerySpec(
        label="woody_legume_cereal_single_cell_gds",
        db="gds",
        term=(
            '(Populus[All Fields] OR Medicago[All Fields] OR Glycine[All Fields] OR '
            'soybean[All Fields] OR sorghum[All Fields] OR barley[All Fields] OR '
            'Hordeum[All Fields] OR Setaria[All Fields] OR cucumber[All Fields] OR '
            'Cucumis[All Fields]) AND ("single cell"[All Fields] OR single-cell[All Fields] '
            'OR scRNA[All Fields] OR snRNA[All Fields] OR "single nucleus"[All Fields] '
            'OR "10x"[All Fields] OR "spatial transcriptomics"[All Fields])'
        ),
    ),
    QuerySpec(
        label="plant_spatial_single_cell_gds",
        db="gds",
        term=(
            '(plant[All Fields] OR Arabidopsis[All Fields] OR Oryza[All Fields] OR '
            'Populus[All Fields] OR Zea[All Fields] OR Triticum[All Fields]) AND '
            '("spatial transcriptomics"[All Fields] OR "spatially resolved"[All Fields] OR '
            'MERFISH[All Fields] OR Visium[All Fields]) AND '
            '("single cell"[All Fields] OR single-cell[All Fields] OR scRNA[All Fields] OR '
            'snRNA[All Fields] OR "single nucleus"[All Fields])'
        ),
    ),
    QuerySpec(
        label="asteraceae_single_cell",
        db="gds",
        term=(
            '(Asteraceae[All Fields] OR sunflower[All Fields] OR Helianthus[All Fields] OR '
            'lettuce[All Fields] OR Lactuca[All Fields] OR chrysanthemum[All Fields] OR '
            'Chrysanthemum[All Fields]) AND ("single cell"[All Fields] OR single-cell[All Fields] '
            'OR scRNA[All Fields] OR snRNA[All Fields] OR "10x"[All Fields])'
        ),
    ),
    QuerySpec(
        label="saussurea_alpine_evidence_sra",
        db="sra",
        term=(
            '(Saussurea[All Fields] OR "snow lotus"[All Fields] OR '
            '"Saussurea involucrata"[All Fields] OR "Saussurea medusa"[All Fields] OR '
            '"Saussurea hypsipeta"[All Fields] OR Dolomiaea[All Fields]) AND '
            '(RNA[All Fields] OR transcriptome[All Fields] OR "RNA-Seq"[All Fields] OR '
            'genome[All Fields] OR "low temperature"[All Fields] OR "low pressure"[All Fields] '
            'OR hypoxia[All Fields] OR alpine[All Fields] OR flavonoid[All Fields])'
        ),
    ),
    QuerySpec(
        label="medicinal_secondary_metabolism_single_cell",
        db="gds",
        term=(
            '(Catharanthus[All Fields] OR Artemisia[All Fields] OR Gossypium[All Fields] OR '
            'medicinal[All Fields] OR terpenoid[All Fields] OR flavonoid[All Fields] OR '
            'glandular[All Fields]) AND ("single cell"[All Fields] OR single-cell[All Fields] '
            'OR scRNA[All Fields] OR snRNA[All Fields] OR "10x"[All Fields])'
        ),
    ),
]


def compact_text(value: Any, max_len: int = 600) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) > max_len:
        return text[: max_len - 3].rstrip() + "..."
    return text


def contains_any_term(text: str, terms: list[str]) -> bool:
    for term in terms:
        term_pattern = re.escape(term).replace(r"\ ", r"[\s-]+")
        if re.search(rf"(?<![a-z0-9]){term_pattern}(?![a-z0-9])", text):
            return True
    return False


def request_json(
    endpoint: str,
    params: dict[str, str | int],
    attempts: int = 4,
    retry_sleep_seconds: float = 3.0,
) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    url = f"{EUTILS_BASE}/{endpoint}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            if attempt == attempts:
                break
            time.sleep(retry_sleep_seconds * attempt)
    raise RuntimeError(f"NCBI request failed after {attempts} attempts: {url}") from last_error


def with_ncbi_identity(params: dict[str, str | int], email: str | None, api_key: str | None) -> None:
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key


def esearch(
    spec: QuerySpec,
    retmax: int,
    email: str | None = None,
    api_key: str | None = None,
) -> list[str]:
    params: dict[str, str | int] = {
        "db": spec.db,
        "term": spec.term,
        "retmode": "json",
        "retmax": retmax,
        "sort": "relevance",
    }
    with_ncbi_identity(params, email, api_key)
    data = request_json("esearch.fcgi", params)
    return [str(uid) for uid in data.get("esearchresult", {}).get("idlist", [])]


def esummary(
    db: str,
    uids: list[str],
    email: str | None = None,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    if not uids:
        return []
    params: dict[str, str | int] = {
        "db": db,
        "id": ",".join(uids),
        "retmode": "json",
    }
    with_ncbi_identity(params, email, api_key)
    data = request_json("esummary.fcgi", params)
    result = data.get("result", {})
    return [result[uid] for uid in result.get("uids", []) if uid in result]


def extract_accessions(text: str) -> list[str]:
    accessions = ACCESSION_RE.findall(text)
    return sorted(set(accessions), key=lambda value: (accession_rank(value), value))


def accession_rank(accession: str) -> int:
    if accession.startswith("GSE"):
        return 0
    if accession.startswith("GDS"):
        return 1
    if accession.startswith("PRJ"):
        return 2
    if accession.startswith("SRP"):
        return 3
    if accession.startswith("SRX"):
        return 4
    if accession.startswith("SRR"):
        return 5
    if accession.startswith("GSM"):
        return 6
    return 9


def url_for_accession(accession: str, db: str, uid: str) -> str:
    if accession.startswith(("GSE", "GDS", "GSM")):
        return f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"
    if accession.startswith("PRJ"):
        return f"https://www.ncbi.nlm.nih.gov/bioproject/{accession}"
    if accession.startswith(("SRP", "SRA", "SRX", "SRR")):
        return f"https://www.ncbi.nlm.nih.gov/sra/?term={urllib.parse.quote(accession)}"
    return f"https://www.ncbi.nlm.nih.gov/{db}/{uid}"


def field_text(item: dict[str, Any], names: list[str], max_len: int = 600) -> str:
    for name in names:
        value = item.get(name)
        if value not in (None, ""):
            return compact_text(value, max_len=max_len)
    return ""


def infer_accession(db: str, uid: str, item: dict[str, Any]) -> str:
    direct = field_text(item, ["accession", "Accession", "gds", "bioproject", "project_acc"])
    if direct and ACCESSION_RE.fullmatch(direct):
        return direct
    text = json.dumps(item, ensure_ascii=False)
    accessions = extract_accessions(text)
    if accessions:
        return accessions[0]
    return f"{db}:{uid}"


def score_and_action(accession: str, title: str, organism: str, summary: str) -> tuple[str, int, str]:
    text = f"{accession} {title} {organism} {summary}".lower()
    score = 0
    has_saussurea = contains_any_term(text, ["saussurea", "snow lotus"])
    has_plant = contains_any_term(text, PLANT_TERMS)
    has_named_plant = contains_any_term(text, NAMED_PLANT_TERMS)
    has_non_plant_organism = contains_any_term(f"{organism} {title}".lower(), NON_PLANT_ORGANISM_TERMS)
    has_single_cell = contains_any_term(
        text, ["single cell", "single-cell", "scrna", "snrna", "single nucleus", "10x"]
    )
    if has_saussurea:
        score += 6
    if has_single_cell:
        score += 4
    if any(term in text for term in ["10x", "filtered_feature_bc_matrix", "matrix.mtx", ".h5", ".rds"]):
        score += 2
    if has_plant:
        score += 2
    if contains_any_term(
        text,
        [
            "stress",
            "hypoxia",
            "low pressure",
            "cold",
            "low temperature",
            "uv",
            "alpine",
            "drought",
            "osmotic",
            "mechanical stress",
        ],
    ):
        score += 1
    if contains_any_term(text, ["terpenoid", "flavonoid", "glandular", "medicinal"]):
        score += 1

    if has_non_plant_organism and not has_named_plant and not has_saussurea:
        return "C", min(score, 2), "out-of-scope non-plant organism unless manual review overrides"
    if not has_plant and not has_saussurea:
        return "C", min(score, 2), "out-of-scope unless manual review finds plant metadata"
    if has_saussurea and has_single_cell:
        return "S", score, "immediate Snow Lotus scRNA review; fetch files and design fine-tuning"
    if accession.startswith("GSE") and has_single_cell:
        priority = "A" if has_named_plant and score >= 6 else "B"
        return priority, score, "fetch GEO supplementary filelist; add downloader if matrix/RDS/H5 exists"
    if has_saussurea:
        return "A", score, "Snow Lotus evidence layer; use for genome/transcriptome/stress support"
    if has_single_cell:
        return "B", score, "plant single-cell candidate; inspect species, tissue, labels, and downloadable files"
    return "C", score, "manual review"


def record_from_summary(db: str, query_label: str, item: dict[str, Any]) -> DiscoveryRecord:
    uid = str(item.get("uid", ""))
    title = field_text(item, ["title", "Title", "expname", "study_title"])
    organism = field_text(item, ["taxon", "organism", "Organism", "species"])
    sample_count = field_text(item, ["n_samples", "samples", "SampleCount", "runs"])
    publication_date = field_text(item, ["pdat", "PDAT", "createdate", "updatedate", "releasedate"])
    summary = field_text(item, ["summary", "Summary", "expxml", "runs"], max_len=900)
    accession = infer_accession(db, uid, item)
    priority, score, action = score_and_action(accession, title, organism, summary)
    return DiscoveryRecord(
        query_label=query_label,
        db=db,
        uid=uid,
        accession=accession,
        title=title,
        organism=organism,
        sample_count=sample_count,
        publication_date=publication_date,
        url=url_for_accession(accession, db, uid),
        priority=priority,
        score=score,
        recommended_action=action,
        matched_queries=query_label,
        summary=summary,
    )


def dedupe_records(records: list[DiscoveryRecord]) -> list[DiscoveryRecord]:
    by_key: dict[tuple[str, str], DiscoveryRecord] = {}
    for record in records:
        key = (record.db, record.accession or record.uid)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = record
            continue
        labels = sorted(set(existing.matched_queries.split(";") + record.matched_queries.split(";")))
        existing.matched_queries = ";".join(label for label in labels if label)
        if record.score > existing.score:
            existing.priority = record.priority
            existing.score = record.score
            existing.recommended_action = record.recommended_action
    return sorted(
        by_key.values(),
        key=lambda item: (PRIORITY_RANK.get(item.priority, 9), -item.score, item.db, item.accession),
    )


def discover(
    queries: list[QuerySpec],
    retmax: int,
    email: str | None = None,
    api_key: str | None = None,
    throttle_seconds: float = 0.34,
    continue_on_error: bool = True,
) -> list[DiscoveryRecord]:
    records: list[DiscoveryRecord] = []
    for spec in queries:
        try:
            uids = esearch(spec, retmax=retmax, email=email, api_key=api_key)
        except Exception as error:
            if not continue_on_error:
                raise
            print(f"warning: query failed during esearch: {spec.label}: {error}", file=sys.stderr)
            continue
        time.sleep(throttle_seconds)
        for start in range(0, len(uids), 200):
            chunk = uids[start : start + 200]
            try:
                summaries = esummary(spec.db, chunk, email=email, api_key=api_key)
            except Exception as error:
                if not continue_on_error:
                    raise
                print(
                    f"warning: query failed during esummary: {spec.label} ids={','.join(chunk)}: {error}",
                    file=sys.stderr,
                )
                continue
            for item in summaries:
                records.append(record_from_summary(spec.db, spec.label, item))
            time.sleep(throttle_seconds)
    return dedupe_records(records)


def write_tsv(records: list[DiscoveryRecord], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(asdict(records[0]).keys()) if records else list(DiscoveryRecord.__dataclass_fields__)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))
    return output


def write_json(records: list[DiscoveryRecord], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover public NCBI/GEO/SRA data for SnowLotus-CellFM")
    parser.add_argument("--retmax", type=int, default=50)
    parser.add_argument("--output-tsv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--email", default=os.environ.get("NCBI_EMAIL"))
    parser.add_argument("--api-key", default=os.environ.get("NCBI_API_KEY"))
    parser.add_argument("--throttle-seconds", type=float, default=0.34)
    parser.add_argument("--strict", action="store_true", help="Fail the run if any NCBI query fails")
    args = parser.parse_args()

    records = discover(
        DEFAULT_QUERIES,
        retmax=args.retmax,
        email=args.email,
        api_key=args.api_key,
        throttle_seconds=args.throttle_seconds,
        continue_on_error=not args.strict,
    )
    write_tsv(records, Path(args.output_tsv))
    write_json(records, Path(args.output_json))
    print(f"discovered_records={len(records)}")
    for record in records[:20]:
        print(f"{record.priority}\t{record.score}\t{record.db}\t{record.accession}\t{record.title}")


if __name__ == "__main__":
    main()
