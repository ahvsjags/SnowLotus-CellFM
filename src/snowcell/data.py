from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sklearn.model_selection import GroupShuffleSplit
from torch.utils.data import Dataset

from .config import DataConfig
from .vocab import LabelVocabulary, Vocabulary


ArrayLike = np.ndarray | sparse.spmatrix


@dataclass
class MatrixData:
    X: ArrayLike
    genes: np.ndarray
    obs: dict[str, np.ndarray]

    @property
    def n_cells(self) -> int:
        return int(self.X.shape[0])

    @property
    def n_genes(self) -> int:
        return int(self.X.shape[1])

    def subset_cells(self, indices: np.ndarray) -> "MatrixData":
        return MatrixData(
            X=self.X[indices],
            genes=self.genes.copy(),
            obs={key: values[indices] for key, values in self.obs.items()},
        )


@dataclass(frozen=True)
class SplitIndices:
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray


@dataclass
class PreparedData:
    matrix: MatrixData
    split: SplitIndices
    gene_vocab: Vocabulary
    fine_vocab: LabelVocabulary | None
    coarse_vocab: LabelVocabulary | None
    species_vocab: LabelVocabulary
    tissue_vocab: LabelVocabulary
    fine_to_coarse: np.ndarray | None
    preprocessing_stats: dict[str, Any]


@dataclass
class InferenceData:
    matrix: MatrixData
    indices: np.ndarray
    gene_vocab: Vocabulary
    species_vocab: LabelVocabulary
    tissue_vocab: LabelVocabulary
    preprocessing_stats: dict[str, Any]


def _string_array(values: Iterable[Any]) -> np.ndarray:
    return np.asarray([str(value) for value in values], dtype=str)


def load_matrix(path: str | Path, config: DataConfig) -> MatrixData:
    data_path = Path(path)
    suffix = data_path.suffix.lower()
    if suffix == ".npz":
        return _load_npz_sparse_aware(data_path)
    if suffix == ".h5ad":
        return _load_h5ad(data_path, config)
    raise ValueError(f"不支持的数据格式 {suffix}；当前支持 .npz 和 .h5ad")


def _load_npz(path: Path) -> MatrixData:
    with np.load(path, allow_pickle=False) as archive:
        if "X" not in archive or "genes" not in archive:
            raise ValueError("NPZ 至少需要 X 和 genes 两个数组")
        X = np.asarray(archive["X"], dtype=np.float32)
        genes = _string_array(archive["genes"])
        obs = {
            key: _string_array(archive[key])
            for key in archive.files
            if key not in {"X", "genes"}
        }
    if X.ndim != 2:
        raise ValueError(f"X 必须是二维矩阵，当前 shape={X.shape}")
    if X.shape[1] != len(genes):
        raise ValueError("X 的基因维与 genes 长度不一致")
    for key, values in obs.items():
        if len(values) != X.shape[0]:
            raise ValueError(f"obs[{key}] 长度与细胞数不一致")
    return MatrixData(X=X, genes=genes, obs=obs)


def _load_npz_sparse_aware(path: Path) -> MatrixData:
    with np.load(path, allow_pickle=False) as archive:
        if "genes" not in archive:
            raise ValueError("NPZ requires genes")
        if "X" in archive:
            X: ArrayLike = np.asarray(archive["X"], dtype=np.float32)
        elif {"X_data", "X_indices", "X_indptr", "X_shape"}.issubset(archive.files):
            X = sparse.csr_matrix(
                (
                    np.asarray(archive["X_data"], dtype=np.float32),
                    np.asarray(archive["X_indices"], dtype=np.int32),
                    np.asarray(archive["X_indptr"], dtype=np.int32),
                ),
                shape=tuple(np.asarray(archive["X_shape"], dtype=np.int64)),
            )
        else:
            raise ValueError("NPZ requires X or CSR arrays")
        genes = _string_array(archive["genes"])
        obs = {
            key: _string_array(archive[key])
            for key in archive.files
            if key not in {"X", "X_data", "X_indices", "X_indptr", "X_shape", "genes"}
        }
    if X.ndim != 2:
        raise ValueError(f"X must be a 2D matrix, got shape={X.shape}")
    if X.shape[1] != len(genes):
        raise ValueError("X gene dimension does not match genes")
    for key, values in obs.items():
        if len(values) != X.shape[0]:
            raise ValueError(f"obs[{key}] length does not match cell count")
    return MatrixData(X=X, genes=genes, obs=obs)


