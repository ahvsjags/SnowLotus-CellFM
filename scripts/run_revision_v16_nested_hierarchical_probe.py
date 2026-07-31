from __future__ import annotations

"""Nested leave-species benchmark for the learned Plant-CellFM transfer head.

This script deliberately treats all model choices as training-fold choices.  For
each outer held-out species, it uses only the remaining species to choose a
regularisation/context/organ-prior configuration through an inner
leave-species-out loop.  The outer species labels are not inspected until the
final scored prediction is written.  This prevents the post-hoc global method
selection that can make small cross-species panels look stronger than they are.
"""

import argparse
import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

import run_revision_v14_context_stc_benchmark as v14


@dataclass(frozen=True)
class Candidate:
    name: str
    c: float
    organ_scale: float
    prior_weight: float


# The grid is intentionally small and declared before evaluation.  It spans a
# no-context probe plus context-aware learned probes without a target-fold tune.
CANDIDATES = (
    Candidate("embedding_lr_c1", c=1.0, organ_scale=0.0, prior_weight=0.0),
    Candidate("hierarchical_lr_c01_o05_p015", c=0.1, organ_scale=0.5, prior_weight=0.15),
    Candidate("hierarchical_lr_c1_o05_p015", c=1.0, organ_scale=0.5, prior_weight=0.15),
    Candidate("hierarchical_lr_c1_o10_p035", c=1.0, organ_scale=1.0, prior_weight=0.35),
    Candidate("hierarchical_lr_c3_o10_p015", c=3.0, organ_scale=1.0, prior_weight=0.15),
)


def read_rows(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def align_inputs(
    embeddings_path: Path,
    obs_path: Path,
    prediction_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict[str, str]]]:
    obs_rows = read_rows(obs_path, delimiter="\t")
    prediction_rows = read_rows(prediction_path)
    aligned, indices = v14.align_obs(obs_rows, prediction_rows)
    x = v14.normalize_rows(np.load(embeddings_path).astype(np.float32)[indices])
    species = np.asarray([v14.canonical_species(row.get("species", "")) for row in aligned], dtype=str)
    labels = np.asarray([v14.canonical_text(row.get("cell_type", "")) for row in aligned], dtype=str)
    organs = np.asarray([v14.organ_group(row.get("tissue", "")) for row in aligned], dtype=str)
    return x, species, labels, organs, aligned


def make_feature_matrix(x: np.ndarray, organs: np.ndarray, organ_levels: tuple[str, ...], scale: float) -> np.ndarray:
    if scale <= 0:
        return x
    lookup = {value: index for index, value in enumerate(organ_levels)}
    context = np.zeros((len(organs), len(organ_levels)), dtype=np.float32)
    for index, organ in enumerate(organs.tolist()):
        if organ in lookup:
            context[index, lookup[organ]] = scale
    return np.concatenate((x, context), axis=1)


def organ_prior(
    labels: np.ndarray,
    organs: np.ndarray,
    target_organs: np.ndarray,
    classes: np.ndarray,
    smooth: float = 6.0,
) -> np.ndarray:
    class_index = {label: index for index, label in enumerate(classes.tolist())}
    global_counts = Counter(labels.tolist())
    global_total = max(len(labels), 1)
    global_prior = np.asarray(
        [(global_counts.get(label, 0) + smooth) / (global_total + smooth * len(classes)) for label in classes],
        dtype=np.float64,
    )
    per_organ: dict[str, Counter[str]] = {}
    for label, organ in zip(labels.tolist(), organs.tolist(), strict=True):
        per_organ.setdefault(organ, Counter())[label] += 1
    output = np.empty((len(target_organs), len(classes)), dtype=np.float64)
    for index, organ in enumerate(target_organs.tolist()):
        counts = per_organ.get(organ)
        if not counts:
            output[index] = global_prior
            continue
        total = sum(counts.values())
        output[index] = np.asarray(
            [
                (counts.get(label, 0) + smooth * global_prior[class_index[label]]) / (total + smooth)
                for label in classes
            ],
            dtype=np.float64,
        )
    return output


def predict_candidate(
    candidate: Candidate,
    train_x: np.ndarray,
    train_y: np.ndarray,
    train_organs: np.ndarray,
    target_x: np.ndarray,
    target_organs: np.ndarray,
    organ_levels: tuple[str, ...],
) -> np.ndarray:
    model = LogisticRegression(
        C=candidate.c,
        max_iter=350,
        solver="lbfgs",
        n_jobs=None,
        random_state=17,
    )
    model.fit(
        make_feature_matrix(train_x, train_organs, organ_levels, candidate.organ_scale),
        train_y,
    )
    probability = model.predict_proba(
        make_feature_matrix(target_x, target_organs, organ_levels, candidate.organ_scale)
    )
    if candidate.prior_weight > 0:
        prior = organ_prior(train_y, train_organs, target_organs, model.classes_)
        probability = (1.0 - candidate.prior_weight) * probability + candidate.prior_weight * prior
    return model.classes_[probability.argmax(axis=1)].astype(str)


def record_score(
    truth: np.ndarray,
    prediction: np.ndarray,
    train_labels: set[str],
    held_out_species: str,
) -> dict[str, Any]:
    result = v14.evaluate(truth, prediction, train_labels)
    result["held_out_species"] = held_out_species
    return result


