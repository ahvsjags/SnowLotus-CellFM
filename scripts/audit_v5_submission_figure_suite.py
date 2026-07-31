from __future__ import annotations

"""Technical and evidence-boundary audit for the v5 figure suite.

The audit intentionally does not emit a subjective journal-readiness score.
It verifies export/source-data integrity and checks that statements which need
new matched external evidence remain marked as open work.
"""

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures" / "plant_cellfm_submission_v5"
MAIN = [
    "plant_cellfm_v5_fig1_foundation_contract",
    "plant_cellfm_v5_fig2_strict_transfer",
    "plant_cellfm_v5_fig3_target_adaptation",
    "plant_cellfm_v5_fig4_external_root_evidence",
]
EXTENDED = [
    "plant_cellfm_v4_ed_fig1_label_integrity",
    "plant_cellfm_v4_ed_fig2_nested_selection_audit",
    "plant_cellfm_v4_ed_fig3_matched_checkpoint_comparison",
    "plant_cellfm_v4_ed_fig4_literature_marker_concordance",
    "plant_cellfm_v4_ed_fig5_external_root_blind_inference",
]
OUTPUT_JSON = ROOT / "release_metadata" / "top_journal_figure_audit_v5.json"
OUTPUT_MD = ROOT / "release_metadata" / "top_journal_figure_audit_v5.md"


def inspect(directory: Path, stem: str) -> dict[str, Any]:
    paths = {suffix: directory / f"{stem}{suffix}" for suffix in (".svg", ".pdf", ".png", ".tiff")}
    source = sorted((FIGURES / "source_data").glob(f"{stem}_*.tsv"))
    svg = paths[".svg"].read_text(encoding="utf-8", errors="replace") if paths[".svg"].exists() else ""
    raster: dict[str, Any] = {"pixels": None, "dpi": None}
    if paths[".tiff"].exists():
        with Image.open(paths[".tiff"]) as image:
            raster["pixels"] = list(image.size)
            dpi = image.info.get("dpi")
            raster["dpi"] = [float(value) for value in dpi] if dpi else None
    return {
        "stem": stem,
        "missing_exports": [suffix for suffix, path in paths.items() if not path.exists()],
        "source_data_tables": [path.name for path in source],
        "editable_svg_text": bool(re.search(r"<text(?: |>)", svg)),
        "raster": raster,
    }


def audit() -> dict[str, Any]:
    records = {
        "v17": json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8")),
        "model_card": json.loads((ROOT / "release_metadata" / "plant_cellfm_model_card_v4.json").read_text(encoding="utf-8")),
        "external_root": json.loads((ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.json").read_text(encoding="utf-8")),
    }
    main = [inspect(FIGURES / "main", stem) for stem in MAIN]
    extended = [inspect(FIGURES / "extended_data", stem) for stem in EXTENDED]
    failures: list[str] = []
    for item in main + extended:
        if item["missing_exports"]:
            failures.append(f"{item['stem']} lacks {', '.join(item['missing_exports'])}.")
        if not item["source_data_tables"]:
            failures.append(f"{item['stem']} has no source-data TSV.")
        if not item["editable_svg_text"]:
            failures.append(f"{item['stem']} SVG does not expose editable text.")
        dpi = item["raster"]["dpi"]
        if dpi and min(dpi) < 599:
            failures.append(f"{item['stem']} TIFF is below 600 dpi.")
    if abs(records["v17"]["summary"]["accuracy_all"] - 0.39959636730575174) > 1e-10:
        failures.append("Frozen v17 primary all-cell accuracy changed unexpectedly.")
    external = records["external_root"]
    root_candidate_path = (
        ROOT
        / "figures"
        / "plant_cellfm_submission_v4"
        / "source_data"
        / "plant_cellfm_v4_fig4_arabidopsis_root_candidate_resource_root_marker_candidates.tsv"
    )
    with root_candidate_path.open(encoding="utf-8", newline="") as handle:
        root_candidate_rows = sum(1 for _ in csv.DictReader(handle, delimiter="\t"))
    if external["input_provenance"]["matrix"]["cells"] != 6566 or external["input_provenance"]["input_has_expert_cell_type_labels"]:
        failures.append("External root evidence no longer matches the label-free 6,566-cell input contract.")
    if external["marker_coherence"]["expected_label_is_top_mean_expression"] != 5:
        failures.append("External marker-coherence record no longer matches the frozen six-anchor audit.")
    if root_candidate_rows != 200:
        failures.append("Root candidate resource no longer has the frozen 10-identity, top-20 (200-row) contract.")
    comparisons = records["model_card"]["comparison_status"]
    if comparisons["scPlantLLM"] == "completed" or comparisons["scPlantAnnotate"] == "completed":
        failures.append("External comparator is marked complete without a matched official benchmark record.")
    return {
        "schema_version": "plant_cellfm_v5_figure_audit_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "state": "TECHNICALLY_READY_PENDING_EDITORIAL_AND_EVIDENCE_REVIEW" if not failures else "EXPORT_OR_EVIDENCE_REPAIR_REQUIRED",
        "technical_failures": failures,
        "figures": {"main": main, "extended_data": extended},
        "frozen_evidence": {
            "v17_all_cell_accuracy": records["v17"]["summary"]["accuracy_all"],
            "external_root_input_cells": external["input_provenance"]["matrix"]["cells"],
            "external_root_label_free": not external["input_provenance"]["input_has_expert_cell_type_labels"],
            "external_root_top_mean_marker_hits": external["marker_coherence"]["expected_label_is_top_mean_expression"],
            "root_candidate_rows": root_candidate_rows,
        },
        "visual_contract": {
            "main_figure_story": [
                "Figure 1: corpus contract and shared evaluation representation",
                "Figure 2: strict transfer with explicit coverage and denominator",
                "Figure 3: target-species adaptation dose response",
                "Figure 4: label-free external root execution and fixed-marker coherence",
            ],
            "manual_review_required": [
                "Confirm readability after final journal-scale placement.",
                "Confirm captions, colour conversion and vector-font handling in the target journal production workflow.",
                "Do not substitute this technical audit for independent labels, wet-lab validation or matched third-party model ranking.",
            ],
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Plant-CellFM v5 Figure Audit",
        "",
        f"- State: `{report['state']}`",
        "- This is an export and evidence-boundary audit. It intentionally does not assign a self-reported journal-quality score.",
        "",
        "## Export Gate",
        "",
        "| Figure | SVG/PDF/PNG/TIFF | Source TSV | Editable SVG text | TIFF pixels |",
        "| --- | --- | --- | --- | --- |",
    ]
    for group in ("main", "extended_data"):
        for item in report["figures"][group]:
            exports = "pass" if not item["missing_exports"] else "missing " + ", ".join(item["missing_exports"])
            pixels = "x".join(map(str, item["raster"]["pixels"] or [])) or "missing"
            lines.append(f"| {item['stem']} | {exports} | {len(item['source_data_tables'])} | {item['editable_svg_text']} | {pixels} |")
    lines.extend(["", "## Evidence Boundary", ""])
    lines.extend(f"- {item}" for item in report["visual_contract"]["manual_review_required"])
    if report["technical_failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {item}" for item in report["technical_failures"])
    return "\n".join(lines) + "\n"


def main() -> int:
    report = audit()
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"state": report["state"], "technical_failures": len(report["technical_failures"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
