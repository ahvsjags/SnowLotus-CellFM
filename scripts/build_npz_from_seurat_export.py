from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import io


DEFAULT_LABEL_KEYS = [
    "CellAnnotation",
    "cell_annotation",
    "annotations",
    "annotation.predicted",
    "annotation_predicted",
    "celltype",
    "cell_type",
    "cell_type_fine",
    "CellType",
    "annotation",
    "annotation_level_1",
    "predicted.celltype",
    "predicted_cell_type",
    "seurat_clusters",
    "cluster",
]

DEFAULT_COARSE_LABEL_KEYS = [
    "cell_type_coarse",
    "celltype_coarse",
    "TissueSystem",
    "tissue_system",
    "annotation.predicted",
    "annotation_predicted",
    "major_celltype",
    "major_cell_type",
    "coarse_annotation",
    "lineage",
    "organ",
]

DEFAULT_SAMPLE_KEYS = [
    "orig.ident",
    "sample_id",
    "sample",
    "batch",
    "library",
    "replicate",
    "Condition",
]


def read_lines(path: Path) -> np.ndarray:
    return np.asarray(path.read_text(encoding="utf-8").splitlines(), dtype=str)


def infer_coarse(labels: pd.Series) -> pd.Series:
    return labels.fillna("unknown").astype(str)


def find_column(meta: pd.DataFrame, candidate: str) -> str | None:
    if candidate in meta:
        return candidate
    lower_to_column = {column.lower(): column for column in meta.columns}
    return lower_to_column.get(candidate.lower())


def first_existing(meta: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
    for candidate in candidates:
        column = find_column(meta, candidate)
        if column is not None:
            return meta[column]
    return None


def constant_or_column(meta: pd.DataFrame, value: str, n_cells: int) -> np.ndarray:
    column = find_column(meta, value)
    if column is not None:
        return meta[column].fillna("unknown").astype(str).to_numpy(dtype=str)
    return np.repeat(value, n_cells).astype(str)


def convert_one(
    sample_dir: Path,
    output_dir: Path,
    dataset_id: str,
    species: str,
    tissue: str,
    label_keys: list[str],
    coarse_label_keys: list[str],
    sample_keys: list[str],
) -> Path:
    matrix = io.mmread(sample_dir / "matrix_cells_by_genes.mtx").tocsr().astype("float32")
    genes = read_lines(sample_dir / "genes.txt")
    cells = read_lines(sample_dir / "cells.txt")
    meta = pd.read_csv(sample_dir / "metadata.csv")
    if len(cells) != matrix.shape[0]:
        raise ValueError(f"{sample_dir}: cell count mismatch")
    if len(genes) != matrix.shape[1]:
        raise ValueError(f"{sample_dir}: gene count mismatch")
    fine_source = first_existing(meta, label_keys)
    fine = fine_source.fillna("unknown").astype(str) if fine_source is not None else pd.Series(["unknown"] * matrix.shape[0])
    coarse_source = first_existing(meta, coarse_label_keys)
    coarse = coarse_source.fillna("unknown").astype(str) if coarse_source is not None else infer_coarse(fine)
    sample_source = first_existing(meta, sample_keys)
    sample_id = sample_source.astype(str) if sample_source is not None else pd.Series([sample_dir.name] * matrix.shape[0])
    cell_ids = meta["cell_id"].astype(str) if "cell_id" in meta else pd.Series(cells)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{sample_dir.name}.npz"
    tmp = output.with_name(f".{output.name}.tmp")
    with tmp.open("wb") as handle:
        np.savez_compressed(
            handle,
            X_data=matrix.data,
            X_indices=matrix.indices,
            X_indptr=matrix.indptr,
            X_shape=np.asarray(matrix.shape, dtype=np.int64),
            genes=genes,
            cell_id=cell_ids.to_numpy(dtype=str),
            cell_type=fine.to_numpy(dtype=str),
            cell_type_coarse=coarse.to_numpy(dtype=str),
            sample_id=sample_id.to_numpy(dtype=str),
            dataset_id=np.repeat(dataset_id, matrix.shape[0]).astype(str),
            species=constant_or_column(meta, species, matrix.shape[0]),
            tissue=constant_or_column(meta, tissue, matrix.shape[0]),
        )
    tmp.replace(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sparse SnowCell NPZ files from Seurat MTX exports")
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--species", required=True)
    parser.add_argument("--tissue", required=True)
    parser.add_argument(
        "--label-key",
        action="append",
        default=list(DEFAULT_LABEL_KEYS),
    )
    parser.add_argument(
        "--coarse-label-key",
        action="append",
        default=list(DEFAULT_COARSE_LABEL_KEYS),
    )
    parser.add_argument(
        "--sample-key",
        action="append",
        default=list(DEFAULT_SAMPLE_KEYS),
    )
    args = parser.parse_args()
    export_dir = Path(args.export_dir)
    output_dir = Path(args.output_dir)
    for sample_dir in sorted(path for path in export_dir.iterdir() if path.is_dir()):
        print(
            convert_one(
                sample_dir,
                output_dir,
                dataset_id=args.dataset_id,
                species=args.species,
                tissue=args.tissue,
                label_keys=args.label_key,
                coarse_label_keys=args.coarse_label_key,
                sample_keys=args.sample_key,
            )
        )


if __name__ == "__main__":
    main()
