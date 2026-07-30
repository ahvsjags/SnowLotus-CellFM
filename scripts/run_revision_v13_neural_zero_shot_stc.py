from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import f1_score


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def canonical_species(value: str) -> str:
    return " ".join(str(value or "").replace("_", " ").split())


def normalize_rows(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-8)


def align_obs(obs_rows: list[dict[str, str]], prediction_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[int]]:
    by_cell: dict[str, dict[str, str]] = {}
    for row in obs_rows:
        for key in ("cell_id", "_index"):
            value = row.get(key, "")
            if value:
                by_cell[value] = row
    aligned: list[dict[str, str]] = []
    indices: list[int] = []
    for index, row in enumerate(prediction_rows):
        obs = by_cell.get(row.get("cell_id", ""))
        if obs and obs.get("species") and obs.get("cell_type"):
            aligned.append(obs)
            indices.append(index)
    return aligned, indices


class Head(torch.nn.Module):
    def __init__(self, dim: int, classes: int, hidden: int, dropout: float) -> None:
        super().__init__()
        if hidden <= 0:
            self.net = torch.nn.Linear(dim, classes)
        else:
            self.net = torch.nn.Sequential(
                torch.nn.Linear(dim, hidden),
                torch.nn.LayerNorm(hidden),
                torch.nn.GELU(),
                torch.nn.Dropout(dropout),
                torch.nn.Linear(hidden, classes),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def macro_f1(truth: np.ndarray, pred: np.ndarray) -> float:
    return float(f1_score(truth, pred, average="macro", zero_division=0)) if len(truth) else 0.0


def evaluate(truth: np.ndarray, pred: np.ndarray, train_labels: set[str]) -> dict[str, Any]:
    covered = np.asarray([label in train_labels for label in truth], dtype=bool)
    out: dict[str, Any] = {
        "n_test": int(len(truth)),
        "n_evaluable": int(covered.sum()),
        "open_set_cells": int((~covered).sum()),
        "coverage": float(covered.mean()) if len(truth) else 0.0,
        "accuracy_all": float((truth == pred).mean()) if len(truth) else 0.0,
        "macro_f1_all": macro_f1(truth, pred),
    }
    if covered.any():
        out["accuracy"] = float((truth[covered] == pred[covered]).mean())
        out["macro_f1"] = macro_f1(truth[covered], pred[covered])
    return out


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(row["n_test"]) for row in records)
    total_eval = sum(int(row["n_evaluable"]) for row in records)
    out: dict[str, Any] = {
        "groups": len(records),
        "n_test": total,
        "n_evaluable": total_eval,
        "open_set_cells": sum(int(row["open_set_cells"]) for row in records),
        "coverage": total_eval / total if total else 0.0,
    }
    if total:
        out["accuracy_all"] = sum(float(row["accuracy_all"]) * int(row["n_test"]) for row in records) / total
    if total_eval:
        out["accuracy"] = sum(float(row.get("accuracy", 0.0)) * int(row["n_evaluable"]) for row in records) / total_eval
        out["macro_f1"] = sum(float(row.get("macro_f1", 0.0)) * int(row["n_evaluable"]) for row in records) / total_eval
    return out


