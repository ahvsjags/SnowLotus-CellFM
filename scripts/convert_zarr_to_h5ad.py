#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad


parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument("destination")
args = parser.parse_args()

source = Path(args.source)
destination = Path(args.destination)
adata = ad.read_zarr(source.as_posix())
destination.parent.mkdir(parents=True, exist_ok=True)
adata.write_h5ad(destination.as_posix(), compression="gzip")
print(f"wrote {destination} shape={adata.shape} bytes={destination.stat().st_size}")
