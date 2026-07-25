from __future__ import annotations

import argparse
import csv
import gzip
import re
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import io, sparse

BRASSICACEAE_SPECIES = {
    "Ath": "Arabidopsis thaliana",
    "Esa": "Eutrema salsugineum",
    "Sir": "Sisymbrium irio",
    "Spa": "Schrenkiella parvula",
    "Csa": "Camelina sativa",
}


@dataclass(frozen=True)
class TenXTriple:
    sample_id: str
    barcodes: Path
    features: Path
    matrix: Path


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def sample_prefix(path: Path, suffix: str) -> str:
    name = path.name
    if not name.endswith(suffix):
        raise ValueError(f"{name} does not end with {suffix}")
    return name[: -len(suffix)]


def is_valid_gzip(path: Path) -> bool:
    try:
        with gzip.open(path, "rb") as handle:
            while handle.read(1024 * 1024):
                pass
        return True
    except (EOFError, OSError, zlib.error):
        return False


def discover_triples(input_dir: str | Path, require_valid_gzip: bool = False) -> list[TenXTriple]:
    root = Path(input_dir)
    barcodes = {
        sample_prefix(path, "_barcodes.tsv.gz"): path
        for path in root.glob("*_barcodes.tsv.gz")
    }
    features = {
        sample_prefix(path, "_features.tsv.gz"): path
        for path in root.glob("*_features.tsv.gz")
    }
    matrices = {
        sample_prefix(path, "_matrix.mtx.gz"): path
        for path in root.glob("*_matrix.mtx.gz")
    }
    common = sorted(set(barcodes) & set(features) & set(matrices))
    triples = [
        TenXTriple(
            sample_id=sample_id,
            barcodes=barcodes[sample_id],
            features=features[sample_id],
            matrix=matrices[sample_id],
        )
        for sample_id in common
    ]
    if require_valid_gzip:
        triples = [
            triple
            for triple in triples
            if all(
                is_valid_gzip(path)
                for path in [triple.barcodes, triple.features, triple.matrix]
            )
        ]
    return triples


def read_first_column(path: Path) -> list[str]:
    with open_text(path) as handle:
        return [line.rstrip("\n").split("\t")[0] for line in handle if line.strip()]


def read_features(path: Path, feature_column: int) -> list[str]:
    genes = []
    with open_text(path) as handle:
        for line in handle:
            if not line.strip():
                continue
            columns = line.rstrip("\n").split("\t")
            index = min(feature_column, len(columns) - 1)
            genes.append(columns[index])
    return genes


def read_matrix(path: Path) -> sparse.csr_matrix:
    with gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb") as handle:
        matrix = io.mmread(handle)
    return matrix.tocsr().astype(np.float32)


def parse_sample(sample_id: str) -> dict[str, str]:
    parts = sample_id.split("_")
    code = parts[1] if len(parts) > 1 and parts[0].startswith("GSM") else "unknown"
    tissue = parts[2].lower() if len(parts) > 2 else "unknown_tissue"
    treatment = parts[3] if len(parts) > 3 else "unknown"
    replicate = parts[-1] if parts else "unknown"
    species = BRASSICACEAE_SPECIES.get(code, code)
    return {
        "species": species,
        "species_code": code,
        "tissue": tissue,
        "treatment": treatment,
        "replicate": replicate,
    }


def write_sparse_npz(
    triple: TenXTriple,
    output_dir: str | Path,
    dataset_id: str,
    feature_column: int,
    label: str,
    coarse_label: str,
) -> Path:
    genes = np.asarray(read_features(triple.features, feature_column), dtype=str)
    barcodes = np.asarray(read_first_column(triple.barcodes), dtype=str)
    matrix = read_matrix(triple.matrix)
    if matrix.shape == (len(genes), len(barcodes)):
        matrix = matrix.T.tocsr()
    elif matrix.shape != (len(barcodes), len(genes)):
        raise ValueError(
            f"{triple.sample_id} matrix shape {matrix.shape} is incompatible with "
            f"{len(barcodes)} barcodes and {len(genes)} genes"
        )

    meta = parse_sample(triple.sample_id)
    output_path = Path(output_dir) / f"{triple.sample_id}.npz"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_name(f".{output_path.name}.tmp")
    n_cells = matrix.shape[0]
    with tmp_path.open("wb") as handle:
        np.savez_compressed(
            handle,
            X_data=matrix.data.astype(np.float32),
            X_indices=matrix.indices.astype(np.int32),
            X_indptr=matrix.indptr.astype(np.int32),
            X_shape=np.asarray(matrix.shape, dtype=np.int64),
            genes=genes,
            cell_id=np.asarray([f"{triple.sample_id}:{barcode}" for barcode in barcodes], dtype=str),
            sample_id=np.repeat(triple.sample_id, n_cells).astype(str),
            dataset_id=np.repeat(dataset_id, n_cells).astype(str),
            species=np.repeat(meta["species"], n_cells).astype(str),
            species_code=np.repeat(meta["species_code"], n_cells).astype(str),
            tissue=np.repeat(meta["tissue"], n_cells).astype(str),
            treatment=np.repeat(meta["treatment"], n_cells).astype(str),
            batch=np.repeat(meta["replicate"], n_cells).astype(str),
            cell_type=np.repeat(label, n_cells).astype(str),
            cell_type_coarse=np.repeat(coarse_label, n_cells).astype(str),
        )
    tmp_path.replace(output_path)
    return output_path


def write_manifest(
    paths: Iterable[Path],
    output: str | Path,
    dataset_id: str,
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
            sample_meta = parse_sample(path.stem)
            writer.writerow(
                [
                    str(path),
                    dataset_id,
                    sample_meta["species"],
                    sample_meta["tissue"],
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
    feature_column: int = 0,
    sample_regex: str | None = None,
    max_samples: int | None = None,
    min_samples: int = 0,
    require_valid_gzip: bool = False,
    manifest_output: str | Path | None = None,
    label: str = "unannotated_root",
    coarse_label: str = "unannotated_root",
) -> list[Path]:
    triples = discover_triples(input_dir, require_valid_gzip=require_valid_gzip)
    if sample_regex:
        pattern = re.compile(sample_regex)
        triples = [triple for triple in triples if pattern.search(triple.sample_id)]
    if max_samples is not None:
        triples = triples[:max_samples]
    if len(triples) < min_samples:
        raise ValueError(f"found {len(triples)} complete 10x triples, need at least {min_samples}")
    paths = [
        write_sparse_npz(
            triple,
            output_dir,
            dataset_id=dataset_id,
            feature_column=feature_column,
            label=label,
            coarse_label=coarse_label,
        )
        for triple in triples
    ]
    if manifest_output:
        write_manifest(paths, manifest_output, dataset_id)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert GEO 10x triples to SnowCell sparse NPZ")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--feature-column", type=int, default=0)
    parser.add_argument("--sample-regex")
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--min-samples", type=int, default=0)
    parser.add_argument("--require-valid-gzip", action="store_true")
    parser.add_argument("--manifest-output")
    parser.add_argument("--label", default="unannotated_root")
    parser.add_argument("--coarse-label", default="unannotated_root")
    args = parser.parse_args()
    for path in convert_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        dataset_id=args.dataset_id,
        feature_column=args.feature_column,
        sample_regex=args.sample_regex,
        max_samples=args.max_samples,
        min_samples=args.min_samples,
        require_valid_gzip=args.require_valid_gzip,
        manifest_output=args.manifest_output,
        label=args.label,
        coarse_label=args.coarse_label,
    ):
        print(path)


if __name__ == "__main__":
    main()
