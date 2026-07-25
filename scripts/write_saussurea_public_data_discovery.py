from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "SnowLotus-CellFM Saussurea public data discovery/0.1"
DATABASES = ["sra", "bioproject", "gds", "pubmed", "pmc"]
PRIMARY_DATA_DBS = {"sra", "bioproject", "gds"}
LOW_CONFIDENCE_COUNT_THRESHOLD = 1000
QUERIES = [
    '"Saussurea involucrata" AND ("single cell" OR single-cell OR scRNA OR snRNA OR "single nucleus" OR "10x")',
    '"Saussurea involucrata" AND ("cell atlas" OR "cell type" OR transcriptome OR RNA-seq OR "RNA sequencing")',
    '"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)',
    '"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)',
    '"Saussurea" AND ("single cell" OR single-cell OR scRNA OR snRNA OR "single nucleus" OR "10x")',
]
MANUAL_LITERATURE_REPORTS = [
    {
        "id": "saussurea_multicellular_spheroid_single_cell_report",
        "title": (
            "Sustainable Cultivation of Rare and Endangered Medicinal Plant "
            "Multicellular Spheroids Producing Bioactive Therapeutics for "
            "Alcohol-Related Liver Disease Therapy"
        ),
        "species": "Saussurea involucrata",
        "doi": "10.1002/adhm.202504623",
        "pmid": "41668397",
        "source_url": "https://advanced.onlinelibrary.wiley.com/doi/10.1002/adhm.202504623",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/41668397/",
        "evidence_type": "reported single-cell transcriptomics in multicellular spheroids",
        "reported_cell_clusters": 9,
        "public_matrix_found": False,
        "data_availability": (
            "Data are available from the corresponding author upon reasonable request; "
            "specific cultivation parameters require an NDA according to the publisher page."
        ),
        "use_in_project": (
            "Use as literature evidence and a data-request target only; do not train or benchmark "
            "SnowLotus-CellFM on this study until a reusable matrix is obtained."
        ),
    }
]
SINGLE_CELL_RE = re.compile(
    r"(single[- ]cell|single nucleus|single-nucleus|scrna|snrna|10x|cell atlas|cell type|单细胞|单核)",
    re.IGNORECASE,
)
SAUSSUREA_INVOLUCRATA_RE = re.compile(
    r"(saussurea\s+involucrata|snow lotus|天山雪莲|雪莲)",
    re.IGNORECASE,
)
XML_TITLE_RE = re.compile(r"<(?:Title|TITLE|Study_Title|STUDY_TITLE)>(.*?)</", re.IGNORECASE | re.DOTALL)
XML_ACC_RE = re.compile(r"\bacc=\"([A-Z]+[A-Z0-9]*\d+)\"")


@dataclass
class NcbiHit:
    db: str
    query: str
    uid: str
    title: str
    source: str
    accession: str
    url: str
    single_cell_terms: bool
    saussurea_involucrata_terms: bool


def ncbi_get(
    path: str,
    params: dict[str, str | int],
    timeout: int = 30,
    attempts: int = 4,
    retry_sleep_seconds: float = 2.0,
) -> Any:
    query = urllib.parse.urlencode(params)
    url = f"{EUTILS}/{path}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(retry_sleep_seconds * attempt)
    raise RuntimeError(f"NCBI request failed after {attempts} attempts: {url}") from last_error


def esearch(db: str, term: str, retmax: int) -> dict[str, Any]:
    return ncbi_get(
        "esearch.fcgi",
        {
            "db": db,
            "term": term,
            "retmode": "json",
            "retmax": retmax,
            "sort": "relevance",
        },
    )


def esummary(db: str, ids: list[str]) -> dict[str, Any]:
    if not ids:
        return {"result": {"uids": []}}
    return ncbi_get(
        "esummary.fcgi",
        {
            "db": db,
            "id": ",".join(ids),
            "retmode": "json",
        },
    )


def flatten_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for child in value.values():
            values.extend(flatten_values(child))
        return values
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(flatten_values(child))
        return values
    if value is None:
        return []
    return [str(value)]


def strip_xml(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)


def xml_title(value: str) -> str:
    match = XML_TITLE_RE.search(value)
    if not match:
        return ""
    return strip_xml(match.group(1)).strip()


def record_text(record: dict[str, Any]) -> str:
    values = []
    for key in [
        "title",
        "caption",
        "summary",
        "description",
        "expname",
        "expxml",
        "runs",
        "bioproject",
        "organism",
        "taxon",
        "source",
    ]:
        value = record.get(key)
        if value:
            values.append(str(value))
    values.extend(flatten_values(record))
    return strip_xml(" ".join(values))


def record_title(record: dict[str, Any]) -> str:
    for key in ["title", "caption", "expname", "project_title"]:
        value = record.get(key)
        if value:
            return str(value)
    for key in ["expxml", "summary", "description"]:
        value = record.get(key)
        if value:
            title = xml_title(str(value))
            if title:
                return title
    return ""


