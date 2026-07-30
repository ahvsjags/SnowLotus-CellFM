from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import f1_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def align_obs_to_predictions(obs_rows: list[dict[str, str]], prediction_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for row in obs_rows:
        for key in ("cell_id", "_index"):
            value = row.get(key, "")
            if value:
                by_id[value] = row
    aligned: list[dict[str, str]] = []
    missing: list[str] = []
    for row in prediction_rows:
        cell_id = row.get("cell_id", "")
        obs = by_id.get(cell_id)
        if obs is None:
            missing.append(cell_id)
            continue
        aligned.append(obs)
    if missing:
        raise ValueError(f"{len(missing)} prediction cell IDs missing from obs TSV; examples={missing[:5]}")
    return aligned


def normalize_rows(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-8)


def canonical_species(value: Any) -> str:
    return " ".join(str(value).replace("_", " ").split())


def macro_f1(true: np.ndarray, pred: np.ndarray) -> float:
    return float(f1_score(true, pred, average="macro", zero_division=0))


def evaluate_predictions(
    truth: np.ndarray,
    pred: np.ndarray,
    train_labels: set[str],
) -> dict[str, Any]:
    covered = np.asarray([label in train_labels for label in truth], dtype=bool)
    result: dict[str, Any] = {
        "n_test": int(len(truth)),
        "n_evaluable": int(covered.sum()),
        "open_set_cells": int((~covered).sum()),
        "coverage": float(covered.mean()) if len(truth) else 0.0,
        "accuracy_all": float((truth == pred).mean()) if len(truth) else 0.0,
        "macro_f1_all": macro_f1(truth, pred) if len(truth) else 0.0,
        "truth_classes": int(len(set(truth.tolist()))),
        "prediction_classes": int(len(set(pred.tolist()))),
        "train_classes": int(len(train_labels)),
    }
    if covered.any():
        result["accuracy"] = float((truth[covered] == pred[covered]).mean())
        result["macro_f1"] = macro_f1(truth[covered], pred[covered])
    return result


def centroid_predict(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray) -> np.ndarray:
    labels = sorted(set(train_y.tolist()))
    centroids = np.asarray([train_x[train_y == label].mean(axis=0) for label in labels], dtype=np.float32)
    centroids = normalize_rows(centroids)
    scores = normalize_rows(test_x.astype(np.float32, copy=False)) @ centroids.T
    return np.asarray([labels[int(index)] for index in scores.argmax(axis=1)], dtype=str)


def fit_predict(method: str, train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray) -> np.ndarray:
    train_x = normalize_rows(train_x.astype(np.float32, copy=False))
    test_x = normalize_rows(test_x.astype(np.float32, copy=False))
    if method == "centroid_cosine":
        return centroid_predict(train_x, train_y, test_x)
    if method.startswith("knn_cosine_k") or method.startswith("knn_cosine_uniform_k"):
        uniform = method.startswith("knn_cosine_uniform_k")
        k = int(method.rsplit("k", 1)[1])
        k = min(k, len(train_y))
        model = KNeighborsClassifier(
            n_neighbors=k,
            metric="cosine",
            weights="uniform" if uniform else "distance",
        )
        model.fit(train_x, train_y)
        return model.predict(test_x).astype(str)
    if method == "linear_svc_balanced":
        model = make_pipeline(
            StandardScaler(with_mean=True, with_std=True),
            LinearSVC(class_weight="balanced", C=0.25, max_iter=10000, dual="auto"),
        )
        model.fit(train_x, train_y)
        return model.predict(test_x).astype(str)
    if method == "sgd_log_balanced":
        model = make_pipeline(
            StandardScaler(with_mean=True, with_std=True),
            SGDClassifier(
                loss="log_loss",
                penalty="elasticnet",
                alpha=1e-4,
                l1_ratio=0.05,
                class_weight="balanced",
                max_iter=3000,
                tol=1e-4,
                random_state=20260731,
            ),
        )
        model.fit(train_x, train_y)
        return model.predict(test_x).astype(str)
    if method == "logreg_balanced":
        # Encode labels explicitly so lbfgs handles moderately many imbalanced classes reliably.
        encoder = LabelEncoder()
        encoded_y = encoder.fit_transform(train_y)
        model = make_pipeline(
            StandardScaler(with_mean=True, with_std=True),
            LogisticRegression(
                class_weight="balanced",
                C=0.5,
                max_iter=2000,
                multi_class="auto",
                solver="lbfgs",
                n_jobs=1,
            ),
        )
        model.fit(train_x, encoded_y)
        pred = model.predict(test_x)
        return encoder.inverse_transform(pred).astype(str)
    raise ValueError(f"unknown method: {method}")


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
        out["macro_f1_all_weighted_by_cells"] = (
            sum(float(row["macro_f1_all"]) * int(row["n_test"]) for row in records) / total
        )
    if total_eval:
        out["accuracy"] = (
            sum(float(row.get("accuracy", 0.0)) * int(row["n_evaluable"]) for row in records) / total_eval
        )
        out["macro_f1"] = (
            sum(float(row.get("macro_f1", 0.0)) * int(row["n_evaluable"]) for row in records) / total_eval
        )
    return out


def run_benchmark(
    embeddings: np.ndarray,
    obs_rows: list[dict[str, str]],
    methods: list[str],
    *,
    label_key: str,
    min_test_cells: int,
) -> dict[str, Any]:
    species = np.asarray([canonical_species(row.get("species", "")) for row in obs_rows], dtype=str)
    labels = np.asarray([row.get(label_key, "") for row in obs_rows], dtype=str)
    keep = np.asarray([bool(label) and bool(group) for label, group in zip(labels, species, strict=True)])
    embeddings = embeddings[keep]
    species = species[keep]
    labels = labels[keep]
    groups = [group for group, count in Counter(species.tolist()).items() if count >= min_test_cells]

    method_records: dict[str, list[dict[str, Any]]] = {method: [] for method in methods}
    for group in sorted(groups):
        test_mask = species == group
        train_mask = ~test_mask
        train_y = labels[train_mask]
        test_y = labels[test_mask]
        train_label_set = set(train_y.tolist())
        if len(train_label_set) < 2 or len(test_y) == 0:
            continue
        for method in methods:
            pred = fit_predict(method, embeddings[train_mask], train_y, embeddings[test_mask])
            row = evaluate_predictions(test_y, pred, train_label_set)
            row["held_out_species"] = group
            row["method"] = method
            method_records[method].append(row)

    return {
        "label_key": label_key,
        "n_cells": int(len(labels)),
        "species": int(len(set(species.tolist()))),
        "methods": {
            method: {
                "summary": aggregate(records),
                "records": records,
            }
            for method, records in method_records.items()
        },
    }


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    lines = [
        "# Plant-CellFM v10 Cross-Species Classifier Benchmark",
        "",
        "This benchmark reuses the frozen v9 runtime-smoke embeddings and the same leave-species-out split. It tests whether classifier/metric calibration can improve exact-label species transfer without changing the held-out species labels or using held-out species for training.",
        "",
        "## Summary",
        "",
        "| Label key | Method | all-cell accuracy | known-label accuracy | macro-F1 | coverage | open-set cells |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for section in payload["benchmarks"]:
        label_key = section["label_key"]
        for method, data in section["methods"].items():
            summary = data["summary"]
            lines.append(
                "| {label_key} | {method} | {all_acc:.4f} | {known:.4f} | {f1:.4f} | {cov:.4f} | {open_set} |".format(
                    label_key=label_key,
                    method=method,
                    all_acc=float(summary.get("accuracy_all", 0.0)),
                    known=float(summary.get("accuracy", 0.0)),
                    f1=float(summary.get("macro_f1", 0.0)),
                    cov=float(summary.get("coverage", 0.0)),
                    open_set=int(summary.get("open_set_cells", 0)),
                )
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "An all-cell improvement here is a real held-out-species improvement for the frozen embedding plus classifier layer. The maximum exact-label all-cell accuracy remains limited by labels absent from the training species folds, so coverage is reported beside every score.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark cross-species classifier calibration on frozen embeddings")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--obs-tsv", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--min-test-cells", type=int, default=20)
    parser.add_argument(
        "--methods",
        nargs="+",
        default=[
            "centroid_cosine",
            "knn_cosine_k1",
            "knn_cosine_k3",
            "knn_cosine_k5",
            "knn_cosine_k7",
            "knn_cosine_k9",
            "knn_cosine_k11",
            "knn_cosine_k15",
            "knn_cosine_k21",
            "knn_cosine_k31",
            "knn_cosine_uniform_k5",
            "knn_cosine_uniform_k9",
            "knn_cosine_uniform_k15",
            "linear_svc_balanced",
            "sgd_log_balanced",
            "logreg_balanced",
        ],
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    embeddings = np.load(args.embeddings)
    obs_rows = read_tsv(args.obs_tsv)
    if args.predictions_csv:
        obs_rows = align_obs_to_predictions(obs_rows, read_csv(args.predictions_csv))
    if embeddings.shape[0] != len(obs_rows):
        raise ValueError(f"embedding rows {embeddings.shape[0]} != obs rows {len(obs_rows)}")
    payload = {
        "schema_version": "plant_cellfm_cross_species_classifier_benchmark_v10",
        "embeddings": str(args.embeddings),
        "obs_tsv": str(args.obs_tsv),
        "predictions_csv": str(args.predictions_csv) if args.predictions_csv else None,
        "embedding_shape": list(embeddings.shape),
        "benchmarks": [
            run_benchmark(
                embeddings,
                obs_rows,
                args.methods,
                label_key="cell_type",
                min_test_cells=args.min_test_cells,
            ),
            run_benchmark(
                embeddings,
                obs_rows,
                args.methods,
                label_key="cell_type_coarse",
                min_test_cells=args.min_test_cells,
            ),
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, args.output_md)
    print(args.output_json)
    for section in payload["benchmarks"]:
        print(section["label_key"])
        for method, data in section["methods"].items():
            summary = data["summary"]
            print(method, json.dumps({k: v for k, v in summary.items() if k != "records"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