def _load_h5ad(path: Path, config: DataConfig) -> MatrixData:
    try:
        import anndata as ad
    except ImportError as exc:
        raise ImportError("读取 .h5ad 需要安装: pip install -e .[singlecell]") from exc

    adata = ad.read_h5ad(path, backed=None)
    X = adata.layers[config.layer] if config.layer else adata.X
    if sparse.issparse(X):
        X = X.tocsr().astype(np.float32)
    else:
        X = np.asarray(X, dtype=np.float32)
    genes = _string_array(adata.var_names)
    obs = {column: _string_array(adata.obs[column].values) for column in adata.obs.columns}
    obs.setdefault(config.cell_id_key, _string_array(adata.obs_names))
    return MatrixData(X=X, genes=genes, obs=obs)


def _require_obs(matrix: MatrixData, key: str, purpose: str) -> np.ndarray:
    if key not in matrix.obs:
        raise ValueError(f"数据缺少 obs['{key}']，无法用于{purpose}")
    return matrix.obs[key]


def load_ortholog_table(path: str | Path, config: DataConfig) -> dict[str, str]:
    table = pd.read_csv(path, sep="\t", dtype=str)
    required = {config.ortholog_source_column, config.ortholog_target_column}
    missing = required - set(table.columns)
    if missing:
        raise ValueError(f"同源映射表缺少列: {sorted(missing)}")
    if (
        config.ortholog_confidence_column
        and config.ortholog_confidence_column in table.columns
    ):
        confidence = pd.to_numeric(
            table[config.ortholog_confidence_column], errors="coerce"
        ).fillna(0.0)
        table = table.loc[confidence >= config.min_ortholog_confidence]
    table = table.dropna(
        subset=[config.ortholog_source_column, config.ortholog_target_column]
    )
    # 多个候选时保留表中第一项；生产数据应事先按可信度与 1:1 关系排序。
    table = table.drop_duplicates(subset=[config.ortholog_source_column], keep="first")
    return dict(
        zip(
            table[config.ortholog_source_column].astype(str),
            table[config.ortholog_target_column].astype(str),
            strict=True,
        )
    )


def collapse_by_ortholog(
    matrix: MatrixData,
    mapping: dict[str, str],
    keep_unmapped: bool = False,
) -> tuple[MatrixData, dict[str, Any]]:
    targets: list[str] = []
    kept_source_indices: list[int] = []
    for index, gene in enumerate(matrix.genes):
        gene_text = str(gene)
        target = mapping.get(gene_text)
        if target is None and keep_unmapped:
            target = gene_text
        if target:
            kept_source_indices.append(index)
            targets.append(str(target))
    if not kept_source_indices:
        raise ValueError("同源映射后没有保留任何基因，请检查 gene ID 命名空间")

    unique_targets = sorted(set(targets))
    target_index = {gene: index for index, gene in enumerate(unique_targets)}
    rows = np.arange(len(kept_source_indices), dtype=np.int64)
    columns = np.asarray([target_index[target] for target in targets], dtype=np.int64)
    projector = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.float32), (rows, columns)),
        shape=(len(rows), len(unique_targets)),
    )
    source = matrix.X[:, np.asarray(kept_source_indices)]
    if sparse.issparse(source):
        collapsed: ArrayLike = (source @ projector).tocsr()
    else:
        collapsed = np.asarray(source @ projector, dtype=np.float32)
    stats = {
        "source_gene_count": int(matrix.n_genes),
        "mapped_source_gene_count": int(len(kept_source_indices)),
        "target_gene_count": int(len(unique_targets)),
        "mapping_rate": float(len(kept_source_indices) / max(matrix.n_genes, 1)),
    }
    return (
        MatrixData(
            X=collapsed,
            genes=np.asarray(unique_targets, dtype=str),
            obs={key: values.copy() for key, values in matrix.obs.items()},
        ),
        stats,
    )