def record_accession(record: dict[str, Any]) -> str:
    for key in ["accession", "caption", "bioproject", "runs", "uid"]:
        value = record.get(key)
        if value:
            text = str(value)
            match = XML_ACC_RE.search(text)
            return match.group(1) if match else text
    return ""


def ncbi_url(db: str, uid: str, accession: str) -> str:
    token = accession.split()[0] if accession else uid
    if db == "sra":
        return f"https://www.ncbi.nlm.nih.gov/sra/{urllib.parse.quote(token)}"
    if db == "bioproject":
        return f"https://www.ncbi.nlm.nih.gov/bioproject/{urllib.parse.quote(token)}"
    if db == "gds":
        return f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={urllib.parse.quote(token)}"
    if db == "pubmed":
        return f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
    if db == "pmc":
        return f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{uid}/"
    return f"https://www.ncbi.nlm.nih.gov/{db}/{uid}"


def query_has_chinese_terms(query: str) -> bool:
    return any(term in query for term in ["天山雪莲", "雪莲", "单细胞", "单核", "转录组"])


def query_quality(query: str, count: int) -> dict[str, Any]:
    if query_has_chinese_terms(query) and count >= LOW_CONFIDENCE_COUNT_THRESHOLD:
        return {
            "reliability": "low_confidence_ncbi_tokenization_noise",
            "usable_for_primary_absence": False,
            "note": (
                "NCBI returned an implausibly broad count for a Chinese-language query; "
                "treat this search as a sanity check only, not as accession-level evidence."
            ),
        }
    if '"Saussurea involucrata"' not in query and count >= LOW_CONFIDENCE_COUNT_THRESHOLD:
        return {
            "reliability": "low_confidence_broad_query",
            "usable_for_primary_absence": False,
            "note": "Broad query returned too many hits for primary-data absence claims.",
        }
    return {
        "reliability": "high_confidence_accession_query",
        "usable_for_primary_absence": True,
        "note": "",
    }


def parse_hits(db: str, query: str, summary: dict[str, Any]) -> list[NcbiHit]:
    result = summary.get("result", {})
    hits: list[NcbiHit] = []
    for uid in result.get("uids", []):
        record = result.get(uid, {})
        text = record_text(record)
        title = record_title(record)
        accession = record_accession(record)
        hits.append(
            NcbiHit(
                db=db,
                query=query,
                uid=uid,
                title=title,
                source=str(record.get("source") or record.get("fulljournalname") or ""),
                accession=accession,
                url=ncbi_url(db, uid, accession),
                single_cell_terms=bool(SINGLE_CELL_RE.search(text)),
                saussurea_involucrata_terms=bool(SAUSSUREA_INVOLUCRATA_RE.search(text)),
            )
        )
    return hits


def deduplicate_hits(hits: list[NcbiHit]) -> list[NcbiHit]:
    seen: set[tuple[str, str]] = set()
    unique: list[NcbiHit] = []
    for hit in hits:
        key = (hit.db, hit.uid)
        if key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique


def run_query(db: str, query: str, retmax: int) -> tuple[dict[str, Any], list[NcbiHit]]:
    search = esearch(db, query, retmax)
    ids = search.get("esearchresult", {}).get("idlist", [])
    count = int(search.get("esearchresult", {}).get("count", "0"))
    summary = esummary(db, ids)
    parsed = parse_hits(db, query, summary)
    return {"db": db, "query": query, "count": count, "ids": ids, **query_quality(query, count)}, parsed


