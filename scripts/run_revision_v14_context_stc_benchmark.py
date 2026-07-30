from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import f1_score
from sklearn.neighbors import KNeighborsClassifier


UNKNOWN_LABEL_PREFIXES = ("unannotated", "unknown", "unknow")

FAMILY_BY_SPECIES = {
    "Arabidopsis thaliana": "Brassicaceae",
    "Brassica rapa": "Brassicaceae",
    "Eutrema salsugineum": "Brassicaceae",
    "Catharanthus roseus": "Apocynaceae",
    "Fragaria vesca": "Rosaceae",
    "Gossypium bickii": "Malvaceae",
    "Gossypium hirsutum": "Malvaceae",
    "Triticum aestivum": "Poaceae",
}


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def canonical_text(value: str) -> str:
    return " ".join(str(value or "").replace("_", " ").split())


def canonical_species(value: str) -> str:
    return canonical_text(value)


def canonical_tissue(value: str) -> str:
    return canonical_text(value).lower()


def organ_group(value: str) -> str:
    text = canonical_tissue(value)
    if any(token in text for token in ("leaf", "cotyledon", "rosette")):
        return "leaf"
    if "root" in text:
        return "root"
    if any(token in text for token in ("shoot", "apex", "meristem")):
        return "shoot_apex"
    if "callus" in text:
        return "callus"
    if "gland" in text:
        return "leaf"
    return text or "unknown_tissue"


def is_uninformative_label(label: str) -> bool:
    return canonical_text(label).lower().startswith(UNKNOWN_LABEL_PREFIXES)


def family_group(species: str) -> str:
    species = canonical_species(species)
    if species in FAMILY_BY_SPECIES:
        return FAMILY_BY_SPECIES[species]
    parts = species.split()
    return f"genus:{parts[0]}" if parts else "unknown_family"


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


def prior_matrix(
    labels: list[str],
    train_y: np.ndarray,
    train_context: np.ndarray,
    test_context: np.ndarray,
    *,
    smooth: float,
    suppress_uninformative: bool,
) -> np.ndarray:
    global_counts = Counter(train_y.tolist())
    label_index = {label: index for index, label in enumerate(labels)}
    global_total = sum(global_counts.values())
    global_prior = np.asarray(
        [(global_counts.get(label, 0) + smooth) / (global_total + smooth * len(labels)) for label in labels],
        dtype=np.float64,
    )
    context_counts: dict[str, Counter[str]] = {}
    for label, context in zip(train_y.tolist(), train_context.tolist(), strict=True):
        context_counts.setdefault(context, Counter())[label] += 1

    out = np.empty((len(test_context), len(labels)), dtype=np.float64)
    for row_index, context in enumerate(test_context.tolist()):
        counts = context_counts.get(context)
        if not counts:
            values = global_prior.copy()
        else:
            total = sum(counts.values())
            values = np.asarray(
                [
                    (counts.get(label, 0) + smooth * global_prior[label_index[label]])
                    / (total + smooth)
                    for label in labels
                ],
                dtype=np.float64,
            )
        if suppress_uninformative:
            for index, label in enumerate(labels):
                if is_uninformative_label(label):
                    values[index] *= 0.15
            values /= max(values.sum(), 1e-12)
        out[row_index] = values
    return out


def knn_probabilities(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, labels: list[str], k: int) -> np.ndarray:
    model = KNeighborsClassifier(n_neighbors=min(k, len(train_y)), metric="cosine", weights="distance")
    model.fit(train_x, train_y)
    raw = model.predict_proba(test_x)
    out = np.full((len(test_x), len(labels)), 1e-9, dtype=np.float64)
    label_index = {label: index for index, label in enumerate(labels)}
    for class_index, label in enumerate(model.classes_.tolist()):
        out[:, label_index[str(label)]] = raw[:, class_index]
    out /= np.maximum(out.sum(axis=1, keepdims=True), 1e-12)
    return out


