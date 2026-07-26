#!/usr/bin/env python3
"""Merge sparse SnowCell NPZ files while preserving cell-level metadata."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from snowcell.corpus import merge_matrices, read_corpus_manifest


def write_npz_corpus(manifest: str | Path, output: str | Path) -> Path:
    matrix = merge_matrices(read_corpus_manifest(manifest))
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_name(f".{output_path.name}.tmp")
    payload: dict[str, np.ndarray] = {
        "X_data": matrix.X.data.astype(np.float32),
        "X_indices": matrix.X.indices.astype(np.int32),
        "X_indptr": matrix.X.indptr.astype(np.int32),
        "X_shape": np.asarray(matrix.X.shape, dtype=np.int64),
        "genes": np.asarray(matrix.genes, dtype=str),
    }
    payload.update({key: np.asarray(values, dtype=str) for key, values in matrix.obs.items()})
    with tmp_path.open("wb") as handle:
        np.savez_compressed(handle, **payload)
    tmp_path.replace(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge SnowCell sparse NPZ corpus files")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = write_npz_corpus(args.manifest, args.output)
    print(output)


if __name__ == "__main__":
    main()
