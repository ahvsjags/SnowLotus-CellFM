from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GSE_RE = re.compile(r"\bGSE\d+\b", re.IGNORECASE)
PLANT_RE = re.compile(
    r"\b("
    r"arabidopsis|oryza|rice|zea|maize|triticum|wheat|solanum|tomato|camellia|"
    r"medicago|populus|glycine|soybean|gossypium|cotton|sorghum|hordeum|barley|"
    r"setaria|cucumis|liriodendron|eucalyptus|legume|legumes|brassicaceae|brassica|"
    r"plant|plants|root|leaf|leaves|flower|stem|xylem|embryonic leaves"
    r")\b",
    re.IGNORECASE,
)
NON_PLANT_RE = re.compile(
    r"\b("
    r"homo sapiens|mus musculus|bombyx|helicoverpa|drosophila|danio rerio|"
    r"rattus norvegicus|caenorhabditis|apostichopus japonicus|sea cucumber|"
    r"mouse|human|silkworm"
    r")\b",
    re.IGNORECASE,
)
REGULATORY_ONLY_RE = re.compile(
    r"\b("
    r"atac|snatac|scatac|chip-seq|chipseq|cut&run|cutandrun|dap-seq|dapseq|"
    r"methylc-seq|methylc|methylation|methylcytosine|bisulfite|wgbs"
    r")\b",
    re.IGNORECASE,
)
RNA_EXPRESSION_RE = re.compile(
    r"\b("
    r"rna|rna-seq|rnaseq|scrna|snrna|transcriptome|transcriptomic|expression|"
    r"gene expression|filtered_feature_bc_matrix|matrix.mtx"
    r")\b",
    re.IGNORECASE,
)


@dataclass
class PromotionCandidate:
    accession: str
    discovered_dataset_id: str
    suggested_dataset_id: str
    organism: str
    title: str
    priority: str
    score: int
    matrix_file_count: int
    file_type_counts: str
    promotion_status: str
    reason: str
    recommended_downloader: str
    source_url: str
    geo_page_url: str


