from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import sparse

from snowcell.config import ExperimentConfig
from snowcell.data import prepare_data


SPLIT_ORDER = ("train", "validation", "test")
STRING_DTYPE = h5py.string_dtype(encoding="utf-8")


def normalise_splits(values: list[str] | None) -> list[str]:
    requested = values or ["all"]
    if "all" in requested:
        return list(SPLIT_ORDER)
    splits: list[str] = []
    for value in requested:
        if value not in SPLIT_ORDER:
            raise ValueError(f"unknown split: {value}")
        if value not in splits:
            splits.append(value)
    return splits


def select_cells(
    prepared: Any,
    split_names: list[str],
    max_cells: int | None,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    index_parts: list[np.ndarray] = []
    split_parts: list[np.ndarray] = []
    for split_name in split_names:
        indices = np.asarray(getattr(prepared.split, split_name), dtype=np.int64)
        index_parts.append(indices)
        split_parts.append(np.repeat(split_name, len(indices)).astype(str))
    indices = np.concatenate(index_parts) if index_parts else np.asarray([], dtype=np.int64)
    split_labels = np.concatenate(split_parts) if split_parts else np.asarray([], dtype=str)
    if max_cells is not None and max_cells > 0 and len(indices) > max_cells:
        rng = np.random.default_rng(seed)
        positions = np.sort(rng.choice(np.arange(len(indices)), size=max_cells, replace=False))
        indices = indices[positions]
        split_labels = split_labels[positions]
    return indices, split_labels


def obs_values(obs: dict[str, np.ndarray], key: str, indices: np.ndarray, default: str) -> np.ndarray:
    values = obs.get(key)
    if values is None:
        return np.repeat(default, len(indices)).astype(str)
    selected = np.asarray(values)[indices].astype(str)
    selected[selected == ""] = default
    selected[selected == "nan"] = default
    return selected


def unique_cell_names(raw_values: np.ndarray) -> np.ndarray:
    counts: dict[str, int] = {}
    names: list[str] = []
    for index, value in enumerate(raw_values):
        base = str(value).strip() or f"snowcell_cell_{index:08d}"
        count = counts.get(base, 0)
        counts[base] = count + 1
        names.append(base if count == 0 else f"{base}__{count}")
    return np.asarray(names, dtype=str)


def dense_matrix_slice(matrix: Any, indices: np.ndarray) -> np.ndarray:
    selected = matrix[indices]
    if sparse.issparse(selected):
        return np.asarray(selected.toarray(), dtype=np.float32)
    return np.asarray(selected, dtype=np.float32)


def load_gene_vocab(path: str | Path | None) -> set[str] | None:
    if path is None:
        return None
    vocab_path = Path(path)
    if not vocab_path.exists():
        return None
    payload = json.loads(vocab_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return {str(key) for key in payload}
    if isinstance(payload, list):
        return {str(item) for item in payload}
    raise ValueError(f"unsupported gene vocab JSON structure: {vocab_path}")


def write_h5(path: Path, matrix: np.ndarray, cell_names: np.ndarray, genes: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as handle:
        group = handle.create_group("count")
        group.create_dataset("data", data=matrix, compression="gzip", compression_opts=4)
        group.create_dataset("cell_names", data=cell_names.astype(STRING_DTYPE))
        group.create_dataset("gene_names", data=genes.astype(str).astype(STRING_DTYPE))


def write_meta(
    path: Path,
    prepared: Any,
    indices: np.ndarray,
    split_labels: np.ndarray,
    cell_names: np.ndarray,
    config: ExperimentConfig,
) -> pd.DataFrame:
    obs = prepared.matrix.obs
    data_config = config.data
    frame = pd.DataFrame(
        {
            "cell": cell_names,
            "orig.ident": obs_values(obs, data_config.batch_key, indices, "batch0"),
            "celltype": obs_values(obs, data_config.label_key, indices, "Unknown"),
            "coarse_celltype": obs_values(obs, data_config.coarse_label_key, indices, "Unknown"),
            "sample_id": obs_values(obs, data_config.group_key, indices, "sample0"),
            "species": obs_values(obs, data_config.species_key, indices, "unknown_species"),
            "tissue": obs_values(obs, data_config.tissue_key, indices, "unknown_tissue"),
            "snowcell_split": split_labels,
            "matrix_index": indices.astype(int),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return frame


def export_scplantllm_input(
    config_path: str | Path,
    output_dir: str | Path,
    split_names: list[str] | None = None,
    max_cells: int | None = 20_000,
    seed: int | None = None,
    gene_vocab_path: str | Path | None = None,
    prefix: str = "snowcell_public_sprint",
) -> dict[str, Any]:
    config = ExperimentConfig.load(config_path)
    prepared = prepare_data(config.data, seed=config.train.seed, require_labels=True)
    splits = normalise_splits(split_names)
    selection_seed = config.train.seed if seed is None else seed
    indices, split_labels = select_cells(prepared, splits, max_cells=max_cells, seed=selection_seed)
    output = Path(output_dir)
    h5_path = output / f"{prefix}.h5"
    meta_path = output / f"{prefix}.meta.csv"

    raw_cell_ids = obs_values(
        prepared.matrix.obs,
        config.data.cell_id_key,
        indices,
        "snowcell_cell",
    )
    cell_names = unique_cell_names(raw_cell_ids)
    matrix = dense_matrix_slice(prepared.matrix.X, indices)
    genes = np.asarray(prepared.matrix.genes, dtype=str)
    write_h5(h5_path, matrix, cell_names, genes)
    meta = write_meta(meta_path, prepared, indices, split_labels, cell_names, config)

    scplantllm_gene_vocab = load_gene_vocab(gene_vocab_path)
    overlap_count = None
    overlap_rate = None
    if scplantllm_gene_vocab is not None:
        overlap_count = sum(1 for gene in genes if str(gene) in scplantllm_gene_vocab)
        overlap_rate = overlap_count / max(len(genes), 1)

    split_counts = {
        split_name: int(np.sum(split_labels == split_name))
        for split_name in splits
    }
    label_counts = {
        str(key): int(value)
        for key, value in meta["celltype"].value_counts().sort_index().items()
    }
    summary: dict[str, Any] = {
        "method": "scplantllm_input_export",
        "config": str(config_path),
        "output_dir": str(output),
        "h5_path": str(h5_path),
        "metadata_csv": str(meta_path),
        "selected_splits": splits,
        "requested_max_cells": max_cells,
        "selected_cells": int(len(indices)),
        "retained_genes": int(len(genes)),
        "split_counts": split_counts,
        "label_counts": label_counts,
        "expression_provenance": {
            "source": "SnowCell prepare_data output",
            "normalize_total": float(config.data.normalize_total),
            "log1p": bool(config.data.log1p),
            "min_genes_per_cell": int(config.data.min_genes_per_cell),
            "min_cells_per_gene": int(config.data.min_cells_per_gene),
        },
        "scplantllm_format": {
            "h5_group": "count",
            "required_datasets": ["count/data", "count/cell_names", "count/gene_names"],
            "metadata_file_suffix": "meta.csv",
            "metadata_required_columns": ["cell", "orig.ident", "celltype"],
        },
        "scplantllm_gene_vocab": {
            "path": str(gene_vocab_path) if gene_vocab_path else None,
            "available": scplantllm_gene_vocab is not None,
            "overlap_count": overlap_count,
            "overlap_rate": overlap_rate,
        },
    }
    summary_path = output / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export SnowCell data in scPlantLLM-compatible HDF5/meta format")
    parser.add_argument("--config", default="configs/foundation_5090_public_sprint.yaml")
    parser.add_argument("--output-dir", default="outputs/external_benchmarks/scplantllm_public_sprint_input")
    parser.add_argument("--split", action="append", choices=["all", *SPLIT_ORDER], default=None)
    parser.add_argument("--max-cells", type=int, default=20_000, help="0 or negative exports all selected cells")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--gene-vocab", default="external/scPlantLLM/gene_vocab.json")
    parser.add_argument("--prefix", default="snowcell_public_sprint")
    args = parser.parse_args()
    max_cells = args.max_cells if args.max_cells > 0 else None
    summary = export_scplantllm_input(
        config_path=args.config,
        output_dir=args.output_dir,
        split_names=args.split,
        max_cells=max_cells,
        seed=args.seed,
        gene_vocab_path=args.gene_vocab,
        prefix=args.prefix,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
