from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


REQUIRED_MANIFEST_COLUMNS = ["path", "dataset_id", "species"]
RECOMMENDED_OBS_KEYS = ["cell_type", "cell_type_coarse", "sample_id", "species", "tissue", "cell_id"]


@dataclass
class MatrixAudit:
    path: str
    exists: bool
    format: str
    readable: bool
    n_cells: int | None
    n_genes: int | None
    obs_keys: str
    missing_recommended_obs: str
    bytes: int
    error: str


@dataclass
class ManifestAudit:
    manifest: str
    exists: bool
    readable: bool
    rows: int
    missing_columns: str
    missing_files: int
    unreadable_files: int
    total_cells: int
    total_genes_max: int
    dataset_ids: str
    species: str
    status: str
    error: str


def resolve_path(project_dir: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_dir / path


def inspect_npz(path: Path) -> tuple[int | None, int | None, list[str], str]:
    try:
        with np.load(path, allow_pickle=False) as archive:
            files = set(archive.files)
            if "X" in files:
                shape = tuple(int(value) for value in archive["X"].shape)
            elif {"X_data", "X_indices", "X_indptr", "X_shape"}.issubset(files):
                shape = tuple(int(value) for value in archive["X_shape"])
            else:
                return None, None, sorted(files - {"genes"}), "missing X or CSR arrays"
            if len(shape) != 2:
                return (
                    None,
                    None,
                    sorted(files - {"X", "X_data", "X_indices", "X_indptr", "X_shape", "genes"}),
                    f"matrix is not 2D: {shape}",
                )
            if "genes" not in files:
                return int(shape[0]), int(shape[1]), sorted(files), "missing genes"
            genes_len = len(archive["genes"])
            if genes_len != int(shape[1]):
                return (
                    int(shape[0]),
                    int(shape[1]),
                    sorted(files - {"X", "X_data", "X_indices", "X_indptr", "X_shape", "genes"}),
                    "gene count mismatch",
                )
            obs_keys = sorted(files - {"X", "X_data", "X_indices", "X_indptr", "X_shape", "genes"})
            bad_obs = []
            for key in obs_keys:
                try:
                    if len(archive[key]) != int(shape[0]):
                        bad_obs.append(key)
                except TypeError:
                    bad_obs.append(key)
            if bad_obs:
                return int(shape[0]), int(shape[1]), obs_keys, f"obs length mismatch: {','.join(bad_obs)}"
            return int(shape[0]), int(shape[1]), obs_keys, ""
    except Exception as error:
        return None, None, [], repr(error)


def inspect_h5ad(path: Path) -> tuple[int | None, int | None, list[str], str]:
    try:
        import anndata as ad

        adata = ad.read_h5ad(path, backed="r")
        try:
            obs_keys = list(adata.obs.columns)
            return int(adata.n_obs), int(adata.n_vars), sorted(obs_keys), ""
        finally:
            if getattr(adata, "file", None) is not None:
                adata.file.close()
    except Exception as anndata_error:
        try:
            import h5py

            with h5py.File(path, "r") as handle:
                if "X" not in handle:
                    return None, None, [], "missing X in h5ad"
                x_node = handle["X"]
                shape_value = x_node.attrs.get("shape")
                if shape_value is None and hasattr(x_node, "shape"):
                    shape_value = x_node.shape
                if shape_value is None and "shape" in x_node:
                    shape_value = x_node["shape"][()]
                if shape_value is None:
                    return None, None, [], "missing X shape in h5ad"
                shape = tuple(int(value) for value in shape_value)
                obs_keys = sorted(handle.get("obs", {}).keys()) if "obs" in handle else []
                if len(shape) != 2:
                    return None, None, obs_keys, f"matrix is not 2D: {shape}"
                return int(shape[0]), int(shape[1]), obs_keys, f"anndata backed read failed: {anndata_error!r}"
        except Exception as h5_error:
            return None, None, [], f"anndata={anndata_error!r}; h5py={h5_error!r}"


def inspect_matrix(project_dir: Path, value: str) -> MatrixAudit:
    path = resolve_path(project_dir, value)
    exists = path.exists()
    suffix = path.suffix.lower()
    if not exists:
        return MatrixAudit(
            path=value,
            exists=False,
            format=suffix.lstrip("."),
            readable=False,
            n_cells=None,
            n_genes=None,
            obs_keys="",
            missing_recommended_obs=";".join(RECOMMENDED_OBS_KEYS),
            bytes=0,
            error="missing file",
        )
    if suffix == ".npz":
        n_cells, n_genes, obs_keys, error = inspect_npz(path)
    elif suffix == ".h5ad":
        n_cells, n_genes, obs_keys, error = inspect_h5ad(path)
    else:
        n_cells, n_genes, obs_keys, error = None, None, [], f"unsupported matrix format: {suffix}"
    missing_obs = [key for key in RECOMMENDED_OBS_KEYS if key not in obs_keys]
    return MatrixAudit(
        path=value,
        exists=True,
        format=suffix.lstrip("."),
        readable=not error or error.startswith("anndata backed read failed"),
        n_cells=n_cells,
        n_genes=n_genes,
        obs_keys=";".join(obs_keys),
        missing_recommended_obs=";".join(missing_obs),
        bytes=path.stat().st_size,
        error=error,
    )


def read_manifest(path: Path) -> tuple[list[dict[str, str]], list[str], str]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            rows = list(reader)
            columns = list(reader.fieldnames or [])
        return rows, columns, ""
    except Exception as error:
        return [], [], repr(error)


def audit_manifest(project_dir: Path, manifest: Path) -> tuple[ManifestAudit, list[MatrixAudit]]:
    relative_manifest = (
        manifest.relative_to(project_dir).as_posix()
        if manifest.is_relative_to(project_dir)
        else manifest.as_posix()
    )
    if not manifest.exists():
        return (
            ManifestAudit(
                manifest=relative_manifest,
                exists=False,
                readable=False,
                rows=0,
                missing_columns=";".join(REQUIRED_MANIFEST_COLUMNS),
                missing_files=0,
                unreadable_files=0,
                total_cells=0,
                total_genes_max=0,
                dataset_ids="",
                species="",
                status="missing_manifest",
                error="missing manifest",
            ),
            [],
        )
    rows, columns, error = read_manifest(manifest)
    missing_columns = [column for column in REQUIRED_MANIFEST_COLUMNS if column not in columns]
    matrix_audits: list[MatrixAudit] = []
    if not error and not missing_columns:
        matrix_audits = [inspect_matrix(project_dir, row.get("path", "")) for row in rows]
    missing_files = sum(1 for item in matrix_audits if not item.exists)
    unreadable_files = sum(1 for item in matrix_audits if item.exists and not item.readable)
    total_cells = sum(item.n_cells or 0 for item in matrix_audits)
    total_genes_max = max([item.n_genes or 0 for item in matrix_audits] or [0])
    if error:
        status = "unreadable_manifest"
    elif missing_columns:
        status = "invalid_manifest"
    elif missing_files or unreadable_files:
        status = "matrix_issues"
    else:
        status = "ready"
    return (
        ManifestAudit(
            manifest=relative_manifest,
            exists=True,
            readable=not error,
            rows=len(rows),
            missing_columns=";".join(missing_columns),
            missing_files=missing_files,
            unreadable_files=unreadable_files,
            total_cells=total_cells,
            total_genes_max=total_genes_max,
            dataset_ids=";".join(sorted({row.get("dataset_id", "") for row in rows if row.get("dataset_id")})),
            species=";".join(sorted({row.get("species", "") for row in rows if row.get("species")})),
            status=status,
            error=error,
        ),
        matrix_audits,
    )


def default_manifest_paths(project_dir: Path) -> list[Path]:
    data_dir = project_dir / "data"
    manifests = sorted(data_dir.glob("corpus_manifest*.tsv"))
    return [
        path
        for path in manifests
        if path.is_file() and ".template." not in path.name and not path.name.endswith("_template.tsv")
    ]


def audit_project(project_dir: Path, manifests: list[Path]) -> dict[str, Any]:
    manifest_items: list[ManifestAudit] = []
    matrix_items: list[MatrixAudit] = []
    for manifest in manifests:
        item, matrices = audit_manifest(project_dir, manifest)
        manifest_items.append(item)
        matrix_items.extend(matrices)
    ready_manifests = sum(1 for item in manifest_items if item.status == "ready")
    issue_manifests = len(manifest_items) - ready_manifests
    return {
        "project_dir": project_dir.as_posix(),
        "summary": {
            "manifest_count": len(manifest_items),
            "ready_manifests": ready_manifests,
            "issue_manifests": issue_manifests,
            "matrix_count": len(matrix_items),
            "missing_files": sum(1 for item in matrix_items if not item.exists),
            "unreadable_files": sum(1 for item in matrix_items if item.exists and not item.readable),
            "total_cells": sum(item.n_cells or 0 for item in matrix_items),
        },
        "manifests": [asdict(item) for item in manifest_items],
        "matrices": [asdict(item) for item in matrix_items],
    }


def write_manifest_tsv(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ManifestAudit.__dataclass_fields__)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in payload["manifests"]:
            writer.writerow(row)
    return output


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# SnowLotus-CellFM Data Integrity Audit",
        "",
        f"- Manifest files audited: `{summary['manifest_count']}`",
        f"- Ready manifests: `{summary['ready_manifests']}`",
        f"- Manifests with issues: `{summary['issue_manifests']}`",
        f"- Matrix files referenced: `{summary['matrix_count']}`",
        f"- Missing matrix files: `{summary['missing_files']}`",
        f"- Unreadable matrix files: `{summary['unreadable_files']}`",
        f"- Total referenced cells across readable matrices: `{summary['total_cells']}`",
        "",
        "## Manifest Status",
        "",
        "| Manifest | Rows | Status | Missing files | Unreadable files | Total cells | Dataset IDs |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for item in payload["manifests"]:
        lines.append(
            "| {manifest} | {rows} | {status} | {missing} | {unreadable} | {cells} | {datasets} |".format(
                manifest=item["manifest"],
                rows=item["rows"],
                status=item["status"],
                missing=item["missing_files"],
                unreadable=item["unreadable_files"],
                cells=item["total_cells"],
                datasets=item["dataset_ids"],
            )
        )
    issue_matrices = [
        item for item in payload["matrices"] if (not item["exists"]) or (not item["readable"]) or item["missing_recommended_obs"]
    ]
    lines.extend(
        [
            "",
            "## Matrix Issues",
            "",
            "| Matrix | Exists | Readable | Missing recommended obs | Error |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in issue_matrices[:80]:
        lines.append(
            "| {path} | {exists} | {readable} | {missing_obs} | {error} |".format(
                path=item["path"],
                exists=item["exists"],
                readable=item["readable"],
                missing_obs=item["missing_recommended_obs"],
                error=str(item["error"]).replace("|", "/"),
            )
        )
    if not issue_matrices:
        lines.append("| None | True | True |  |  |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit SnowLotus-CellFM matrix manifests and corpus inputs")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--manifest", action="append", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-tsv", required=True, type=Path)
    args = parser.parse_args()
    project_dir = args.project_dir
    manifests = (
        [resolve_path(project_dir, path) for path in args.manifest]
        if args.manifest
        else default_manifest_paths(project_dir)
    )
    payload = audit_project(project_dir, manifests)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    write_manifest_tsv(payload, args.output_tsv)
    print(args.output_md)
    print(args.output_json)
    print(args.output_tsv)


if __name__ == "__main__":
    main()