def read_tsv(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def latest_file(root: Path, pattern: str) -> Path | None:
    files = [path for path in root.glob(pattern) if path.is_file()]
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def extract_gse(value: str) -> str:
    match = GSE_RE.search(value or "")
    return match.group(0).upper() if match else ""


def manifest_gse_accessions(root: Path) -> set[str]:
    accessions: set[str] = set()
    for row in read_tsv(root / "data" / "public_dataset_manifest.tsv"):
        accession = extract_gse(f"{row.get('accession_or_doi', '')} {row.get('source_url', '')}")
        if accession:
            accessions.add(accession)
    return accessions


def int_value(value: str | None) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def is_truthy(value: str | None) -> bool:
    return str(value or "").lower() in {"true", "1", "yes", "y"}


def compact_slug(text: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    stop = {"of", "and", "the", "in", "for", "by", "via", "with", "from", "during"}
    useful = [token for token in tokens if token not in stop]
    return "_".join(useful[:7]) or "public_geo_candidate"


def suggested_dataset_id(accession: str, organism: str, title: str) -> str:
    organism_hint = compact_slug(organism).split("_")[:2]
    title_hint = compact_slug(title).split("_")[:5]
    parts = ["geo", accession.lower(), *organism_hint, *title_hint]
    return "_".join(part for part in parts if part)[:96]


def recommended_downloader(file_type_counts: str) -> str:
    if "h5ad:" in file_type_counts:
        return "manual_h5ad_download_then_obs_var_audit"
    if "tenx_h5:" in file_type_counts:
        return "download_geo_raw_tar_h5_subset.sh"
    if "mtx_archive:" in file_type_counts or "mtx_component:" in file_type_counts:
        return "download_geo_raw_tar_mtx_subset.sh"
    if "seurat_rds:" in file_type_counts:
        return "download_geo_rds_subset.sh"
    return "manual_review"


def classify_candidate(row: dict[str, str], discovery: dict[str, str]) -> tuple[str, str]:
    organism = discovery.get("organism", "")
    organism_plant_like = bool(PLANT_RE.search(organism))
    organism_non_plant_like = bool(NON_PLANT_RE.search(organism))
    if organism_non_plant_like and not organism_plant_like:
        return "HOLD_NON_PLANT", "Organism terms indicate a non-plant dataset."

    text = " ".join(
        [
            organism,
            discovery.get("title", ""),
            discovery.get("summary", ""),
            row.get("file_type_counts", ""),
        ]
    )
    title_summary = " ".join([discovery.get("title", ""), discovery.get("summary", "")])
    if REGULATORY_ONLY_RE.search(discovery.get("title", "")):
        return (
            "HOLD_REGULATORY_ONLY",
            "Title indicates ATAC, methylation, DAP-seq, or another regulatory-only modality rather than RNA expression.",
        )
    plant_like = bool(PLANT_RE.search(text))
    non_plant_like = bool(NON_PLANT_RE.search(text))
    matrix_count = int_value(row.get("matrix_file_count"))
    if matrix_count == 0 or not is_truthy(row.get("download_ready")):
        return "HOLD_NO_MATRIX", "No download-ready expression-like supplementary matrix was detected."
    if non_plant_like and not plant_like:
        return "HOLD_NON_PLANT", "Organism/title terms indicate a non-plant dataset."
    if non_plant_like and plant_like:
        return "MANUAL_REVIEW_MIXED_ORGANISM", "Plant and non-plant organism terms both appear; inspect before corpus use."
    if REGULATORY_ONLY_RE.search(title_summary) and not RNA_EXPRESSION_RE.search(title_summary):
        return (
            "HOLD_REGULATORY_ONLY",
            "Title/summary indicate ATAC, methylation, DAP-seq, or another regulatory-only modality rather than RNA expression.",
        )
    if not plant_like:
        return "MANUAL_REVIEW_AMBIGUOUS_ORGANISM", "Plant terms were not strong enough for automatic promotion."
    return "PROMOTE_DOWNLOAD_CANDIDATE", "Plant-like GEO record with download-ready supplementary matrix files."


def build_candidates(project_dir: Path) -> dict[str, Any]:
    discovery_dir = project_dir / "data" / "public_discovery"
    discovery_path = latest_file(discovery_dir, "ncbi_discovery_*.tsv")
    geo_review_path = latest_file(discovery_dir, "geo_supplementary_review_*.tsv")
    discovery_rows = {row.get("accession", "").upper(): row for row in read_tsv(discovery_path)}
    known = manifest_gse_accessions(project_dir)
    candidates: list[PromotionCandidate] = []
    for row in read_tsv(geo_review_path):
        accession = (row.get("accession") or "").upper()
        if not accession or accession in known:
            continue
        if row.get("status") != "ncbi_discovery_candidate":
            continue
        if not is_truthy(row.get("download_ready")):
            continue
        discovery = discovery_rows.get(accession, {})
        status, reason = classify_candidate(row, discovery)
        candidates.append(
            PromotionCandidate(
                accession=accession,
                discovered_dataset_id=row.get("dataset_id", ""),
                suggested_dataset_id=suggested_dataset_id(
                    accession,
                    discovery.get("organism", ""),
                    discovery.get("title", ""),
                ),
                organism=discovery.get("organism", ""),
                title=discovery.get("title", ""),
                priority=discovery.get("priority", row.get("priority", "")),
                score=int_value(discovery.get("score")),
                matrix_file_count=int_value(row.get("matrix_file_count")),
                file_type_counts=row.get("file_type_counts", ""),
                promotion_status=status,
                reason=reason,
                recommended_downloader=recommended_downloader(row.get("file_type_counts", "")),
                source_url=discovery.get("url", row.get("source_url", "")),
                geo_page_url=row.get("page_url", ""),
            )
        )
    candidates.sort(
        key=lambda item: (
            {
                "PROMOTE_DOWNLOAD_CANDIDATE": 0,
                "MANUAL_REVIEW_MIXED_ORGANISM": 1,
                "MANUAL_REVIEW_AMBIGUOUS_ORGANISM": 2,
                "HOLD_NON_PLANT": 3,
                "HOLD_NO_MATRIX": 4,
            }.get(item.promotion_status, 9),
            -item.score,
            -item.matrix_file_count,
            item.accession,
        )
    )
    rows = [asdict(candidate) for candidate in candidates]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "latest_ncbi_discovery": discovery_path.as_posix() if discovery_path else None,
        "latest_geo_review": geo_review_path.as_posix() if geo_review_path else None,
        "candidate_count": len(rows),
        "promote_download_candidate_count": sum(
            row["promotion_status"] == "PROMOTE_DOWNLOAD_CANDIDATE" for row in rows
        ),
        "manual_review_count": sum(row["promotion_status"].startswith("MANUAL_REVIEW") for row in rows),
        "hold_non_plant_count": sum(row["promotion_status"] == "HOLD_NON_PLANT" for row in rows),
    }
    return {"summary": summary, "candidates": rows}


def write_tsv(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["candidates"]
    fields = list(asdict(PromotionCandidate("", "", "", "", "", "", 0, 0, "", "", "", "", "", "")).keys())
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(output)
    return output


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# GEO Manifest Promotion Candidates",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        f"- Candidates: `{summary['candidate_count']}`",
        f"- Promote/download candidates: `{summary['promote_download_candidate_count']}`",
        f"- Manual-review candidates: `{summary['manual_review_count']}`",
        f"- Non-plant holds: `{summary['hold_non_plant_count']}`",
        "",
        "## Candidates",
        "",
        "| Status | Accession | Suggested dataset | Organism | Matrices | Files | Downloader | Title | Reason |",
        "| --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in payload["candidates"]:
        lines.append(
            "| {status} | {accession} | {dataset} | {organism} | {matrices} | {files} | {downloader} | {title} | {reason} |".format(
                status=row["promotion_status"],
                accession=row["accession"],
                dataset=row["suggested_dataset_id"],
                organism=(row["organism"] or "").replace("|", "/")[:80],
                matrices=row["matrix_file_count"],
                files=(row["file_type_counts"] or "").replace("|", "/"),
                downloader=row["recommended_downloader"],
                title=(row["title"] or "").replace("|", "/")[:100],
                reason=(row["reason"] or "").replace("|", "/"),
            )
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank unknown GEO-ready candidates for safe manifest promotion.")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-tsv", required=True, type=Path)
    args = parser.parse_args()
    payload = build_candidates(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    write_tsv(payload, args.output_tsv)


if __name__ == "__main__":
    main()
