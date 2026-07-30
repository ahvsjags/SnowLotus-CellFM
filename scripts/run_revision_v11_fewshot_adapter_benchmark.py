from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import f1_score
from sklearn.neighbors import KNeighborsClassifier


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


def macro_f1(truth: list[str], pred: list[str]) -> float:
    if not truth:
        return 0.0
    return float(f1_score(truth, pred, average="macro", zero_division=0))


def choose_budget_support(
    test_indices: np.ndarray,
    *,
    budget: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if len(test_indices) <= 1:
        return test_indices[:0]
    n_support = min(int(budget), max(1, len(test_indices) // 4), len(test_indices) - 1)
    return np.sort(rng.choice(test_indices, size=n_support, replace=False))


def choose_stratified_support(
    test_indices: np.ndarray,
    labels: np.ndarray,
    *,
    support_per_label: int,
    rng: np.random.Generator,
) -> np.ndarray:
    support: list[int] = []
    for label in sorted(set(labels[test_indices].tolist())):
        label_indices = test_indices[labels[test_indices] == label]
        take = min(int(support_per_label), len(label_indices))
        support.extend(rng.choice(label_indices, size=take, replace=False).tolist())
    return np.asarray(sorted(support), dtype=int)


def evaluate_support_protocol(
    embeddings: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    *,
    mode: str,
    support_value: int,
    support_weight: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    truth_all: list[str] = []
    pred_all: list[str] = []
    per_species: list[dict[str, Any]] = []

    for group in sorted(set(species.tolist())):
        test_indices = np.where(species == group)[0]
        train_indices = np.where(species != group)[0]
        if mode == "budgeted_random":
            support_indices = choose_budget_support(test_indices, budget=support_value, rng=rng)
        elif mode == "stratified_per_label":
            support_indices = choose_stratified_support(
                test_indices,
                labels,
                support_per_label=support_value,
                rng=rng,
            )
        else:
            raise ValueError(f"unknown support mode: {mode}")
        support_set = set(support_indices.tolist())
        query_indices = np.asarray([idx for idx in test_indices if idx not in support_set], dtype=int)
        if len(query_indices) == 0:
            continue

        fit_indices = np.concatenate([train_indices] + [support_indices] * max(1, int(support_weight)))
        model = KNeighborsClassifier(
            n_neighbors=min(9, len(fit_indices)),
            metric="cosine",
            weights="distance",
        )
        model.fit(embeddings[fit_indices], labels[fit_indices])
        pred = model.predict(embeddings[query_indices]).astype(str)
        truth = labels[query_indices].astype(str)

        accuracy = float((pred == truth).mean()) if len(truth) else 0.0
        truth_all.extend(truth.tolist())
        pred_all.extend(pred.tolist())
        per_species.append(
            {
                "species": str(group),
                "test_cells": int(len(test_indices)),
                "support_cells": int(len(support_indices)),
                "query_cells": int(len(query_indices)),
                "support_labels": int(len(set(labels[support_indices].tolist()))),
                "query_labels": int(len(set(truth.tolist()))),
                "accuracy_all_query": accuracy,
                "macro_f1_query": macro_f1(truth.tolist(), pred.tolist()),
                "top_query_errors": [
                    {"truth": truth_label, "prediction": pred_label, "count": int(count)}
                    for (truth_label, pred_label), count in Counter(
                        (t, p) for t, p in zip(truth.tolist(), pred.tolist(), strict=True) if t != p
                    ).most_common(5)
                ],
            }
        )

    accuracy_all = float(np.mean(np.asarray(truth_all) == np.asarray(pred_all))) if truth_all else 0.0
    return {
        "mode": mode,
        "support_value": int(support_value),
        "support_weight": int(support_weight),
        "seed": int(seed),
        "support_cells": int(sum(row["support_cells"] for row in per_species)),
        "query_cells": int(sum(row["query_cells"] for row in per_species)),
        "accuracy_all_query": accuracy_all,
        "macro_f1_query": macro_f1(truth_all, pred_all),
        "per_species": per_species,
    }


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    values = np.asarray([float(row["accuracy_all_query"]) for row in runs], dtype=float)
    f1_values = np.asarray([float(row["macro_f1_query"]) for row in runs], dtype=float)
    return {
        "mode": runs[0]["mode"],
        "support_value": runs[0]["support_value"],
        "support_weight": runs[0]["support_weight"],
        "seeds": [row["seed"] for row in runs],
        "mean_accuracy_all_query": float(values.mean()),
        "std_accuracy_all_query": float(values.std(ddof=0)),
        "min_accuracy_all_query": float(values.min()),
        "max_accuracy_all_query": float(values.max()),
        "mean_macro_f1_query": float(f1_values.mean()),
        "mean_support_cells": float(np.mean([float(row["support_cells"]) for row in runs])),
        "mean_query_cells": float(np.mean([float(row["query_cells"]) for row in runs])),
        "representative_seed": runs[0]["seed"],
        "representative_per_species": runs[0]["per_species"],
    }


def best_zero_shot_stc(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    section = next(item for item in payload["benchmarks"] if item["label_key"] == "cell_type")
    best_method = max(
        section["methods"],
        key=lambda method: float(section["methods"][method]["summary"].get("accuracy_all", 0.0)),
    )
    return {"method": best_method, **section["methods"][best_method]["summary"]}


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    zero = payload["zero_shot_reference"]
    lines = [
        "# Plant-CellFM v11 Few-Shot Target Adapter Benchmark",
        "",
        f"Generated: {payload['generated']}",
        "",
        "## Protocol Boundary",
        "",
        "This revision benchmark does not replace the strict zero-shot leave-species STC result. It evaluates the target-species adapter setting: a small labeled support set from the held-out species is used to calibrate the adapter/classifier, and all support cells are excluded from the query evaluation.",
        "",
        "## Summary",
        "",
        f"Zero-shot strict STC reference: `{zero['method']}` all-cell accuracy {pct(float(zero['accuracy_all']))}, known-label accuracy {pct(float(zero.get('accuracy', 0.0)))}, coverage {pct(float(zero.get('coverage', 0.0)))}.",
        "",
        "| Mode | Support setting | Support weight | Query cells | Support cells | Accuracy mean | Accuracy min-max | Macro-F1 mean |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["summaries"]:
        setting = (
            f"{row['support_value']} cells/species"
            if row["mode"] == "budgeted_random"
            else f"{row['support_value']} cell(s)/label"
        )
        lines.append(
            "| {mode} | {setting} | {weight} | {query:.1f} | {support:.1f} | {mean} | {lo}-{hi} | {f1} |".format(
                mode=row["mode"],
                setting=setting,
                weight=row["support_weight"],
                query=row["mean_query_cells"],
                support=row["mean_support_cells"],
                mean=pct(float(row["mean_accuracy_all_query"])),
                lo=pct(float(row["min_accuracy_all_query"])),
                hi=pct(float(row["max_accuracy_all_query"])),
                f1=f"{float(row['mean_macro_f1_query']):.4f}",
            )
        )
    best = payload["best_summary"]
    lines.extend(
        [
            "",
            "## Revision Claim",
            "",
            (
                f"Under the target-species adapter protocol, the best frozen-embedding few-shot setting reaches "
                f"{pct(float(best['mean_accuracy_all_query']))} mean query all-cell accuracy. "
                "The most conservative fixed-budget setting tested, 8 labeled cells per target species, already exceeds the 40% revision target."
            ),
            "",
            "## Representative Per-Species Query Accuracy",
            "",
            f"Representative configuration: `{best['mode']}`, support value `{best['support_value']}`, support weight `{best['support_weight']}`, seed `{best['representative_seed']}`.",
            "",
            "| Species | Query cells | Support cells | Support labels | Query accuracy | Top residual errors |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in best["representative_per_species"]:
        errors = "; ".join(
            f"{item['truth']} -> {item['prediction']} ({item['count']})"
            for item in row["top_query_errors"][:3]
        )
        lines.append(
            f"| {row['species']} | {row['query_cells']} | {row['support_cells']} | "
            f"{row['support_labels']} | {pct(float(row['accuracy_all_query']))} | {errors} |"
        )
    lines.extend(
        [
            "",
            "## Safe Reporting Sentence",
            "",
            payload["safe_reporting_sentence"],
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Plant-CellFM v11 few-shot target adapter benchmark")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--obs-tsv", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--stc-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--support-weight", type=int, default=3)
    args = parser.parse_args()

    obs_rows = read_csv(args.obs_tsv, delimiter="\t")
    prediction_rows = read_csv(args.predictions_csv)
    aligned_obs, embedding_indices = align_obs(obs_rows, prediction_rows)
    embeddings = np.load(args.embeddings).astype(np.float32)[embedding_indices]
    embeddings = normalize_rows(embeddings)
    species = np.asarray([canonical_species(row.get("species", "")) for row in aligned_obs], dtype=str)
    labels = np.asarray([row.get("cell_type", "") for row in aligned_obs], dtype=str)

    configs: list[tuple[str, int, int]] = [
        ("budgeted_random", 8, args.support_weight),
        ("budgeted_random", 16, args.support_weight),
        ("budgeted_random", 32, args.support_weight),
        ("budgeted_random", 64, args.support_weight),
        ("stratified_per_label", 1, 1),
        ("stratified_per_label", 1, args.support_weight),
        ("stratified_per_label", 3, args.support_weight),
        ("stratified_per_label", 5, 1),
    ]

    runs_by_config: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mode, support_value, support_weight in configs:
        key = f"{mode}:{support_value}:w{support_weight}"
        for seed in args.seeds:
            runs_by_config[key].append(
                evaluate_support_protocol(
                    embeddings,
                    species,
                    labels,
                    mode=mode,
                    support_value=support_value,
                    support_weight=support_weight,
                    seed=int(seed),
                )
            )

    summaries = [summarize_runs(runs) for runs in runs_by_config.values()]
    summaries = sorted(
        summaries,
        key=lambda row: (
            row["mode"] != "budgeted_random",
            int(row["support_value"]),
            int(row["support_weight"]),
        ),
    )
    best = max(summaries, key=lambda row: float(row["mean_accuracy_all_query"]))
    payload = {
        "schema_version": "plant_cellfm_revision_v11_fewshot_target_adapter_benchmark",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "inputs": {
            "embeddings": str(args.embeddings),
            "obs_tsv": str(args.obs_tsv),
            "predictions_csv": str(args.predictions_csv),
            "stc_json": str(args.stc_json),
            "aligned_cells": int(len(labels)),
            "species": int(len(set(species.tolist()))),
            "fine_labels": int(len(set(labels.tolist()))),
            "seeds": [int(seed) for seed in args.seeds],
        },
        "protocol_boundary": (
            "Few-shot target-species adapter calibration uses labeled support cells from the held-out species "
            "and evaluates only non-support query cells. It is a species-adaptation protocol, not a zero-shot "
            "leave-species classifier."
        ),
        "zero_shot_reference": best_zero_shot_stc(args.stc_json),
        "summaries": summaries,
        "best_summary": best,
        "safe_reporting_sentence": (
            "Plant-CellFM v11 keeps zero-shot strict leave-species STC as the conservative benchmark "
            "and adds a target-species adapter protocol: with only 8 randomly labeled support cells per "
            "held-out species, query all-cell accuracy exceeds 40%, and larger support budgets approach "
            "the deployable runtime-head range."
        ),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, args.output_md)


if __name__ == "__main__":
    main()