def inner_select(
    candidates: tuple[Candidate, ...],
    x: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    organs: np.ndarray,
    train_mask: np.ndarray,
    organ_levels: tuple[str, ...],
) -> tuple[Candidate, list[dict[str, Any]]]:
    source_species = sorted(set(species[train_mask].tolist()))
    candidate_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows: list[dict[str, Any]] = []
        for held in source_species:
            validation_mask = train_mask & (species == held)
            fit_mask = train_mask & ~validation_mask
            prediction = predict_candidate(
                candidate,
                x[fit_mask],
                labels[fit_mask],
                organs[fit_mask],
                x[validation_mask],
                organs[validation_mask],
                organ_levels,
            )
            rows.append(record_score(labels[validation_mask], prediction, set(labels[fit_mask].tolist()), held))
        summary = v14.aggregate(rows)
        candidate_rows.append({"candidate": asdict(candidate), "summary": summary})
    candidate_rows.sort(
        key=lambda row: (
            float(row["summary"].get("accuracy_all", 0.0)),
            float(row["summary"].get("macro_f1", 0.0)),
            float(row["summary"].get("accuracy", 0.0)),
        ),
        reverse=True,
    )
    selected = Candidate(**candidate_rows[0]["candidate"])
    return selected, candidate_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Nested learned hierarchical strict leave-species benchmark")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--obs-tsv", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--predictions-output", type=Path, required=True)
    args = parser.parse_args()

    x, species, labels, organs, aligned = align_inputs(args.embeddings, args.obs_tsv, args.predictions_csv)
    organ_levels = tuple(sorted(set(organs.tolist())))
    outer_rows: list[dict[str, Any]] = []
    selected_configs: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    for held_out in sorted(set(species.tolist())):
        test_mask = species == held_out
        train_mask = ~test_mask
        selected, inner_rows = inner_select(CANDIDATES, x, species, labels, organs, train_mask, organ_levels)
        prediction = predict_candidate(
            selected,
            x[train_mask],
            labels[train_mask],
            organs[train_mask],
            x[test_mask],
            organs[test_mask],
            organ_levels,
        )
        row = record_score(labels[test_mask], prediction, set(labels[train_mask].tolist()), held_out)
        row["selected_candidate"] = selected.name
        outer_rows.append(row)
        selected_configs.append(
            {
                "held_out_species": held_out,
                "selected_candidate": asdict(selected),
                "inner_candidate_ranking": inner_rows,
            }
        )
        test_indices = np.flatnonzero(test_mask)
        for index, predicted in zip(test_indices.tolist(), prediction.tolist(), strict=True):
            metadata = aligned[index]
            prediction_rows.append(
                {
                    "cell_id": metadata.get("cell_id", ""),
                    "species": species[index],
                    "organ": organs[index],
                    "truth_label": labels[index],
                    "strict_prediction": predicted,
                    "covered_by_train_labels": str(labels[index] in set(labels[train_mask].tolist())).lower(),
                    "selected_candidate": selected.name,
                }
            )
        print(
            f"{held_out}\t{selected.name}\tall={row.get('accuracy_all', 0.0):.4f}\t"
            f"known={row.get('accuracy', 0.0):.4f}",
            flush=True,
        )

    summary = v14.aggregate(outer_rows)
    payload: dict[str, Any] = {
        "schema_version": "plant_cellfm_revision_v16_nested_hierarchical_probe",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "protocol": {
            "outer_split": "leave one canonical species out",
            "inner_selection": "leave one source species out within each outer training fold",
            "selection_objective": "all-cell accuracy, then known-label macro-F1, then known-label accuracy",
            "held_out_label_access": "none until final outer-fold scoring",
            "candidates": [asdict(candidate) for candidate in CANDIDATES],
            "input_features": "frozen 256-dimensional normalized Plant-CellFM embedding plus optional training-fold organ one-hot context",
            "prior": "optional organ-conditioned label prior estimated from each fit fold only",
        },
        "inputs": {
            "aligned_cells": int(len(labels)),
            "species": int(len(set(species.tolist()))),
            "fine_labels": int(len(set(labels.tolist()))),
            "organs": list(organ_levels),
        },
        "summary": summary,
        "outer_species_records": outer_rows,
        "selected_configs": selected_configs,
        "interpretation": (
            "This is a learned classifier-side ablation on frozen embeddings. It is a strict zero-shot result only "
            "because every configuration is selected within outer training species. It does not use target-species "
            "labels, target-cell support labels or the deployment annotation head."
        ),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with args.predictions_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(prediction_rows[0]))
        writer.writeheader()
        writer.writerows(prediction_rows)
    lines = [
        "# Plant-CellFM v16 Nested Hierarchical Probe",
        "",
        f"Generated: {payload['generated']}",
        "",
        "## Protocol",
        "",
        "Every outer held-out species uses a separately selected learned classifier. Candidate selection is nested inside the remaining source species, so no held-out label is used to select regularisation, organ-context scale or prior weight.",
        "",
        "| Summary metric | Value |",
        "| --- | ---: |",
        f"| All-cell accuracy | {summary.get('accuracy_all', 0.0):.4f} |",
        f"| Known-label accuracy | {summary.get('accuracy', 0.0):.4f} |",
        f"| Known-label macro-F1 | {summary.get('macro_f1', 0.0):.4f} |",
        f"| Train-label coverage | {summary.get('coverage', 0.0):.4f} |",
        "",
        "| Held-out species | Selected nested configuration | Cells | Coverage | All-cell accuracy | Known-label accuracy |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(outer_rows, key=lambda value: str(value["held_out_species"])):
        lines.append(
            f"| {row['held_out_species']} | `{row['selected_candidate']}` | {row['n_test']} | "
            f"{row['coverage']:.4f} | {row['accuracy_all']:.4f} | {row.get('accuracy', 0.0):.4f} |"
        )
    lines.extend(["", "## Claim boundary", "", payload["interpretation"], ""])
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"summary": summary, "json": str(args.output_json)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
