from __future__ import annotations

import argparse
import csv
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Any


USER_AGENT = "SnowLotus-CellFM/0.1 geo-supplementary-review"
GSE_RE = re.compile(r"\bGSE\d+\b", re.IGNORECASE)
SUPPLEMENT_RE = re.compile(
    r"\b(?:GSM\d+|GSE\d+)_[A-Za-z0-9_.%+\-()]+"
    r"(?:\.h5ad(?:\.gz)?|\.h5(?:\.gz)?|\.rds(?:\.gz)?|\.tar(?:\.gz)?|"
    r"\.tgz|\.mtx(?:\.gz)?|\.tsv(?:\.gz)?|\.csv(?:\.gz)?)\b",
    re.IGNORECASE,
)


@dataclass
class GeoFile:
    url: str
    filename: str
    file_type: str


@dataclass
class GeoReview:
    dataset_id: str
    species: str
    tissue_or_scope: str
    priority: str
    status: str
    accession: str
    source_url: str
    page_url: str
    fetch_status: str
    file_count: int
    file_type_counts: str
    matrix_file_count: int
    candidate_files: str
    recommended_action: str
    download_ready: bool
    error: str


@dataclass
class GeoFileReview:
    dataset_id: str
    accession: str
    species: str
    tissue_or_scope: str
    priority: str
    status: str
    filename: str
    file_type: str
    url: str
    matrix_like: bool


def geo_sample_url(filename: str) -> str:
    sample_accession = filename.split("_", 1)[0]
    sample_bucket = f"{sample_accession[:-3]}nnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/samples/{sample_bucket}/{sample_accession}/suppl/{filename}"


def geo_series_download_url(accession: str, filename: str) -> str:
    return (
        "https://www.ncbi.nlm.nih.gov/geo/download/"
        f"?acc={accession.upper()}&format=file&file={urllib.parse.quote(filename)}"
    )


