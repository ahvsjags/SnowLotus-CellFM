from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize a deterministic backed AnnData benchmark subset")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-cells-per-dataset", type=int, default=256)
    parser.add_argument("--dataset-key", default="dataset_id")
    parser.add_argument("--seed", type=int, default=20260729)
    args = parser.parse_args()

    if args.max_cells_per_dataset < 1:
        raise ValueError("--max-cells-per-dataset must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    source = ad.read_h5ad(args.input.as_posix(), backed="r")
    try:
        if args.dataset_key in source.obs:
            groups = np.asarray(source.obs[args.dataset_key].astype(str).to_numpy(), dtype=str)
        else:
            groups = np.repeat("unknown_dataset", source.n_obs)
        rng = np.random.default_rng(args.seed)
        selected: list[np.ndarray] = []
        for group in sorted(set(groups.tolist())):
            indices = np.flatnonzero(groups == group)
            if len(indices) > args.max_cells_per_dataset:
                indices = rng.choice(indices, size=args.max_cells_per_dataset, replace=False)
            selected.append(np.asarray(indices, dtype=np.int64))
        selected_indices = np.sort(np.concatenate(selected)) if selected else np.empty(0, dtype=np.int64)
        if not len(selected_indices):
            raise ValueError("no cells selected")
        subset = source[selected_indices].to_memory()
        subset.write_h5ad(args.output.as_posix(), compression="gzip")
        print(
            f"wrote {args.output} cells={subset.n_obs} genes={subset.n_vars} "
            f"datasets={len(set(groups[selected_indices].tolist()))}",
            flush=True,
        )
    finally:
        if getattr(source, "file", None) is not None:
            source.file.close()


if __name__ == "__main__":
    main()
