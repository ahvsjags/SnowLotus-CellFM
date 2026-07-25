from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_OBS_FIELDS = [
    "cell_id",
    "cell_type",
    "cell_type_coarse",
    "sample_id",
    "species",
    "tissue",
    "batch",
]

REQUESTED_FILES = [
    {
        "name": "processed_anndata",
        "description": "Processed AnnData .h5ad or equivalent sparse matrix with genes by cells.",
        "required": True,
    },
    {
        "name": "raw_or_filtered_matrix",
        "description": "10x H5, MTX+barcodes+features, Loom, or another sparse count matrix export.",
        "required": True,
    },
    {
        "name": "cell_metadata",
        "description": "Per-cell metadata containing labels, sample identifiers, tissue, condition, batch, and QC fields.",
        "required": True,
    },
    {
        "name": "gene_metadata",
        "description": "Gene identifiers, aliases, ortholog hints, and genome annotation version.",
        "required": True,
    },
    {
        "name": "raw_fastq_or_repository_accession",
        "description": "Raw reads or a stable SRA/ENA/GSA/GEO accession for reproducibility.",
        "required": False,
    },
    {
        "name": "protocol_and_license",
        "description": "Library protocol, preprocessing steps, citation terms, data license, and model-training permission.",
        "required": True,
    },
]

VALIDATION_COMMANDS = [
    (
        "python scripts/validate_saussurea_h5ad_contract.py "
        "--input data/saussurea_involucrata.h5ad "
        "--output-md outputs/publication_package/saussurea_h5ad_contract.md "
        "--output-json outputs/publication_package/saussurea_h5ad_contract.json"
    ),
    "bash scripts/generate_publication_package.sh",
    "bash scripts/top_journal_pipeline.sh",
]


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def manual_request_candidates(discovery: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for report in discovery.get("manual_literature_reports", []):
        if report.get("public_matrix_found"):
            continue
        if "saussurea" not in str(report.get("species", "")).lower():
            continue
        candidates.append(
            {
                "dataset_id": report.get("id") or "manual_literature_report",
                "title": report.get("title", ""),
                "species": report.get("species", ""),
                "evidence_type": report.get("evidence_type", ""),
                "doi": report.get("doi", ""),
                "pmid": report.get("pmid", ""),
                "source_url": report.get("source_url", ""),
                "pubmed_url": report.get("pubmed_url", ""),
                "data_availability": report.get("data_availability", ""),
                "reason_to_request": report.get("use_in_project", ""),
                "public_matrix_found": False,
            }
        )
    return candidates


def supporting_request_candidates(supporting: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for row in supporting:
        if row.get("status") != "literature_request_candidate":
            continue
        candidates.append(
            {
                "dataset_id": row.get("dataset_id", ""),
                "title": "",
                "species": row.get("species", ""),
                "evidence_type": row.get("data_type", ""),
                "doi": row.get("accession_or_doi", ""),
                "pmid": "",
                "source_url": row.get("source_url", ""),
                "pubmed_url": "",
                "data_availability": "Request-only or not directly downloadable from the public package.",
                "reason_to_request": row.get("role", ""),
                "public_matrix_found": False,
            }
        )
    return candidates


def merge_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        key = str(candidate.get("dataset_id") or candidate.get("doi") or candidate.get("source_url"))
        if key in merged:
            for field, value in candidate.items():
                if value and not merged[key].get(field):
                    merged[key][field] = value
        else:
            merged[key] = dict(candidate)
    return sorted(merged.values(), key=lambda item: str(item.get("dataset_id") or ""))


def build_email_template(candidates: list[dict[str, Any]]) -> str:
    primary = candidates[0] if candidates else {}
    title = primary.get("title") or "your Saussurea involucrata single-cell transcriptomics study"
    doi = primary.get("doi") or "the publication DOI"
    return "\n".join(
        [
            "Subject: Request for Saussurea involucrata single-cell transcriptomics data",
            "",
            "Dear Professor / Corresponding Author,",
            "",
            (
                "I am developing SnowLotus-CellFM, a plant single-cell foundation model "
                "for cross-species cell-type annotation and Snow Lotus transfer analysis. "
                f"Your study, \"{title}\" ({doi}), is directly relevant because it reports "
                "Saussurea involucrata single-cell transcriptomics."
            ),
            "",
            "Could you share, under your preferred data-use terms, the reusable single-cell data needed for reproducible analysis?",
            "",
            "Requested materials:",
            "- processed AnnData .h5ad or equivalent sparse matrix;",
            "- raw or filtered count matrix files;",
            "- per-cell metadata with cell type, sample, tissue, condition, batch, and QC fields;",
            "- gene metadata and genome annotation version;",
            "- raw FASTQ files or a repository accession if available;",
            "- citation, license, and model-training/benchmarking permission terms.",
            "",
            (
                "We will validate the files with an auditable h5ad contract, cite the study, "
                "and keep claims limited to the permissions and evidence available."
            ),
            "",
            "Best regards,",
            "SnowLotus-CellFM project team",
        ]
    )


def build_payload(project_dir: Path) -> dict[str, Any]:
    package_dir = project_dir / "outputs" / "publication_package"
    discovery = read_json(package_dir / "saussurea_public_data_discovery.json") or {}
    supporting = read_json(package_dir / "saussurea_supporting_evidence.json") or []
    contract = read_json(package_dir / "saussurea_h5ad_contract.json") or {}
    if not isinstance(supporting, list):
        supporting = []
    candidates = merge_candidates(
        manual_request_candidates(discovery) + supporting_request_candidates(supporting)
    )
    public_matrix_found = bool(
        (discovery.get("summary") or {}).get("public_downloadable_saussurea_single_cell_matrix_found")
    )
    contract_ready = bool(
        contract.get("contract_ready")
        or (contract.get("summary") or {}).get("contract_ready")
    )
    email_template = build_email_template(candidates)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "request_candidate_count": len(candidates),
            "package_ready": bool(candidates) and not public_matrix_found,
            "public_downloadable_matrix_found": public_matrix_found,
            "saussurea_h5ad_contract_ready": contract_ready,
            "required_obs_field_count": len(REQUIRED_OBS_FIELDS),
            "requested_file_count": len(REQUESTED_FILES),
        },
        "request_candidates": candidates,
        "required_obs_fields": REQUIRED_OBS_FIELDS,
        "requested_files": REQUESTED_FILES,
        "validation_commands": VALIDATION_COMMANDS,
        "email_template": email_template,
        "interpretation": (
            "This package converts request-only Saussurea involucrata single-cell literature "
            "into a concrete acquisition workflow. It is evidence for an active data-request "
            "path, not evidence that the data are already available for model training."
        ),
    }


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return output


