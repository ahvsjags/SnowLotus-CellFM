"""Small, auditable tools used by the Plant-CellFM annotation agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import accuracy_score, f1_score

from .config import DataConfig
from .data import load_matrix, preprocess_matrix
from .markers import mine_marker_candidates, write_marker_candidates


OPEN_SET_LABELS = {"unknown", "unknow", "unavailable", "open_set", "open"}


def _summary(values: np.ndarray) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return {"n": 0}
    return {
        "n": int(values.size),
        "min": float(np.min(values)),
        "median": float(np.median(values)),
        "mean": float(np.mean(values)),
        "max": float(np.max(values)),
    }


def input_audit(data_path: str | Path, config: DataConfig) -> dict[str, Any]:
    """Inspect matrix shape, identifiers and sparsity before model invocation."""

    path = Path(data_path)
    matrix = load_matrix(path, config)
    X = matrix.X
    if sparse.issparse(X):
        detected_cells = np.asarray(X.getnnz(axis=1)).ravel()
        library = np.asarray(X.sum(axis=1)).ravel()
        nonzero = int(X.nnz)
    else:
        dense = np.asarray(X)
        detected_cells = np.count_nonzero(dense > 0, axis=1)
        library = dense.sum(axis=1)
        nonzero = int(np.count_nonzero(dense > 0))

    genes = np.asarray(matrix.genes, dtype=str)
    cell_ids = np.asarray(
        matrix.obs.get(config.cell_id_key, np.asarray([str(i) for i in range(matrix.n_cells)])),
        dtype=str,
    )
    species_key = next(
        (key for key in ("species", "Species", "organism", "Organism") if key in matrix.obs),
        config.species_key if config.species_key in matrix.obs else None,
    )
    tissue_key = next(
        (key for key in ("tissue", "Tissue", "organ", "Organ") if key in matrix.obs),
        config.tissue_key if config.tissue_key in matrix.obs else None,
    )
    species = np.asarray(
        matrix.obs[species_key] if species_key else np.repeat("unknown_species", matrix.n_cells),
        dtype=str,
    )
    tissue = np.asarray(
        matrix.obs[tissue_key] if tissue_key else np.repeat("unknown_tissue", matrix.n_cells),
        dtype=str,
    )
    return {
        "path": str(path),
        "format": path.suffix.lower() or path.name,
        "layer": config.layer,
        "n_cells": matrix.n_cells,
        "n_genes": matrix.n_genes,
        "nonzero_entries": nonzero,
        "matrix_density": float(nonzero / max(matrix.n_cells * matrix.n_genes, 1)),
        "gene_id_unique_fraction": float(len(set(genes.tolist())) / max(len(genes), 1)),
        "cell_id_unique_fraction": float(len(set(cell_ids.tolist())) / max(len(cell_ids), 1)),
        "detected_genes_per_cell": _summary(detected_cells),
        "library_size": _summary(library),
        "obs_keys": sorted(matrix.obs),
        "species": {
            "key": species_key,
            "configured_key": config.species_key,
            "values": sorted(set(species.tolist())),
            "counts": _counts(species),
        },
        "tissue": {
            "key": tissue_key,
            "configured_key": config.tissue_key,
            "values": sorted(set(tissue.tolist())),
            "counts": _counts(tissue),
        },
        "missing_required_obs": [
            key for key in (config.species_key, config.tissue_key, config.cell_id_key) if key not in matrix.obs
        ],
    }


def _counts(values: np.ndarray) -> dict[str, int]:
    unique, counts = np.unique(np.asarray(values, dtype=str), return_counts=True)
    return {str(key): int(value) for key, value in zip(unique, counts, strict=True)}


def support_table_info(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {"path": None, "exists": False, "n_rows": 0, "label_key": None}
    support_path = Path(path)
    if not support_path.is_file():
        return {"path": str(support_path), "exists": False, "n_rows": 0, "label_key": None}
    table = pd.read_csv(support_path, sep=None, engine="python", dtype=str)
    label_key = next((key for key in ("fine_label", "label", "cell_type") if key in table.columns), None)
    return {
        "path": str(support_path),
        "exists": True,
        "n_rows": int(len(table)),
        "n_unique_cells": int(table["cell_id"].nunique()) if "cell_id" in table else 0,
        "label_key": label_key,
        "n_labels": int(table[label_key].nunique()) if label_key else 0,
        "columns": [str(column) for column in table.columns],
    }


def assess_predictions(
    prediction_path: str | Path,
    review_threshold: float,
) -> dict[str, Any]:
    """Compute selective-annotation quantities without requiring ground truth."""

    table = pd.read_csv(prediction_path)
    required = {"cell_id", "fine_label", "fine_confidence"}
    missing = required - set(table.columns)
    if missing:
        raise ValueError(f"prediction table missing columns: {sorted(missing)}")
    labels = table["fine_label"].fillna("unknown").astype(str)
    confidence = pd.to_numeric(table["fine_confidence"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
    open_mask = labels.str.lower().isin(OPEN_SET_LABELS)
    accepted_mask = (confidence >= review_threshold) & ~open_mask
    review_mask = ~accepted_mask
    counts = labels.value_counts().head(25).to_dict()
    return {
        "n_cells": int(len(table)),
        "accepted_cells": int(accepted_mask.sum()),
        "accepted_coverage": float(accepted_mask.mean()) if len(table) else 0.0,
        "review_cells": int(review_mask.sum()),
        "review_fraction": float(review_mask.mean()) if len(table) else 1.0,
        "open_set_cells": int(open_mask.sum()),
        "open_set_fraction": float(open_mask.mean()) if len(table) else 0.0,
        "mean_confidence": float(confidence.mean()) if len(table) else 0.0,
        "accepted_mean_confidence": float(confidence[accepted_mask].mean()) if accepted_mask.any() else 0.0,
        "label_count": int(labels.nunique()),
        "top_labels": {str(key): int(value) for key, value in counts.items()},
        "review_threshold": float(review_threshold),
    }


def evaluate_predictions_against_reference(
    data_path: str | Path,
    prediction_path: str | Path,
    config: DataConfig,
    review_threshold: float,
) -> dict[str, Any]:
    """Evaluate direct or Agent predictions against the locked cell labels.

    The cell denominator is reconstructed with the same preprocessing contract
    used by inference. If the input has no declared label column, the function
    returns an explicit ``reference_unavailable`` status instead of guessing.
    """

    matrix, preprocessing_stats = preprocess_matrix(
        DataConfig(**{**config.__dict__, "path": str(data_path)})
    )
    if config.label_key not in matrix.obs:
        return {
            "status": "reference_unavailable",
            "data_path": str(data_path),
            "label_key": config.label_key,
            "n_reference": int(matrix.n_cells),
        }
    predictions = pd.read_csv(prediction_path)
    cell_ids = np.asarray(
        matrix.obs.get(config.cell_id_key, [str(index) for index in range(matrix.n_cells)]), dtype=str
    )
    reference = pd.DataFrame(
        {"cell_id": cell_ids, "reference_label": np.asarray(matrix.obs[config.label_key], dtype=str)}
    )
    required = {"cell_id", "fine_label", "fine_confidence"}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"prediction table missing columns: {sorted(missing)}")
    predictions = predictions.copy()
    predictions["cell_id"] = predictions["cell_id"].astype(str)
    merged = reference.merge(predictions, on="cell_id", how="inner", validate="one_to_one")
    if merged.empty:
        return {
            "status": "no_cell_id_overlap",
            "data_path": str(data_path),
            "label_key": config.label_key,
            "n_reference": int(len(reference)),
            "n_matched": 0,
        }
    true = merged["reference_label"].fillna("unknown").astype(str)
    predicted = merged["fine_label"].fillna("unknown").astype(str)
    confidence = pd.to_numeric(merged["fine_confidence"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
    open_mask = predicted.str.lower().isin(OPEN_SET_LABELS)
    accepted = (confidence >= review_threshold) & ~open_mask
    labels = sorted(set(true.tolist()) | set(predicted.tolist()))
    true_unknown = true.str.lower().str.replace("-", "_", regex=False).str.contains(
        "unknown|unknow|unannotated|unavailable|open_set", regex=True
    )
    metrics: dict[str, Any] = {
        "status": "ok",
        "data_path": str(data_path),
        "label_key": config.label_key,
        "n_reference": int(len(reference)),
        "n_matched": int(len(merged)),
        "all_cell_accuracy": float(accuracy_score(true, predicted)),
        "macro_f1": float(f1_score(true, predicted, labels=labels, average="macro", zero_division=0)),
        "coverage": float(accepted.mean()),
        "accepted_cells": int(accepted.sum()),
        "accepted_cell_accuracy": float(accuracy_score(true[accepted], predicted[accepted])) if accepted.any() else 0.0,
        "accepted_macro_f1": (
            float(
                f1_score(
                    true[accepted],
                    predicted[accepted],
                    labels=labels,
                    average="macro",
                    zero_division=0,
                )
            )
            if accepted.any()
            else 0.0
        ),
        "review_fraction": float((~accepted).mean()),
        "open_set_fraction": float(open_mask.mean()),
        "unknown_reference_cells": int(true_unknown.sum()),
        "unknown_state_recall": (
            float(open_mask[true_unknown].mean()) if true_unknown.any() else None
        ),
        "mean_confidence": float(confidence.mean()),
        "accepted_mean_confidence": float(confidence[accepted].mean()) if accepted.any() else 0.0,
        "preprocessing_stats": preprocessing_stats,
    }
    return metrics


def write_uncertainty_review(
    prediction_path: str | Path,
    output_path: str | Path,
    review_threshold: float,
    force_all_review: bool = False,
) -> Path:
    table = pd.read_csv(prediction_path)
    labels = table["fine_label"].fillna("unknown").astype(str)
    confidence = pd.to_numeric(table["fine_confidence"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
    open_mask = labels.str.lower().isin(OPEN_SET_LABELS)
    review_mask = np.ones(len(table), dtype=bool) if force_all_review else (confidence < review_threshold) | open_mask
    review = table.loc[review_mask].copy()
    reason = np.where(
        force_all_review,
        "specialist_contract_failure",
        np.where(open_mask[review_mask], "open_set_label", "low_confidence"),
    )
    review.insert(0, "review_reason", reason)
    review["review_threshold"] = float(review_threshold)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(output, sep="\t", index=False)
    return output


def _normalise_rows(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-8)


def apply_fewshot_prototypes(
    prediction_path: str | Path,
    embedding_path: str | Path,
    support_path: str | Path,
    output_path: str | Path,
    min_support: int = 8,
) -> dict[str, Any]:
    """Calibrate labels using labelled support embeddings, without gradient updates."""

    predictions = pd.read_csv(prediction_path)
    support = pd.read_csv(support_path, sep=None, engine="python", dtype=str)
    label_key = next((key for key in ("fine_label", "label", "cell_type") if key in support.columns), None)
    if "cell_id" not in support.columns or label_key is None:
        raise ValueError("support table requires cell_id and one of fine_label/label/cell_type")
    support = support[["cell_id", label_key]].rename(columns={label_key: "support_label"}).dropna()
    support = support.drop_duplicates("cell_id")
    if len(support) < min_support:
        raise ValueError(f"few-shot support requires at least {min_support} unique cells")
    embeddings = np.asarray(np.load(embedding_path), dtype=np.float32)
    if len(embeddings) != len(predictions):
        raise ValueError("embedding rows must match prediction rows")
    id_to_index = {str(cell_id): index for index, cell_id in enumerate(predictions["cell_id"].astype(str))}
    support = support[support["cell_id"].isin(id_to_index)].copy()
    if len(support) < min_support:
        raise ValueError("few-shot support cells are not represented in the inference bundle")
    grouped: list[np.ndarray] = []
    labels: list[str] = []
    for label, group in support.groupby("support_label", sort=True):
        indices = [id_to_index[str(cell_id)] for cell_id in group["cell_id"]]
        grouped.append(_normalise_rows(embeddings[indices]).mean(axis=0))
        labels.append(str(label))
    centroids = _normalise_rows(np.vstack(grouped).astype(np.float32))
    scores = _normalise_rows(embeddings) @ centroids.T
    order = np.argsort(scores, axis=1)[:, ::-1]
    top = order[:, 0]
    best = scores[np.arange(len(scores)), top]
    second = scores[np.arange(len(scores)), order[:, 1]] if scores.shape[1] > 1 else np.full(len(scores), -1.0)
    confidence = 1.0 / (1.0 + np.exp(-12.0 * (best - second)))
    calibrated = predictions.copy()
    calibrated["fine_label"] = [labels[index] for index in top]
    calibrated["fine_confidence"] = np.round(confidence, 6)
    calibrated["agent_route"] = "fewshot_adapter"
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    calibrated.to_csv(output, index=False)
    return {
        "support_rows": int(len(support)),
        "support_labels": labels,
        "prototype_count": len(labels),
        "mean_similarity": float(best.mean()) if len(best) else 0.0,
        "mean_margin": float((best - second).mean()) if len(best) else 0.0,
        "output": str(output),
    }


def write_predicted_marker_evidence(
    data_path: str | Path,
    prediction_path: str | Path,
    output_path: str | Path,
    config: DataConfig,
    top_n: int = 10,
    min_cells: int = 20,
) -> dict[str, Any]:
    """Generate exploratory marker evidence for accepted predicted labels."""

    matrix = load_matrix(data_path, config)
    predictions = pd.read_csv(prediction_path)
    pred_by_id = predictions.set_index(predictions["cell_id"].astype(str))
    ids = np.asarray(matrix.obs.get(config.cell_id_key, [str(i) for i in range(matrix.n_cells)]), dtype=str)
    matched = [index for index, cell_id in enumerate(ids) if cell_id in pred_by_id.index]
    if not matched:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("label_key\tlabel\trank\tgene\tscore\n", encoding="utf-8")
        return {"matched_cells": 0, "marker_rows": 0, "status": "no_cell_id_overlap"}
    subset = matrix.subset_cells(np.asarray(matched, dtype=np.int64))
    subset.obs["predicted_fine_label"] = np.asarray(
        [str(pred_by_id.loc[cell_id, "fine_label"]) for cell_id in ids[matched]], dtype=str
    )
    rows = mine_marker_candidates(subset, "predicted_fine_label", top_n=top_n, min_cells=min_cells)
    write_marker_candidates(rows, output_path)
    return {
        "matched_cells": int(len(matched)),
        "marker_rows": int(len(rows)),
        "marker_labels": int(len({str(row["label"]) for row in rows})),
        "status": "ok" if rows else "insufficient_predicted_label_support",
    }
