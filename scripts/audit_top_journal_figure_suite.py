from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "agents" / "top_journal_figure_auditor"
DEFAULT_BLUEPRINT = ROOT / "docs" / "top_journal_figure_study_and_blueprint_v1.md"
DEFAULT_MANIFEST = ROOT / "release_metadata" / "top_journal_figure_asset_manifest.json"
DEFAULT_RUBRIC = AGENT_ROOT / "references" / "audit_rubric.json"
DEFAULT_ANCHORS = AGENT_ROOT / "references" / "top_journal_figure_anchors.json"
DEFAULT_OUTPUT_MD = ROOT / "release_metadata" / "top_journal_figure_audit_latest.md"
DEFAULT_OUTPUT_JSON = ROOT / "release_metadata" / "top_journal_figure_audit_latest.json"
DEFAULT_VISUAL_REVIEW = ROOT / "release_metadata" / "top_journal_visual_review_v3.json"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_visual_review(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "score_out_of_100": 0.0,
            "summary": "No human visual-quality review is recorded.",
        }
    review = read_json(path)
    review.setdefault("status", "missing")
    review.setdefault("score_out_of_100", 0.0)
    review.setdefault("summary", "No visual-review summary provided.")
    return review


def find_numbered_ids(text: str, label: str, expected_count: int) -> dict[str, Any]:
    pattern = re.compile(rf"{re.escape(label)}\s+(\d+)", flags=re.IGNORECASE)
    found = sorted({int(value) for value in pattern.findall(text)})
    expected = list(range(1, expected_count + 1))
    missing = [value for value in expected if value not in found]
    return {"found": found, "expected": expected, "missing": missing, "complete": not missing}


def file_set_for_stem(project_root: Path, stem: str) -> list[Path]:
    stem_path = project_root / stem
    suffixes = (".svg", ".pdf", ".tif", ".tiff", ".png")
    return [stem_path.with_suffix(suffix) for suffix in suffixes if stem_path.with_suffix(suffix).exists()]


def inspect_asset(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "suffix": path.suffix.lower(),
        "bytes": path.stat().st_size,
    }
    if path.suffix.lower() == ".svg":
        content = path.read_text(encoding="utf-8", errors="ignore")
        text_nodes = len(re.findall(r"<text(?:\s|>)", content))
        panel_labels = sorted(set(re.findall(r">\s*([a-i])\s*<", content)))
        result.update({"editable_svg_text_nodes": text_nodes, "panel_labels": panel_labels})
        return result

    if path.suffix.lower() in {".png", ".tif", ".tiff"}:
        try:
            from PIL import Image

            with Image.open(path) as image:
                dpi = image.info.get("dpi")
                normalized_dpi = [float(value) for value in dpi] if dpi else None
                result.update({"pixels": list(image.size), "dpi": normalized_dpi})
        except ImportError:
            result["image_inspection"] = "Pillow unavailable"
        except OSError as exc:
            result["image_inspection"] = f"unable to inspect: {exc}"
    return result


def score_fraction(found: int, required: int) -> float:
    return 1.0 if required == 0 else min(found / required, 1.0)


def has_required_claims(text: str, tokens: list[str]) -> tuple[list[str], list[str]]:
    present = [token for token in tokens if token.lower() in text.lower()]
    missing = [token for token in tokens if token not in present]
    return present, missing


