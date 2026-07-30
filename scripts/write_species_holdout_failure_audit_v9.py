from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
V9_JSON = ROOT / "release_metadata" / "v9_benchmarks" / "v9_lora_cross_species_benchmark.json"
V3_JSON = ROOT / "release_metadata" / "v9_benchmarks" / "v3_on_v9_shared_subset_cross_species_benchmark.json"
OUT_MD = ROOT / "release_metadata" / "species_holdout_failure_audit_v9.md"
OUT_JSON = ROOT / "release_metadata" / "species_holdout_failure_audit_v9.json"
OUT_TSV = ROOT / "release_metadata" / "species_holdout_failure_audit_v9.tsv"


def load_records(path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data["protocols"]["leave_species_out_fine"]["records"]
    return data, {record["held_out_group"]: record for record in records}


def pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{100 * value:.2f}%"


def num(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def classify(row: dict[str, Any]) -> tuple[str, str]:
    if row["v9_status"] == "no_label_overlap" or row["v9_coverage"] == 0:
        return (
            "ontology_gap_no_label_overlap",
            "No test labels are present in the training fold; this species requires label ontology mapping before accuracy is interpretable.",
        )
    if row["v9_coverage"] < 0.6:
        return (
            "label_coverage_bottleneck",
            "The all-cell score is dominated by labels absent from the training fold; expand or harmonize the label ontology before claiming species transfer.",
        )
    if row["v9_coverage"] >= 0.9 and row["v9_known_accuracy"] is not None and row["v9_known_accuracy"] < 0.1:
        return (
            "covered_label_transfer_failure",
            "Most labels are evaluable, but the transferred representation fails on the covered labels; prioritize species-specific adapter or tissue-context calibration.",
        )
    if row["delta_accuracy_all"] is not None and row["delta_accuracy_all"] < -0.05:
        return (
            "regression_vs_v3",
            "The frozen v9 candidate underperforms v3 on this held-out species; keep it visible as a revision target.",
        )
    if row["v9_accuracy_all"] >= 0.8:
        return (
            "strong_transfer",
            "The species provides positive evidence that the v9 representation can transfer when label coverage and tissue context are favorable.",
        )
    return (
        "mixed_transfer",
        "The species is partially supported, but accuracy and macro-F1 should be interpreted as a mixed open-set transfer result.",
    )


def build_rows(v9_records: dict[str, dict[str, Any]], v3_records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for species in sorted(v9_records):
        v9 = v9_records[species]
        v3 = v3_records.get(species, {})
        n_test = int(v9.get("n_test", 0))
        n_evaluable = int(v9.get("n_evaluable", 0))
        coverage = float(v9.get("coverage", 0.0))
        accuracy = v9.get("accuracy")
        accuracy_all = float(v9.get("accuracy_all", 0.0))
        v3_accuracy_all = v3.get("accuracy_all")
        delta = accuracy_all - float(v3_accuracy_all) if v3_accuracy_all is not None else None

        open_set_cells = n_test - n_evaluable
        correct_all = accuracy_all * n_test
        all_errors = n_test - correct_all
        known_errors = n_evaluable * (1.0 - float(accuracy)) if accuracy is not None else 0.0
        open_set_error_share = open_set_cells / all_errors if all_errors > 0 else 0.0

        row = {
            "species": species,
            "v9_status": v9.get("status"),
            "n_test": n_test,
            "n_evaluable": n_evaluable,
            "open_set_cells": open_set_cells,
            "v9_coverage": coverage,
            "v9_accuracy_all": accuracy_all,
            "v9_known_accuracy": float(accuracy) if accuracy is not None else None,
            "v9_known_macro_f1": v9.get("macro_f1"),
            "v3_accuracy_all": float(v3_accuracy_all) if v3_accuracy_all is not None else None,
            "delta_accuracy_all": delta,
            "test_classes": v9.get("test_classes"),
            "train_classes": v9.get("train_classes"),
            "estimated_correct_all": correct_all,
            "estimated_all_errors": all_errors,
            "estimated_open_set_errors": float(open_set_cells),
            "estimated_known_label_errors": known_errors,
            "open_set_error_share": open_set_error_share,
        }
        category, interpretation = classify(row)
        row["failure_category"] = category
        row["interpretation"] = interpretation
        rows.append(row)
    return rows


def aggregate(v9_data: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = v9_data["protocols"]["leave_species_out_fine"]
    total_test = int(summary["n_test"])
    total_evaluable = int(summary["n_evaluable"])
    total_correct = sum(row["estimated_correct_all"] for row in rows)
    total_open_set = sum(row["open_set_cells"] for row in rows)
    total_known_errors = sum(row["estimated_known_label_errors"] for row in rows)
    total_errors = total_test - total_correct
    return {
        "n_test": total_test,
        "n_evaluable": total_evaluable,
        "open_set_cells": total_open_set,
        "coverage": float(summary["coverage"]),
        "accuracy_all": float(summary["accuracy_all"]),
        "known_label_accuracy": float(summary["accuracy"]),
        "known_label_macro_f1": float(summary["macro_f1"]),
        "estimated_correct_all": total_correct,
        "estimated_all_errors": total_errors,
        "estimated_open_set_errors": total_open_set,
        "estimated_known_label_errors": total_known_errors,
        "open_set_error_share": total_open_set / total_errors if total_errors > 0 else 0.0,
    }


def write_tsv(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "species",
        "failure_category",
        "v9_status",
        "n_test",
        "n_evaluable",
        "open_set_cells",
        "v9_coverage",
        "v9_accuracy_all",
        "v9_known_accuracy",
        "v9_known_macro_f1",
        "v3_accuracy_all",
        "delta_accuracy_all",
        "test_classes",
        "train_classes",
        "estimated_open_set_errors",
        "estimated_known_label_errors",
        "open_set_error_share",
        "interpretation",
    ]
    with OUT_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def write_json(v9_data: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {
        "schema_version": "plant_cellfm_v9_species_holdout_failure_audit_v1",
        "source_files": {
            "v9": V9_JSON.relative_to(ROOT).as_posix(),
            "v3": V3_JSON.relative_to(ROOT).as_posix(),
        },
        "protocol": "leave_species_out_fine_with_species_label_normalization",
        "claim_boundary": "The audit explains the strict open-set species-holdout result; it does not convert the result into a universal high-accuracy claim.",
        "aggregate": aggregate(v9_data, rows),
        "rows": rows,
        "priority_actions": [
            {
                "priority": "P1",
                "target": "Catharanthus roseus",
                "reason": "High coverage but near-zero known-label accuracy indicates a genuine transfer failure rather than only open-set label absence.",
                "action": "Review tissue/label mapping and add a species- or tissue-aware adapter calibration experiment.",
            },
            {
                "priority": "P1",
                "target": "Gossypium hirsutum",
                "reason": "No label overlap makes the species unassessable under the current ontology.",
                "action": "Map the held-out label into the shared plant cell-state ontology or add a comparable training label.",
            },
            {
                "priority": "P2",
                "target": "Arabidopsis thaliana",
                "reason": "This species dominates the test set and has low coverage after species holdout.",
                "action": "Separate ontology coverage from representation error and report open-set cells explicitly.",
            },
            {
                "priority": "P2",
                "target": "Fragaria vesca and Gossypium bickii",
                "reason": "v9 regresses against v3 on these species despite moderate-to-high coverage.",
                "action": "Inspect label harmonization and adapter selection before claiming broad species gains.",
            },
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def write_md(payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    agg = payload["aggregate"]
    lines = [
        "# Plant-CellFM v9 Species-Holdout Failure Audit",
        "",
        "This audit decomposes the strict normalized leave-species-out benchmark into per-species coverage, known-label performance and open-set error sources. It is reviewer-facing evidence for why the headline species-holdout score must be interpreted as open-set transfer evidence, not as universal high-accuracy annotation.",
        "",
        "## Aggregate Decomposition",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Test cells | {agg['n_test']} |",
        f"| Evaluable known-label cells | {agg['n_evaluable']} |",
        f"| Open-set cells without train-fold label overlap | {agg['open_set_cells']} |",
        f"| Coverage | {pct(agg['coverage'])} |",
        f"| All-cell accuracy | {pct(agg['accuracy_all'])} |",
        f"| Known-label conditional accuracy | {pct(agg['known_label_accuracy'])} |",
        f"| Known-label conditional macro-F1 | {num(agg['known_label_macro_f1'], 4)} |",
        f"| Estimated all-cell errors attributed to open-set label absence | {pct(agg['open_set_error_share'])} |",
        "",
        "## Per-Species Diagnostic Table",
        "",
        "| Species | Category | n | coverage | v9 all-cell acc. | v9 known-label acc. | v3 all-cell acc. | delta | Main interpretation |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["species"],
                    row["failure_category"],
                    str(row["n_test"]),
                    pct(row["v9_coverage"]),
                    pct(row["v9_accuracy_all"]),
                    pct(row["v9_known_accuracy"]),
                    pct(row["v3_accuracy_all"]),
                    pct(row["delta_accuracy_all"]),
                    row["interpretation"],
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Reviewer-Safe Interpretation",
            "",
            "The normalized species-holdout benchmark contains two distinct sources of error. First, 1,748 of 3,964 held-out cells have reference labels absent from the corresponding training fold; these cells are counted as errors in the all-cell open-set metric. Second, among the 2,216 cells whose labels are evaluable, several species remain difficult, especially Catharanthus roseus. This explains why the correct headline is 23.54% all-cell accuracy at 55.90% coverage, while 42.10% is only a conditional known-label value.",
            "",
            "## Revision Priorities",
            "",
        ]
    )
    for item in payload["priority_actions"]:
        lines.append(
            f"- **{item['priority']} {item['target']}.** {item['reason']} {item['action']}"
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            f"- Source v9 benchmark: `{V9_JSON.relative_to(ROOT).as_posix()}`",
            f"- Source v3 benchmark: `{V3_JSON.relative_to(ROOT).as_posix()}`",
            f"- Machine-readable audit: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
            f"- Per-species table: `{OUT_TSV.relative_to(ROOT).as_posix()}`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    v9_data, v9_records = load_records(V9_JSON)
    _, v3_records = load_records(V3_JSON)
    rows = build_rows(v9_records, v3_records)
    write_tsv(rows)
    payload = write_json(v9_data, rows)
    write_md(payload)
    print(OUT_MD.relative_to(ROOT).as_posix())
    print(OUT_JSON.relative_to(ROOT).as_posix())
    print(OUT_TSV.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
