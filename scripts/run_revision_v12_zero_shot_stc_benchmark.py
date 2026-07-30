from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import f1_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC


UNKNOWN = ""


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def canonical_species(value: str) -> str:
    return " ".join(str(value or "").replace("_", " ").split())


def normalize_rows(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-8)


def align_obs(
    obs_rows: list[dict[str, str]],
    prediction_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[int]]:
    by_cell: dict[str, dict[str, str]] = {}
    for row in obs_rows:
        for key in ("cell_id", "_index"):
            value = row.get(key, "")
            if value:
                by_cell[value] = row
    aligned: list[dict[str, str]] = []
    embedding_indices: list[int] = []
    missing: list[str] = []
    for index, row in enumerate(prediction_rows):
        cell_id = row.get("cell_id", "")
        obs = by_cell.get(cell_id)
        if obs is None:
            missing.append(cell_id)
            continue
        if obs.get("species") and obs.get("cell_type"):
            aligned.append(obs)
            embedding_indices.append(index)
    if missing:
        raise ValueError(f"{len(missing)} prediction IDs missing from obs; examples={missing[:5]}")
    return aligned, embedding_indices


def macro_f1(truth: np.ndarray, pred: np.ndarray) -> float:
    if len(truth) == 0:
        return 0.0
    return float(f1_score(truth, pred, average="macro", zero_division=0))


def evaluate_predictions(truth: np.ndarray, pred: np.ndarray, train_labels: set[str]) -> dict[str, Any]:
    covered = np.asarray([label in train_labels for label in truth], dtype=bool)
    result: dict[str, Any] = {
        "n_test": int(len(truth)),
        "n_evaluable": int(covered.sum()),
        "open_set_cells": int((~covered).sum()),
        "coverage": float(covered.mean()) if len(truth) else 0.0,
        "accuracy_all": float((truth == pred).mean()) if len(truth) else 0.0,
        "macro_f1_all": macro_f1(truth, pred),
        "truth_classes": int(len(set(truth.tolist()))),
        "prediction_classes": int(len(set(pred.tolist()))),
        "train_classes": int(len(train_labels)),
    }
    if covered.any():
        result["accuracy"] = float((truth[covered] == pred[covered]).mean())
        result["macro_f1"] = macro_f1(truth[covered], pred[covered])
    return result


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


class Fold:
    def __init__(
        self,
        train_x: np.ndarray,
        train_y: np.ndarray,
        test_x: np.ndarray,
        train_tissue: np.ndarray,
        test_tissue: np.ndarray,
        train_coarse: np.ndarray,
        test_species: str,
    ) -> None:
        self.train_x = train_x
        self.train_y = train_y
        self.test_x = test_x
        self.train_tissue = train_tissue
        self.test_tissue = test_tissue
        self.train_coarse = train_coarse
        self.test_species = test_species


Predictor = Callable[[Fold], np.ndarray]


def centroid_predictor() -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        labels = sorted(set(fold.train_y.tolist()))
        centroids = normalize_rows(
            np.asarray([fold.train_x[fold.train_y == label].mean(axis=0) for label in labels], dtype=np.float32)
        )
        return np.asarray([labels[int(index)] for index in (fold.test_x @ centroids.T).argmax(axis=1)], dtype=str)

    return predict


def knn_predictor(k: int, weights: str = "distance") -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        model = KNeighborsClassifier(n_neighbors=min(k, len(fold.train_y)), metric="cosine", weights=weights)
        model.fit(fold.train_x, fold.train_y)
        return model.predict(fold.test_x).astype(str)

    return predict


def linear_svc_predictor(c_value: float) -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        model = make_pipeline(
            StandardScaler(with_mean=True, with_std=True),
            LinearSVC(C=c_value, class_weight="balanced", max_iter=20000, dual="auto"),
        )
        model.fit(fold.train_x, fold.train_y)
        return model.predict(fold.test_x).astype(str)

    return predict


