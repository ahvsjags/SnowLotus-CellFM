from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
V9_JSON = ROOT / "release_metadata" / "v9_benchmarks" / "v9_lora_cross_species_benchmark.json"
OBS_TSV = ROOT / "release_metadata" / "species_ontology_obs_labels_v9.tsv"
OUT_MD = ROOT / "release_metadata" / "species_ontology_coverage_audit_v9.md"
OUT_JSON = ROOT / "release_metadata" / "species_ontology_coverage_audit_v9.json"
OUT_TSV = ROOT / "release_metadata" / "species_ontology_coverage_audit_v9.tsv"
OUT_MAPPING_TSV = ROOT / "release_metadata" / "plant_cell_state_ontology_mapping_v9.tsv"
OUT_MAPPING_JSON = ROOT / "release_metadata" / "plant_cell_state_ontology_mapping_v9.json"

UNKNOWN_ONTOLOGY = "unknown_or_unannotated"


def pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{100 * value:.2f}%"


def canonicalize_species_label(label: Any) -> str:
    return " ".join(str(label).replace("_", " ").split())


def label_text(label: Any) -> str:
    value = str(label or "").strip()
    value = value.replace("_", " ").replace("-", " ").replace("/", " ")
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    value = re.sub(r"[^0-9A-Za-z]+", " ", value)
    return " ".join(value.lower().split())


def canonical_ontology(label: Any) -> str:
    text = label_text(label)
    if not text:
        return UNKNOWN_ONTOLOGY
    if text.isdigit() or re.fullmatch(r"rna\s*\d+", text):
        return UNKNOWN_ONTOLOGY
    if any(token in text for token in ("unannotated", "unknown", "unknow", "not assigned")):
        return UNKNOWN_ONTOLOGY
    if "hydathode" in text:
        return "hydathode"
    if "idioblast" in text or "glandular" in text or "secretory" in text:
        return "secretory_or_specialized_epidermis"
    if "root hair" in text or "trichoblast" in text:
        return "root_hair_or_trichoblast"
    if "atrichoblast" in text or "non hair" in text or "nonhair" in text:
        return "nonhair_or_atrichoblast"
    if "lateral root cap" in text:
        return "lateral_root_cap"
    if "root cap" in text or "columella" in text:
        return "root_cap"
    if "cortex" in text or "cortical" in text:
        return "cortex"
    if "endodermis" in text or "endodermal" in text:
        return "endodermis"
    if "pericycle" in text or "pericyle" in text or "pericylce" in text:
        return "pericycle"
    if "xylem" in text:
        return "xylem"
    if "phloem" in text or "companion" in text or "sieve" in text:
        return "phloem"
    if "procamb" in text:
        return "procambium"
    if "vascular" in text or "vasculature" in text or "stele" in text:
        return "vascular_stele"
    if "meristem" in text or "stem cell niche" in text or text == "scn":
        return "meristem_or_stem_cell_niche"
    if "mesophyll" in text:
        return "mesophyll"
    if "guard" in text or "stomatal" in text or "stoma" in text:
        return "guard_or_stomatal_cell"
    if "epiderm" in text or "pavement" in text:
        return "epidermis"
    if "s phase" in text or "g2" in text or "g1" in text or "cell cycle" in text:
        return "cell_cycle_state"
    if "callus" in text:
        return "callus"
    if "parenchyma" in text:
        return "parenchyma"
    if "precursor" in text:
        return "developmental_precursor"
    return text.replace(" ", "_")


def load_benchmark() -> dict[str, Any]:
    return json.loads(V9_JSON.read_text(encoding="utf-8"))


def load_obs_rows() -> list[dict[str, str]]:
    with OBS_TSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def select_indices(rows: list[dict[str, str]], max_cells_per_dataset: int, seed: int) -> np.ndarray:
    groups = np.asarray([row["dataset_id"] for row in rows], dtype=str)
    rng = np.random.default_rng(seed)
    selected = []
    for group in sorted(set(groups.tolist())):
        candidates = np.flatnonzero(groups == group)
        if len(candidates) > max_cells_per_dataset:
            candidates = rng.choice(candidates, size=max_cells_per_dataset, replace=False)
        selected.append(np.sort(candidates))
    if not selected:
        return np.empty(0, dtype=np.int64)
    return np.sort(np.concatenate(selected).astype(np.int64))


