from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse
from sklearn.metrics import accuracy_score, f1_score

from .config import ExperimentConfig
from .data import PreparedData, prepare_data


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norm, 1e-8)


def _as_csr(matrix: np.ndarray | sparse.spmatrix) -> sparse.csr_matrix:
    return matrix.tocsr().astype(np.float32) if sparse.issparse(matrix) else sparse.csr_matrix(matrix)


def fit_centroids(X: sparse.csr_matrix, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    classes = np.asarray(sorted(set(labels.tolist())), dtype=np.int64)
    centroids = []
    for cls in classes:
        rows = X[labels == cls]
        centroid = np.asarray(rows.mean(axis=0)).ravel().astype(np.float32)
        centroids.append(centroid)
    return classes, _normalize_rows(np.vstack(centroids))


def predict_centroids(
    X: sparse.csr_matrix,
    classes: np.ndarray,
    centroids: np.ndarray,
) -> np.ndarray:
    row_norms = np.sqrt(X.multiply(X).sum(axis=1)).A.ravel()
    normalized = X.multiply(1.0 / np.maximum(row_norms, 1e-8)[:, None])
    scores = normalized @ centroids.T
    return classes[np.asarray(scores.argmax(axis=1)).ravel()]


def evaluate_labels(y_true: np.ndarray, y_pred: np.ndarray, prefix: str) -> dict[str, float]:
    return {
        f"{prefix}_accuracy": float(accuracy_score(y_true, y_pred)),
        f"{prefix}_macro_f1": float(f1_score(y_true, y_pred, average="macro")),
    }


def _label_arrays(prepared: PreparedData, label_kind: str) -> np.ndarray:
    if label_kind == "fine":
        if prepared.fine_vocab is None:
            raise ValueError("fine labels are unavailable")
        return np.asarray(prepared.fine_vocab.encode(prepared.matrix.obs["cell_type"]), dtype=np.int64)
    if label_kind == "coarse":
        if prepared.coarse_vocab is None:
            raise ValueError("coarse labels are unavailable")
        return np.asarray(
            prepared.coarse_vocab.encode(prepared.matrix.obs["cell_type_coarse"]),
            dtype=np.int64,
        )
    raise ValueError(f"unknown label_kind: {label_kind}")


def run_centroid_baseline(config_path: str | Path, output: str | Path) -> Path:
    config = ExperimentConfig.load(config_path)
    prepared = prepare_data(config.data, seed=config.train.seed, require_labels=True)
    X = _as_csr(prepared.matrix.X)
    result: dict[str, Any] = {
        "config": str(config_path),
        "method": "cosine_nearest_centroid",
        "split": prepared.preprocessing_stats.get("split", {}),
    }
    for label_kind in ["fine", "coarse"]:
        labels = _label_arrays(prepared, label_kind)
        classes, centroids = fit_centroids(X[prepared.split.train], labels[prepared.split.train])
        for split_name in ["validation", "test"]:
            indices = getattr(prepared.split, split_name)
            predictions = predict_centroids(X[indices], classes, centroids)
            result.update(
                evaluate_labels(
                    labels[indices],
                    predictions,
                    prefix=f"{label_kind}_{split_name}",
                )
            )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path