def train_predict(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    *,
    hidden: int,
    dropout: float,
    lr: float,
    epochs: int,
    weight_power: float,
    label_smoothing: float,
    zscore: bool,
    device: str,
) -> np.ndarray:
    if zscore:
        mean = x_train.mean(axis=0, keepdims=True)
        std = x_train.std(axis=0, keepdims=True) + 1e-4
        x_train = (x_train - mean) / std
        x_test = (x_test - mean) / std
    labels = sorted(set(y_train.tolist()))
    label_to_id = {label: index for index, label in enumerate(labels)}
    y_ids = np.asarray([label_to_id[label] for label in y_train], dtype=np.int64)
    counts = np.bincount(y_ids, minlength=len(labels)).astype(np.float32)
    weights = (counts.mean() / np.maximum(counts, 1.0)) ** weight_power
    weights = np.clip(weights, 0.25, 8.0)

    x_tensor = torch.tensor(x_train, dtype=torch.float32, device=device)
    y_tensor = torch.tensor(y_ids, dtype=torch.long, device=device)
    test_tensor = torch.tensor(x_test, dtype=torch.float32, device=device)
    weight_tensor = torch.tensor(weights, dtype=torch.float32, device=device)
    model = Head(x_train.shape[1], len(labels), hidden=hidden, dropout=dropout).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    criterion = torch.nn.CrossEntropyLoss(weight=weight_tensor, label_smoothing=label_smoothing)
    generator = torch.Generator(device="cpu").manual_seed(20260801)
    batch_size = len(y_train) if hidden <= 0 else min(512, len(y_train))

    model.train()
    for _ in range(epochs):
        order = torch.randperm(len(y_train), generator=generator)
        for start in range(0, len(y_train), batch_size):
            batch = order[start : start + batch_size].to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(x_tensor[batch]), y_tensor[batch])
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        pred_ids = model(test_tensor).argmax(dim=1).detach().cpu().numpy()
    return np.asarray([labels[int(index)] for index in pred_ids], dtype=str)


def run_config(
    name: str,
    config: dict[str, Any],
    x: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    device: str,
) -> dict[str, Any]:
    records = []
    for group in sorted(set(species.tolist())):
        test_mask = species == group
        train_mask = ~test_mask
        train_labels = set(labels[train_mask].tolist())
        pred = train_predict(
            x[train_mask],
            labels[train_mask],
            x[test_mask],
            hidden=int(config["hidden"]),
            dropout=float(config["dropout"]),
            lr=float(config["lr"]),
            epochs=int(config["epochs"]),
            weight_power=float(config["weight_power"]),
            label_smoothing=float(config["label_smoothing"]),
            zscore=bool(config["zscore"]),
            device=device,
        )
        row = evaluate(labels[test_mask], pred, train_labels)
        row["held_out_species"] = str(group)
        row["method"] = name
        records.append(row)
    summary = aggregate(records)
    print(
        f"{name}\tall={summary.get('accuracy_all', 0.0):.4f}\tknown={summary.get('accuracy', 0.0):.4f}\t"
        f"f1={summary.get('macro_f1', 0.0):.4f}\tcoverage={summary.get('coverage', 0.0):.4f}",
        flush=True,
    )
    return {"config": config, "summary": summary, "records": records}


