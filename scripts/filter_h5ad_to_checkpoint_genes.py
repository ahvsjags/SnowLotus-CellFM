from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np

from snowcell.artifacts import load_checkpoint


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter a backed H5AD to a checkpoint-compatible gene space")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()

    checkpoint = load_checkpoint(args.checkpoint, map_location="cpu")
    checkpoint_genes = set(str(gene) for gene in checkpoint["gene_vocab"][4:])
    source = ad.read_h5ad(args.input.as_posix(), backed="r")
    try:
        source_genes = np.asarray(source.var_names.astype(str), dtype=str)
        keep = np.flatnonzero(np.isin(source_genes, sorted(checkpoint_genes)))
        if not len(keep):
            raise ValueError("no checkpoint genes found in input H5AD")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        subset = source[:, keep].to_memory()
        subset.write_h5ad(args.output.as_posix(), compression="gzip")
        print(
            f"wrote {args.output} cells={subset.n_obs} genes={subset.n_vars} "
            f"checkpoint_genes={len(checkpoint_genes)}",
            flush=True,
        )
    finally:
        if getattr(source, "file", None) is not None:
            source.file.close()


if __name__ == "__main__":
    main()
