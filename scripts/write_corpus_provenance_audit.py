from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ACCESSION_RE = re.compile(
    r"(?<![A-Za-z0-9])(GSE\d+|GSM\d+|GDS\d+|SRP\d+|SRX\d+|SRR\d+|PRJNA\d+|PRJEB\d+|PRJDB\d+)(?![A-Za-z0-9])",
    re.IGNORECASE,
)


@dataclass
class ProvenanceDataset:
    manifest: str
    dataset_id: str
    species: str
    rows: int
    existing_rows: int
    missing_rows: int
    bytes: int
    source_registered: bool
    accession_or_doi: str
    source_url: str
    public_manifest_status: str
    public_manifest_priority: str
    source_registration_method: str
    inferred_accessions: str
    status: str


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def manifest_paths(root: Path) -> list[Path]:
    manifests = sorted((root / "data").glob("corpus_manifest*.tsv"))
    return [
        path
        for path in manifests
        if path.is_file() and ".template." not in path.name and not path.name.endswith("_template.tsv")
    ]


def public_manifest_by_dataset(root: Path) -> dict[str, dict[str, str]]:
    rows = read_tsv(root / "data" / "public_dataset_manifest.tsv")
    return {row.get("dataset_id", ""): row for row in rows if row.get("dataset_id")}