def top_counter(counter: Counter[str], limit: int = 8) -> list[dict[str, Any]]:
    return [{"label": label, "count": int(count)} for label, count in counter.most_common(limit)]


def row_summary(
    species: str,
    record: dict[str, Any],
    selected_rows: list[dict[str, str]],
) -> dict[str, Any]:
    test_rows = [row for row in selected_rows if row["species_canonical"] == species]
    train_rows = [row for row in selected_rows if row["species_canonical"] != species]
    train_labels = [row["cell_type"] for row in train_rows if row.get("cell_type")]
    test_labels = [row["cell_type"] for row in test_rows if row.get("cell_type")]
    train_label_set = set(train_labels)

    exact_covered = [label in train_label_set for label in test_labels]
    test_ontology = [canonical_ontology(label) for label in test_labels]
    train_ontology_set = {
        canonical_ontology(label)
        for label in train_labels
        if canonical_ontology(label) != UNKNOWN_ONTOLOGY
    }
    ontology_covered = [
        ontology != UNKNOWN_ONTOLOGY and ontology in train_ontology_set
        for ontology in test_ontology
    ]
    exact_missed_but_ontology_covered = [
        (label, ontology)
        for label, exact, ontology, covered in zip(
            test_labels, exact_covered, test_ontology, ontology_covered, strict=True
        )
        if not exact and covered
    ]
    unknown_counter = Counter(
        label for label, ontology in zip(test_labels, test_ontology, strict=True) if ontology == UNKNOWN_ONTOLOGY
    )
    rescue_label_counter = Counter(label for label, _ in exact_missed_but_ontology_covered)
    rescue_ontology_counter = Counter(ontology for _, ontology in exact_missed_but_ontology_covered)

    n_test = len(test_labels)
    obs_exact_evaluable = int(sum(exact_covered))
    ontology_evaluable = int(sum(ontology_covered))
    frozen_n_evaluable = int(record.get("n_evaluable", 0))
    frozen_n_test = int(record.get("n_test", 0))
    obs_n_test_delta = n_test - frozen_n_test
    obs_exact_delta = obs_exact_evaluable - frozen_n_evaluable
    ontology_gain_vs_frozen = ontology_evaluable - frozen_n_evaluable

    if frozen_n_test and obs_n_test_delta == 0 and abs(obs_exact_delta) <= max(20, int(0.02 * frozen_n_test)):
        reconstruction_status = "near_exact"
    elif frozen_n_test and obs_n_test_delta == 0:
        reconstruction_status = "same_cells_label_delta"
    else:
        reconstruction_status = "selection_delta"

    return {
        "species": species,
        "benchmark_status": record.get("status"),
        "frozen_n_test": frozen_n_test,
        "obs_n_test": n_test,
        "obs_n_test_delta": obs_n_test_delta,
        "frozen_exact_n_evaluable": frozen_n_evaluable,
        "frozen_exact_coverage": float(record.get("coverage", 0.0)),
        "obs_exact_n_evaluable": obs_exact_evaluable,
        "obs_exact_coverage": obs_exact_evaluable / n_test if n_test else 0.0,
        "obs_exact_delta_vs_frozen": obs_exact_delta,
        "ontology_n_evaluable": ontology_evaluable,
        "ontology_coverage": ontology_evaluable / n_test if n_test else 0.0,
        "ontology_gain_cells_vs_frozen": ontology_gain_vs_frozen,
        "ontology_gain_points_vs_frozen": (ontology_evaluable / n_test - float(record.get("coverage", 0.0)))
        if n_test
        else 0.0,
        "unknown_or_unannotated_cells": int(sum(ontology == UNKNOWN_ONTOLOGY for ontology in test_ontology)),
        "unknown_or_unannotated_fraction": (
            sum(ontology == UNKNOWN_ONTOLOGY for ontology in test_ontology) / n_test if n_test else 0.0
        ),
        "rescue_candidates": len(exact_missed_but_ontology_covered),
        "reconstruction_status": reconstruction_status,
        "alignment_method": test_rows[0].get("alignment_method", "unknown") if test_rows else "missing",
        "top_rescued_labels": top_counter(rescue_label_counter),
        "top_rescued_ontology": top_counter(rescue_ontology_counter),
        "top_unknown_labels": top_counter(unknown_counter),
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_test = sum(int(row["frozen_n_test"]) for row in rows)
    frozen_evaluable = sum(int(row["frozen_exact_n_evaluable"]) for row in rows)
    obs_exact = sum(int(row["obs_exact_n_evaluable"]) for row in rows)
    ontology = sum(int(row["ontology_n_evaluable"]) for row in rows)
    unknown = sum(int(row["unknown_or_unannotated_cells"]) for row in rows)
    rescue = sum(int(row["rescue_candidates"]) for row in rows)
    return {
        "n_test": total_test,
        "frozen_exact_n_evaluable": frozen_evaluable,
        "frozen_exact_coverage": frozen_evaluable / total_test if total_test else 0.0,
        "obs_exact_n_evaluable": obs_exact,
        "obs_exact_coverage": obs_exact / total_test if total_test else 0.0,
        "obs_exact_delta_vs_frozen": obs_exact - frozen_evaluable,
        "ontology_n_evaluable": ontology,
        "ontology_coverage": ontology / total_test if total_test else 0.0,
        "ontology_gain_cells_vs_frozen": ontology - frozen_evaluable,
        "ontology_gain_points_vs_frozen": (ontology - frozen_evaluable) / total_test if total_test else 0.0,
        "unknown_or_unannotated_cells": unknown,
        "unknown_or_unannotated_fraction": unknown / total_test if total_test else 0.0,
        "rescue_candidates": rescue,
    }


def write_tsv(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "species",
        "benchmark_status",
        "frozen_n_test",
        "obs_n_test",
        "obs_n_test_delta",
        "frozen_exact_n_evaluable",
        "frozen_exact_coverage",
        "obs_exact_n_evaluable",
        "obs_exact_coverage",
        "obs_exact_delta_vs_frozen",
        "ontology_n_evaluable",
        "ontology_coverage",
        "ontology_gain_cells_vs_frozen",
        "ontology_gain_points_vs_frozen",
        "unknown_or_unannotated_cells",
        "unknown_or_unannotated_fraction",
        "rescue_candidates",
        "reconstruction_status",
        "alignment_method",
    ]
    with OUT_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def write_mapping(all_rows: list[dict[str, str]], selected_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    all_counts = Counter(row.get("cell_type", "") for row in all_rows)
    selected_counts = Counter(row.get("cell_type", "") for row in selected_rows)
    mapping_rows = []
    for label in sorted(all_counts, key=lambda value: (canonical_ontology(value), label_text(value), value)):
        ontology = canonical_ontology(label)
        mapping_rows.append(
            {
                "raw_label": label,
                "normalized_label": label_text(label),
                "ontology_label": ontology,
                "actionable": ontology != UNKNOWN_ONTOLOGY,
                "all_obs_count": int(all_counts[label]),
                "benchmark_aligned_count": int(selected_counts.get(label, 0)),
            }
        )
    with OUT_MAPPING_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            delimiter="\t",
            fieldnames=[
                "raw_label",
                "normalized_label",
                "ontology_label",
                "actionable",
                "all_obs_count",
                "benchmark_aligned_count",
            ],
        )
        writer.writeheader()
        writer.writerows(mapping_rows)
    OUT_MAPPING_JSON.write_text(
        json.dumps(
            {
                "schema_version": "plant_cell_state_ontology_mapping_v1",
                "source": OBS_TSV.relative_to(ROOT).as_posix(),
                "unknown_or_unannotated_excluded_from_actionable_coverage": True,
                "mapping_count": len(mapping_rows),
                "rows": mapping_rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return mapping_rows


def write_json(payload: dict[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md(payload: dict[str, Any]) -> None:
    agg = payload["aggregate"]
    lines = [
        "# Plant-CellFM v9 Species Ontology Coverage Audit",
        "",
        "This audit adds a label-ontology view on top of the frozen normalized leave-species-out benchmark. It uses the server-exported benchmark `obs` labels, aligns them to the frozen per-species test counts, and maps fine labels into a conservative plant cell-state ontology. The ontology table is a coverage and triage audit; it does not change the frozen v9 accuracy, macro-F1 or v9-v3 comparison.",
        "",
        "## Aggregate Coverage",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Frozen leave-species test cells | {agg['n_test']} |",
        f"| Frozen exact fine-label evaluable cells | {agg['frozen_exact_n_evaluable']} |",
        f"| Frozen exact fine-label coverage | {pct(agg['frozen_exact_coverage'])} |",
        f"| Obs-derived exact-label reconstruction | {agg['obs_exact_n_evaluable']} cells ({pct(agg['obs_exact_coverage'])}) |",
        f"| Reconstruction delta vs frozen JSON | {agg['obs_exact_delta_vs_frozen']} cells |",
        f"| Ontology-mapped actionable evaluable cells | {agg['ontology_n_evaluable']} |",
        f"| Ontology-mapped actionable coverage | {pct(agg['ontology_coverage'])} |",
        f"| Ontology delta vs frozen exact coverage | {agg['ontology_gain_cells_vs_frozen']} cells ({pct(agg['ontology_gain_points_vs_frozen'])}) |",
        f"| Unknown/unannotated cells excluded from ontology coverage | {agg['unknown_or_unannotated_cells']} ({pct(agg['unknown_or_unannotated_fraction'])}) |",
        f"| Exact-missed but ontology-covered rescue candidates | {agg['rescue_candidates']} |",
        "",
        "## Per-Species Table",
        "",
        "| Species | frozen coverage | obs exact | ontology coverage | ontology delta | unknown/unannotated | rescue candidates | alignment | reconstruction |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["species"],
                    pct(row["frozen_exact_coverage"]),
                    f"{row['obs_exact_n_evaluable']} ({pct(row['obs_exact_coverage'])})",
                    f"{row['ontology_n_evaluable']} ({pct(row['ontology_coverage'])})",
                    f"{row['ontology_gain_cells_vs_frozen']} ({pct(row['ontology_gain_points_vs_frozen'])})",
                    f"{row['unknown_or_unannotated_cells']} ({pct(row['unknown_or_unannotated_fraction'])})",
                    str(row["rescue_candidates"]),
                    row["alignment_method"],
                    row["reconstruction_status"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Top Ontology Rescue Signals",
            "",
        ]
    )
    for row in payload["rows"]:
        if not row["top_rescued_ontology"] and not row["top_unknown_labels"]:
            continue
        rescue = ", ".join(
            f"{item['label']}={item['count']}" for item in row["top_rescued_ontology"]
        ) or "none"
        unknown = ", ".join(
            f"{item['label']}={item['count']}" for item in row["top_unknown_labels"]
        ) or "none"
        lines.append(f"- **{row['species']}**: rescued ontology groups: {rescue}; unknown/unannotated labels: {unknown}.")
    lines.extend(
        [
            "",
            "## Reviewer-Safe Interpretation",
            "",
            "The strict benchmark remains the controlling performance claim. The ontology view shows whether low leave-species coverage is caused by genuinely absent biological states, superficial label wording differences, or uninformative labels such as unknown/unannotated classes. Because unknown and unannotated labels are excluded from actionable ontology coverage, this audit is deliberately conservative: it identifies what can be fixed by label harmonization without inflating model accuracy.",
            "",
            "The main near-term use is to guide the next frozen benchmark: keep the current all-cell and known-label metrics, add an explicit plant cell-state ontology mapping file, and report exact-label and ontology-label coverage side by side before rerunning species holdout.",
            "",
            "## Files",
            "",
            f"- Frozen benchmark JSON: `{V9_JSON.relative_to(ROOT).as_posix()}`",
            f"- Server-exported obs labels: `{OBS_TSV.relative_to(ROOT).as_posix()}`",
            f"- Cell-state ontology mapping table: `{OUT_MAPPING_TSV.relative_to(ROOT).as_posix()}`",
            f"- Machine-readable audit: `{OUT_JSON.relative_to(ROOT).as_posix()}`",
            f"- Per-species TSV: `{OUT_TSV.relative_to(ROOT).as_posix()}`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    benchmark = load_benchmark()
    rows = load_obs_rows()
    selection = benchmark["selection"]
    records = {
        record["held_out_group"]: record
        for record in benchmark["protocols"]["leave_species_out_fine"]["records"]
    }
    for row in rows:
        row["species_canonical"] = canonicalize_species_label(row["species"])

    rng = np.random.default_rng(int(selection["seed"]))
    selected_rows: list[dict[str, str]] = []
    for species in sorted(records):
        target = int(records[species]["n_test"])
        canonical_candidates = [row for row in rows if row["species_canonical"] == species]
        exact_raw_candidates = [row for row in canonical_candidates if row["species"] == species]
        if len(exact_raw_candidates) == target:
            species_rows = exact_raw_candidates
            alignment_method = "raw_species_exact_count"
        elif len(canonical_candidates) == target:
            species_rows = canonical_candidates
            alignment_method = "canonical_species_exact_count"
        elif len(canonical_candidates) > target:
            indices = np.asarray(rng.choice(len(canonical_candidates), size=target, replace=False), dtype=np.int64)
            species_rows = [canonical_candidates[int(index)] for index in sorted(indices.tolist())]
            alignment_method = "canonical_species_seeded_count_alignment"
        else:
            species_rows = canonical_candidates
            alignment_method = "canonical_species_shortfall"
        for row in species_rows:
            item = row.copy()
            item["alignment_method"] = alignment_method
            selected_rows.append(item)

    report_rows = [
        row_summary(species, records[species], selected_rows)
        for species in sorted(records)
    ]
    mapping_rows = write_mapping(rows, selected_rows)
    payload = {
        "schema_version": "plant_cellfm_v9_species_ontology_coverage_audit_v1",
        "source_files": {
            "benchmark": V9_JSON.relative_to(ROOT).as_posix(),
            "obs_labels": OBS_TSV.relative_to(ROOT).as_posix(),
            "ontology_mapping_tsv": OUT_MAPPING_TSV.relative_to(ROOT).as_posix(),
            "ontology_mapping_json": OUT_MAPPING_JSON.relative_to(ROOT).as_posix(),
        },
        "protocol": "leave_species_out_fine_obs_ontology_coverage_audit",
        "claim_boundary": "Coverage audit only; does not revise frozen v9 accuracy, macro-F1, Seurat comparison, or v9-v3 benchmark metrics.",
        "selection": {
            "seed": int(selection["seed"]),
            "max_cells_per_dataset": int(selection["max_cells_per_dataset"]),
            "selected_cells": int(len(selected_rows)),
            "benchmark_selected_cells": int(selection["selected_cells"]),
            "species_label_normalization": selection.get("species_label_normalization"),
            "obs_alignment": "count-aligned to frozen leave_species_out_fine records because the raw H5AD obs table has more cells than the prepared benchmark matrix",
        },
        "ontology_policy": {
            "unknown_or_unannotated_excluded": True,
            "mapping_scope": "coarse plant cell-state ontology for label harmonization triage",
            "primary_label_key": "cell_type",
            "mapping_rows": len(mapping_rows),
        },
        "aggregate": aggregate(report_rows),
        "rows": report_rows,
    }
    write_tsv(report_rows)
    write_json(payload)
    write_md(payload)
    print(OUT_MD.relative_to(ROOT).as_posix())
    print(OUT_JSON.relative_to(ROOT).as_posix())
    print(OUT_TSV.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
