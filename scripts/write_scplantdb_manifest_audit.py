from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ScPlantDBMatrixAudit:
    dataset_id: str
    path: str
    species: str
    tissue: str
    exists: bool
    readable: bool
    n_cells: int
    n_genes: int
    label_key: str
    coarse_label_key: str
    sample_key: str
    label_key_present: bool
    coarse_label_key_present: bool
    sample_key_present: bool
    obs_column_count: int
    obs_columns_preview: str
    bytes: int
    status: str
    error: str


def resolve_path(project_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_dir / path


def read_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def inspect_h5ad(path: Path) -> tuple[int, int, list[str], str]:
    try:
        import anndata as ad

        adata = ad.read_h5ad(path, backed="r")
        try:
            return int(adata.n_obs), int(adata.n_vars), list(adata.obs.columns), ""
        finally:
            if getattr(adata, "file", None) is not None:
                adata.file.close()
    except Exception as error:
        return 0, 0, [], repr(error)


def audit_row(project_dir: Path, row: dict[str, str]) -> ScPlantDBMatrixAudit:
    manifest_path = row.get("path", "")
    path = resolve_path(project_dir, manifest_path)
    label_key = row.get("label_key", "")
    coarse_label_key = row.get("coarse_label_key", "")
    sample_key = row.get("sample_key", "")
    if not path.exists():
        return ScPlantDBMatrixAudit(
            dataset_id=row.get("dataset_id", ""),
            path=manifest_path,
            species=row.get("species", ""),
            tissue=row.get("tissue", ""),
            exists=False,
            readable=False,
            n_cells=0,
            n_genes=0,
            label_key=label_key,
            coarse_label_key=coarse_label_key,
            sample_key=sample_key,
            label_key_present=False,
            coarse_label_key_present=False,
            sample_key_present=False,
            obs_column_count=0,
            obs_columns_preview="",
            bytes=0,
            status="missing_file",
            error="missing file",
        )
    n_cells, n_genes, obs_columns, error = inspect_h5ad(path)
    obs_set = set(obs_columns)
    label_key_present = bool(label_key) and label_key in obs_set
    coarse_label_key_present = bool(coarse_label_key) and coarse_label_key in obs_set
    sample_key_present = bool(sample_key) and sample_key in obs_set
    if error:
        status = "unreadable_h5ad"
    elif not (label_key_present and coarse_label_key_present and sample_key_present):
        status = "missing_training_obs_keys"
    else:
        status = "ready"
    return ScPlantDBMatrixAudit(
        dataset_id=row.get("dataset_id", ""),
        path=manifest_path,
        species=row.get("species", ""),
        tissue=row.get("tissue", ""),
        exists=True,
        readable=not error,
        n_cells=n_cells,
        n_genes=n_genes,
        label_key=label_key,
        coarse_label_key=coarse_label_key,
        sample_key=sample_key,
        label_key_present=label_key_present,
        coarse_label_key_present=coarse_label_key_present,
        sample_key_present=sample_key_present,
        obs_column_count=len(obs_columns),
        obs_columns_preview=";".join(obs_columns[:30]),
        bytes=path.stat().st_size,
        status=status,
        error=error,
    )


def build_audit(project_dir: Path, manifest: Path) -> dict[str, Any]:
    resolved_manifest = resolve_path(project_dir, manifest.as_posix())
    rows = read_manifest(resolved_manifest)
    items = [audit_row(project_dir, row) for row in rows]
    ready = sum(1 for item in items if item.status == "ready")
    species = sorted({item.species for item in items if item.species})
    tissues = sorted({item.tissue for item in items if item.tissue})
    return {
        "project_dir": project_dir.as_posix(),
        "manifest": (
            resolved_manifest.relative_to(project_dir).as_posix()
            if resolved_manifest.exists() and resolved_manifest.is_relative_to(project_dir)
            else resolved_manifest.as_posix()
        ),
        "summary": {
            "rows": len(items),
            "ready_rows": ready,
            "issue_rows": len(items) - ready,
            "missing_files": sum(1 for item in items if not item.exists),
            "unreadable_files": sum(1 for item in items if item.exists and not item.readable),
            "missing_training_obs_key_rows": sum(
                1 for item in items if item.status == "missing_training_obs_keys"
            ),
            "total_cells": sum(item.n_cells for item in items),
            "max_genes": max([item.n_genes for item in items] or [0]),
            "species_count": len(species),
            "species": species,
            "tissue_count": len(tissues),
        },
        "datasets": [asdict(item) for item in items],
    }


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return output


def write_tsv(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ScPlantDBMatrixAudit.__dataclass_fields__)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in payload["datasets"]:
            writer.writerow(row)
    print(output)
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# scPlantDB Manifest Audit",
        "",
        f"- Manifest: `{payload['manifest']}`",
        f"- Rows: `{summary['rows']}`",
        f"- Ready rows: `{summary['ready_rows']}`",
        f"- Issue rows: `{summary['issue_rows']}`",
        f"- Missing files: `{summary['missing_files']}`",
        f"- Unreadable files: `{summary['unreadable_files']}`",
        f"- Rows missing training obs keys: `{summary['missing_training_obs_key_rows']}`",
        f"- Total cells: `{summary['total_cells']}`",
        f"- Species count: `{summary['species_count']}`",
        "",
        "## Datasets",
        "",
        "| Dataset | Species | Tissue | Cells | Genes | Label | Sample | Status |",
        "| --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for item in payload["datasets"]:
        lines.append(
            "| {dataset_id} | {species} | {tissue} | {cells} | {genes} | {label} | {sample} | {status} |".format(
                dataset_id=item["dataset_id"],
                species=item["species"],
                tissue=str(item["tissue"]).replace("|", "/"),
                cells=item["n_cells"],
                genes=item["n_genes"],
                label="yes" if item["label_key_present"] else "no",
                sample="yes" if item["sample_key_present"] else "no",
                status=item["status"],
            )
        )
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit scPlantDB H5AD manifest label/sample readiness")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--manifest", default="data/corpus_manifest.scplantdb.tsv", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-tsv", required=True, type=Path)
    args = parser.parse_args()
    payload = build_audit(args.project_dir, args.manifest)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    write_tsv(payload, args.output_tsv)


if __name__ == "__main__":
    main()
