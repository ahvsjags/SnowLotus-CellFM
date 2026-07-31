from __future__ import annotations

"""Run a label-integrity curated companion to the v17 strict benchmark.

The frozen v17 benchmark is intentionally retained as the all-public-label
stress test.  This companion protocol removes labels beginning with
``unknown``, ``unknow`` or ``unannotated`` *before* fitting, nested candidate
selection and scoring.  It therefore answers a narrower but biologically
meaningful question: how well does the decoder transfer explicit cell
identities, rather than dataset-specific placeholders.
"""

import argparse
import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

import run_revision_v14_context_stc_benchmark as v14
import run_revision_v17_nested_metadata_gate as v17


def filter_identity_labels(
    x: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    organs: np.ndarray,
    aligned: list[dict[str, str]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict[str, str]], dict[str, Any]]:
    """Remove non-identities once, before any target fold is constructed."""
    keep = np.asarray([not v14.is_uninformative_label(label) for label in labels], dtype=bool)
    total_by_species = {name: int((species == name).sum()) for name in sorted(set(species.tolist()))}
    kept_by_species = {name: int((species[keep] == name).sum()) for name in sorted(set(species.tolist()))}
    excluded_by_species = {
        name: total_by_species[name] - kept_by_species.get(name, 0) for name in total_by_species
    }
    audit = {
        "input_cells": int(len(labels)),
        "identity_curated_cells": int(keep.sum()),
        "excluded_uninformative_cells": int((~keep).sum()),
        "input_species": int(len(total_by_species)),
        "identity_curated_species": int(sum(count > 0 for count in kept_by_species.values())),
        "dropped_all_uninformative_species": [
            name for name, count in kept_by_species.items() if count == 0
        ],
        "total_cells_by_species": total_by_species,
        "kept_cells_by_species": kept_by_species,
        "excluded_cells_by_species": excluded_by_species,
        "filter_rule": "labels beginning with unknown, unknow or unannotated are audit-only, never fit or score identities",
    }
    return x[keep], species[keep], labels[keep], organs[keep], [row for row, flag in zip(aligned, keep, strict=True) if flag], audit


def run_benchmark(
    x: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    organs: np.ndarray,
    aligned: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    outer_records: list[dict[str, Any]] = []
    selected_configs: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, str]] = []
    for held in sorted(set(species.tolist())):
        test_mask = species == held
        train_mask = ~test_mask
        candidate, ranking = v17.select_candidate(x, species, labels, organs, train_mask)
        prediction, decision = v17.predict(candidate, x, species, labels, organs, train_mask, test_mask, held)
        record = v14.evaluate(labels[test_mask], prediction, set(labels[train_mask].tolist()))
        record.update(
            {
                "held_out_species": held,
                "selected_candidate": candidate.name,
                "decision": decision,
            }
        )
        outer_records.append(record)
        selected_configs.append(
            {
                "held_out_species": held,
                "selected_candidate": asdict(candidate),
                "inner_candidate_ranking": ranking,
            }
        )
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
        print(
            f"{held}\t{candidate.name}\tall={record['accuracy_all']:.4f}\t"
            f"coverage={record['coverage']:.4f}",
            flush=True,
        )
    return outer_records, selected_configs, prediction_rows


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    audit = payload["label_integrity_audit"]
    lines = [
        "# Plant-CellFM v18 Identity-Curated Nested Strict Transfer",
        "",
        f"Generated: {payload['generated']}",
        "",
        "## Protocol",
        "",
        "This is a companion benchmark, not a replacement for v17. Before any outer split, model fitting or inner candidate selection, labels beginning with `unknown`, `unknow` or `unannotated` are moved to an audit-only set. Target species labels remain inaccessible until final scoring.",
        "",
        "| Label-integrity item | Value |",
        "| --- | ---: |",
        f"| All public-label cells | {audit['input_cells']:,} |",
        f"| Curated explicit-identity cells | {audit['identity_curated_cells']:,} |",
        f"| Audit-only unknown/unannotated cells | {audit['excluded_uninformative_cells']:,} |",
        f"| Species retained | {audit['identity_curated_species']} / {audit['input_species']} |",
        "",
        "| Metric on curated explicit identities | Value |",
        "| --- | ---: |",
        f"| All-cell accuracy | {summary.get('accuracy_all', 0.0):.4f} |",
        f"| Known-label accuracy | {summary.get('accuracy', 0.0):.4f} |",
        f"| Known-label macro-F1 | {summary.get('macro_f1', 0.0):.4f} |",
        f"| Train-label coverage | {summary.get('coverage', 0.0):.4f} |",
        "",
        "| Held-out species | Cells | Coverage | All-cell accuracy | Known-label accuracy | Nested selected decoder |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in sorted(payload["outer_species_records"], key=lambda item: str(item["held_out_species"])):
        lines.append(
            f"| {row['held_out_species']} | {row['n_test']} | {row['coverage']:.4f} | "
            f"{row['accuracy_all']:.4f} | {row.get('accuracy', 0.0):.4f} | `{row['selected_candidate']}` |"
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "The v18 cohort contains only explicit reference identities and five species with at least one such identity. It does not establish universal species transfer, and it must be reported beside the full v17 all-public-label stress test rather than substituted for it.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run identity-curated nested strict species transfer")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--obs-tsv", type=Path, required=True)
    parser.add_argument("--predictions-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--predictions-output", type=Path, required=True)
    args = parser.parse_args()

    x, species, labels, organs, aligned = v17.load_inputs(
        args.embeddings, args.obs_tsv, args.predictions_csv
    )
    x, species, labels, organs, aligned, audit = filter_identity_labels(
        x, species, labels, organs, aligned
    )
    outer_records, selected_configs, prediction_rows = run_benchmark(
        x, species, labels, organs, aligned
    )
    payload = {
        "schema_version": "plant_cellfm_revision_v18_identity_curated_nested_strict",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "protocol": {
            "outer_split": "leave one canonical species out after a fixed label-integrity filter",
            "inner_selection": "source-species leave-one-species-out",
            "selection_objective": "all-cell accuracy, then macro-F1, then known-label accuracy",
            "held_out_label_access": "none until final scoring",
            "candidates": [asdict(candidate) for candidate in v17.CANDIDATES],
            "target_metadata_permitted": "canonical target species identity and supplied tissue/organ metadata",
        },
        "label_integrity_audit": audit,
        "inputs": {
            "aligned_cells_after_filter": int(len(labels)),
            "species_after_filter": int(len(set(species.tolist()))),
            "fine_labels_after_filter": int(len(set(labels.tolist()))),
        },
        "summary": v14.aggregate(outer_records),
        "outer_species_records": outer_records,
        "selected_configs": selected_configs,
        "claim_boundary": "Companion identity-curated protocol; report beside, never instead of, the all-public-label v17 stress test.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(payload), encoding="utf-8")
    with args.predictions_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(prediction_rows[0]))
        writer.writeheader()
        writer.writerows(prediction_rows)
    print(json.dumps({"summary": payload["summary"], "audit": audit}, ensure_ascii=False))


if __name__ == "__main__":
    main()