def audit(project_root: Path, blueprint_path: Path, manifest_path: Path, rubric_path: Path, anchors_path: Path,
          visual_reviewed: bool, visual_review_path: Path = DEFAULT_VISUAL_REVIEW) -> dict[str, Any]:
    blueprint = blueprint_path.read_text(encoding="utf-8")
    manifest = read_json(manifest_path)
    rubric = read_json(rubric_path)
    anchors = read_json(anchors_path)
    visual_review = load_visual_review(visual_review_path)
    visual_score = max(0.0, min(float(visual_review["score_out_of_100"]), 100.0))
    visual_passed = visual_review["status"] == "approved" and visual_score >= 85.0
    required = rubric["required_package"]

    plan = {
        "main_figures": find_numbered_ids(blueprint, "Figure", required["main_figures"]),
        "extended_data": find_numbered_ids(blueprint, "Extended Data Fig.", required["extended_data_figures"]),
        "supplementary_figures": find_numbered_ids(blueprint, "Supplementary Fig.", required["supplementary_figures"]),
        "supplementary_tables": find_numbered_ids(blueprint, "Supplementary Table", required["supplementary_tables"]),
        "source_data": find_numbered_ids(blueprint, "Source Data Fig.", required["source_data_groups"]),
        "supplementary_notes": find_numbered_ids(blueprint, "Supplementary Note", required["supplementary_notes"]),
    }
    plan_complete = all(section["complete"] for section in plan.values())
    present_claims, missing_claims = has_required_claims(blueprint, rubric["required_claim_tokens"])

    final_groups = manifest["main_figures"] + manifest["extended_data"]
    final_assets: list[dict[str, Any]] = []
    ready_groups = 0
    technical_passes = 0
    for group in final_groups:
        files = file_set_for_stem(project_root, group["stem"])
        inspections = [inspect_asset(path) for path in files]
        suffixes = {item["suffix"] for item in inspections}
        has_vector = bool(suffixes.intersection(rubric["technical_rules"]["required_vector_extensions"]))
        has_raster = bool(suffixes.intersection(rubric["technical_rules"]["required_raster_extensions"]))
        ready = has_vector and has_raster
        if ready:
            ready_groups += 1
        svg_items = [item for item in inspections if item["suffix"] == ".svg"]
        svg_text_ok = bool(svg_items) and all(item.get("editable_svg_text_nodes", 0) > 0 for item in svg_items)
        raster_items = [item for item in inspections if item["suffix"] in {".png", ".tif", ".tiff"}]
        dpi_ok = bool(raster_items) and any(
            item.get("dpi") and min(item["dpi"]) >= rubric["technical_rules"]["minimum_raster_dpi"]
            for item in raster_items
        )
        if ready and svg_text_ok and dpi_ok:
            technical_passes += 1
        final_assets.append({
            "id": group["id"],
            "status": group["status"],
            "files": inspections,
            "ready": ready,
            "svg_text_ok": svg_text_ok,
            "dpi_ok": dpi_ok,
        })

    prototype_assets = []
    for group in manifest.get("prototypes", []):
        files = [inspect_asset(path) for path in file_set_for_stem(project_root, group["stem"])]
        prototype_assets.append({"id": group["id"], "status": group["status"], "files": files})

    counts = {
        "main_figures": len(plan["main_figures"]["found"]),
        "extended_data_figures": len(plan["extended_data"]["found"]),
        "supplementary_figures": len(plan["supplementary_figures"]["found"]),
        "supplementary_tables": len(plan["supplementary_tables"]["found"]),
        "source_data_groups": len(plan["source_data"]["found"]),
        "supplementary_notes": len(plan["supplementary_notes"]["found"]),
    }
    plan_fraction = score_fraction(counts["main_figures"], required["main_figures"])
    support_fraction = sum(
        score_fraction(counts[key], required[key])
        for key in ("extended_data_figures", "supplementary_figures", "supplementary_tables", "source_data_groups", "supplementary_notes")
    ) / 5
    asset_fraction = score_fraction(ready_groups, len(final_groups))
    technical_fraction = score_fraction(technical_passes, len(final_groups))
    integrity_fraction = score_fraction(len(present_claims), len(rubric["required_claim_tokens"]))
    weights = rubric["weights"]
    score_components = {
        "blueprint_completeness": round(weights["blueprint_completeness"] * plan_fraction, 2),
        "evidence_integrity": round(weights["evidence_integrity"] * integrity_fraction, 2),
        "supporting_package": round(weights["supporting_package"] * support_fraction, 2),
        "rendered_asset_coverage": round(weights["rendered_asset_coverage"] * asset_fraction, 2),
        "technical_export_quality": round(weights["technical_export_quality"] * technical_fraction, 2),
        "visual_review": round(weights["visual_review"] * visual_score / 100.0, 2),
    }
    technical_readiness_score = round(sum(score_components.values()), 2)
    # A complete manifest cannot compensate for a visually failed main-figure story.
    overall = technical_readiness_score if visual_passed else round(min(technical_readiness_score, visual_score), 2)

    blockers = []
    if not plan_complete:
        blockers.append("The blueprint is missing required primary, Extended Data, supplementary, source-data or note entries.")
    if missing_claims:
        blockers.append("Missing evidence-boundary tokens: " + ", ".join(missing_claims))
    if ready_groups < len(final_groups):
        blockers.append(
            f"Only {ready_groups}/{len(final_groups)} final figure groups have both vector and raster outputs."
        )
    if technical_passes < ready_groups:
        blockers.append("At least one rendered group lacks editable SVG text or a raster at the minimum 300 dpi.")
    if not visual_passed:
        blockers.append(
            "Visual quality is not approved: "
            f"status={visual_review['status']}, score={visual_score:.1f}/100. "
            "Technical export checks cannot substitute for editorial visual review."
        )

    if not plan_complete:
        state = "BLUEPRINT_INCOMPLETE"
    elif ready_groups < len(final_groups):
        state = "BLUEPRINT_READY_RENDERING_NOT_STARTED"
    elif not visual_passed:
        state = "VISUAL_REBUILD_REQUIRED"
    elif overall >= 90:
        state = "SUBMISSION_READY"
    else:
        state = "REVISE_TO_CLEAR_90"

    return {
        "schema_version": "plant_cellfm_top_journal_figure_audit_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "state": state,
        "overall_score": overall,
        "technical_readiness_score": technical_readiness_score,
        "anchor_corpus": {"count": len(anchors["anchors"]), "scope": anchors["scope"]},
        "package_counts": counts,
        "plan": plan,
        "claim_integrity": {"present": present_claims, "missing": missing_claims},
        "visual_review": {
            "status": visual_review["status"],
            "score_out_of_100": visual_score,
            "summary": visual_review["summary"],
            "approved": visual_passed,
        },
        "asset_coverage": {"ready_groups": ready_groups, "required_groups": len(final_groups), "assets": final_assets},
        "prototypes": prototype_assets,
        "score_components": score_components,
        "hard_blockers": blockers,
        "next_actions": [
            "Export the canonical Supplementary Tables before drawing quantitative panels.",
            "Create final assets with the figure-asset manifest stems and SVG/PDF/TIFF/PNG exports.",
            "Run this audit after every figure batch and record visual QA only after inspecting final-size exports.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Plant-CellFM Top-Journal Figure Audit",
        "",
        f"- State: `{report['state']}`",
        f"- Overall score: `{report['overall_score']:.2f}/100`",
        f"- Technical / metadata readiness: `{report['technical_readiness_score']:.2f}/100`",
        f"- Visual review: `{report['visual_review']['score_out_of_100']:.1f}/100` ({report['visual_review']['status']})",
        f"- Visual review summary: {report['visual_review']['summary']}",
        f"- Verified reference anchors: `{report['anchor_corpus']['count']}`",
        "",
        "## Package Coverage",
        "",
        "| Component | Planned | Required |",
        "|---|---:|---:|",
    ]
    required_names = {
        "main_figures": "Main figures",
        "extended_data_figures": "Extended Data figures",
        "supplementary_figures": "Supplementary figures",
        "supplementary_tables": "Supplementary tables",
        "source_data_groups": "Source-data groups",
        "supplementary_notes": "Supplementary notes",
    }
    required = {
        "main_figures": 6,
        "extended_data_figures": 9,
        "supplementary_figures": 13,
        "supplementary_tables": 13,
        "source_data_groups": 6,
        "supplementary_notes": 5,
    }
    for key, label in required_names.items():
        lines.append(f"| {label} | {report['package_counts'][key]} | {required[key]} |")
    lines.extend([
        "",
        "## Score Components",
        "",
        "| Component | Score |",
        "|---|---:|",
    ])
    for name, score in report["score_components"].items():
        lines.append(f"| {name} | {score:.2f} |")
    lines.extend(["", "## Hard Blockers", ""])
    if report["hard_blockers"]:
        lines.extend(f"- {item}" for item in report["hard_blockers"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"1. {item}" for item in report["next_actions"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the Plant-CellFM top-journal figure suite.")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--blueprint", type=Path, default=DEFAULT_BLUEPRINT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    parser.add_argument("--anchors", type=Path, default=DEFAULT_ANCHORS)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--visual-reviewed", action="store_true")
    parser.add_argument("--visual-review", type=Path, default=DEFAULT_VISUAL_REVIEW)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    report = audit(
        project_root,
        args.blueprint.resolve(),
        args.manifest.resolve(),
        args.rubric.resolve(),
        args.anchors.resolve(),
        args.visual_reviewed,
        args.visual_review.resolve(),
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"state": report["state"], "score": report["overall_score"], "blockers": len(report["hard_blockers"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
