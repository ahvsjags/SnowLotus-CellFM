"""Replay PlantCell-Agent on the locked public case inputs.

This runner never copies old benchmark numbers into an Agent result. A case is
marked ``NOT_REPLAYED_INPUT_MISSING`` when its raw matrix or checkpoint is not
available in the current checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import torch

from snowcell.agent import run_agent
from snowcell.agent_tools import evaluate_predictions_against_reference
from snowcell.artifacts import load_checkpoint
from snowcell.config import DataConfig, ExperimentConfig


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "release_metadata" / "plantcell_agent_replay_manifest_v1.json"
DEFAULT_OUTPUT = ROOT / "release_metadata" / "plantcell_agent_replay_v1.json"
DEFAULT_MARKDOWN = ROOT / "release_metadata" / "plantcell_agent_replay_v1.md"


def _path(value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _device(value: str) -> torch.device:
    if value == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(value)


def _config_for_case(case: dict[str, Any], checkpoint: dict[str, Any]) -> DataConfig:
    experiment = ExperimentConfig.from_dict(checkpoint["experiment_config"])
    values = {
        **experiment.data.__dict__,
        "path": str(_path(case["data"])),
        "ortholog_map": str(_path(case["ortholog_map"])) if case.get("ortholog_map") else experiment.data.ortholog_map,
        "ortholog_aggregation": case.get("ortholog_aggregation", experiment.data.ortholog_aggregation),
    }
    return DataConfig(**values)


def _run_case(
    case: dict[str, Any],
    review_threshold: float,
    coverage_target: float,
    device: torch.device,
    batch_size: int,
    force: bool,
    repeat: bool,
) -> dict[str, Any]:
    checkpoint_path = _path(case["checkpoint"])
    data_path = _path(case["data"])
    output_dir = _path(case["output_dir"])
    missing = [str(path) for path in (checkpoint_path, data_path) if not path.exists()]
    if missing:
        return {
            "case_id": case["case_id"],
            "label": case["label"],
            "status": "NOT_REPLAYED_INPUT_MISSING",
            "missing_inputs": missing,
            "expected_route": case.get("expected_route"),
        }
    if case.get("ortholog_map") and not _path(case["ortholog_map"]).exists():
        return {
            "case_id": case["case_id"],
            "label": case["label"],
            "status": "NOT_REPLAYED_ORTHOLOG_MAP_MISSING",
            "missing_inputs": [str(_path(case["ortholog_map"]))],
            "expected_route": case.get("expected_route"),
        }

    result_path = output_dir / "agent_result.json"
    if force or not result_path.exists():
        result = run_agent(
            checkpoint_path=checkpoint_path,
            data_path=data_path,
            output_dir=output_dir,
            species=case.get("species"),
            ortholog_map=_path(case["ortholog_map"]) if case.get("ortholog_map") else None,
            ortholog_aggregation=case.get("ortholog_aggregation"),
            review_threshold=review_threshold,
            accepted_coverage_target=coverage_target,
            batch_size=batch_size,
            device=device,
        )
    else:
        result = json.loads(result_path.read_text(encoding="utf-8"))

    checkpoint = load_checkpoint(checkpoint_path, map_location="cpu")
    config = _config_for_case(case, checkpoint)
    direct_metrics = evaluate_predictions_against_reference(
        data_path, output_dir / "predictions_direct.csv", config, review_threshold
    )
    agent_metrics = evaluate_predictions_against_reference(
        data_path, output_dir / "predictions.csv", config, review_threshold
    )
    route = result.get("route_decision", {})
    specialist_plan = route.get("specialist_plan", {})
    primary_specialist = specialist_plan.get("primary_agent", {}).get("agent_id")
    evidence_status = result.get("quality", {}).get("specialist_verification", {}).get("status")
    raw_input_end_to_end = data_path.suffix.lower() == ".h5ad" and data_path.exists()
    payload: dict[str, Any] = {
        "case_id": case["case_id"],
        "label": case["label"],
        "status": result.get("status"),
        "raw_input_end_to_end": raw_input_end_to_end,
        "raw_input_sha256": _sha256(data_path) if raw_input_end_to_end else None,
        "replay_evidence_mode": "raw_h5ad_end_to_end" if raw_input_end_to_end else "locked_bundle_replay",
        "route": result.get("route"),
        "expected_route": case.get("expected_route"),
        "route_correct": result.get("route") == case.get("expected_route"),
        "species_metadata_mismatch": route.get("species_metadata_mismatch"),
        "primary_specialist_agent": primary_specialist,
        "specialist_evidence_status": evidence_status,
        "direct": direct_metrics,
        "agent": agent_metrics,
        "quality": result.get("quality", {}),
        "artifacts": result.get("artifacts", {}),
        "input_audit": result.get("input_audit", {}),
    }

    if repeat:
        repeat_dir = output_dir.parent / f"{output_dir.name}_repeat"
        repeat_result = run_agent(
            checkpoint_path=checkpoint_path,
            data_path=data_path,
            output_dir=repeat_dir,
            species=case.get("species"),
            ortholog_map=_path(case["ortholog_map"]) if case.get("ortholog_map") else None,
            ortholog_aggregation=case.get("ortholog_aggregation"),
            review_threshold=review_threshold,
            accepted_coverage_target=coverage_target,
            batch_size=batch_size,
            device=device,
        )
        files = ("predictions_direct.csv", "predictions.csv", "embeddings.npy")
        payload["repeatability"] = {
            "status": "exact_match" if all(
                _sha256(output_dir / name) == _sha256(repeat_dir / name) for name in files
            ) else "content_difference",
            "files": {
                name: {
                    "first_sha256": _sha256(output_dir / name),
                    "repeat_sha256": _sha256(repeat_dir / name),
                }
                for name in files
            },
            "repeat_run_id": repeat_result.get("run_id"),
        }
    else:
        payload["repeatability"] = {"status": "not_run"}
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# PlantCell-Agent replay v1",
        "",
        "The report separates frozen direct inference from Agent acceptance and review. Missing local inputs are not assigned metrics.",
        "",
        "| Case | Status | Route | Primary specialist | Contract | Direct accuracy | Agent accuracy | Agent coverage | Review fraction | Repeatability |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in payload["cases"]:
        direct = case.get("direct", {})
        agent = case.get("agent", {})
        lines.append(
            "| {label} | {status} | {route} | {specialist} | {contract} | {direct_acc} | {agent_acc} | {coverage} | {review} | {repeat} |".format(
                label=case["label"],
                status=case["status"],
                route=case.get("route", "-"),
                specialist=case.get("primary_specialist_agent") or "-",
                contract=case.get("specialist_evidence_status") or "-",
                direct_acc=f"{direct.get('all_cell_accuracy', 0.0):.4f}" if direct.get("status") == "ok" else "-",
                agent_acc=f"{agent.get('all_cell_accuracy', 0.0):.4f}" if agent.get("status") == "ok" else "-",
                coverage=f"{agent.get('coverage', 0.0):.4f}" if agent.get("status") == "ok" else "-",
                review=f"{agent.get('review_fraction', 0.0):.4f}" if agent.get("status") == "ok" else "-",
                repeat=case.get("repeatability", {}).get("status", "-"),
            )
        )
    lines.extend(
        [
            "",
            "## Locked interpretation",
            "",
            "- `all_cell_accuracy` uses the complete matched denominator.",
            "- `coverage` is the fraction accepted by the Agent confidence/open-set policy.",
            "- `accepted_cell_accuracy` is reported separately and is never substituted for all-cell accuracy.",
            "- A route mismatch or species metadata mismatch remains visible in the JSON output.",
            "- The strict case is labelled `raw_h5ad_end_to_end` only when the manifest H5AD exists and is directly passed to the Agent; otherwise it remains `locked_bundle_replay` with no inferred raw-input metrics.",
            "- Specialist contract status is reported per end-to-end case; a failed contract activates Review Agent and preserves direct predictions.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--repeat", action="store_true")
    args = parser.parse_args()
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = [
        _run_case(
            case,
            review_threshold=float(manifest.get("review_threshold", 0.7)),
            coverage_target=float(manifest.get("accepted_coverage_target", 0.8)),
            device=_device(args.device),
            batch_size=args.batch_size,
            force=args.force,
            repeat=args.repeat,
        )
        for case in manifest["cases"]
    ]
    payload = {
        "schema_version": "plantcell_agent_replay_v1",
        "manifest": str(manifest_path),
        "review_threshold": manifest.get("review_threshold", 0.7),
        "accepted_coverage_target": manifest.get("accepted_coverage_target", 0.8),
        "cases": cases,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    markdown = args.markdown if args.markdown.is_absolute() else ROOT / args.markdown
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"output": str(output), "markdown": str(markdown), "cases": cases}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