def logreg_predictor(c_value: float) -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        encoder = LabelEncoder()
        encoded = encoder.fit_transform(fold.train_y)
        model = make_pipeline(
            StandardScaler(with_mean=True, with_std=True),
            LogisticRegression(
                C=c_value,
                class_weight="balanced",
                max_iter=2500,
                solver="lbfgs",
                n_jobs=1,
            ),
        )
        model.fit(fold.train_x, encoded)
        return encoder.inverse_transform(model.predict(fold.test_x)).astype(str)

    return predict


def sgd_predictor(alpha: float) -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        model = make_pipeline(
            StandardScaler(with_mean=True, with_std=True),
            SGDClassifier(
                loss="modified_huber",
                alpha=alpha,
                class_weight="balanced",
                max_iter=5000,
                tol=1e-4,
                random_state=20260801,
            ),
        )
        model.fit(fold.train_x, fold.train_y)
        return model.predict(fold.test_x).astype(str)

    return predict


def label_topk_predictor(k: int, *, centered: bool = False) -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        train_x = fold.train_x
        test_x = fold.test_x
        if centered:
            train_x = normalize_rows(train_x - train_x.mean(axis=0, keepdims=True))
            test_x = normalize_rows(test_x - test_x.mean(axis=0, keepdims=True))
        labels = sorted(set(fold.train_y.tolist()))
        label_indices = {label: np.where(fold.train_y == label)[0] for label in labels}
        scores = test_x @ train_x.T
        out: list[str] = []
        for row in scores:
            best_label = labels[0]
            best_score = -1e9
            for label, indices in label_indices.items():
                values = row[indices]
                kk = min(k, len(values))
                top = np.partition(values, -kk)[-kk:]
                score = float(top.mean())
                if score > best_score:
                    best_score = score
                    best_label = label
            out.append(best_label)
        return np.asarray(out, dtype=str)

    return predict