def filter_and_normalize(
    matrix: MatrixData,
    config: DataConfig,
) -> tuple[MatrixData, dict[str, Any]]:
    X = matrix.X
    if np.any(X.data < 0) if sparse.issparse(X) else np.any(X < 0):
        raise ValueError("表达矩阵包含负值；请输入原始 counts 或非负表达量")

    if sparse.issparse(X):
        detected_per_cell = np.asarray(X.getnnz(axis=1)).ravel()
        detected_per_gene = np.asarray(X.getnnz(axis=0)).ravel()
    else:
        detected_per_cell = np.count_nonzero(X > 0, axis=1)
        detected_per_gene = np.count_nonzero(X > 0, axis=0)

    cell_mask = detected_per_cell >= config.min_genes_per_cell
    gene_mask = detected_per_gene >= config.min_cells_per_gene
    if not np.any(cell_mask):
        raise ValueError("质控后没有细胞；请降低 min_genes_per_cell 或检查矩阵")
    if not np.any(gene_mask):
        raise ValueError("质控后没有基因；请降低 min_cells_per_gene 或检查矩阵")

    cell_indices = np.flatnonzero(cell_mask)
    gene_indices = np.flatnonzero(gene_mask)
    X = X[cell_indices][:, gene_indices]
    genes = matrix.genes[gene_indices]
    obs = {key: values[cell_indices] for key, values in matrix.obs.items()}

    library_size = np.asarray(X.sum(axis=1)).ravel().astype(np.float64)
    nonzero = library_size > 0
    if not np.all(nonzero):
        keep = np.flatnonzero(nonzero)
        X = X[keep]
        obs = {key: values[keep] for key, values in obs.items()}
        library_size = library_size[keep]
    scale = config.normalize_total / np.maximum(library_size, 1.0)
    if sparse.issparse(X):
        X = sparse.diags(scale.astype(np.float32)) @ X
        X = X.tocsr().astype(np.float32)
        if config.log1p:
            X.data = np.log1p(X.data)
    else:
        X = np.asarray(X, dtype=np.float32) * scale[:, None].astype(np.float32)
        if config.log1p:
            X = np.log1p(X)

    stats = {
        "input_cells": int(matrix.n_cells),
        "input_genes": int(matrix.n_genes),
        "retained_cells": int(X.shape[0]),
        "retained_genes": int(X.shape[1]),
        "median_library_size_before_normalization": float(np.median(library_size)),
        "normalize_total": float(config.normalize_total),
        "log1p": bool(config.log1p),
    }
    return MatrixData(X=X, genes=genes, obs=obs), stats


def group_split(
    groups: np.ndarray,
    validation_fraction: float,
    test_fraction: float,
    seed: int,
) -> SplitIndices:
    groups = _string_array(groups)
    if len(np.unique(groups)) < 3:
        raise ValueError("按样本拆分至少需要 3 个不同 group；请提供 sample_id/donor/batch")
    all_indices = np.arange(len(groups))
    outer = GroupShuffleSplit(n_splits=1, test_size=test_fraction, random_state=seed)
    train_val_indices, test_indices = next(outer.split(all_indices, groups=groups))

    relative_validation = validation_fraction / (1.0 - test_fraction)
    inner = GroupShuffleSplit(
        n_splits=1,
        test_size=relative_validation,
        random_state=seed + 1,
    )
    train_relative, validation_relative = next(
        inner.split(train_val_indices, groups=groups[train_val_indices])
    )
    train_indices = train_val_indices[train_relative]
    validation_indices = train_val_indices[validation_relative]
    return SplitIndices(
        train=np.sort(train_indices),
        validation=np.sort(validation_indices),
        test=np.sort(test_indices),
    )


def explicit_leaveout_split(
    leaveout_values: np.ndarray,
    group_values: np.ndarray,
    test_values: list[str],
    validation_values: list[str],
    validation_fraction: float,
    seed: int,
) -> SplitIndices:
    leaveout_values = _string_array(leaveout_values)
    group_values = _string_array(group_values)
    requested_test = {str(value) for value in test_values}
    requested_validation = {str(value) for value in validation_values}
    observed = set(leaveout_values.tolist())
    missing = (requested_test | requested_validation) - observed
    if missing:
        raise ValueError(f"leaveout values not present in data: {sorted(missing)}")

    test_mask = np.isin(leaveout_values, list(requested_test))
    validation_mask = np.isin(leaveout_values, list(requested_validation))
    if not np.any(test_mask):
        raise ValueError("explicit_leaveout produced an empty test split")
    if validation_values and not np.any(validation_mask):
        raise ValueError("explicit_leaveout produced an empty validation split")

    train_mask = ~(test_mask | validation_mask)
    if not np.any(train_mask):
        raise ValueError("explicit_leaveout produced an empty train split")

    if not validation_values:
        train_candidates = np.flatnonzero(train_mask)
        candidate_groups = group_values[train_candidates]
        if len(np.unique(candidate_groups)) < 2:
            raise ValueError(
                "explicit_leaveout without validation values requires at least 2 remaining groups"
            )
        splitter = GroupShuffleSplit(
            n_splits=1,
            test_size=validation_fraction,
            random_state=seed + 1,
        )
        train_relative, validation_relative = next(
            splitter.split(train_candidates, groups=candidate_groups)
        )
        train_indices = train_candidates[train_relative]
        validation_indices = train_candidates[validation_relative]
    else:
        train_indices = np.flatnonzero(train_mask)
        validation_indices = np.flatnonzero(validation_mask)

    return SplitIndices(
        train=np.sort(train_indices),
        validation=np.sort(validation_indices),
        test=np.sort(np.flatnonzero(test_mask)),
    )