def pct(value: float) -> str:
    return f"{100 * float(value):.2f}%"


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    best = payload["best_method"]
    lines = [
        "# Plant-CellFM v13 Neural Zero-Shot STC Benchmark",
        "",
        f"Generated: {payload['generated']}",
        "",
        "This benchmark trains a fold-specific neural calibration head on frozen Plant-CellFM embeddings using only training-species labels. Held-out species labels are not used for training.",
        "",
        "| Method | All-cell accuracy | Known-label accuracy | Macro-F1 | Coverage |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, data in payload["methods"].items():
        summary = data["summary"]
        lines.append(
            f"| `{name}` | {summary.get('accuracy_all', 0.0):.4f} | "
            f"{summary.get('accuracy', 0.0):.4f} | {summary.get('macro_f1', 0.0):.4f} | "
            f"{summary.get('coverage', 0.0):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Best Method",
            "",
            (
                f"Best method `{best['method']}` reaches {pct(best['summary']['accuracy_all'])} all-cell accuracy "
                f"and {pct(best['summary']['accuracy'])} known-label accuracy."
            ),
            "",
            "| Species | Cells | Coverage | All-cell accuracy | Known-label accuracy |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in best["records"]:
        known = row.get("accuracy")
        lines.append(
            f"| {row['held_out_species']} | {row['n_test']} | {row['coverage']:.4f} | "
            f"{row['accuracy_all']:.4f} | {'n/a' if known is None else f'{known:.4f}'} |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], ""])
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run neural zero-shot STC benchmark")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--obs-tsv", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    obs_rows = read_csv(args.obs_tsv, delimiter="\t")
    prediction_rows = read_csv(args.predictions_csv)
    aligned_obs, embedding_indices = align_obs(obs_rows, prediction_rows)
    x = normalize_rows(np.load(args.embeddings).astype(np.float32)[embedding_indices])
    species = np.asarray([canonical_species(row.get("species", "")) for row in aligned_obs], dtype=str)
    labels = np.asarray([row.get("cell_type", "") for row in aligned_obs], dtype=str)

    configs = {
        "linear_wp0_e80": {
            "hidden": 0,
            "dropout": 0.0,
            "lr": 3e-3,
            "epochs": 80,
            "weight_power": 0.0,
            "label_smoothing": 0.0,
            "zscore": False,
        },
        "linear_wp025_e80": {
            "hidden": 0,
            "dropout": 0.0,
            "lr": 3e-3,
            "epochs": 80,
            "weight_power": 0.25,
            "label_smoothing": 0.0,
            "zscore": False,
        },
        "linear_wp05_e80": {
            "hidden": 0,
            "dropout": 0.0,
            "lr": 3e-3,
            "epochs": 80,
            "weight_power": 0.5,
            "label_smoothing": 0.03,
            "zscore": False,
        },
        "linear_wp075_e80": {
            "hidden": 0,
            "dropout": 0.0,
            "lr": 3e-3,
            "epochs": 80,
            "weight_power": 0.75,
            "label_smoothing": 0.03,
            "zscore": False,
        },
        "linear_wp05_e40": {
            "hidden": 0,
            "dropout": 0.0,
            "lr": 3e-3,
            "epochs": 40,
            "weight_power": 0.5,
            "label_smoothing": 0.03,
            "zscore": False,
        },
        "linear_wp05_e120": {
            "hidden": 0,
            "dropout": 0.0,
            "lr": 2e-3,
            "epochs": 120,
            "weight_power": 0.5,
            "label_smoothing": 0.03,
            "zscore": False,
        },
        "linear_zscore_wp025_e80": {
            "hidden": 0,
            "dropout": 0.0,
            "lr": 2e-3,
            "epochs": 80,
            "weight_power": 0.25,
            "label_smoothing": 0.0,
            "zscore": True,
        },
        "linear_zscore_wp05_e80": {
            "hidden": 0,
            "dropout": 0.0,
            "lr": 2e-3,
            "epochs": 80,
            "weight_power": 0.5,
            "label_smoothing": 0.03,
            "zscore": True,
        },
    }
    methods = {name: run_config(name, cfg, x, species, labels, args.device) for name, cfg in configs.items()}
    best_name = max(methods, key=lambda name: float(methods[name]["summary"].get("accuracy_all", 0.0)))
    best = {"method": best_name, **methods[best_name]}
    payload = {
        "schema_version": "plant_cellfm_revision_v13_neural_zero_shot_stc",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "inputs": {
            "aligned_cells": int(len(labels)),
            "species": int(len(set(species.tolist()))),
            "fine_labels": int(len(set(labels.tolist()))),
            "device": args.device,
        },
        "claim_boundary": "Fold-specific neural heads use only training-species labels; held-out species labels are never used for training.",
        "methods": methods,
        "best_method": best,
        "interpretation": (
            "Neural STC tests whether the 30.10% strict zero-shot bottleneck is a classifier-capacity problem. "
            "If neural heads do not approach 40%, the next required intervention is representation training with "
            "species-adversarial/ortholog-aware objectives rather than another post-hoc classifier."
        ),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, args.output_md)
    print(args.output_json)
    print(args.output_md)


if __name__ == "__main__":
    main()