def subcentroid_predictor(max_clusters: int, min_cluster_size: int = 16) -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        prototypes: list[np.ndarray] = []
        prototype_labels: list[str] = []
        for label in sorted(set(fold.train_y.tolist())):
            values = fold.train_x[fold.train_y == label]
            clusters = max(1, min(max_clusters, len(values) // min_cluster_size))
            if clusters == 1:
                prototypes.append(values.mean(axis=0))
                prototype_labels.append(label)
                continue
            model = MiniBatchKMeans(
                n_clusters=clusters,
                random_state=20260801,
                batch_size=256,
                n_init=3,
                max_iter=80,
            )
            model.fit(values)
            for center in model.cluster_centers_:
                prototypes.append(center)
                prototype_labels.append(label)
        prototype_matrix = normalize_rows(np.asarray(prototypes, dtype=np.float32))
        return np.asarray([prototype_labels[int(index)] for index in (fold.test_x @ prototype_matrix.T).argmax(axis=1)])

    return predict


def tissue_gated_knn_predictor(k: int) -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        out = np.empty(len(fold.test_x), dtype=object)
        fallback = KNeighborsClassifier(n_neighbors=min(k, len(fold.train_y)), metric="cosine", weights="distance")
        fallback.fit(fold.train_x, fold.train_y)
        for tissue in sorted(set(fold.test_tissue.tolist())):
            test_mask = fold.test_tissue == tissue
            train_mask = fold.train_tissue == tissue
            if int(train_mask.sum()) >= max(16, k):
                model = KNeighborsClassifier(
                    n_neighbors=min(k, int(train_mask.sum())),
                    metric="cosine",
                    weights="distance",
                )
                model.fit(fold.train_x[train_mask], fold.train_y[train_mask])
                out[test_mask] = model.predict(fold.test_x[test_mask]).astype(str)
            else:
                out[test_mask] = fallback.predict(fold.test_x[test_mask]).astype(str)
        return out.astype(str)

    return predict


def diagonal_coral(base: Predictor) -> Predictor:
    def predict(fold: Fold) -> np.ndarray:
        train_mu = fold.train_x.mean(axis=0, keepdims=True)
        train_sd = fold.train_x.std(axis=0, keepdims=True) + 1e-4
        test_mu = fold.test_x.mean(axis=0, keepdims=True)
        test_sd = fold.test_x.std(axis=0, keepdims=True) + 1e-4
        shifted_test = normalize_rows((fold.test_x - test_mu) / test_sd * train_sd + train_mu)
        return base(
            Fold(
                fold.train_x,
                fold.train_y,
                shifted_test,
                fold.train_tissue,
                fold.test_tissue,
                fold.train_coarse,
                fold.test_species,
            )
        )

    return predict


def run_benchmark(
    embeddings: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    tissues: np.ndarray,
    coarse: np.ndarray,
    methods: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    out_methods: dict[str, dict[str, Any]] = {}
    for method_name, method in methods.items():
        predictor: Predictor = method["predictor"]
        records = []
        for group in sorted(set(species.tolist())):
            test_mask = species == group
            train_mask = ~test_mask
            train_labels = set(labels[train_mask].tolist())
            fold = Fold(
                embeddings[train_mask],
                labels[train_mask],
                embeddings[test_mask],
                tissues[train_mask],
                tissues[test_mask],
                coarse[train_mask],
                str(group),
            )
            pred = predictor(fold)
            row = evaluate_predictions(labels[test_mask], pred, train_labels)
            row["held_out_species"] = str(group)
            row["method"] = method_name
            row["protocol"] = method["protocol"]
            records.append(row)
        summary = aggregate(records)
        out_methods[method_name] = {
            "protocol": method["protocol"],
            "summary": summary,
            "records": records,
        }
        print(
            f"{method_name}\t{method['protocol']}\tall={summary.get('accuracy_all', 0.0):.4f}\t"
            f"known={summary.get('accuracy', 0.0):.4f}\tf1={summary.get('macro_f1', 0.0):.4f}\t"
            f"coverage={summary.get('coverage', 0.0):.4f}",
            flush=True,
        )
    return out_methods


def pct(value: float) -> str:
    return f"{100 * float(value):.2f}%"


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    best = payload["best_method"]
    baseline = payload["baseline_method"]
    lines = [
        "# Plant-CellFM v12 Strict Zero-Shot STC Benchmark",
        "",
        f"Generated: {payload['generated']}",
        "",
        "## Protocol",
        "",
        "This benchmark keeps the same frozen runtime-smoke embeddings and the same leave-species split. Methods marked `inductive_zero_shot` use only training-species labeled cells. Methods marked `zero_label_transductive` may use the unlabeled held-out species embedding distribution, but never held-out labels.",
        "",
        "## Summary",
        "",
        "| Method | Protocol | All-cell accuracy | Known-label accuracy | Macro-F1 | Coverage |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for name, data in payload["methods"].items():
        summary = data["summary"]
        lines.append(
            f"| `{name}` | {data['protocol']} | {summary.get('accuracy_all', 0.0):.4f} | "
            f"{summary.get('accuracy', 0.0):.4f} | {summary.get('macro_f1', 0.0):.4f} | "
            f"{summary.get('coverage', 0.0):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Best Strict Result",
            "",
            (
                f"Baseline v10 `knn_cosine_k9`: {pct(baseline['summary']['accuracy_all'])} all-cell, "
                f"{pct(baseline['summary']['accuracy'])} known-label."
            ),
            (
                f"Best v12 method `{best['method']}` ({best['protocol']}): "
                f"{pct(best['summary']['accuracy_all'])} all-cell, "
                f"{pct(best['summary']['accuracy'])} known-label."
            ),
            "",
            "## Per-Species Records For Best Method",
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
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v12 strict zero-shot STC benchmark")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--obs-tsv", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    obs_rows = read_csv(args.obs_tsv, delimiter="\t")
    prediction_rows = read_csv(args.predictions_csv)
    aligned_obs, embedding_indices = align_obs(obs_rows, prediction_rows)
    embeddings = normalize_rows(np.load(args.embeddings).astype(np.float32)[embedding_indices])
    species = np.asarray([canonical_species(row.get("species", "")) for row in aligned_obs], dtype=str)
    labels = np.asarray([row.get("cell_type", "") for row in aligned_obs], dtype=str)
    tissues = np.asarray([canonical_species(row.get("tissue", "")) or UNKNOWN for row in aligned_obs], dtype=str)
    coarse = np.asarray([row.get("cell_type_coarse", "") or UNKNOWN for row in aligned_obs], dtype=str)

    methods = {
        "centroid_cosine": {"protocol": "inductive_zero_shot", "predictor": centroid_predictor()},
        "knn_cosine_k9": {"protocol": "inductive_zero_shot", "predictor": knn_predictor(9)},
        "sgd_huber_a1e_4": {"protocol": "inductive_zero_shot", "predictor": sgd_predictor(1e-4)},
        "sgd_huber_a1e_5": {"protocol": "inductive_zero_shot", "predictor": sgd_predictor(1e-5)},
        "logreg_c0_1": {"protocol": "inductive_zero_shot", "predictor": logreg_predictor(0.1)},
        "logreg_c1": {"protocol": "inductive_zero_shot", "predictor": logreg_predictor(1.0)},
        "label_top3_mean": {"protocol": "inductive_zero_shot", "predictor": label_topk_predictor(3)},
        "label_top5_mean": {"protocol": "inductive_zero_shot", "predictor": label_topk_predictor(5)},
        "label_top9_mean": {"protocol": "inductive_zero_shot", "predictor": label_topk_predictor(9)},
        "subcentroid_max4": {"protocol": "inductive_zero_shot", "predictor": subcentroid_predictor(4)},
        "subcentroid_max8": {"protocol": "inductive_zero_shot", "predictor": subcentroid_predictor(8)},
        "tissue_gated_knn_k9": {"protocol": "inductive_zero_shot", "predictor": tissue_gated_knn_predictor(9)},
        "centered_label_top5": {"protocol": "zero_label_transductive", "predictor": label_topk_predictor(5, centered=True)},
        "coral_centroid": {"protocol": "zero_label_transductive", "predictor": diagonal_coral(centroid_predictor())},
        "coral_knn_k9": {"protocol": "zero_label_transductive", "predictor": diagonal_coral(knn_predictor(9))},
        "coral_label_top5": {"protocol": "zero_label_transductive", "predictor": diagonal_coral(label_topk_predictor(5))},
    }

    method_results = run_benchmark(embeddings, species, labels, tissues, coarse, methods)
    baseline = method_results["knn_cosine_k9"]
    best_name = max(method_results, key=lambda name: float(method_results[name]["summary"].get("accuracy_all", 0.0)))
    best = {"method": best_name, **method_results[best_name]}
    interpretation = (
        "v12 tests stronger zero-label calibration while preserving the held-out-label boundary. "
        "If the best method remains below 40% all-cell, the remaining bottleneck is not packaging but "
        "representation/domain transfer for high-coverage failing species such as Catharanthus and cotton."
    )
    payload = {
        "schema_version": "plant_cellfm_revision_v12_zero_shot_stc_benchmark",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "inputs": {
            "embeddings": str(args.embeddings),
            "obs_tsv": str(args.obs_tsv),
            "predictions_csv": str(args.predictions_csv),
            "aligned_cells": int(len(labels)),
            "species": int(len(set(species.tolist()))),
            "fine_labels": int(len(set(labels.tolist()))),
        },
        "claim_boundary": (
            "Held-out species labels are never used for classifier training. "
            "inductive_zero_shot uses only training-species labeled cells; zero_label_transductive additionally "
            "uses the unlabeled held-out embedding distribution."
        ),
        "methods": {
            name: {key: value for key, value in data.items() if key != "predictor"}
            for name, data in method_results.items()
        },
        "baseline_method": {"method": "knn_cosine_k9", **baseline},
        "best_method": best,
        "interpretation": interpretation,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, args.output_md)
    print(args.output_json)
    print(args.output_md)


if __name__ == "__main__":
    main()
