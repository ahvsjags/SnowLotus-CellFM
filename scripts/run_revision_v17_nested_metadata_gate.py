from __future__ import annotations

"""Nested, metadata-conditioned strict zero-shot transfer benchmark.

The previous context gate used one globally selected heuristic.  Here every
outer held-out species chooses its gate only through source-species inner
validation.  The test species contributes its identity and supplied organ
metadata, but never its cell labels.
"""

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

import run_revision_v14_context_stc_benchmark as v14


@dataclass(frozen=True)
class Candidate:
    name: str
    kind: str
    scope: str = "none"
    minimum_family_support: int = 0
    k: int = 9


CANDIDATES = (
    Candidate("organ_context_prior", kind="organ"),
    Candidate("expression_knn_k9", kind="knn", k=9),
    Candidate("gate_leaf_support_0", kind="gate", scope="leaf", minimum_family_support=0),
    Candidate("gate_leaf_support_64", kind="gate", scope="leaf", minimum_family_support=64),
    Candidate("gate_leaf_support_128", kind="gate", scope="leaf", minimum_family_support=128),
    Candidate("gate_leaf_support_256", kind="gate", scope="leaf", minimum_family_support=256),
    Candidate("gate_single_organ_support_128", kind="gate", scope="single", minimum_family_support=128),
    Candidate("gate_any_organ_support_128", kind="gate", scope="any", minimum_family_support=128),
    Candidate("gate_any_organ_support_256", kind="gate", scope="any", minimum_family_support=256),
)


def load_inputs(
    embeddings_path: Path, obs_path: Path, predictions_path: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict[str, str]]]:
    obs_rows = v14.read_csv(obs_path, delimiter="\t")
    prediction_rows = v14.read_csv(predictions_path)
    aligned, indices = v14.align_obs(obs_rows, prediction_rows)
    x = v14.normalize_rows(np.load(embeddings_path).astype(np.float32)[indices])
    species = np.asarray([v14.canonical_species(row.get("species", "")) for row in aligned], dtype=str)
    labels = np.asarray([v14.canonical_text(row.get("cell_type", "")) for row in aligned], dtype=str)
    organs = np.asarray([v14.organ_group(row.get("tissue", "")) for row in aligned], dtype=str)
    return x, species, labels, organs, aligned


def same_family_support(train_species: np.ndarray, train_labels: np.ndarray, held_out_species: str) -> int:
    target_family = v14.family_group(held_out_species)
    return sum(
        v14.family_group(str(species)) == target_family and not v14.is_uninformative_label(str(label))
        for species, label in zip(train_species.tolist(), train_labels.tolist(), strict=True)
    )


def scope_matches(scope: str, test_organs: np.ndarray) -> bool:
    observed = set(test_organs.tolist())
    if scope == "leaf":
        return observed == {"leaf"}
    if scope == "single":
        return len(observed) == 1
    if scope == "any":
        return bool(observed)
    return False


def predict(
    candidate: Candidate,
    x: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    organs: np.ndarray,
    fit_mask: np.ndarray,
    test_mask: np.ndarray,
    held_out_species: str,
) -> tuple[np.ndarray, str]:
    train_x, train_y, train_organs = x[fit_mask], labels[fit_mask], organs[fit_mask]
    test_x, test_organs = x[test_mask], organs[test_mask]
    if candidate.kind == "organ":
        return (
            v14.context_majority(train_y, train_organs, test_organs, suppress_uninformative=False),
            "organ_context_prior",
        )
    if candidate.kind == "knn":
        return (
            v14.blend_predictions(
                train_x, train_y, test_x, train_organs, test_organs,
                base="knn", k=candidate.k, prior_weight=0.0, smooth=8.0, suppress_uninformative=False,
            ),
            "expression_knn",
        )
    support = same_family_support(species[fit_mask], train_y, held_out_species)
    use_expression = scope_matches(candidate.scope, test_organs) and support >= candidate.minimum_family_support
    if use_expression:
        return (
            v14.blend_predictions(
                train_x, train_y, test_x, train_organs, test_organs,
                base="knn", k=candidate.k, prior_weight=0.0, smooth=8.0, suppress_uninformative=False,
            ),
            f"expression_scope={candidate.scope};same_family_support={support}",
        )
    return (
        v14.context_majority(train_y, train_organs, test_organs, suppress_uninformative=False),
        f"organ_scope={candidate.scope};same_family_support={support}",
    )