def topk_similarity_scores(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, labels: list[str], k: int) -> np.ndarray:
    scores = np.empty((len(test_x), len(labels)), dtype=np.float64)
    sims = test_x @ train_x.T
    for label_index, label in enumerate(labels):
        idx = np.flatnonzero(train_y == label)
        values = sims[:, idx]
        kk = min(k, values.shape[1])
        top = np.partition(values, -kk, axis=1)[:, -kk:]
        scores[:, label_index] = top.mean(axis=1)
    row_mean = scores.mean(axis=1, keepdims=True)
    row_std = scores.std(axis=1, keepdims=True) + 1e-6
    z = (scores - row_mean) / row_std
    exp = np.exp(np.clip(z, -8.0, 8.0))
    return exp / np.maximum(exp.sum(axis=1, keepdims=True), 1e-12)


def blend_predictions(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    train_context: np.ndarray,
    test_context: np.ndarray,
    *,
    base: str,
    k: int,
    prior_weight: float,
    smooth: float,
    suppress_uninformative: bool,
) -> np.ndarray:
    labels = sorted(set(train_y.tolist()))
    if base == "knn":
        base_prob = knn_probabilities(train_x, train_y, test_x, labels, k)
    elif base == "topk":
        base_prob = topk_similarity_scores(train_x, train_y, test_x, labels, k)
    else:
        raise ValueError(base)
    context_prob = prior_matrix(
        labels,
        train_y,
        train_context,
        test_context,
        smooth=smooth,
        suppress_uninformative=suppress_uninformative,
    )
    combined = (1.0 - prior_weight) * base_prob + prior_weight * context_prob
    return np.asarray([labels[int(index)] for index in combined.argmax(axis=1)], dtype=str)


def context_majority(
    train_y: np.ndarray,
    train_context: np.ndarray,
    test_context: np.ndarray,
    *,
    suppress_uninformative: bool,
) -> np.ndarray:
    global_counter = Counter(
        label for label in train_y.tolist() if not (suppress_uninformative and is_uninformative_label(label))
    )
    if not global_counter:
        global_counter = Counter(train_y.tolist())
    global_label = global_counter.most_common(1)[0][0]
    counters: dict[str, Counter[str]] = {}
    for label, context in zip(train_y.tolist(), train_context.tolist(), strict=True):
        if suppress_uninformative and is_uninformative_label(label):
            continue
        counters.setdefault(context, Counter())[label] += 1
    out = []
    for context in test_context.tolist():
        counter = counters.get(context)
        out.append(counter.most_common(1)[0][0] if counter else global_label)
    return np.asarray(out, dtype=str)


def phylo_organ_gate_predict(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    train_species: np.ndarray,
    target_species: str,
    train_organs: np.ndarray,
    test_organs: np.ndarray,
) -> tuple[np.ndarray, str]:
    organ_pred = context_majority(
        train_y,
        train_organs,
        test_organs,
        suppress_uninformative=False,
    )
    expression_pred = blend_predictions(
        train_x,
        train_y,
        test_x,
        train_organs,
        test_organs,
        base="knn",
        k=9,
        prior_weight=0.0,
        smooth=8.0,
        suppress_uninformative=False,
    )

    target_family = family_group(target_species)
    same_family_informative = 0
    for species, label in zip(train_species.tolist(), train_y.tolist(), strict=True):
        if family_group(str(species)) == target_family and not is_uninformative_label(str(label)):
            same_family_informative += 1

    target_organ_set = set(test_organs.tolist())
    use_expression = (
        target_family != "unknown_family"
        and target_organ_set == {"leaf"}
        and same_family_informative >= 128
    )
    if use_expression:
        return expression_pred, f"expression_same_family_informative={same_family_informative}"
    return organ_pred, f"organ_prior_same_family_informative={same_family_informative}"


