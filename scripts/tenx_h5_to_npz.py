from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np
from scipy import sparse


def _decode_array(values: Iterable[object]) -> np.ndarray:
    decoded = []
    for value in values:
        if isinstance(value, bytes):
            decoded.append(value.decode("utf-8"))
        else:
            decoded.append(str(value))
    return np.asarray(decoded, dtype=str)


def read_10x_h5(path: str | Path, feature_column: str = "id") -> tuple[sparse.csr_matrix, np.ndarray, np.ndarray]:
    with h5py.File(path, "r") as handle:
        matrix_group = handle["matrix"]
        shape = tuple(np.asarray(matrix_group["shape"], dtype=np.int64))
        csc = sparse.csc_matrix(
            (
                np.asarray(matrix_group["data"], dtype=np.float32),
                np.asarray(matrix_group["indices"], dtype=np.int32),
                np.asarray(matrix_group["indptr"], dtype=np.int32),
            ),
            shape=shape,
        )
        feature_group = matrix_group["features"]
        if feature_column not in feature_group:
            feature_column = "name" if "name" in feature_group else "id"
        genes = _decode_array(feature_group[feature_column][()])
        barcodes = _decode_array(matrix_group["barcodes"][()])
    return csc.T.tocsr().astype(np.float32), genes, barcodes


def sample_id_from_path(path: Path) -> str:
    return path.name.removesuffix(".h5")


def discover_h5(input_dir: str | Path, pattern: str = "*.h5") -> list[Path]:
    return sorted(Path(input_dir).glob(pattern))


def write_sparse_npz(
    path: Path,
    output_dir: str | Path,
    dataset_id: str,
    species: str,
    tissue: str,
    label: str,
    coarse_label: str,
    feature_column: str,
) -> Path:
    matrix, genes, barcodes = read_10x_h5(path, feature_column=feature_column)
    sample_id = sample_id_from_path(path)
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


def write_manifest(
    paths: Iterable[Path],
    output: str | Path,
    dataset_id: str,
    species: str,
    tissue: str,
) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "path",
                "dataset_id",
                "species",
                "tissue",
                "layer",
                "label_key",
                "coarse_label_key",
                "sample_key",
            ]
        )
        for path in paths:
            writer.writerow(
                [
                    str(path),
                    dataset_id,
                    species,
                    tissue,
                    "",
                    "cell_type",
                    "cell_type_coarse",
                    "sample_id",
                ]
            )
    return output_path


def convert_directory(
    input_dir: str | Path,
    output_dir: str | Path,
    dataset_id: str,
    species: str,
    tissue: str,
    label: str = "unannotated_root",
    coarse_label: str = "unannotated_root",
    pattern: str = "*.h5",
    sample_regex: str | None = None,
    max_files: int | None = None,
    min_files: int = 0,
    feature_column: str = "id",
    manifest_output: str | Path | None = None,
) -> list[Path]:
    paths = discover_h5(input_dir, pattern=pattern)
    if sample_regex:
        regex = re.compile(sample_regex)
        paths = [path for path in paths if regex.search(path.name)]
    if max_files is not None:
        paths = paths[:max_files]
    if len(paths) < min_files:
        raise ValueError(f"found {len(paths)} H5 files, need at least {min_files}")
    outputs = [
        write_sparse_npz(
            path,
            output_dir,
            dataset_id=dataset_id,
            species=species,
            tissue=tissue,
            label=label,
            coarse_label=coarse_label,
            feature_column=feature_column,
        )
        for path in paths
    ]
    if manifest_output:
        write_manifest(outputs, manifest_output, dataset_id, species, tissue)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert 10x HDF5 matrices to SnowCell NPZ")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--species", required=True)
    parser.add_argument("--tissue", required=True)
    parser.add_argument("--label", default="unannotated_root")
    parser.add_argument("--coarse-label", default="unannotated_root")
    parser.add_argument("--pattern", default="*.h5")
    parser.add_argument("--sample-regex")
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--min-files", type=int, default=0)
    parser.add_argument("--feature-column", default="id")
    parser.add_argument("--manifest-output")
    args = parser.parse_args()
    for output in convert_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        dataset_id=args.dataset_id,
        species=args.species,
        tissue=args.tissue,
        label=args.label,
        coarse_label=args.coarse_label,
        pattern=args.pattern,
        sample_regex=args.sample_regex,
        max_files=args.max_files,
        min_files=args.min_files,
        feature_column=args.feature_column,
        manifest_output=args.manifest_output,
    ):
        print(output)


if __name__ == "__main__":
    main()
