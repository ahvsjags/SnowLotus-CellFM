#!/usr/bin/env python3
"""Filter a CSR H5AD gene vocabulary without repeated column slicing."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import anndata as ad
import h5py
import numpy as np


def count_detected_cells(source: Path, chunk_size: int) -> tuple[np.ndarray, int, int]:
    with h5py.File(source, "r") as handle:
        indices = handle["X"]["indices"]
        n_obs = int(handle["obs"]["_index"]["values"].shape[0])
        n_vars = int(handle["var"]["_index"]["values"].shape[0])
        detected = np.zeros(n_vars, dtype=np.int64)
        for start in range(0, int(indices.shape[0]), chunk_size):
            stop = min(start + chunk_size, int(indices.shape[0]))
            block = np.asarray(indices[start:stop], dtype=np.int64)
            detected += np.bincount(block, minlength=n_vars)
            if start == 0 or stop == int(indices.shape[0]) or stop % (chunk_size * 8) == 0:
                print(f"counted_indices={stop}/{indices.shape[0]}", flush=True)
    return detected, n_obs, n_vars


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--max-genes", type=int, default=60000)
    parser.add_argument("--chunk-size", type=int, default=16_000_000)
    args = parser.parse_args()

    detected, n_obs, n_vars = count_detected_cells(args.source, args.chunk_size)
    keep_count = min(args.max_genes, n_vars)
    selected = np.argsort(-detected, kind="stable")[:keep_count]
    selected.sort()
    print(f"selected_genes={keep_count} cells={n_obs} source_genes={n_vars}", flush=True)

    backed = ad.read_h5ad(args.source.as_posix(), backed="r")
    try:
        subset = backed[:, selected].to_memory()
    finally:
        backed.file.close()
    subset.var["detected_cells"] = detected[selected]
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.destination.with_suffix(args.destination.suffix + ".part")
    if temporary.exists():
        temporary.unlink()
    subset.write_h5ad(temporary.as_posix(), compression="gzip")
    os.replace(temporary, args.destination)
    print(
        f"wrote {args.destination} shape={subset.shape} selected={keep_count} "
        f"bytes={args.destination.stat().st_size}",
        flush=True,
    )


if __name__ == "__main__":
    main()