def build_discovery(retmax: int = 20, recovery_rounds: int = 2) -> dict[str, Any]:
    searches = []
    hits: list[NcbiHit] = []
    errors = []
    pending = [(db, query) for db in DATABASES for query in QUERIES]
    for round_index in range(recovery_rounds + 1):
        next_pending = []
        for db, query in pending:
            try:
                search_info, parsed = run_query(db, query, retmax)
                hits.extend(parsed)
                searches.append(search_info)
            except Exception as exc:  # pragma: no cover - network errors are environment-specific
                if round_index < recovery_rounds:
                    next_pending.append((db, query))
                else:
                    errors.append({"db": db, "query": query, "error": f"{type(exc).__name__}: {exc}"})
            finally:
                time.sleep(0.34)
        pending = next_pending
        if not pending:
            break
    unique_hits = deduplicate_hits(hits)
    primary_single_cell_hits = [
        hit
        for hit in unique_hits
        if hit.saussurea_involucrata_terms and hit.single_cell_terms and hit.db in PRIMARY_DATA_DBS
    ]
    low_confidence_searches = [
        search for search in searches if not search.get("usable_for_primary_absence", True)
    ]
    manual_public_matrices = [
        report for report in MANUAL_LITERATURE_REPORTS if report.get("public_matrix_found")
    ]
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "database_count": len(DATABASES),
            "query_count": len(DATABASES) * len(QUERIES),
            "high_confidence_query_count": len(searches) - len(low_confidence_searches),
            "low_confidence_query_count": len(low_confidence_searches),
            "unique_hit_count": len(unique_hits),
            "primary_saussurea_involucrata_single_cell_hit_count": len(primary_single_cell_hits),
            "snow_lotus_primary_scrna_publicly_found": bool(primary_single_cell_hits),
            "single_cell_literature_report_count": len(MANUAL_LITERATURE_REPORTS),
            "public_downloadable_saussurea_single_cell_matrix_found": bool(
                primary_single_cell_hits or manual_public_matrices
            ),
            "recovery_rounds": recovery_rounds,
            "error_count": len(errors),
        },
        "searches": searches,
        "low_confidence_searches": low_confidence_searches,
        "errors": errors,
        "hits": [hit.__dict__ for hit in unique_hits],
        "primary_saussurea_involucrata_single_cell_hits": [
            hit.__dict__ for hit in primary_single_cell_hits
        ],
        "manual_literature_reports": MANUAL_LITERATURE_REPORTS,
        "interpretation": (
            "This automated NCBI pass searches SRA, BioProject, GEO DataSets, PubMed, "
            "and PMC for Saussurea/Saussurea involucrata single-cell evidence. It also "
            "tracks a 2026 Advanced Healthcare Materials report of single-cell "
            "transcriptomics in Saussurea involucrata multicellular spheroids. A zero "
            "primary-data hit count plus no public manual matrix means the project should "
            "not claim a reusable public Snow Lotus single-cell atlas or train on it yet; "
            "genome, bulk transcriptome, literature, and close-genus evidence remain "
            "supporting data only."
        ),
    }


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Saussurea Public Data Discovery",
        "",
        f"- Databases searched: `{summary['database_count']}`",
        f"- Query executions: `{summary['query_count']}`",
        f"- Unique hits: `{summary['unique_hit_count']}`",
        (
            "- Primary `Saussurea involucrata` single-cell hits: "
            f"`{summary['primary_saussurea_involucrata_single_cell_hit_count']}`"
        ),
        (
            "- Public Snow Lotus scRNA/snRNA found: "
            f"`{summary['snow_lotus_primary_scrna_publicly_found']}`"
        ),
        (
            "- Literature reports of Snow Lotus single-cell transcriptomics: "
            f"`{summary['single_cell_literature_report_count']}`"
        ),
        (
            "- Public downloadable Snow Lotus single-cell matrix found: "
            f"`{summary['public_downloadable_saussurea_single_cell_matrix_found']}`"
        ),
        f"- Low-confidence/noisy query executions: `{summary['low_confidence_query_count']}`",
        f"- Query errors: `{summary['error_count']}`",
        "",
        payload["interpretation"],
        "",
        "## Manual Literature Reports",
        "",
        "| ID | Evidence | DOI/PMID | Public matrix | Data availability | Use |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for report in payload["manual_literature_reports"]:
        lines.append(
            "| {id} | {evidence} | {doi} / PMID:{pmid} | {matrix} | {availability} | {use} |".format(
                id=report["id"],
                evidence=report["evidence_type"],
                doi=report["doi"],
                pmid=report["pmid"],
                matrix=report["public_matrix_found"],
                availability=report["data_availability"].replace("|", "/"),
                use=report["use_in_project"].replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Low-Confidence Query Guard",
            "",
        ]
    )
    noisy = payload.get("low_confidence_searches", [])
    if noisy:
        lines.extend(
            f"- `{item['db']}` `{item['query']}` count=`{item['count']}`: {item['note']}"
            for item in noisy
        )
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
        "## Primary Single-Cell Hits",
        "",
        ]
    )
    primary = payload["primary_saussurea_involucrata_single_cell_hits"]
    if primary:
        lines.extend(
            f"- `{hit['db']}` `{hit['accession'] or hit['uid']}`: {hit['title']} ({hit['url']})"
            for hit in primary
        )
    else:
        lines.append("- None detected in this pass.")
    lines.extend(["", "## All Hits", "", "| DB | Accession/UID | Single-cell terms | Snow Lotus terms | Title | URL |", "| --- | --- | --- | --- | --- | --- |"])
    for hit in payload["hits"][:80]:
        title = str(hit["title"]).replace("|", "/")[:180]
        lines.append(
            "| {db} | `{acc}` | {single} | {snow} | {title} | {url} |".format(
                db=hit["db"],
                acc=hit["accession"] or hit["uid"],
                single=hit["single_cell_terms"],
                snow=hit["saussurea_involucrata_terms"],
                title=title,
                url=hit["url"],
            )
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Search public NCBI resources for Saussurea single-cell data.")
    parser.add_argument("--retmax", default=20, type=int)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    payload = build_discovery(retmax=args.retmax)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
