from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import io, sparse


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def first_existing(paths: Iterable[Path], patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(path for root in paths for path in root.glob(pattern))
        if matches:
            return matches[0]
    return None


def first_existing_direct(path: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(path.glob(pattern))
        if matches:
            return matches[0]
    return None


def read_first_column(path: Path) -> np.ndarray:
    values: list[str] = []
    with open_text(path) as handle:
        for line in handle:
            if line.strip():
                values.append(line.rstrip("\n").split("\t")[0])
    return np.asarray(values, dtype=str)


def read_features(path: Path, feature_column: int) -> np.ndarray:
    values: list[str] = []
    with open_text(path) as handle:
        for line in handle:
            if not line.strip():
                continue
            columns = line.rstrip("\n").split("\t")
            values.append(columns[min(feature_column, len(columns) - 1)])
    return np.asarray(values, dtype=str)


def read_matrix(path: Path) -> sparse.csr_matrix:
    with gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb") as handle:
        matrix = io.mmread(handle)
    return matrix.tocsr().astype(np.float32)


def sample_id_from_dir(path: Path) -> str:
    name = path.name
    for suffix in [".tar.gz", "_mtx", "_matrix"]:
        name = name.removesuffix(suffix)
    return name


def discover_sample_dirs(input_dir: str | Path) -> list[Path]:
    root = Path(input_dir)
    candidates = [root] + sorted(path for path in root.rglob("*") if path.is_dir())
    sample_dirs = []
    for path in candidates:
        matrix = first_existing_direct(path, ["*matrix*.mtx*", "*.mtx*"])
        features = first_existing_direct(path, ["*features*.tsv*", "*genes*.tsv*", "genes.txt"])
        barcodes = first_existing_direct(path, ["*barcodes*.tsv*", "cells.txt"])
        if matrix and features and barcodes:
            sample_dirs.append(path)
    return sorted(set(sample_dirs))


def convert_one(
    sample_dir: Path,
    output_dir: str | Path,
    dataset_id: str,
    species: str,
    tissue: str,
    feature_column: int,
    label: str,
    coarse_label: str,
) -> Path:
    roots = [sample_dir]
    matrix_path = first_existing(roots, ["**/*matrix*.mtx*", "**/*.mtx*"])
    feature_path = first_existing(roots, ["**/*features*.tsv*", "**/*genes*.tsv*", "**/genes.txt"])
    barcode_path = first_existing(roots, ["**/*barcodes*.tsv*", "**/cells.txt"])
    if matrix_path is None or feature_path is None or barcode_path is None:
        raise ValueError(f"{sample_dir}: missing matrix/features/barcodes")

    matrix = read_matrix(matrix_path)
    genes = read_features(feature_path, feature_column)
    barcodes = read_first_column(barcode_path)
    if matrix.shape == (len(genes), len(barcodes)):
        matrix = matrix.T.tocsr()
    elif matrix.shape != (len(barcodes), len(genes)):
        raise ValueError(
            f"{sample_dir}: matrix shape {matrix.shape} incompatible with "
            f"{len(barcodes)} barcodes and {len(genes)} genes"
        )

    sample_id = sample_id_from_dir(sample_dir)
    output = Path(output_dir) / f"{sample_id}.npz"
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(f".{output.name}.tmp")
    n_cells = matrix.shape[0]
    with tmp.open("wb") as handle:
        np.savez_compressed(
            handle,
            X_data=matrix.data.astype(np.float32),
            X_indices=matrix.indices.astype(np.int32),
            X_indptr=matrix.indptr.astype(np.int32),
            X_shape=np.asarray(matrix.shape, dtype=np.int64),
            genes=genes,
            cell_id=np.asarray([f"{sample_id}:{barcode}" for barcode in barcodes], dtype=str),
            sample_id=np.repeat(sample_id, n_cells).astype(str),
            dataset_id=np.repeat(dataset_id, n_cells).astype(str),
            species=np.repeat(species, n_cells).astype(str),
            tissue=np.repeat(tissue, n_cells).astype(str),
            cell_type=np.repeat(label, n_cells).astype(str),
            cell_type_coarse=np.repeat(coarse_label, n_cells).astype(str),
        )
    tmp.replace(output)
    return output


def write_manifest(paths: Iterable[Path], output: str | Path, dataset_id: str, species: str, tissue: str) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["path", "dataset_id", "species", "tissue", "layer", "label_key", "coarse_label_key", "sample_key"])
        for path in paths:
            writer.writerow([str(path), dataset_id, species, tissue, "", "cell_type", "cell_type_coarse", "sample_id"])
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert extracted GEO MTX archives to SnowCell sparse NPZ")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--species", required=True)
    parser.add_argument("--tissue", required=True)
    parser.add_argument("--feature-column", type=int, default=0)
    parser.add_argument("--label", default="unannotated")
    parser.add_argument("--coarse-label", default="unannotated")
    parser.add_argument("--manifest-output")
    parser.add_argument("--min-samples", type=int, default=1)
    args = parser.parse_args()

    sample_dirs = discover_sample_dirs(args.input_dir)
    if len(sample_dirs) < args.min_samples:
        raise ValueError(f"found {len(sample_dirs)} extracted MTX samples, need at least {args.min_samples}")
    outputs = [
        convert_one(
            sample_dir,
            output_dir=args.output_dir,
            dataset_id=args.dataset_id,
            species=args.species,
            tissue=args.tissue,
            feature_column=args.feature_column,
            label=args.label,
            coarse_label=args.coarse_label,
        )
        for sample_dir in sample_dirs
    ]
    if args.manifest_output:
        write_manifest(outputs, args.manifest_output, args.dataset_id, args.species, args.tissue)
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