def _build_fine_to_coarse(
    fine_labels: np.ndarray,
    coarse_labels: np.ndarray,
    fine_vocab: LabelVocabulary,
    coarse_vocab: LabelVocabulary,
) -> tuple[np.ndarray, dict[str, list[str]]]:
    mapping = np.full(len(fine_vocab), -1, dtype=np.int64)
    fine_lookup = fine_vocab.stoi
    coarse_lookup = coarse_vocab.stoi
    observed: dict[int, set[int]] = {}
    for fine, coarse in zip(fine_labels, coarse_labels, strict=True):
        fine_id = fine_lookup[str(fine)]
        coarse_id = coarse_lookup[str(coarse)]
        observed.setdefault(fine_id, set()).add(coarse_id)

    conflicts: dict[str, list[str]] = {}
    for fine_id, coarse_ids in observed.items():
        if len(coarse_ids) == 1:
            mapping[fine_id] = next(iter(coarse_ids))
            continue
        conflicts[fine_vocab.labels[fine_id]] = sorted(
            coarse_vocab.labels[coarse_id] for coarse_id in coarse_ids
        )

    if len(observed) != len(fine_vocab):
        missing = [
            fine_vocab.labels[fine_id]
            for fine_id in range(len(fine_vocab))
            if fine_id not in observed
        ]
        raise ValueError(f"Fine labels without coarse mapping: {missing}")
    return mapping, conflicts


def preprocess_matrix(config: DataConfig) -> tuple[MatrixData, dict[str, Any]]:
    matrix = load_matrix(config.path, config)
    ortholog_stats: dict[str, Any] | None = None
    if config.ortholog_map:
        mapping = load_ortholog_table(config.ortholog_map, config)
        matrix, ortholog_stats = collapse_by_ortholog(
            matrix,
            mapping,
            keep_unmapped=config.ortholog_keep_unmapped,
        )
    matrix, qc_stats = filter_and_normalize(matrix, config)

    stats: dict[str, Any] = {"quality_control": qc_stats}
    if ortholog_stats is not None:
        stats["ortholog_mapping"] = ortholog_stats
    return matrix, stats


