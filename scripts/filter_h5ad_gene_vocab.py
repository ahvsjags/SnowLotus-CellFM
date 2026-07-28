#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument("destination")
parser.add_argument("--max-genes", type=int, default=60000)
parser.add_argument("--chunk-size", type=int, default=2048)
args = parser.parse_args()

source = Path(args.source)
destination = Path(args.destination)
adata = ad.read_h5ad(source.as_posix(), backed="r")
detected = np.zeros(adata.n_vars, dtype=np.int64)
for start in range(0, adata.n_vars, args.chunk_size):
    stop = min(start + args.chunk_size, adata.n_vars)
    block = adata.X[:, start:stop]
    if hasattr(block, "to_memory"):
        block = block.to_memory()
    detected[start:stop] = np.asarray(block.getnnz(axis=0)).reshape(-1)
keep_count = min(args.max_genes, adata.n_vars)
selected = np.argsort(-detected, kind="stable")[:keep_count]
selected.sort()
subset = adata[:, selected].to_memory()
subset.var["detected_cells"] = detected[selected]
destination.parent.mkdir(parents=True, exist_ok=True)
subset.write_h5ad(destination.as_posix(), compression="gzip")
print(f"wrote {destination} shape={subset.shape} selected={keep_count} bytes={destination.stat().st_size}")