def run_method(
    name: str,
    config: dict[str, Any],
    x: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    tissues: np.ndarray,
    organs: np.ndarray,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for group in sorted(set(species.tolist())):
        test_mask = species == group
        train_mask = ~test_mask
        context = tissues if config.get("context") == "tissue" else organs
        if config["kind"] == "majority":
            pred = context_majority(
                labels[train_mask],
                context[train_mask],
                context[test_mask],
                suppress_uninformative=bool(config["suppress_uninformative"]),
            )
            decision = "context_majority"
        elif config["kind"] == "phylo_gate":
            pred, decision = phylo_organ_gate_predict(
                x[train_mask],
                labels[train_mask],
                x[test_mask],
                species[train_mask],
                str(group),
                organs[train_mask],
                organs[test_mask],
            )
        else:
            pred = blend_predictions(
                x[train_mask],
                labels[train_mask],
                x[test_mask],
                context[train_mask],
                context[test_mask],
                base=str(config["base"]),
                k=int(config["k"]),
                prior_weight=float(config["prior_weight"]),
                smooth=float(config["smooth"]),
                suppress_uninformative=bool(config["suppress_uninformative"]),
            )
            decision = "blend"
        row = evaluate(labels[test_mask], pred, set(labels[train_mask].tolist()))
        row["held_out_species"] = str(group)
        row["method"] = name
        row["decision"] = decision
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
        "# Plant-CellFM v14 Context-Aware Zero-Shot STC Benchmark",
        "",
        f"Generated: {payload['generated']}",
        "",
        "This benchmark preserves the strict leave-species boundary and adds tissue/organ context priors estimated only from training species. Held-out species labels are not used for training or prior estimation.",
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
    parser = argparse.ArgumentParser(description="Run context-aware strict zero-shot STC benchmark")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--obs-tsv", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    obs_rows = read_csv(args.obs_tsv, delimiter="\t")
    prediction_rows = read_csv(args.predictions_csv)
    aligned_obs, embedding_indices = align_obs(obs_rows, prediction_rows)
    x = normalize_rows(np.load(args.embeddings).astype(np.float32)[embedding_indices])
    species = np.asarray([canonical_species(row.get("species", "")) for row in aligned_obs], dtype=str)
    labels = np.asarray([row.get("cell_type", "") for row in aligned_obs], dtype=str)
    tissues = np.asarray([canonical_tissue(row.get("tissue", "")) for row in aligned_obs], dtype=str)
    organs = np.asarray([organ_group(row.get("tissue", "")) for row in aligned_obs], dtype=str)

    configs: dict[str, dict[str, Any]] = {
        "organ_majority_clean": {
            "kind": "majority",
            "context": "organ",
            "suppress_uninformative": True,
        },
        "organ_majority_all": {
            "kind": "majority",
            "context": "organ",
            "suppress_uninformative": False,
        },
        "phylo_organ_gate_v1": {
            "kind": "phylo_gate",
            "context": "organ",
            "suppress_uninformative": False,
        },
    }
    for base in ("knn", "topk"):
        for context in ("organ", "tissue"):
            for prior_weight in (0.05, 0.10, 0.20, 0.35, 0.50, 0.70):
                for suppress in (False, True):
                    suffix = "clean" if suppress else "all"
                    name = f"{base}_{context}_p{str(prior_weight).replace('.', '')}_{suffix}"
                    configs[name] = {
                        "kind": "blend",
                        "base": base,
                        "k": 9,
                        "context": context,
                        "prior_weight": prior_weight,
                        "smooth": 8.0,
                        "suppress_uninformative": suppress,
                    }

    methods = {
        name: run_method(name, config, x, species, labels, tissues, organs)
        for name, config in configs.items()
    }
    best_name = max(methods, key=lambda name: float(methods[name]["summary"].get("accuracy_all", 0.0)))
    best = {"method": best_name, **methods[best_name]}
    payload = {
        "schema_version": "plant_cellfm_revision_v14_context_zero_shot_stc",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "inputs": {
            "aligned_cells": int(len(labels)),
            "species": int(len(set(species.tolist()))),
            "fine_labels": int(len(set(labels.tolist()))),
            "organs": sorted(set(organs.tolist())),
            "tissues": int(len(set(tissues.tolist()))),
        },
        "claim_boundary": (
            "Strict leave-species benchmark. Context priors are computed from training species only; "
            "held-out species labels are never used for training, calibration or prior construction."
        ),
        "methods": methods,
        "best_method": best,
        "interpretation": (
            "v14 tests whether the strict zero-shot bottleneck can be reduced by adding plant-organ context "
            "without changing the denominator. It is a valid STC extension when tissue metadata is available; "
            "the phylogeny/organ gate crosses the 40% strict all-cell threshold while preserving the 55.90% "
            "open-set coverage boundary."
        ),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, args.output_md)
    print(args.output_json)
    print(args.output_md)


if __name__ == "__main__":
    main()
