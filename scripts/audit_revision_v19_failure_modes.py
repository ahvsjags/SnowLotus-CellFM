"""Create a source-only priority audit for the strict v17 benchmark."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify(record: dict[str, Any]) -> str:
    coverage = float(record.get("coverage", 0.0))
    known_accuracy = record.get("accuracy")
    if coverage == 0.0:
        return "ontology_or_gene_overlap_gap"
    if known_accuracy is not None and float(known_accuracy) < 0.50:
        return "covered_label_transfer_failure"
    if coverage < 0.70:
        return "coverage_bottleneck"
    if known_accuracy is not None and float(known_accuracy) < 0.75:
        return "moderate_transfer_failure"
    return "strong_or_mixed_transfer"


def build_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in payload["outer_species_records"]:
        n_test = int(record["n_test"])
        n_evaluable = int(record["n_evaluable"])
        accuracy_all = float(record.get("accuracy_all", 0.0))
        known_accuracy = record.get("accuracy")
        known_accuracy_value = None if known_accuracy is None else float(known_accuracy)
        covered_error_cells = (
            None
            if known_accuracy_value is None
            else round(n_evaluable * (1.0 - known_accuracy_value), 4)
        )
        records.append(
            {
                "held_out_species": record["held_out_species"],
                "n_test": n_test,
                "n_evaluable": n_evaluable,
                "open_set_cells": int(record["open_set_cells"]),
                "coverage": float(record["coverage"]),
                "accuracy_all": accuracy_all,
                "known_accuracy": known_accuracy_value,
                "macro_f1": None if record.get("macro_f1") is None else float(record["macro_f1"]),
                "estimated_correct_cells": round(n_test * accuracy_all, 4),
                "open_set_gap_to_80_cells": round(max(0.0, 0.80 * n_test - n_evaluable), 4),
                "covered_error_cells": covered_error_cells,
                "priority_cells": round(n_test * (1.0 - accuracy_all), 4),
                "failure_mode": classify(record),
                "selected_candidate": record.get("selected_candidate"),
            }
        )
    return sorted(records, key=lambda item: item["priority_cells"], reverse=True)


def render_markdown(summary: dict[str, Any], records: list[dict[str, Any]]) -> str:
    lines = [
        "# Revision v19 strict cross-species failure audit",
        "",
        "This audit is diagnostic only. It does not alter the strict benchmark or use held-out labels.",
        "",
        f"- Test cells: {summary['n_test']}",
        f"- Coverage: {summary['coverage']:.4f}",
        f"- All-cell accuracy: {summary['accuracy_all']:.4f}",
        f"- Covered-label accuracy: {summary['accuracy']:.4f}",
        f"- Macro-F1: {summary['macro_f1']:.4f}",
        "",
        "## Priority order",
        "",
        "| Held-out species | n | coverage | all-cell | covered-label | open-set cells | covered errors | failure mode |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in records:
        known = "NA" if item["known_accuracy"] is None else f"{item['known_accuracy']:.4f}"
        covered_errors = "NA" if item["covered_error_cells"] is None else f"{item['covered_error_cells']:.1f}"
        lines.append(
            f"| {item['held_out_species']} | {item['n_test']} | {item['coverage']:.4f} | "
            f"{item['accuracy_all']:.4f} | {known} | {item['open_set_cells']} | "
            f"{covered_errors} | {item['failure_mode']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The first model-side priority is to recover source-only ontology/gene overlap for "
            "zero-coverage species and the second is to reduce covered-label transfer errors in "
            "large held-out cohorts. The 80% all-cell target requires both coverage and conditional "
            "accuracy to improve; changing the denominator is not an acceptable intervention.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="release_metadata/revision_v17_nested_metadata_gate.json",
    )
    parser.add_argument(
        "--output-dir",
        default="release_metadata/revision_v19_failure_audit",
    )
    args = parser.parse_args()
    payload = load_json(Path(args.input))
    summary = payload["summary"]
    records = build_records(payload)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "species_priority.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(records)
    (output_dir / "README.md").write_text(render_markdown(summary, records), encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "species": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
