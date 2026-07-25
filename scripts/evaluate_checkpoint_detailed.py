from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from snowcell.artifacts import load_checkpoint, model_from_checkpoint, vocabs_from_checkpoint
from snowcell.config import ExperimentConfig
from snowcell.data import ExpressionDataset, prepare_data
from snowcell.train import make_loader, move_batch


def device_from_string(value: str) -> torch.device:
    if value == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(value)


def obs_value(matrix_obs: dict[str, np.ndarray], key: str, index: int, default: str = "") -> str:
    if key not in matrix_obs:
        return default
    return str(matrix_obs[key][index])


def labels_for(ids: list[int], labels: tuple[str, ...]) -> list[str]:
    result = []
    for value in ids:
        result.append(labels[int(value)] if 0 <= int(value) < len(labels) else "unknown")
    return result


def metric_summary(true: list[str], pred: list[str]) -> dict[str, Any]:
    if not true:
        return {
            "accuracy": None,
            "macro_f1": None,
            "weighted_f1": None,
            "class_count": 0,
            "classification_report": {},
        }
    return {
        "accuracy": float(accuracy_score(true, pred)),
        "macro_f1": float(f1_score(true, pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(true, pred, average="weighted", zero_division=0)),
        "class_count": len(set(true)),
        "classification_report": classification_report(
            true,
            pred,
            output_dict=True,
            zero_division=0,
        ),
    }


def confidence_summary(values: list[float], correct: list[bool]) -> dict[str, Any]:
    if not values:
        return {
            "mean": None,
            "median": None,
            "mean_correct": None,
            "mean_incorrect": None,
        }
    array = np.asarray(values, dtype=np.float64)
    correct_array = np.asarray(correct, dtype=bool)
    return {
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "mean_correct": float(np.mean(array[correct_array])) if np.any(correct_array) else None,
        "mean_incorrect": float(np.mean(array[~correct_array])) if np.any(~correct_array) else None,
    }


def write_prediction_tsv(rows: list[dict[str, Any]], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cell_index",
        "cell_id",
        "sample_id",
        "species",
        "tissue",
        "true_fine",
        "pred_fine",
        "fine_confidence",
        "fine_correct",
        "true_coarse",
        "pred_coarse",
        "coarse_confidence",
        "coarse_correct",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output


def write_confusion_tsv(labels: list[str], matrix: np.ndarray, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["true_label"] + labels)
        for label, row in zip(labels, matrix.tolist(), strict=True):
            writer.writerow([label] + row)
    return output


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    fine = summary["fine"]
    coarse = summary["coarse"]
    lines = [
        "# SnowLotus-CellFM Detailed Checkpoint Evaluation",
        "",
        f"- Generated UTC: `{payload['generated_at_utc']}`",
        f"- Config: `{payload['config_path']}`",
        f"- Checkpoint: `{payload['checkpoint_path']}`",
        f"- Split: `{payload['split']}`",
        f"- Evaluated cells: `{summary['evaluated_cells']}`",
        f"- Fine accuracy: `{fine['accuracy']:.4f}`" if fine["accuracy"] is not None else "- Fine accuracy: `-`",
        f"- Fine macro-F1: `{fine['macro_f1']:.4f}`" if fine["macro_f1"] is not None else "- Fine macro-F1: `-`",
        f"- Coarse accuracy: `{coarse['accuracy']:.4f}`" if coarse["accuracy"] is not None else "- Coarse accuracy: `-`",
        f"- Coarse macro-F1: `{coarse['macro_f1']:.4f}`" if coarse["macro_f1"] is not None else "- Coarse macro-F1: `-`",
        "",
        "## Low Fine-F1 Classes",
        "",
        "| Label | Support | Precision | Recall | F1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["low_fine_f1_classes"]:
        lines.append(
            "| {label} | {support} | {precision:.4f} | {recall:.4f} | {f1:.4f} |".format(
                label=str(item["label"]).replace("|", "/"),
                support=int(item["support"]),
                precision=float(item["precision"]),
                recall=float(item["recall"]),
                f1=float(item["f1-score"]),
            )
        )
    lines.extend(["", "## High-Confidence Fine Errors", ""])
    if payload["high_confidence_fine_errors"]:
        for item in payload["high_confidence_fine_errors"]:
            lines.append(
                "- `{cell_id}` true `{true_fine}` predicted `{pred_fine}` confidence `{confidence:.4f}`".format(
                    cell_id=item["cell_id"],
                    true_fine=item["true_fine"],
                    pred_fine=item["pred_fine"],
                    confidence=float(item["fine_confidence"]),
                )
            )
    else:
        lines.append("- None.")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


@torch.no_grad()
def run_detailed_evaluation(
    *,
    config_path: Path,
    checkpoint_path: Path,
    split: str,
    output_dir: Path,
    device: torch.device,
    batch_size: int | None = None,
    max_batches: int | None = None,
) -> dict[str, Any]:
    config = ExperimentConfig.load(config_path)
    prepared = prepare_data(config.data, config.train.seed, require_labels=True)
    checkpoint = load_checkpoint(checkpoint_path, map_location=device)
    model = model_from_checkpoint(checkpoint, device=device)
    gene_vocab, fine_vocab, coarse_vocab, species_vocab, tissue_vocab = vocabs_from_checkpoint(checkpoint)
    if fine_vocab is None or coarse_vocab is None:
        raise ValueError("checkpoint has no fine/coarse label vocabulary")
    split_indices = getattr(prepared.split, split)
    dataset = ExpressionDataset(
        prepared.matrix,
        split_indices,
        config.data,
        gene_vocab,
        fine_vocab=fine_vocab,
        coarse_vocab=coarse_vocab,
        species_vocab=species_vocab,
        tissue_vocab=tissue_vocab,
    )
    loader = make_loader(
        dataset,
        batch_size or config.train.eval_batch_size,
        shuffle=False,
        num_workers=0,
    )
    cell_ids = prepared.matrix.obs.get(
        config.data.cell_id_key,
        np.asarray([str(index) for index in range(prepared.matrix.n_cells)], dtype=str),
    )
    fine_true_ids: list[int] = []
    fine_pred_ids: list[int] = []
    coarse_true_ids: list[int] = []
    coarse_pred_ids: list[int] = []
    fine_conf: list[float] = []
    coarse_conf: list[float] = []
    rows: list[dict[str, Any]] = []
    model.eval()
    for batch_index, raw_batch in enumerate(loader, start=1):
        if max_batches is not None and batch_index > max_batches:
            break
        batch = move_batch(raw_batch, device)
        outputs = model(
            gene_ids=batch["gene_ids"],
            values=batch["values"],
            padding_mask=batch["padding_mask"],
            species_id=batch["species_id"],
            tissue_id=batch["tissue_id"],
        )
        fine_probs = torch.softmax(outputs["fine_logits"], dim=-1)
        coarse_probs = torch.softmax(outputs["coarse_logits"], dim=-1)
        fine_score, fine_pred = fine_probs.max(dim=-1)
        coarse_score, coarse_pred = coarse_probs.max(dim=-1)
        batch_cell_indices = raw_batch["cell_index"].detach().cpu().numpy().astype(int).tolist()
        batch_fine_true = raw_batch["fine_label"].detach().cpu().numpy().astype(int).tolist()
        batch_coarse_true = raw_batch["coarse_label"].detach().cpu().numpy().astype(int).tolist()
        batch_fine_pred = fine_pred.detach().cpu().numpy().astype(int).tolist()
        batch_coarse_pred = coarse_pred.detach().cpu().numpy().astype(int).tolist()
        batch_fine_conf = fine_score.detach().cpu().numpy().astype(float).tolist()
        batch_coarse_conf = coarse_score.detach().cpu().numpy().astype(float).tolist()
        fine_true_ids.extend(batch_fine_true)
        fine_pred_ids.extend(batch_fine_pred)
        coarse_true_ids.extend(batch_coarse_true)
        coarse_pred_ids.extend(batch_coarse_pred)
        fine_conf.extend(batch_fine_conf)
        coarse_conf.extend(batch_coarse_conf)
        true_fine_labels = labels_for(batch_fine_true, fine_vocab.labels)
        pred_fine_labels = labels_for(batch_fine_pred, fine_vocab.labels)
        true_coarse_labels = labels_for(batch_coarse_true, coarse_vocab.labels)
        pred_coarse_labels = labels_for(batch_coarse_pred, coarse_vocab.labels)
        for position, matrix_index in enumerate(batch_cell_indices):
            rows.append(
                {
                    "cell_index": matrix_index,
                    "cell_id": str(cell_ids[matrix_index]),
                    "sample_id": obs_value(prepared.matrix.obs, config.data.group_key, matrix_index),
                    "species": obs_value(prepared.matrix.obs, config.data.species_key, matrix_index),
                    "tissue": obs_value(prepared.matrix.obs, config.data.tissue_key, matrix_index),
                    "true_fine": true_fine_labels[position],
                    "pred_fine": pred_fine_labels[position],
                    "fine_confidence": f"{batch_fine_conf[position]:.6f}",
                    "fine_correct": str(true_fine_labels[position] == pred_fine_labels[position]),
                    "true_coarse": true_coarse_labels[position],
                    "pred_coarse": pred_coarse_labels[position],
                    "coarse_confidence": f"{batch_coarse_conf[position]:.6f}",
                    "coarse_correct": str(true_coarse_labels[position] == pred_coarse_labels[position]),
                }
            )

    fine_true = labels_for(fine_true_ids, fine_vocab.labels)
    fine_pred_labels = labels_for(fine_pred_ids, fine_vocab.labels)
    coarse_true = labels_for(coarse_true_ids, coarse_vocab.labels)
    coarse_pred_labels = labels_for(coarse_pred_ids, coarse_vocab.labels)
    fine_correct = [truth == pred for truth, pred in zip(fine_true, fine_pred_labels, strict=True)]
    coarse_correct = [truth == pred for truth, pred in zip(coarse_true, coarse_pred_labels, strict=True)]
    fine_labels = list(fine_vocab.labels)
    coarse_labels = list(coarse_vocab.labels)
    fine_report = metric_summary(fine_true, fine_pred_labels)
    coarse_report = metric_summary(coarse_true, coarse_pred_labels)
    low_fine = []
    aggregate_rows = {"accuracy", "macro avg", "micro avg", "weighted avg", "samples avg"}
    for label, values in fine_report["classification_report"].items():
        if isinstance(values, dict) and "f1-score" in values:
            if label in aggregate_rows:
                continue
            low_fine.append({"label": label, **values})
    low_fine = sorted(
        low_fine,
        key=lambda item: (
            float(item.get("f1-score") or 0.0),
            -float(item.get("support") or 0.0),
        ),
    )[:10]
    high_conf_errors = [row for row in rows if row["fine_correct"] == "False"]
    high_conf_errors = sorted(
        high_conf_errors,
        key=lambda row: float(row["fine_confidence"]),
        reverse=True,
    )[:25]

    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_tsv = write_prediction_tsv(rows, output_dir / "predictions.tsv")
    fine_confusion_tsv = write_confusion_tsv(
        fine_labels,
        confusion_matrix(fine_true, fine_pred_labels, labels=fine_labels),
        output_dir / "fine_confusion_matrix.tsv",
    )
    coarse_confusion_tsv = write_confusion_tsv(
        coarse_labels,
        confusion_matrix(coarse_true, coarse_pred_labels, labels=coarse_labels),
        output_dir / "coarse_confusion_matrix.tsv",
    )
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_epoch": checkpoint.get("epoch"),
        "checkpoint_metrics": checkpoint.get("metrics", {}),
        "split": split,
        "device": str(device),
        "batch_size": batch_size or config.train.eval_batch_size,
        "max_batches": max_batches,
        "summary": {
            "evaluated_cells": len(rows),
            "fine": fine_report,
            "coarse": coarse_report,
            "fine_confidence": confidence_summary(fine_conf, fine_correct),
            "coarse_confidence": confidence_summary(coarse_conf, coarse_correct),
        },
        "low_fine_f1_classes": low_fine,
        "high_confidence_fine_errors": high_conf_errors,
        "artifacts": {
            "predictions_tsv": str(predictions_tsv),
            "fine_confusion_matrix_tsv": str(fine_confusion_tsv),
            "coarse_confusion_matrix_tsv": str(coarse_confusion_tsv),
        },
    }
    write_json(payload, output_dir / "detailed_metrics.json")
    write_markdown(payload, output_dir / "detailed_evaluation.md")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run detailed checkpoint evaluation on a configured split")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--split", default="test", choices=["train", "validation", "test"])
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch-size", default=None, type=int)
    parser.add_argument("--max-batches", default=None, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_detailed_evaluation(
        config_path=args.config,
        checkpoint_path=args.checkpoint,
        split=args.split,
        output_dir=args.output_dir,
        device=device_from_string(args.device),
        batch_size=args.batch_size,
        max_batches=args.max_batches,
    )
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
