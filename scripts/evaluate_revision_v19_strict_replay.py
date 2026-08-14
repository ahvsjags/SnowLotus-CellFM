"""Evaluate a v19 checkpoint on a locked leave-species input.

The script never uses target labels for training, calibration, routing, or
checkpoint selection. It reports canonical ontology performance separately
from explicit unknown/open-set detection so the denominator remains visible.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from snowcell.artifacts import load_checkpoint, vocabs_from_checkpoint
from snowcell.config import DataConfig, ExperimentConfig
from snowcell.data import load_matrix, preprocess_matrix
from snowcell.train import predict_to_csv


UNKNOWN_LABELS = {"unknown", "unknow", "unannotated", "unavailable", "open set", "open_set"}


def _is_unknown(values: pd.Series) -> np.ndarray:
    normalized = values.fillna("unknown").astype(str).str.lower()
    return normalized.isin(UNKNOWN_LABELS).to_numpy()


def _bootstrap_ci(values: np.ndarray, seed: int, replicates: int) -> list[float] | None:
    values = np.asarray(values, dtype=np.float32)
    if replicates <= 0 or len(values) < 2:
        return None
    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, len(values), size=(replicates, len(values)))
    estimates = values[sampled].mean(axis=1)
    return [float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))]


def _metrics(
    frame: pd.DataFrame,
    model_labels: set[str],
    *,
    label_column: str = "reference_label",
    bootstrap_seed: int = 20260814,
    bootstrap_replicates: int = 1000,
) -> dict[str, Any]:
    true = frame[label_column].astype(str)
    predicted = frame["predicted_label"].astype(str)
    covered = true.isin(model_labels).to_numpy()
    unknown = _is_unknown(true)
    actionable = ~unknown
    labels = sorted(set(true.tolist()) | set(predicted.tolist()))
    correct = (true.to_numpy() == predicted.to_numpy()).astype(np.float32)
    result: dict[str, Any] = {
        "n_test": int(len(frame)),
        "n_evaluable_by_model_vocab": int(covered.sum()),
        "coverage": float(covered.mean()) if len(frame) else 0.0,
        "all_cell_accuracy": float(accuracy_score(true, predicted)) if len(frame) else None,
        "all_cell_accuracy_ci95": _bootstrap_ci(
            correct, bootstrap_seed, bootstrap_replicates
        ),
        "macro_f1_all": float(f1_score(true, predicted, labels=labels, average="macro", zero_division=0))
        if len(frame)
        else None,
        "unknown_reference_cells": int(unknown.sum()),
        "unknown_reference_fraction": float(unknown.mean()) if len(frame) else 0.0,
        "unknown_detection_recall": (
            float(_is_unknown(predicted[unknown]).mean()) if unknown.any() else None
        ),
        "actionable_cells": int(actionable.sum()),
        "actionable_coverage": float(covered[actionable].mean()) if actionable.any() else None,
        "actionable_all_accuracy": float(accuracy_score(true[actionable], predicted[actionable]))
        if actionable.any()
        else None,
        "actionable_all_accuracy_ci95": (
            _bootstrap_ci(
                (true[actionable].to_numpy() == predicted[actionable].to_numpy()).astype(np.float32),
                bootstrap_seed + 1,
                bootstrap_replicates,
            )
            if actionable.any()
            else None
        ),
    }
    if covered.any():
        result["covered_label_accuracy"] = float(accuracy_score(true[covered], predicted[covered]))
        result["covered_label_accuracy_ci95"] = _bootstrap_ci(
            (true[covered].to_numpy() == predicted[covered].to_numpy()).astype(np.float32),
            bootstrap_seed + 2,
            bootstrap_replicates,
        )
        result["covered_label_macro_f1"] = float(
            f1_score(
                true[covered],
                predicted[covered],
                labels=sorted(set(true[covered].tolist()) | set(predicted[covered].tolist())),
                average="macro",
                zero_division=0,
            )
        )
    else:
        result["covered_label_accuracy"] = None
        result["covered_label_macro_f1"] = None
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260814)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = load_checkpoint(args.checkpoint, map_location="cpu")
    experiment = ExperimentConfig.from_dict(checkpoint["experiment_config"])
    data_config = DataConfig(**{**experiment.data.__dict__, "path": str(args.data)})
    raw_config = DataConfig(
        **{**data_config.__dict__, "ontology_contract": None, "ontology_unknown_policy": "keep"}
    )
    raw_matrix = load_matrix(args.data, raw_config)
    matrix, preprocessing_stats = preprocess_matrix(data_config)
    cell_ids = np.asarray(
        matrix.obs.get(data_config.cell_id_key, [str(index) for index in range(matrix.n_cells)]),
        dtype=str,
    )
    species = np.asarray(
        matrix.obs.get(data_config.species_key, ["unknown_species"] * matrix.n_cells),
        dtype=str,
    )
    raw_cell_ids = np.asarray(
        raw_matrix.obs.get(data_config.cell_id_key, [str(index) for index in range(raw_matrix.n_cells)]),
        dtype=str,
    )
    raw_labels = np.asarray(
        raw_matrix.obs.get(data_config.label_key, ["unknown"] * raw_matrix.n_cells), dtype=str
    )
    raw_label_by_id = {str(cell_id): str(label) for cell_id, label in zip(raw_cell_ids, raw_labels, strict=True)}
    reference = pd.DataFrame(
        {
            "cell_id": cell_ids,
            "species": species,
            "reference_label": np.asarray(matrix.obs.get(data_config.label_key, ["unknown"] * matrix.n_cells), dtype=str),
            "raw_reference_label": [raw_label_by_id.get(str(cell_id), "unknown") for cell_id in cell_ids],
        }
    )
    prediction_path = output_dir / "predictions.csv"
    predict_to_csv(
        checkpoint_path=args.checkpoint,
        data_path=args.data,
        output_path=prediction_path,
        batch_size=args.batch_size,
        device=args.device,
    )
    predictions = pd.read_csv(prediction_path, dtype={"cell_id": str})
    predictions = predictions.rename(columns={"fine_label": "predicted_label"})
    frame = reference.merge(
        predictions[["cell_id", "predicted_label"]],
        on="cell_id",
        how="inner",
        validate="one_to_one",
    )
    if len(frame) != len(reference):
        raise ValueError(f"prediction/reference row mismatch: {len(frame)} vs {len(reference)}")
    _, fine_vocab, _, _, _ = vocabs_from_checkpoint(checkpoint)
    model_labels = set(fine_vocab.labels) if fine_vocab is not None else set()
    canonical_metrics = _metrics(
        frame,
        model_labels,
        bootstrap_seed=args.bootstrap_seed,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    raw_metrics = _metrics(
        frame,
        model_labels,
        label_column="raw_reference_label",
        bootstrap_seed=args.bootstrap_seed + 100,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    payload = {
        "schema_version": "plant_cellfm_revision_v19_strict_replay_v1",
        "checkpoint": str(args.checkpoint),
        "data": str(args.data),
        "n_test": int(len(frame)),
        "denominator_locked": True,
        "target_labels_used_for_training_or_calibration": False,
        "model_labels": sorted(model_labels),
        "preprocessing_stats": preprocessing_stats,
        "overall": canonical_metrics,
        "raw_label_replay": raw_metrics,
        "per_species": {
            str(species_name): {
                "canonical": _metrics(
                    group,
                    model_labels,
                    bootstrap_seed=args.bootstrap_seed + index * 10,
                    bootstrap_replicates=args.bootstrap_replicates,
                ),
                "raw_label_replay": _metrics(
                    group,
                    model_labels,
                    label_column="raw_reference_label",
                    bootstrap_seed=args.bootstrap_seed + 100 + index * 10,
                    bootstrap_replicates=args.bootstrap_replicates,
                ),
            }
            for index, (species_name, group) in enumerate(frame.groupby("species", sort=True))
        },
    }
    (output_dir / "strict_replay.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    frame.to_csv(output_dir / "strict_replay_cells.tsv", sep="\t", index=False)
    print(json.dumps(payload["overall"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