def write_email(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload["email_template"] + "\n", encoding="utf-8")
    print(output)
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Saussurea Data Request Package",
        "",
        f"- Request candidates: `{summary['request_candidate_count']}`",
        f"- Package ready: `{summary['package_ready']}`",
        f"- Public downloadable matrix already found: `{summary['public_downloadable_matrix_found']}`",
        f"- Saussurea h5ad contract ready: `{summary['saussurea_h5ad_contract_ready']}`",
        "",
        payload["interpretation"],
        "",
        "## Request Candidates",
        "",
        "| Dataset | Species | Evidence | DOI/PMID | Source | Data availability |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in payload["request_candidates"]:
        lines.append(
            "| {dataset} | {species} | {evidence} | {doi} {pmid} | {source} | {availability} |".format(
                dataset=str(candidate.get("dataset_id", "")).replace("|", "/"),
                species=str(candidate.get("species", "")).replace("|", "/"),
                evidence=str(candidate.get("evidence_type", "")).replace("|", "/"),
                doi=str(candidate.get("doi", "")).replace("|", "/"),
                pmid=str(candidate.get("pmid", "")).replace("|", "/"),
                source=str(candidate.get("source_url", "")).replace("|", "/"),
                availability=str(candidate.get("data_availability", "")).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Required Cell Metadata",
            "",
            ", ".join(f"`{field}`" for field in payload["required_obs_fields"]),
            "",
            "## Requested Files",
            "",
            "| File class | Required | Description |",
            "| --- | --- | --- |",
        ]
    )
    for item in payload["requested_files"]:
        lines.append(
            f"| `{item['name']}` | `{item['required']}` | {item['description']} |"
        )
    lines.extend(["", "## Validation Commands", ""])
    for command in payload["validation_commands"]:
        lines.extend(["```bash", command, "```", ""])
    lines.extend(["## Email Template", "", "```text", payload["email_template"], "```"])
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a request package for non-public Saussurea single-cell data.")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-email", required=True, type=Path)
    args = parser.parse_args()
    payload = build_payload(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    write_email(payload, args.output_email)


if __name__ == "__main__":
    main()
