from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import sparse

from .config import DataConfig
from .data import MatrixData, load_matrix


@dataclass(frozen=True)
class CorpusItem:
    path: str
    dataset_id: str
    species: str
    tissue: str = "unknown_tissue"
    layer: str | None = None
    label_key: str = "cell_type"
    coarse_label_key: str = "cell_type_coarse"
    sample_key: str = "sample_id"


def read_corpus_manifest(path: str | Path) -> list[CorpusItem]:
    table = pd.read_csv(path, sep="\t", dtype=str).fillna("")
    required = {"path", "dataset_id", "species"}
    missing = required - set(table.columns)
    if missing:
        raise ValueError(f"corpus manifest missing columns: {sorted(missing)}")
    items: list[CorpusItem] = []
    for record in table.to_dict(orient="records"):
        items.append(
            CorpusItem(
                path=record["path"],
                dataset_id=record["dataset_id"],
                species=record["species"],
                tissue=record.get("tissue", "") or "unknown_tissue",
                layer=record.get("layer", "") or None,
                label_key=record.get("label_key", "") or "cell_type",
                coarse_label_key=record.get("coarse_label_key", "") or "cell_type_coarse",
                sample_key=record.get("sample_key", "") or "sample_id",
            )
        )
    return items


def _string_array(values: Iterable[object]) -> np.ndarray:
    return np.asarray([str(value) for value in values], dtype=str)


def _load_item(item: CorpusItem) -> MatrixData:
    config = DataConfig(
        path=item.path,
        layer=item.layer,
        label_key=item.label_key,
        coarse_label_key=item.coarse_label_key,
        group_key=item.sample_key,
        min_genes_per_cell=1,
        min_cells_per_gene=1,
        validation_fraction=0.1,
        test_fraction=0.1,
    )
    matrix = load_matrix(item.path, config)
    obs = {key: values.copy() for key, values in matrix.obs.items()}
    obs.setdefault("cell_type", obs.get(item.label_key, np.repeat("unknown", matrix.n_cells)))
    obs.setdefault(
        "cell_type_coarse",
        obs.get(item.coarse_label_key, np.repeat("unknown", matrix.n_cells)),
    )
    obs.setdefault("sample_id", obs.get(item.sample_key, np.arange(matrix.n_cells).astype(str)))
    obs["dataset_id"] = np.repeat(item.dataset_id, matrix.n_cells)
    obs["species"] = np.repeat(item.species, matrix.n_cells)
    obs["tissue"] = np.repeat(item.tissue, matrix.n_cells)
    obs["cell_id"] = _string_array(
        [
            f"{item.dataset_id}:{cell_id}"
            for cell_id in obs.get("cell_id", np.arange(matrix.n_cells).astype(str))
        ]
    )
    return MatrixData(X=matrix.X, genes=matrix.genes, obs=obs)


def _as_csr(matrix: np.ndarray | sparse.spmatrix) -> sparse.csr_matrix:
    if sparse.issparse(matrix):
        return matrix.tocsr().astype(np.float32)
    return sparse.csr_matrix(np.asarray(matrix, dtype=np.float32))


def merge_matrices(items: list[CorpusItem]) -> MatrixData:
    loaded = [_load_item(item) for item in items]
    if not loaded:
        raise ValueError("no corpus items")
    all_genes = sorted({str(gene) for matrix in loaded for gene in matrix.genes})
    gene_index = {gene: index for index, gene in enumerate(all_genes)}
    blocks = []
    merged_obs: dict[str, list[np.ndarray]] = {}
    obs_keys = sorted({key for matrix in loaded for key in matrix.obs})

    for matrix in loaded:
        source = _as_csr(matrix.X)
        rows = np.arange(matrix.n_genes, dtype=np.int64)
        columns = np.asarray([gene_index[str(gene)] for gene in matrix.genes], dtype=np.int64)
        projector = sparse.csr_matrix(
            (np.ones(matrix.n_genes, dtype=np.float32), (rows, columns)),
            shape=(matrix.n_genes, len(all_genes)),
        )
        blocks.append((source @ projector).tocsr())
        for key in obs_keys:
            values = matrix.obs.get(key, np.repeat("", matrix.n_cells))
            merged_obs.setdefault(key, []).append(_string_array(values))

    return MatrixData(
        X=sparse.vstack(blocks, format="csr"),
        genes=np.asarray(all_genes, dtype=str),
        obs={key: np.concatenate(chunks) for key, chunks in merged_obs.items()},
    )


def write_h5ad(matrix: MatrixData, output: str | Path) -> Path:
    try:
        import anndata as ad
    except ImportError as exc:
        raise ImportError("writing h5ad requires: pip install -e .[pipeline]") from exc

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    obs = pd.DataFrame(matrix.obs)
    obs.index = obs["cell_id"] if "cell_id" in obs else [f"cell_{i}" for i in range(matrix.n_cells)]
    var = pd.DataFrame(index=_string_array(matrix.genes))
    adata = ad.AnnData(X=_as_csr(matrix.X), obs=obs, var=var)
    adata.write_h5ad(output_path, compression="gzip")
    return output_path


def build_corpus(manifest: str | Path, output: str | Path) -> Path:
    items = read_corpus_manifest(manifest)
    matrix = merge_matrices(items)
    return write_h5ad(matrix, output)