def public_manifest_by_accession(public_rows: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    by_accession: dict[str, dict[str, str]] = {}
    for dataset_id, row in public_rows.items():
        for accession in inferred_accessions(
            dataset_id,
            row.get("accession_or_doi", ""),
            row.get("source_url", ""),
        ):
            by_accession.setdefault(accession, row)
    return by_accession


def inferred_accessions(*values: str) -> list[str]:
    found: set[str] = set()
    for value in values:
        found.update(token.upper() for token in ACCESSION_RE.findall(value or ""))
    return sorted(found)


def source_row_for_dataset(
    dataset_id: str,
    manifest: Path,
    public_rows: dict[str, dict[str, str]],
    public_by_accession: dict[str, dict[str, str]],
) -> tuple[dict[str, str], str]:
    if dataset_id in public_rows:
        return public_rows[dataset_id], "exact_dataset_id"
    if dataset_id.startswith("scplantdb_") and "scplantdb_global" in public_rows:
        return public_rows["scplantdb_global"], "scplantdb_global_scope"
    for accession in inferred_accessions(dataset_id):
        if accession in public_by_accession:
            return public_by_accession[accession], "accession_match"
    for accession in inferred_accessions(manifest.name):
        if accession in public_by_accession:
            return public_by_accession[accession], "accession_match"
    if dataset_id.startswith("scplantllm_") and "scplantllm_reference" in public_rows:
        return public_rows["scplantllm_reference"], "scplantllm_reference_scope"
    return {}, "unregistered"


def dataset_status(rows: int, missing_rows: int, source_registered: bool) -> str:
    if rows == 0:
        return "empty_manifest"
    if missing_rows:
        return "missing_matrix_files"
    if not source_registered:
        return "ready_unregistered_source"
    return "ready_registered_source"


def summarize_manifest_dataset(
    root: Path,
    manifest: Path,
    dataset_id: str,
    rows: list[dict[str, str]],
    public_rows: dict[str, dict[str, str]],
    public_by_accession: dict[str, dict[str, str]],
) -> ProvenanceDataset:
    public_row, registration_method = source_row_for_dataset(
        dataset_id,
        manifest,
        public_rows,
        public_by_accession,
    )
    species = ";".join(sorted({row.get("species", "") for row in rows if row.get("species")}))
    existing_rows = 0
    total_bytes = 0
    for row in rows:
        matrix = resolve_path(root, row.get("path", ""))
        if matrix.is_file():
            existing_rows += 1
            total_bytes += matrix.stat().st_size
    missing_rows = len(rows) - existing_rows
    dataset_accessions = inferred_accessions(dataset_id)
    fallback_manifest = [manifest.name] if not dataset_accessions else []
    accessions = inferred_accessions(
        dataset_id,
        *fallback_manifest,
        public_row.get("accession_or_doi", ""),
        public_row.get("source_url", ""),
    )
    source_registered = bool(public_row)
    return ProvenanceDataset(
        manifest=relpath(root, manifest),
        dataset_id=dataset_id,
        species=species,
        rows=len(rows),
        existing_rows=existing_rows,
        missing_rows=missing_rows,
        bytes=total_bytes,
        source_registered=source_registered,
        accession_or_doi=public_row.get("accession_or_doi", ""),
        source_url=public_row.get("source_url", ""),
        public_manifest_status=public_row.get("status", ""),
        public_manifest_priority=public_row.get("priority", ""),
        source_registration_method=registration_method,
        inferred_accessions=";".join(accessions),
        status=dataset_status(len(rows), missing_rows, source_registered),
    )


def build_audit(project_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    public_rows = public_manifest_by_dataset(root)
    public_by_accession = public_manifest_by_accession(public_rows)
    datasets: list[ProvenanceDataset] = []
    manifest_overview = []
    for manifest in manifest_paths(root):
        rows = read_tsv(manifest)
        by_dataset: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            by_dataset[row.get("dataset_id", "") or "unknown_dataset"].append(row)
        for dataset_id, dataset_rows in sorted(by_dataset.items()):
            datasets.append(
                summarize_manifest_dataset(
                    root,
                    manifest,
                    dataset_id,
                    dataset_rows,
                    public_rows,
                    public_by_accession,
                )
            )
        manifest_overview.append(
            {
                "manifest": relpath(root, manifest),
                "rows": len(rows),
                "dataset_count": len(by_dataset),
                "empty": len(rows) == 0,
            }
        )
    status_counts = Counter(item.status for item in datasets)
    unique_dataset_ids = {item.dataset_id for item in datasets}
    source_accessions = {
        accession
        for item in datasets
        for accession in item.inferred_accessions.split(";")
        if accession
    }
    summary = {
        "manifest_count": len(manifest_overview),
        "nonempty_manifest_count": sum(1 for item in manifest_overview if not item["empty"]),
        "dataset_count": len(unique_dataset_ids),
        "dataset_manifest_entries": len(datasets),
        "registered_dataset_entries": sum(1 for item in datasets if item.source_registered),
        "unregistered_dataset_entries": sum(1 for item in datasets if not item.source_registered),
        "matrix_rows": sum(item.rows for item in datasets),
        "existing_matrix_rows": sum(item.existing_rows for item in datasets),
        "missing_matrix_rows": sum(item.missing_rows for item in datasets),
        "total_matrix_bytes": sum(item.bytes for item in datasets),
        "source_accession_count": len(source_accessions),
        "species_count": len({item.species for item in datasets if item.species}),
        "status_counts": dict(sorted(status_counts.items())),
        "all_matrix_rows_exist": all(item.missing_rows == 0 for item in datasets),
        "all_dataset_entries_registered": all(item.source_registered for item in datasets),
    }
    return {
        "project_dir": str(root),
        "summary": summary,
        "manifests": manifest_overview,
        "datasets": [asdict(item) for item in datasets],
    }


def human_bytes(value: int) -> str:
    size = float(value)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TiB"


def table_cell(value: str, max_chars: int = 180) -> str:
    text = str(value or "").replace("|", "/").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Corpus Provenance Audit",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Manifest files | {summary['manifest_count']} |",
        f"| Non-empty manifests | {summary['nonempty_manifest_count']} |",
        f"| Dataset manifest entries | {summary['dataset_manifest_entries']} |",
        f"| Registered dataset entries | {summary['registered_dataset_entries']} |",
        f"| Unregistered dataset entries | {summary['unregistered_dataset_entries']} |",
        f"| Matrix rows | {summary['matrix_rows']} |",
        f"| Existing matrix rows | {summary['existing_matrix_rows']} |",
        f"| Missing matrix rows | {summary['missing_matrix_rows']} |",
        f"| Total matrix bytes | {human_bytes(summary['total_matrix_bytes'])} |",
        f"| Source accession count | {summary['source_accession_count']} |",
        "",
        "## Dataset Entries",
        "",
        "| Manifest | Dataset | Species | Rows | Existing | Missing | Source | Accessions | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for item in payload["datasets"]:
        lines.append(
            "| {manifest} | {dataset} | {species} | {rows} | {existing} | {missing} | {source} | {accessions} | {status} |".format(
                manifest=table_cell(item["manifest"], 140),
                dataset=table_cell(item["dataset_id"], 140),
                species=table_cell(item["species"]),
                rows=item["rows"],
                existing=item["existing_rows"],
                missing=item["missing_rows"],
                source="registered" if item["source_registered"] else "unregistered",
                accessions=table_cell(item["inferred_accessions"] or item["source_registration_method"], 120),
                status=item["status"],
            )
        )
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output_path)
    return output_path


def write_tsv(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ProvenanceDataset.__dataclass_fields__)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in payload["datasets"]:
            writer.writerow(row)
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write corpus provenance audit.")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-tsv", required=True, type=Path)
    args = parser.parse_args()
    payload = build_audit(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    write_tsv(payload, args.output_tsv)


if __name__ == "__main__":
    main()
