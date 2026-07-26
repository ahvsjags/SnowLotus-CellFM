#!/usr/bin/env python3
"""Evaluate a transparent Transformer + expression-centroid fusion head."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from scipy import sparse
from sklearn.metrics import accuracy_score, f1_score

from snowcell.artifacts import load_checkpoint, model_from_checkpoint, vocabs_from_checkpoint
from snowcell.baselines import fit_centroids
from snowcell.config import ExperimentConfig
from snowcell.data import ExpressionDataset, prepare_data
from snowcell.train import make_loader, move_batch


def row_cosine_scores(matrix: sparse.csr_matrix, centroids: np.ndarray) -> np.ndarray:
    row_norms = np.sqrt(matrix.multiply(matrix).sum(axis=1)).A.ravel()
    normalized = matrix.multiply(1.0 / np.maximum(row_norms, 1e-8)[:, None])
    return np.asarray(normalized @ centroids.T, dtype=np.float32)


def metric(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def write_predictions(
    output: Path,
    labels: np.ndarray,
    model_probs: np.ndarray,
    centroid_probs: np.ndarray,
    fusion_probs: np.ndarray,
    label_names: tuple[str, ...],
    cell_indices: np.ndarray,
    cell_ids: np.ndarray,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "cell_index",
        "cell_id",
        "true_label",
        "model_label",
        "centroid_label",
        "fusion_label",
        "model_confidence",
        "centroid_confidence",
        "fusion_confidence",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        model_pred = model_probs.argmax(axis=1)
        centroid_pred = centroid_probs.argmax(axis=1)
        fusion_pred = fusion_probs.argmax(axis=1)
        for row in range(labels.shape[0]):
            writer.writerow(
                {
                    "cell_index": int(cell_indices[row]),
                    "cell_id": str(cell_ids[row]),
                    "true_label": label_names[int(labels[row])],
                    "model_label": label_names[int(model_pred[row])],
                    "centroid_label": label_names[int(centroid_pred[row])],
                    "fusion_label": label_names[int(fusion_pred[row])],
                    "model_confidence": f"{float(model_probs[row, model_pred[row]]):.6f}",
                    "centroid_confidence": f"{float(centroid_probs[row, centroid_pred[row]]):.6f}",
                    "fusion_confidence": f"{float(fusion_probs[row, fusion_pred[row]]):.6f}",
                }
            )
    return output


@torch.no_grad()
def collect_model_logits(
    prepared: Any,
    config: ExperimentConfig,
    checkpoint_path: Path,
    split_name: str,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    checkpoint = load_checkpoint(checkpoint_path, map_location=device)
    model = model_from_checkpoint(checkpoint, device=device)
    gene_vocab, fine_vocab, coarse_vocab, species_vocab, tissue_vocab = vocabs_from_checkpoint(checkpoint)
    if fine_vocab is None or coarse_vocab is None:
        raise ValueError("checkpoint has no supervised vocabularies")
    indices = getattr(prepared.split, split_name)
    dataset = ExpressionDataset(
        prepared.matrix,
        indices,
        config.data,
        gene_vocab,
        fine_vocab=fine_vocab,
        coarse_vocab=coarse_vocab,
        species_vocab=species_vocab,
        tissue_vocab=tissue_vocab,
    )
    loader = make_loader(dataset, config.train.eval_batch_size, shuffle=False, num_workers=0)
    fine_logits: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    model.eval()
    for raw_batch in loader:
        batch = move_batch(raw_batch, device)
        outputs = model(
            gene_ids=batch["gene_ids"],
            values=batch["values"],
            padding_mask=batch["padding_mask"],
            species_id=batch["species_id"],
            tissue_id=batch["tissue_id"],
        )
        fine_logits.append(outputs["fine_logits"].detach().cpu().numpy())
        labels.append(raw_batch["fine_label"].detach().cpu().numpy())
    return np.concatenate(fine_logits), np.concatenate(labels)


def softmax(values: np.ndarray, temperature: float) -> np.ndarray:
    scaled = values / max(float(temperature), 1e-6)
    scaled = scaled - scaled.max(axis=1, keepdims=True)
    exp_values = np.exp(scaled)
    return exp_values / np.maximum(exp_values.sum(axis=1, keepdims=True), 1e-12)


def evaluate_split(
    *,
    prepared: Any,
    config: ExperimentConfig,
    checkpoint_path: Path,
    split_name: str,
    centroids: np.ndarray,
    device: torch.device,
    alpha: float,
    model_temperature: float,
    centroid_temperature: float,
) -> dict[str, Any]:
    model_logits, labels = collect_model_logits(
        prepared, config, checkpoint_path, split_name, device
    )
    indices = getattr(prepared.split, split_name)
    centroid_scores = row_cosine_scores(prepared.matrix.X[indices].tocsr(), centroids)
    model_probs = softmax(model_logits, model_temperature)
    centroid_probs = softmax(centroid_scores, centroid_temperature)
    fused_probs = (1.0 - alpha) * model_probs + alpha * centroid_probs
    model_pred = model_probs.argmax(axis=1)
    centroid_pred = centroid_probs.argmax(axis=1)
    fused_pred = fused_probs.argmax(axis=1)
    return {
        "split": split_name,
        "n_cells": int(labels.shape[0]),
        "model": metric(labels, model_pred),
        "centroid": metric(labels, centroid_pred),
        "fusion": metric(labels, fused_pred),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    config = ExperimentConfig.load(args.config)
    device = torch.device(args.device)
    prepared = prepare_data(config.data, seed=config.train.seed, require_labels=True)
    labels = np.asarray(prepared.fine_vocab.encode(prepared.matrix.obs[config.data.label_key]), dtype=np.int64)
    classes, centroids = fit_centroids(
        prepared.matrix.X[prepared.split.train].tocsr(), labels[prepared.split.train]
    )
    if not np.array_equal(classes, np.arange(len(classes))):
        raise ValueError("fine class ids are not contiguous; fusion alignment is ambiguous")

    validation_logits, validation_labels = collect_model_logits(
        prepared, config, args.checkpoint, "validation", device
    )
    test_logits, test_labels = collect_model_logits(
        prepared, config, args.checkpoint, "test", device
    )
    validation_indices = prepared.split.validation
    test_indices = prepared.split.test
    validation_centroid_scores = row_cosine_scores(
        prepared.matrix.X[validation_indices].tocsr(), centroids
    )
    test_centroid_scores = row_cosine_scores(
        prepared.matrix.X[test_indices].tocsr(), centroids
    )
    validation_model_probs = softmax(validation_logits, 1.0)
    validation_centroid_probs = softmax(validation_centroid_scores, 0.05)
    test_model_probs = softmax(test_logits, 1.0)
    test_centroid_probs = softmax(test_centroid_scores, 0.05)

    grid: list[dict[str, Any]] = []
    for alpha in np.linspace(0.0, 1.0, 21):
        fused_probs = (1.0 - float(alpha)) * validation_model_probs + float(alpha) * validation_centroid_probs
        grid.append(
            {
                "alpha": float(alpha),
                **metric(validation_labels, fused_probs.argmax(axis=1)),
            }
        )
    best = max(grid, key=lambda item: (item["macro_f1"], item["accuracy"]))
    alpha = float(best["alpha"])
    test_fused_probs = (1.0 - alpha) * test_model_probs + alpha * test_centroid_probs
    test = {
        "split": "test",
        "n_cells": int(test_labels.shape[0]),
        "model": metric(test_labels, test_model_probs.argmax(axis=1)),
        "centroid": metric(test_labels, test_centroid_probs.argmax(axis=1)),
        "fusion": metric(test_labels, test_fused_probs.argmax(axis=1)),
    }
    test_cell_indices = np.asarray(prepared.split.test, dtype=np.int64)
    test_cell_ids = np.asarray(
        prepared.matrix.obs.get(
            config.data.cell_id_key,
            np.asarray([str(index) for index in range(prepared.matrix.n_cells)], dtype=str),
        )[test_cell_indices],
        dtype=str,
    )
    prediction_path = write_predictions(
        args.output.parent / "hybrid_fusion_test_predictions.tsv",
        test_labels,
        test_model_probs,
        test_centroid_probs,
        test_fused_probs,
        prepared.fine_vocab.labels,
        test_cell_indices,
        test_cell_ids,
    )
    payload = {
        "config": str(args.config),
        "checkpoint": str(args.checkpoint),
        "method": "probability_fusion_transformer_centroid",
        "centroid_temperature": 0.05,
        "model_temperature": 1.0,
        "validation_grid": grid,
        "selected_alpha": float(best["alpha"]),
        "selected_validation": best,
        "test": test,
        "artifacts": {"test_predictions_tsv": str(prediction_path)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