def fetch_text(url: str, attempts: int = 4, sleep_seconds: float = 3.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            if attempt == attempts:
                break
            time.sleep(sleep_seconds * attempt)
    raise RuntimeError(f"failed to fetch {url}") from last_error


def normalize_href(accession: str, href: str) -> tuple[str, str] | None:
    href = html.unescape(urllib.parse.unquote(href))
    parsed = urllib.parse.urlparse(href)
    query = urllib.parse.parse_qs(parsed.query)
    file_param = query.get("file", [""])[0]
    filename = Path(file_param or parsed.path).name
    if not filename:
        return None
    if href.startswith("//"):
        url = "https:" + href
    elif href.startswith("/"):
        url = "https://www.ncbi.nlm.nih.gov" + href
    elif href.startswith("ftp://ftp.ncbi.nlm.nih.gov/"):
        url = "https://" + href.removeprefix("ftp://")
    elif href.startswith(("http://", "https://")):
        url = href
    elif filename.startswith("GSM"):
        url = geo_sample_url(filename)
    elif filename.upper().startswith(accession.upper()):
        url = geo_series_download_url(accession, filename)
    else:
        return None
    return url, filename


def classify_file(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith((".h5ad", ".h5ad.gz")):
        return "h5ad"
    if lower.endswith((".rds", ".rds.gz")):
        return "seurat_rds"
    if lower.endswith((".h5", ".h5.gz")):
        return "tenx_h5"
    if lower.endswith((".mtx", ".mtx.gz")):
        return "mtx_component"
    if lower.endswith((".tar", ".tar.gz", ".tgz")):
        if any(token in lower for token in ["matrix", "mtx", "barcodes", "features", "raw"]):
            return "mtx_archive"
        return "archive"
    if lower.endswith((".tsv", ".tsv.gz", ".csv", ".csv.gz")):
        return "metadata_table"
    return "other"


def is_matrix_type(file_type: str) -> bool:
    return file_type in {"h5ad", "seurat_rds", "tenx_h5", "mtx_component", "mtx_archive"}


def appears_atac_only(files: list[GeoFile]) -> bool:
    if not files:
        return False
    filenames = " ".join(file.filename.lower() for file in files)
    has_atac = any(token in filenames for token in ["atac", "snatac", "scatac"])
    has_rna = any(
        token in filenames
        for token in [
            "rna",
            "snrna",
            "scrna",
            "expression",
            "filtered_feature_bc_matrix",
            "gene_expression",
        ]
    )
    return has_atac and not has_rna


def recommended_action(files: list[GeoFile]) -> tuple[str, bool]:
    type_counts = Counter(file.file_type for file in files)
    if appears_atac_only(files):
        return (
            "h5ad/MTX files appear ATAC-only; keep as regulatory evidence and do not add to expression corpus until an RNA layer is verified",
            False,
        )
    if type_counts["h5ad"]:
        return "download h5ad; inspect obs/var fields; add direct AnnData corpus manifest", True
    if type_counts["tenx_h5"]:
        return "download 10x H5 subset; convert with tenx_h5_to_npz.py; add corpus manifest", True
    if type_counts["mtx_archive"] or type_counts["mtx_component"]:
        return "download MTX/10x archive; convert with geo_mtx_tar_to_npz.py or geo_10x_to_npz.py", True
    if type_counts["seurat_rds"]:
        return "download Seurat RDS; export with export_seurat_rds_to_mtx.R; build NPZ manifest", True
    if files:
        return "supplementary files found but no obvious matrix; inspect manually before training use", False
    return "no supplementary matrix files found on GEO page; keep as metadata-only or inspect SRA", False


def discover_geo_files(
    accession: str,
    fetcher: Callable[[str], str] = fetch_text,
) -> tuple[str, list[GeoFile], str]:
    accession = accession.upper()
    page_url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"
    try:
        text = fetcher(page_url)
    except Exception as error:
        return page_url, [], str(error)

    seen: set[str] = set()
    files: list[GeoFile] = []
    for href in re.findall(r"href=['\"]([^'\"]+)['\"]", text):
        normalized = normalize_href(accession, href)
        if normalized is None:
            continue
        url, filename = normalized
        if not SUPPLEMENT_RE.search(filename):
            continue
        if filename in seen:
            continue
        seen.add(filename)
        files.append(GeoFile(url=url, filename=filename, file_type=classify_file(filename)))

    decoded = html.unescape(urllib.parse.unquote(text))
    for filename in SUPPLEMENT_RE.findall(decoded):
        if filename in seen:
            continue
        seen.add(filename)
        if filename.startswith("GSM"):
            url = geo_sample_url(filename)
        else:
            url = geo_series_download_url(accession, filename)
        files.append(GeoFile(url=url, filename=filename, file_type=classify_file(filename)))

    return page_url, sorted(files, key=lambda item: item.filename), ""


def extract_gse_accession(value: str) -> str:
    match = GSE_RE.search(value or "")
    return match.group(0).upper() if match else ""


def read_manifest(path: Path, statuses: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    candidates = []
    for row in rows:
        accession = extract_gse_accession(row.get("accession_or_doi", ""))
        if not accession:
            continue
        if statuses and row.get("status", "") not in statuses:
            continue
        item = dict(row)
        item["gse_accession"] = accession
        candidates.append(item)
    return candidates


def read_tsv(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def manifest_gse_accessions(manifest: Path) -> set[str]:
    accessions: set[str] = set()
    for row in read_tsv(manifest):
        accession = extract_gse_accession(
            f"{row.get('accession_or_doi', '')} {row.get('source_url', '')}"
        )
        if accession:
            accessions.add(accession)
    return accessions


def priority_rank(priority: str) -> int:
    return {"S": 0, "A": 1, "B": 2}.get(priority.upper(), 9)


def discovery_gse_candidates(
    discovery_tsv: Path | None,
    known_accessions: set[str],
    priorities: set[str],
    max_candidates: int,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for row in read_tsv(discovery_tsv):
        accession = extract_gse_accession(f"{row.get('accession', '')} {row.get('url', '')}")
        if not accession or accession in known_accessions:
            continue
        priority = (row.get("priority") or "").upper()
        if priorities and priority not in priorities:
            continue
        action = row.get("recommended_action", "")
        if "out-of-scope" in action.lower():
            continue
        try:
            score = int(float(row.get("score") or 0))
        except ValueError:
            score = 0
        candidates.append(
            {
                "dataset_id": f"discovered_{accession.lower()}",
                "species": row.get("organism", ""),
                "tissue_or_scope": "public discovery candidate",
                "data_type": row.get("data_type", "") or row.get("matched_queries", ""),
                "priority": priority,
                "accession_or_doi": accession,
                "source_url": row.get("url", ""),
                "why_use": action,
                "status": "ncbi_discovery_candidate",
                "gse_accession": accession,
                "score": str(score),
            }
        )
    return sorted(
        candidates,
        key=lambda item: (priority_rank(item.get("priority", "")), -int(item.get("score") or 0), item["gse_accession"]),
    )[:max_candidates]


def review_one(
    row: dict[str, str],
    fetcher: Callable[[str], str] = fetch_text,
) -> GeoReview:
    review, _ = review_one_with_files(row, fetcher=fetcher)
    return review


def review_one_with_files(
    row: dict[str, str],
    fetcher: Callable[[str], str] = fetch_text,
) -> tuple[GeoReview, list[GeoFileReview]]:
    accession = row["gse_accession"]
    page_url, files, error = discover_geo_files(accession, fetcher=fetcher)
    type_counts = Counter(file.file_type for file in files)
    action, ready = recommended_action(files)
    candidate_files = ";".join(file.filename for file in files[:12])
    matrix_file_count = sum(1 for file in files if is_matrix_type(file.file_type))
    review = GeoReview(
        dataset_id=row.get("dataset_id", ""),
        species=row.get("species", ""),
        tissue_or_scope=row.get("tissue_or_scope", ""),
        priority=row.get("priority", ""),
        status=row.get("status", ""),
        accession=accession,
        source_url=row.get("source_url", ""),
        page_url=page_url,
        fetch_status="failed" if error else "ok",
        file_count=len(files),
        file_type_counts=";".join(f"{key}:{type_counts[key]}" for key in sorted(type_counts)),
        matrix_file_count=matrix_file_count,
        candidate_files=candidate_files,
        recommended_action=action,
        download_ready=ready,
        error=error,
    )
    file_reviews = [
        GeoFileReview(
            dataset_id=row.get("dataset_id", ""),
            accession=accession,
            species=row.get("species", ""),
            tissue_or_scope=row.get("tissue_or_scope", ""),
            priority=row.get("priority", ""),
            status=row.get("status", ""),
            filename=file.filename,
            file_type=file.file_type,
            url=file.url,
            matrix_like=is_matrix_type(file.file_type),
        )
        for file in files
    ]
    return review, file_reviews


def review_manifest(
    manifest: Path,
    statuses: set[str],
    fetcher: Callable[[str], str] = fetch_text,
    throttle_seconds: float = 0.5,
) -> list[GeoReview]:
    reviews, _ = review_manifest_with_files(
        manifest,
        statuses=statuses,
        fetcher=fetcher,
        throttle_seconds=throttle_seconds,
    )
    return reviews


def review_manifest_with_files(
    manifest: Path,
    statuses: set[str],
    fetcher: Callable[[str], str] = fetch_text,
    throttle_seconds: float = 0.5,
    discovery_tsv: Path | None = None,
    discovery_priorities: set[str] | None = None,
    max_discovery_gse: int = 25,
) -> tuple[list[GeoReview], list[GeoFileReview]]:
    reviews: list[GeoReview] = []
    file_reviews: list[GeoFileReview] = []
    rows = read_manifest(manifest, statuses)
    if discovery_tsv is not None:
        rows.extend(
            discovery_gse_candidates(
                discovery_tsv,
                known_accessions=manifest_gse_accessions(manifest),
                priorities=discovery_priorities or {"S", "A"},
                max_candidates=max_discovery_gse,
            )
        )
    for row in rows:
        review, files = review_one_with_files(row, fetcher=fetcher)
        reviews.append(review)
        file_reviews.extend(files)
        time.sleep(throttle_seconds)
    sorted_reviews = sorted(
        reviews,
        key=lambda item: (
            not item.download_ready,
            -item.matrix_file_count,
            item.priority,
            item.accession,
        ),
    )
    sorted_file_reviews = sorted(
        file_reviews,
        key=lambda item: (not item.matrix_like, item.accession, item.file_type, item.filename),
    )
    return sorted_reviews, sorted_file_reviews


def write_tsv(reviews: list[GeoReview], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(GeoReview.__dataclass_fields__)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for review in reviews:
            writer.writerow(asdict(review))
    return output


def write_file_tsv(file_reviews: list[GeoFileReview], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(GeoFileReview.__dataclass_fields__)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for review in file_reviews:
            writer.writerow(asdict(review))
    return output


def write_json(reviews: list[GeoReview], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload: list[dict[str, Any]] = [asdict(review) for review in reviews]
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_file_json(file_reviews: list[GeoFileReview], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload: list[dict[str, Any]] = [asdict(review) for review in file_reviews]
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Review GEO supplementary files for SnowCell public candidates")
    parser.add_argument("--manifest", default="data/public_dataset_manifest.tsv", type=Path)
    parser.add_argument("--status", action="append", default=["discovery_candidate"])
    parser.add_argument("--output-tsv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--file-output-tsv", type=Path)
    parser.add_argument("--file-output-json", type=Path)
    parser.add_argument("--throttle-seconds", type=float, default=0.5)
    parser.add_argument("--discovery-tsv", type=Path)
    parser.add_argument("--discovery-priority", action="append")
    parser.add_argument("--max-discovery-gse", type=int, default=25)
    args = parser.parse_args()

    reviews, file_reviews = review_manifest_with_files(
        args.manifest,
        statuses=set(args.status),
        throttle_seconds=args.throttle_seconds,
        discovery_tsv=args.discovery_tsv,
        discovery_priorities=set(args.discovery_priority or ["S", "A"]),
        max_discovery_gse=args.max_discovery_gse,
    )
    write_tsv(reviews, args.output_tsv)
    write_json(reviews, args.output_json)
    if args.file_output_tsv:
        write_file_tsv(file_reviews, args.file_output_tsv)
    if args.file_output_json:
        write_file_json(file_reviews, args.file_output_json)
    print(f"geo_reviews={len(reviews)}")
    print(f"geo_files={len(file_reviews)}")
    for review in reviews[:20]:
        print(
            "\t".join(
                [
                    review.accession,
                    review.dataset_id,
                    str(review.file_count),
                    str(review.matrix_file_count),
                    review.file_type_counts,
                    review.recommended_action,
                ]
            )
        )


if __name__ == "__main__":
    main()