def prepare_data(config: DataConfig, seed: int, require_labels: bool = True) -> PreparedData:
    matrix, stats = preprocess_matrix(config)
    group_values = _require_obs(matrix, config.group_key, "无泄漏的数据集拆分")
    if config.split_strategy == "explicit_leaveout":
        leaveout_key = config.leaveout_key or config.group_key
        leaveout_values = _require_obs(matrix, leaveout_key, "显式留出拆分")
        split = explicit_leaveout_split(
            leaveout_values,
            group_values,
            test_values=config.leaveout_test_values,
            validation_values=config.leaveout_validation_values,
            validation_fraction=config.validation_fraction,
            seed=seed,
        )
    else:
        leaveout_key = None
        leaveout_values = group_values
        split = group_split(
            group_values,
            validation_fraction=config.validation_fraction,
            test_fraction=config.test_fraction,
            seed=seed,
        )
    gene_vocab = Vocabulary.build(matrix.genes)
    species = matrix.obs.get(config.species_key, np.repeat("unknown_species", matrix.n_cells))
    tissue = matrix.obs.get(config.tissue_key, np.repeat("unknown_tissue", matrix.n_cells))
    species_vocab = LabelVocabulary.build(species)
    tissue_vocab = LabelVocabulary.build(tissue)

    fine_vocab: LabelVocabulary | None = None
    coarse_vocab: LabelVocabulary | None = None
    fine_to_coarse: np.ndarray | None = None
    if require_labels:
        fine = _require_obs(matrix, config.label_key, "监督训练")
        coarse = _require_obs(matrix, config.coarse_label_key, "层级监督训练")
        fine_vocab = LabelVocabulary.build(fine)
        coarse_vocab = LabelVocabulary.build(coarse)
        fine_to_coarse, hierarchy_conflicts = _build_fine_to_coarse(
            fine, coarse, fine_vocab, coarse_vocab
        )
        stats["label_hierarchy"] = {
            "ambiguous_fine_label_count": len(hierarchy_conflicts),
            "ambiguous_fine_labels": hierarchy_conflicts,
        }

    stats["split"] = {
        "strategy": config.split_strategy,
        "leaveout_key": leaveout_key,
        "leaveout_test_values": list(config.leaveout_test_values),
        "leaveout_validation_values": list(config.leaveout_validation_values),
        "train_cells": int(len(split.train)),
        "validation_cells": int(len(split.validation)),
        "test_cells": int(len(split.test)),
        "train_groups": sorted(set(group_values[split.train].tolist())),
        "validation_groups": sorted(set(group_values[split.validation].tolist())),
        "test_groups": sorted(set(group_values[split.test].tolist())),
        "train_leaveout_values": sorted(set(leaveout_values[split.train].tolist())),
        "validation_leaveout_values": sorted(set(leaveout_values[split.validation].tolist())),
        "test_leaveout_values": sorted(set(leaveout_values[split.test].tolist())),
    }
    return PreparedData(
        matrix=matrix,
        split=split,
        gene_vocab=gene_vocab,
        fine_vocab=fine_vocab,
        coarse_vocab=coarse_vocab,
        species_vocab=species_vocab,
        tissue_vocab=tissue_vocab,
        fine_to_coarse=fine_to_coarse,
        preprocessing_stats=stats,
    )


def prepare_inference_data(
    config: DataConfig,
    gene_vocab: Vocabulary,
    species_vocab: LabelVocabulary,
    tissue_vocab: LabelVocabulary,
) -> InferenceData:
    matrix, stats = preprocess_matrix(config)
    return InferenceData(
        matrix=matrix,
        indices=np.arange(matrix.n_cells, dtype=np.int64),
        gene_vocab=gene_vocab,
        species_vocab=species_vocab,
        tissue_vocab=tissue_vocab,
        preprocessing_stats=stats,
    )


class ExpressionDataset(Dataset[dict[str, torch.Tensor]]):
    def __init__(
        self,
        matrix: MatrixData,
        indices: np.ndarray,
        config: DataConfig,
        gene_vocab: Vocabulary,
        fine_vocab: LabelVocabulary | None = None,
        coarse_vocab: LabelVocabulary | None = None,
        species_vocab: LabelVocabulary | None = None,
        tissue_vocab: LabelVocabulary | None = None,
    ) -> None:
        self.matrix = matrix
        self.indices = np.asarray(indices, dtype=np.int64)
        self.config = config
        self.gene_vocab = gene_vocab
        self.max_genes = config.max_genes
        self.gene_ids = np.asarray(gene_vocab.encode(matrix.genes), dtype=np.int64)
        self.fine_ids = self._encode_obs(config.label_key, fine_vocab)
        self.coarse_ids = self._encode_obs(config.coarse_label_key, coarse_vocab)
        self.species_ids = self._encode_obs(config.species_key, species_vocab, default="unknown_species")
        self.tissue_ids = self._encode_obs(config.tissue_key, tissue_vocab, default="unknown_tissue")

    def _encode_obs(
        self,
        key: str,
        vocab: LabelVocabulary | None,
        default: str | None = None,
    ) -> np.ndarray:
        if vocab is None:
            return np.full(self.matrix.n_cells, -1, dtype=np.int64)
        if key in self.matrix.obs:
            values = self.matrix.obs[key]
        elif default is not None:
            values = np.repeat(default, self.matrix.n_cells)
        else:
            return np.full(self.matrix.n_cells, -1, dtype=np.int64)
        return np.asarray(vocab.encode(values), dtype=np.int64)

    def __len__(self) -> int:
        return len(self.indices)

    def _dense_row(self, matrix_index: int) -> np.ndarray:
        row = self.matrix.X[matrix_index]
        if sparse.issparse(row):
            return np.asarray(row.toarray()).ravel().astype(np.float32)
        return np.asarray(row, dtype=np.float32).ravel()

    def __getitem__(self, item: int) -> dict[str, torch.Tensor]:
        matrix_index = int(self.indices[item])
        row = self._dense_row(matrix_index)
        nonzero = np.flatnonzero(row > 0)
        if len(nonzero) > self.max_genes:
            values = row[nonzero]
            selected_relative = np.argpartition(values, -self.max_genes)[-self.max_genes :]
            selected = nonzero[selected_relative]
        else:
            selected = nonzero
        if len(selected):
            selected = selected[np.argsort(row[selected])[::-1]]

        sequence_length = self.max_genes + 1
        genes = np.full(sequence_length, self.gene_vocab.pad_id, dtype=np.int64)
        values = np.zeros(sequence_length, dtype=np.float32)
        padding = np.ones(sequence_length, dtype=bool)
        genes[0] = self.gene_vocab.cls_id
        padding[0] = False
        count = min(len(selected), self.max_genes)
        if count:
            genes[1 : count + 1] = self.gene_ids[selected[:count]]
            values[1 : count + 1] = row[selected[:count]]
            padding[1 : count + 1] = False
        return {
            "gene_ids": torch.from_numpy(genes),
            "values": torch.from_numpy(values),
            "padding_mask": torch.from_numpy(padding),
            "fine_label": torch.tensor(self.fine_ids[matrix_index], dtype=torch.long),
            "coarse_label": torch.tensor(self.coarse_ids[matrix_index], dtype=torch.long),
            "species_id": torch.tensor(self.species_ids[matrix_index], dtype=torch.long),
            "tissue_id": torch.tensor(self.tissue_ids[matrix_index], dtype=torch.long),
            "cell_index": torch.tensor(matrix_index, dtype=torch.long),
        }


