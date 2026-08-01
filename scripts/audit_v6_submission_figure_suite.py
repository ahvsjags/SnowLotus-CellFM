from __future__ import annotations

"""Technical and evidence-boundary audit for the Plant-CellFM v6 suite."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures" / "plant_cellfm_submission_v6"
MAIN = [
    "plant_cellfm_v6_fig1_foundation_contract",
    "plant_cellfm_v6_fig2_strict_transfer",
    "plant_cellfm_v6_fig3_target_adaptation",
    "plant_cellfm_v6_fig4_external_root_evidence",
    "plant_cellfm_v6_fig5_wheat_adapter",
]
EXTENDED = [
    "plant_cellfm_v6_ed_fig7_zero_target_transfer",
    "plant_cellfm_v6_ed_fig8_scplantllm_matched_reference",
]
OUTPUT_JSON = ROOT / "release_metadata" / "top_journal_figure_audit_v6.json"
OUTPUT_MD = ROOT / "release_metadata" / "top_journal_figure_audit_v6.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(directory: Path, stem: str) -> dict[str, Any]:
    paths = {suffix: directory / f"{stem}{suffix}" for suffix in (".svg", ".pdf", ".png", ".tiff")}
    source = sorted((FIGURES / "source_data").glob(f"{stem}_*.tsv"))
    svg = paths[".svg"].read_text(encoding="utf-8", errors="replace") if paths[".svg"].exists() else ""
    font_sizes = [float(value) for value in re.findall(r"font-size:\s*([0-9.]+)px", svg)]
    raster: dict[str, Any] = {"pixels": None, "dpi": None}
    if paths[".tiff"].exists():
        with Image.open(paths[".tiff"]) as image:
            raster["pixels"] = list(image.size)
            dpi = image.info.get("dpi")
            raster["dpi"] = [float(value) for value in dpi] if dpi else None
    return {
        "stem": stem,
        "sha256": {suffix.lstrip("."): sha256(path) for suffix, path in paths.items() if path.exists()},
        "missing_exports": [suffix for suffix, path in paths.items() if not path.exists()],
        "source_data_tables": [path.name for path in source],
        "editable_svg_text": bool(re.search(r"<text(?: |>)", svg)),
        "minimum_svg_font_size_pt": min(font_sizes) if font_sizes else None,
        "raster": raster,
    }


def audit() -> dict[str, Any]:
    v17 = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))["summary"]
    v14 = json.loads((ROOT / "release_metadata" / "revision_v14_context_stc_benchmark.json").read_text(encoding="utf-8"))["best_method"]["summary"]
    root = json.loads((ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.json").read_text(encoding="utf-8"))
    wheat = json.loads((ROOT / "release_metadata" / "gse270342_wheat_lora_adapter_audit_v1.json").read_text(encoding="utf-8"))
    zero_target = json.loads((ROOT / "release_metadata" / "gse270140_to_gse270342_zero_target_transfer_audit_v1.json").read_text(encoding="utf-8"))
    scplantllm = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_matched_embedding_probe_v1.json").read_text(encoding="utf-8"))
    scplantllm_partial = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_partial_finetune_v1.json").read_text(encoding="utf-8"))
    scplantllm_partial_replay = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_partial_finetune_audit_v1.json").read_text(encoding="utf-8"))
    main = [inspect(FIGURES / "main", stem) for stem in MAIN]
    extended = [inspect(FIGURES / "extended_data", stem) for stem in EXTENDED]
    failures: list[str] = []
    for item in main + extended:
        if item["missing_exports"]:
            failures.append(f"{item['stem']} lacks {', '.join(item['missing_exports'])}.")
        if not item["source_data_tables"]:
            failures.append(f"{item['stem']} has no tidy source-data TSV.")
        if not item["editable_svg_text"]:
            failures.append(f"{item['stem']} SVG does not expose editable text.")
        if item["minimum_svg_font_size_pt"] is None or item["minimum_svg_font_size_pt"] < 5.0:
            failures.append(f"{item['stem']} contains SVG text below the five-point floor.")
        dpi = item["raster"]["dpi"]
        if dpi and min(dpi) < 599:
            failures.append(f"{item['stem']} TIFF is below 600 dpi.")
    if abs(v17["accuracy_all"] - 0.39959636730575174) > 1e-10:
        failures.append("Locked v17 primary all-cell accuracy changed unexpectedly.")
    if abs(v14["accuracy_all"] - 0.42356205852674067) > 1e-10:
        failures.append("v14 sensitivity result changed unexpectedly.")
    primary = zero_target["results"]["primary_three_state"]["source_only_decoders"]
    frozen_zero = primary["frozen_root_checkpoint"]["knn_9"]
    source_zero = primary["gse270140_source_adapter"]["knn_9"]
    if abs(frozen_zero["macro_f1"] - 0.4230552091778434) > 1e-10:
        failures.append("Zero-target frozen-root primary macro-F1 changed unexpectedly.")
    if abs(source_zero["macro_f1"] - 0.4035913021321366) > 1e-10:
        failures.append("Zero-target source-adapter primary macro-F1 changed unexpectedly.")
    if source_zero["macro_f1"] >= frozen_zero["macro_f1"]:
        failures.append("Negative zero-target adapter result is no longer represented correctly.")
    if abs(scplantllm["metrics"]["accuracy"] - 0.2107466852756455) > 1e-10:
        failures.append("Matched frozen scPlantLLM reference accuracy changed unexpectedly.")
    if scplantllm["split_contract"]["locked_test_cells"] != 1433 or not scplantllm["split_contract"]["locked_test_barcode_match_to_plantcellm"]:
        failures.append("Matched scPlantLLM reference no longer has the shared locked test contract.")
    if scplantllm["model"]["checkpoint_load"]["missing_keys"] or scplantllm["model"]["checkpoint_load"]["unexpected_keys"]:
        failures.append("Official scPlantLLM checkpoint no longer loads cleanly.")
    partial_metrics = scplantllm_partial["locked_test"]
    partial_adapter = ROOT / scplantllm_partial["artifacts"]["adapter_checkpoint"]
    if scplantllm_partial["status"] != "COMPLETED_MATCHED_PARTIAL_BACKBONE_ADAPTATION":
        failures.append("Matched partial scPlantLLM adaptation is not release eligible.")
    if scplantllm_partial["split_contract"]["locked_test_cells"] != 1433 or not scplantllm_partial["split_contract"]["locked_test_barcode_match_to_plantcellm"]:
        failures.append("Matched partial scPlantLLM adaptation no longer has the shared locked test contract.")
    if scplantllm_partial["model"]["checkpoint_load"]["missing_keys"] or scplantllm_partial["model"]["checkpoint_load"]["unexpected_keys"]:
        failures.append("Official scPlantLLM checkpoint no longer loads cleanly before partial adaptation.")
    if scplantllm_partial["model"]["adaptation"]["mode"] != "new_13_class_head_plus_final_transformer_block":
        failures.append("Partial scPlantLLM adaptation mode changed unexpectedly.")
    if abs(partial_metrics["accuracy"] - 0.34263782274947663) > 1e-10 or abs(partial_metrics["macro_f1"] - 0.2997591328009322) > 1e-10:
        failures.append("Matched partial scPlantLLM locked-test metrics changed unexpectedly.")
    if not partial_adapter.is_file() or sha256(partial_adapter) != scplantllm_partial["artifacts"]["adapter_checkpoint_sha256"]:
        failures.append("Partial scPlantLLM adapter checkpoint is missing or fails its checksum.")
    if scplantllm_partial_replay["state"] != "REPLAY_CONFIRMED":
        failures.append("Partial scPlantLLM adapter does not have an exact replay confirmation.")
    wheat_checkpoint = ROOT / wheat["checkpoint"]["path"]
    if not wheat_checkpoint.is_file() or sha256(wheat_checkpoint) != wheat["checkpoint"]["sha256"]:
        failures.append("Released wheat adapter checkpoint is missing or fails its checksum.")
    root_record_ok = root["input_provenance"]["matrix"]["cells"] == 6566 and not root["input_provenance"]["input_has_expert_cell_type_labels"]
    if not root_record_ok:
        failures.append("External root input no longer matches its label-free 6,566-cell contract.")
    if root["marker_coherence"]["expected_label_is_top_mean_expression"] != 5:
        failures.append("External root marker-coherence audit changed unexpectedly.")
    return {
        "schema_version": "plant_cellfm_v6_figure_audit_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "state": "TECHNICALLY_READY_PENDING_EVIDENCE_COMPLETION" if not failures else "EXPORT_OR_EVIDENCE_REPAIR_REQUIRED",
        "technical_failures": failures,
        "figures": {"main": main, "extended_data": extended},
        "frozen_evidence": {
            "v17_primary_all_cell_accuracy": v17["accuracy_all"],
            "v17_primary_coverage": v17["coverage"],
            "v14_sensitivity_all_cell_accuracy": v14["accuracy_all"],
            "external_root_label_free_cells": root["input_provenance"]["matrix"]["cells"],
            "external_root_fixed_marker_top_mean_hits": root["marker_coherence"]["expected_label_is_top_mean_expression"],
            "wheat_locked_test_accuracy": wheat["locked_full_13_class_test"]["accuracy"],
            "wheat_locked_test_macro_f1": wheat["locked_full_13_class_test"]["macro_f1"],
            "zero_target_frozen_k9_macro_f1": frozen_zero["macro_f1"],
            "zero_target_source_adapter_k9_macro_f1": source_zero["macro_f1"],
            "scplantllm_frozen_reference_accuracy": scplantllm["metrics"]["accuracy"],
            "scplantllm_frozen_reference_macro_f1": scplantllm["metrics"]["macro_f1"],
            "scplantllm_partial_reference_accuracy": partial_metrics["accuracy"],
            "scplantllm_partial_reference_macro_f1": partial_metrics["macro_f1"],
            "scplantllm_partial_best_validation_epoch": scplantllm_partial["selection"]["best_epoch"],
        },
        "evidence_open_items": [
            "The matched scPlantLLM partial adaptation closes the frozen-reference gap, but full-backbone or compute-budget-matched scPlantLLM and a runnable scPlantAnnotate comparison remain open.",
            "The label-free external-root execution has no expert ground truth and no wet-lab validation; it remains a fixed-marker coherence case.",
            "The strict leave-species score is a transparent primary benchmark, but is not yet sufficient to claim universal high-accuracy plant annotation.",
        ],
        "manual_editorial_checks": [
            "Inspect final figure scale in the target journal template and confirm colour conversion after production export.",
            "Verify caption prose uses the scope boundaries shown directly in Figures 2, 4, 5 and Extended Data 7-8.",
            "Do not turn this technical audit into a self-assigned journal-quality or acceptance score.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Plant-CellFM v6 Figure Audit",
        "",
        f"- State: `{report['state']}`",
        "- This is a source-data, export and claim-boundary audit. It is not a journal-acceptance assessment.",
        "",
        "## Export Gate",
        "",
        "| Figure | SVG/PDF/PNG/TIFF | Source TSV | Editable SVG text | Minimum SVG font (pt) | TIFF pixels |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for group in ("main", "extended_data"):
        for item in report["figures"][group]:
            exports = "pass" if not item["missing_exports"] else "missing " + ", ".join(item["missing_exports"])
            pixels = "x".join(map(str, item["raster"]["pixels"] or [])) or "missing"
            minimum = item["minimum_svg_font_size_pt"]
            font_display = f"{minimum:.2f}" if minimum is not None else "missing"
            lines.append(f"| {item['stem']} | {exports} | {len(item['source_data_tables'])} | {item['editable_svg_text']} | {font_display} | {pixels} |")
    lines.extend(["", "## Evidence Still Open", ""])
    lines.extend(f"- {item}" for item in report["evidence_open_items"])
    lines.extend(["", "## Manual Editorial Checks", ""])
    lines.extend(f"- {item}" for item in report["manual_editorial_checks"])
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