def select_candidate(
    x: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    organs: np.ndarray,
    outer_train_mask: np.ndarray,
) -> tuple[Candidate, list[dict[str, Any]]]:
    source_species = sorted(set(species[outer_train_mask].tolist()))
    rows: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        inner_records = []
        for held in source_species:
            validation_mask = outer_train_mask & (species == held)
            fit_mask = outer_train_mask & ~validation_mask
            prediction, _ = predict(candidate, x, species, labels, organs, fit_mask, validation_mask, held)
            record = v14.evaluate(labels[validation_mask], prediction, set(labels[fit_mask].tolist()))
            record["held_out_species"] = held
            inner_records.append(record)
        rows.append({"candidate": asdict(candidate), "summary": v14.aggregate(inner_records)})
    rows.sort(
        key=lambda row: (
            float(row["summary"].get("accuracy_all", 0.0)),
            float(row["summary"].get("macro_f1", 0.0)),
            float(row["summary"].get("accuracy", 0.0)),
        ),
        reverse=True,
    )
    return Candidate(**rows[0]["candidate"]), rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Nested metadata gate strict leave-species evaluation")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--obs-tsv", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--predictions-output", type=Path, required=True)
    args = parser.parse_args()

    x, species, labels, organs, aligned = load_inputs(args.embeddings, args.obs_tsv, args.predictions_csv)
    outer_records: list[dict[str, Any]] = []
    selected_configs: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    for held in sorted(set(species.tolist())):
        test_mask = species == held
        train_mask = ~test_mask
        candidate, ranking = select_candidate(x, species, labels, organs, train_mask)
        prediction, decision = predict(candidate, x, species, labels, organs, train_mask, test_mask, held)
        record = v14.evaluate(labels[test_mask], prediction, set(labels[train_mask].tolist()))
        record.update({"held_out_species": held, "selected_candidate": candidate.name, "decision": decision})
        outer_records.append(record)
        selected_configs.append({"held_out_species": held, "selected_candidate": asdict(candidate), "inner_candidate_ranking": ranking})
        for index, label in zip(np.flatnonzero(test_mask).tolist(), prediction.tolist(), strict=True):
            source = aligned[index]
            prediction_rows.append(
                {
                    "cell_id": source.get("cell_id", ""),
                    "species": species[index],
                    "organ": organs[index],
                    "truth_label": labels[index],
                    "strict_prediction": label,
                    "covered_by_train_labels": str(labels[index] in set(labels[train_mask].tolist())).lower(),
                    "selected_candidate": candidate.name,
                    "decision": decision,
                }
            )
        print(f"{held}\t{candidate.name}\t{decision}\tall={record['accuracy_all']:.4f}", flush=True)

    summary = v14.aggregate(outer_records)
    payload = {
        "schema_version": "plant_cellfm_revision_v17_nested_metadata_gate",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "protocol": {
            "outer_split": "leave one canonical species out",
            "inner_selection": "source-species leave-one-species-out",
            "selection_objective": "all-cell accuracy, then macro-F1, then known-label accuracy",
            "held_out_label_access": "none until final scoring",
            "candidates": [asdict(candidate) for candidate in CANDIDATES],
            "target_metadata_permitted": "canonical target species identity and input tissue/organ metadata",
        },
        "inputs": {"aligned_cells": int(len(labels)), "species": int(len(set(species.tolist()))), "fine_labels": int(len(set(labels.tolist())))},
        "summary": summary,
        "outer_species_records": outer_records,
        "selected_configs": selected_configs,
        "interpretation": (
            "This experiment replaces a globally selected rule with nested source-species selection. "
            "It remains strict zero-shot because target labels are excluded from training, gate selection and prior estimation."
        ),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with args.predictions_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(prediction_rows[0]))
        writer.writeheader()
        writer.writerows(prediction_rows)
    lines = [
        "# Plant-CellFM v17 Nested Metadata-Gated Transfer",
        "",
        f"Generated: {payload['generated']}",
        "",
        "Every configuration is selected inside each outer training fold by leaving source species out. Target cell labels never enter selector fitting, model fitting or calibration.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| All-cell accuracy | {summary.get('accuracy_all', 0.0):.4f} |",
        f"| Known-label accuracy | {summary.get('accuracy', 0.0):.4f} |",
        f"| Known-label macro-F1 | {summary.get('macro_f1', 0.0):.4f} |",
        f"| Train-label coverage | {summary.get('coverage', 0.0):.4f} |",
        "",
        "| Held-out species | Nested selected method | Cells | Coverage | All-cell accuracy | Known-label accuracy |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(outer_records, key=lambda value: str(value["held_out_species"])):
        lines.append(
            f"| {row['held_out_species']} | `{row['selected_candidate']}` | {row['n_test']} | {row['coverage']:.4f} | "
            f"{row['accuracy_all']:.4f} | {row.get('accuracy', 0.0):.4f} |"
        )
    lines.extend(["", "## Claim boundary", "", payload["interpretation"], ""])
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"summary": summary, "json": str(args.output_json)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
