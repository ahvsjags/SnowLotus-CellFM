from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import io, sparse

from snowcell.config import ExperimentConfig
from snowcell.data import prepare_data


OBS_KEYS = ["cell_type", "cell_type_coarse", "sample_id", "species", "tissue", "cell_id", "dataset_id"]


def as_csr(matrix: Any) -> sparse.csr_matrix:
    return matrix.tocsr() if sparse.issparse(matrix) else sparse.csr_matrix(matrix)


def split_indices(prepared: Any, split_name: str) -> Any:
    if split_name not in {"train", "validation", "test"}:
        raise ValueError(f"unknown split: {split_name}")
    return getattr(prepared.split, split_name)


def metadata_frame(prepared: Any, indices: Any, split_name: str) -> pd.DataFrame:
    obs = prepared.matrix.obs
    frame = pd.DataFrame(
        {
            key: obs.get(key, np.repeat("", prepared.matrix.n_cells))[indices]
            for key in OBS_KEYS
        }
    )
    frame.insert(0, "matrix_index", indices)
    frame.insert(1, "split", split_name)
    if "cell_id" not in frame or frame["cell_id"].eq("").all():
        frame["cell_id"] = [f"{split_name}_cell_{index}" for index in range(len(indices))]
    return frame


def export_split(config_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    config = ExperimentConfig.load(config_path)
    prepared = prepare_data(config.data, seed=config.train.seed, require_labels=True)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    genes = [str(gene) for gene in prepared.matrix.genes]
    (output / "genes.tsv").write_text("\n".join(genes) + "\n", encoding="utf-8")
    X = as_csr(prepared.matrix.X)
    summary: dict[str, Any] = {
        "config": str(config_path),
        "output_dir": str(output),
        "n_genes": len(genes),
        "splits": {},
    }
    for split_name in ["train", "validation", "test"]:
        indices = split_indices(prepared, split_name)
        matrix_path = output / f"{split_name}.mtx"
        meta_path = output / f"{split_name}_metadata.tsv"
        io.mmwrite(matrix_path, X[indices].T.tocoo())
        meta = metadata_frame(prepared, indices, split_name)
        meta.to_csv(meta_path, sep="\t", index=False)
        summary["splits"][split_name] = {
            "cells": int(len(indices)),
            "matrix": str(matrix_path),
            "metadata": str(meta_path),
        }
    summary_path = output / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a SnowCell config split for Seurat label transfer")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    summary = export_split(args.config, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