def make_demo_data(
    output: str | Path,
    n_cells: int = 480,
    n_genes: int = 160,
    n_samples: int = 12,
    seed: int = 7,
) -> Path:
    if n_genes < 80:
        raise ValueError("演示数据至少需要 80 个基因")
    if n_samples < 6:
        raise ValueError("演示数据至少需要 6 个样本")
    rng = np.random.default_rng(seed)
    fine_types = np.asarray(
        ["guard_cell", "epidermis", "xylem", "phloem", "mesophyll", "meristem"],
        dtype=str,
    )
    coarse_map = {
        "guard_cell": "dermal",
        "epidermis": "dermal",
        "xylem": "vascular",
        "phloem": "vascular",
        "mesophyll": "ground",
        "meristem": "stem_like",
    }
    genes = np.asarray([f"ORTHO_{index:05d}" for index in range(n_genes)], dtype=str)
    cell_type = fine_types[np.arange(n_cells) % len(fine_types)]
    sample_number = (np.arange(n_cells) // len(fine_types)) % n_samples
    sample_id = np.asarray([f"sample_{index:02d}" for index in sample_number], dtype=str)
    batch = np.asarray([f"batch_{index % 3}" for index in sample_number], dtype=str)
    coarse = np.asarray([coarse_map[label] for label in cell_type], dtype=str)

    base_rate = rng.gamma(shape=1.2, scale=0.35, size=(n_cells, n_genes))
    marker_width = 10
    for class_index, label in enumerate(fine_types):
        mask = cell_type == label
        start = class_index * marker_width
        stop = start + marker_width
        base_rate[mask, start:stop] += rng.uniform(5.0, 9.0, size=(mask.sum(), marker_width))
    batch_scale = 0.85 + 0.15 * (sample_number % 3)
    library_scale = rng.lognormal(mean=0.0, sigma=0.25, size=n_cells)
    rate = base_rate * batch_scale[:, None] * library_scale[:, None]
    X = rng.poisson(rate).astype(np.float32)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        X=X,
        genes=genes,
        cell_type=cell_type,
        cell_type_coarse=coarse,
        sample_id=sample_id,
        batch=batch,
        species=np.repeat("Saussurea_involucrata", n_cells).astype(str),
        tissue=np.repeat("leaf", n_cells).astype(str),
        cell_id=np.asarray([f"demo_cell_{index:05d}" for index in range(n_cells)], dtype=str),
    )
    return output_path


def write_ortholog_template(genes: Iterable[str], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["source_gene", "target_gene", "confidence", "evidence"])
        for gene in genes:
            writer.writerow([str(gene), "", "", ""])
    return output_path
