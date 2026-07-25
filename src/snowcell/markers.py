from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

from .config import ExperimentConfig
from .data import MatrixData, preprocess_matrix


def _as_csr(matrix: np.ndarray | sparse.spmatrix) -> sparse.csr_matrix:
    return matrix.tocsr().astype(np.float32) if sparse.issparse(matrix) else sparse.csr_matrix(matrix)


def _mean(matrix: sparse.csr_matrix) -> np.ndarray:
    return np.asarray(matrix.mean(axis=0)).ravel().astype(np.float32)


def _detection_fraction(matrix: sparse.csr_matrix) -> np.ndarray:
    return np.asarray(matrix.getnnz(axis=0), dtype=np.float32) / max(matrix.shape[0], 1)


def mine_marker_candidates(
    matrix: MatrixData,
    label_key: str,
    top_n: int = 25,
    min_cells: int = 20,
    pseudocount: float = 1e-3,
) -> list[dict[str, Any]]:
    if label_key not in matrix.obs:
        raise ValueError(f"label key not found in obs: {label_key}")
    labels = np.asarray(matrix.obs[label_key], dtype=str)
    X = _as_csr(matrix.X)
    genes = np.asarray(matrix.genes, dtype=str)
    rows: list[dict[str, Any]] = []
    for label in sorted(set(labels.tolist())):
        mask = labels == label
        n_in = int(mask.sum())
        n_out = int((~mask).sum())
        if n_in < min_cells or n_out == 0:
            continue
        X_in = X[mask]
        X_out = X[~mask]
        mean_in = _mean(X_in)
        mean_out = _mean(X_out)
        detection_in = _detection_fraction(X_in)
        detection_out = _detection_fraction(X_out)
        log2fc = np.log2((mean_in + pseudocount) / (mean_out + pseudocount))
        detection_delta = detection_in - detection_out
        score = log2fc * np.maximum(detection_delta, 0.0)
        finite = np.isfinite(score)
        candidate_indices = np.flatnonzero(finite & (mean_in > 0))
        if not len(candidate_indices):
            continue
        ordered = candidate_indices[np.argsort(score[candidate_indices])[::-1]][:top_n]
        for rank, gene_index in enumerate(ordered, start=1):
            rows.append(
                {
                    "label_key": label_key,
                    "label": label,
                    "rank": rank,
                    "gene": str(genes[gene_index]),
                    "score": float(score[gene_index]),
                    "log2fc": float(log2fc[gene_index]),
                    "mean_in": float(mean_in[gene_index]),
                    "mean_out": float(mean_out[gene_index]),
                    "detection_in": float(detection_in[gene_index]),
                    "detection_out": float(detection_out[gene_index]),
                    "n_cells_in": n_in,
                    "n_cells_out": n_out,
                }
            )
    return rows


def write_marker_candidates(
    rows: list[dict[str, Any]],
    output: str | Path,
    summary_output: str | Path | None = None,
) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "label_key",
        "label",
        "rank",
        "gene",
        "score",
        "log2fc",
        "mean_in",
        "mean_out",
        "detection_in",
        "detection_out",
        "n_cells_in",
        "n_cells_out",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    if summary_output:
        labels = sorted({str(row["label"]) for row in rows})
        summary = {
            "output": str(output_path),
            "n_rows": len(rows),
            "n_labels": len(labels),
            "labels": labels,
            "top_gene_examples": rows[: min(10, len(rows))],
        }
        summary_path = Path(summary_output)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return output_path


def run_marker_candidates(
    config_path: str | Path,
    output: str | Path,
    label_key: str | None = None,
    top_n: int = 25,
    min_cells: int = 20,
    summary_output: str | Path | None = None,
) -> Path:
    config = ExperimentConfig.load(config_path)
    matrix, _ = preprocess_matrix(config.data)
    key = label_key or config.data.label_key
    rows = mine_marker_candidates(matrix, key, top_n=top_n, min_cells=min_cells)
    return write_marker_candidates(rows, output, summary_output=summary_output)
