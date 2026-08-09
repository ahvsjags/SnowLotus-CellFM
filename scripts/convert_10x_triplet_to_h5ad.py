"""Convert one public 10x triplet into an H5AD source for strict replay."""

from __future__ import annotations

import argparse
import gzip
from pathlib import Path

import anndata as ad
import pandas as pd
from scipy import io, sparse


def open_text(path: Path, mode: str):
    return gzip.open(path, mode, encoding="utf-8") if path.suffix == ".gz" else path.open(mode, encoding="utf-8")


def open_binary(path: Path):
    return gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--barcodes", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset-id", default="")
    parser.add_argument("--sample-id", default="")
    args = parser.parse_args()
    with open_text(args.barcodes, "rt") as handle:
        barcodes = [line.strip() for line in handle if line.strip()]
    with open_text(args.features, "rt") as handle:
        features = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
    feature_ids = [row[0] for row in features]
    feature_names = [row[1] if len(row) > 1 and row[1] else row[0] for row in features]
    matrix = sparse.csr_matrix(io.mmread(open_binary(args.matrix)).T)
    obs = pd.DataFrame(index=pd.Index(barcodes, dtype=str))
    if args.dataset_id:
        obs["dataset_id"] = args.dataset_id
    if args.sample_id:
        obs["sample_id"] = args.sample_id
    var = pd.DataFrame({"gene_id": feature_ids}, index=pd.Index(feature_names, dtype=str))
    result = ad.AnnData(X=matrix, obs=obs, var=var)
    result.var_names_make_unique()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.write_h5ad(args.output, compression="gzip")
    print(f"wrote {args.output} cells={result.n_obs} genes={result.n_vars}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
