"""Evidence-aware orchestration layer for Plant-CellFM.

The agent is a constrained plan-act-verify state machine. Model inference stays
in :func:`snowcell.train.annotate_to_bundle`; this module adds auditable input
checks, route selection, optional support-prototype calibration and review
artifacts around that frozen inference contract.
"""

from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

import torch

from .adapters import load_registry, normalize_species
from .agent_policy import choose_route, review_decision
from .agent_report import write_agent_report
from .agent_schema import AgentConfig, AgentEvent, AgentRunResult
from .agent_tools import (
    apply_fewshot_prototypes,
    assess_predictions,
    input_audit,
    support_table_info,
    write_predicted_marker_evidence,
    write_uncertainty_review,
)
from .artifacts import load_checkpoint, read_json, write_json
from .config import DataConfig, ExperimentConfig
from .specialist_agents import (
    select_specialist_plan,
    verify_specialist_outputs,
    write_specialist_manifest,
)
from .train import annotate_to_bundle


def _device(value: torch.device | str | None) -> torch.device:
    if isinstance(value, torch.device):
        return value
    if value in (None, "auto"):
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(str(value))


def _species_from_audit(audit: dict[str, Any], requested: str | None) -> str | None:
    if requested:
        return requested
    values = audit.get("species", {}).get("values", [])
    return values[0] if len(values) == 1 and values[0] != "unknown_species" else None


def _write_trace(path: Path, events: list[AgentEvent]) -> None:
    path.write_text(
        "".join(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def _force_review_quality(quality: dict[str, Any], reason: str) -> dict[str, Any]:
    """Convert a failed specialist contract into an explicit review-only result."""

    forced = dict(quality)
    forced["accepted_cells"] = 0
    forced["accepted_coverage"] = 0.0
    forced["accepted_mean_confidence"] = 0.0
    forced["review_cells"] = int(quality.get("n_cells", 0))
    forced["review_fraction"] = 1.0 if quality.get("n_cells", 0) else 0.0
    forced["fallback_forced_review"] = True
    forced["fallback_reason"] = reason
    return forced


def run_agent(
    checkpoint_path: str | Path,
    data_path: str | Path,
    output_dir: str | Path,
    species: str | None = None,
    registry_path: str | Path = "release_metadata/plant_species_adapters.json",
    specialist_manifest_path: str | Path | None = None,
    layer: str | None = None,
    ortholog_map: str | Path | None = None,
    ortholog_aggregation: str | None = None,
    support_labels: str | Path | None = None,
    review_threshold: float = 0.70,
    accepted_coverage_target: float = 0.80,
    batch_size: int = 128,
    device: torch.device | str | None = None,
) -> dict[str, Any]:
    """Run one fully auditable agent annotation job."""

    run_id = f"agent-{uuid.uuid4().hex[:12]}"
    started = time.perf_counter()
    bundle = Path(output_dir)
    bundle.mkdir(parents=True, exist_ok=True)
    events: list[AgentEvent] = []

    def event(stage: str, action: str, status: str, **evidence: Any) -> None:
        events.append(AgentEvent(stage=stage, action=action, status=status, evidence=evidence))

    checkpoint = load_checkpoint(checkpoint_path, map_location="cpu")
    experiment = ExperimentConfig.from_dict(checkpoint["experiment_config"])
    data_config = DataConfig(
        **{
            **experiment.data.__dict__,
            "path": str(data_path),
            "layer": experiment.data.layer if layer is None else layer,
            "ortholog_map": str(ortholog_map) if ortholog_map else experiment.data.ortholog_map,
            "ortholog_aggregation": ortholog_aggregation or experiment.data.ortholog_aggregation,
        }
    )
    policy = AgentConfig(
        review_threshold=review_threshold,
        accepted_coverage_target=accepted_coverage_target,
        batch_size=batch_size,
    )

    event("audit", "load_input_matrix", "running", data_path=str(data_path))
    audit = input_audit(data_path, data_config)
    event(
        "audit",
        "load_input_matrix",
        "complete",
        n_cells=audit["n_cells"],
        n_genes=audit["n_genes"],
        density=audit["matrix_density"],
    )

    resolved_species = _species_from_audit(audit, species)
    registry = load_registry(registry_path)
    adapter, used_fallback = registry.resolve(resolved_species)
    support_info = support_table_info(support_labels)
    route_decision = choose_route(
        adapter=adapter,
        used_fallback=used_fallback,
        has_ortholog_map=bool(ortholog_map or data_config.ortholog_map),
        support_count=int(support_info.get("n_unique_cells", 0)),
        fewshot_min_support=policy.fewshot_min_support,
    )
    route_decision.update(
        {
            "requested_species": species,
            "resolved_species": resolved_species,
            "metadata_species_values": audit.get("species", {}).get("values", []),
            "species_metadata_mismatch": bool(
                species
                and audit.get("species", {}).get("values")
                and not any(
                    normalize_species(species) == normalize_species(value)
                    for value in audit.get("species", {}).get("values", [])
                )
            ),
            "support": support_info,
        }
    )
    specialist_plan = select_specialist_plan(registry, adapter, route_decision, audit)
    specialist_capability_path = bundle / "specialist_capabilities.json"
    if specialist_manifest_path:
        write_specialist_manifest(registry, specialist_manifest_path)
        specialist_capability_path.write_bytes(Path(specialist_manifest_path).read_bytes())
    else:
        write_specialist_manifest(registry, specialist_capability_path)
    specialist_plan_path = bundle / "specialist_plan.json"
    write_json(specialist_plan_path, specialist_plan)
    route_decision["specialist_plan"] = specialist_plan
    write_json(bundle / "route_decision.json", route_decision)
    event("plan", "resolve_species_adapter", "complete", **route_decision)
    event(
        "plan",
        "select_specialist_agent",
        "complete",
        primary_agent_id=specialist_plan["primary_agent"]["agent_id"],
        auxiliary_agent_ids=[item["agent_id"] for item in specialist_plan["auxiliary_agents"]],
        fallback_agent_ids=[item["agent_id"] for item in specialist_plan["fallback_chain"]],
    )

    plan = {
        "run_id": run_id,
        "agent": "PlantCell-Agent",
        "version": "0.2.0",
        "objective": "reproducible plant single-cell annotation with explicit uncertainty review",
        "checkpoint_unchanged": True,
        "central_model_id": "plant_cellfm.central_model",
        "specialist_plan": specialist_plan,
        "route_decision": route_decision,
        "policy": {
            "review_threshold": policy.review_threshold,
            "accepted_coverage_target": policy.accepted_coverage_target,
            "fewshot_min_support": policy.fewshot_min_support,
            "marker_top_n": policy.marker_top_n,
            "marker_min_cells": policy.marker_min_cells,
        },
        "steps": [
            "input_audit",
            "species_adapter_resolution",
            "specialist_agent_selection",
            "frozen_checkpoint_inference",
            "optional_embedding_prototype_calibration",
            "ortholog_fallback_retry_if_required",
            "confidence_and_open_set_review",
            "predicted_marker_evidence",
            "audit_report",
        ],
    }
    write_json(bundle / "agent_plan.json", plan)

    event("act", "frozen_checkpoint_inference", "running", device=str(_device(device)))
    annotation = annotate_to_bundle(
        checkpoint_path=checkpoint_path,
        data_path=data_path,
        output_dir=bundle,
        layer=layer,
        ortholog_map=ortholog_map,
        ortholog_aggregation=ortholog_aggregation,
        batch_size=policy.batch_size,
        device=_device(device),
    )
    prediction_path = bundle / "predictions.csv"
    direct_prediction_path = bundle / "predictions_direct.csv"
    direct_prediction_path.write_bytes(prediction_path.read_bytes())
    event("act", "frozen_checkpoint_inference", "complete", **annotation)
    verification = verify_specialist_outputs(bundle, int(audit["n_cells"]))
    write_json(bundle / "evidence_verification.json", verification)
    verification_event = dict(verification)
    verification_event["contract_status"] = verification_event.pop("status", "unknown")
    event("verify", "specialist_output_contract", verification_event["contract_status"], **verification_event)
    if verification["status"] == "failed" and not prediction_path.is_file():
        raise RuntimeError("specialist output contract failed before predictions were written")
    force_review = bool(verification["force_review"])

    calibration: dict[str, Any] | None = None
    if route_decision["route"] == "fewshot_adapter":
        event("act", "embedding_prototype_calibration", "running", support_rows=support_info["n_rows"])
        try:
            calibration = apply_fewshot_prototypes(
                prediction_path=direct_prediction_path,
                embedding_path=bundle / "embeddings.npy",
                support_path=support_labels,
                output_path=prediction_path,
                min_support=policy.fewshot_min_support,
            )
            event("act", "embedding_prototype_calibration", "complete", **calibration)
        except (OSError, ValueError, KeyError) as exc:
            calibration = {"status": "failed", "error": str(exc), "fallback": "direct_predictions"}
            event("act", "embedding_prototype_calibration", "failed", error=str(exc))
            prediction_path.write_bytes(direct_prediction_path.read_bytes())
    else:
        event("act", "embedding_prototype_calibration", "skipped", reason="support contract not met")

    quality = assess_predictions(prediction_path, policy.review_threshold)
    if force_review:
        quality = _force_review_quality(quality, "; ".join(verification["errors"]))
    decision = review_decision(quality, policy.review_threshold, policy.accepted_coverage_target)
    retry_summary: dict[str, Any] | None = None
    retry_dir: Path | None = None
    retry_is_allowed = (
        not force_review
        and not decision["passed"]
        and route_decision["route"] != "fewshot_adapter"
        and bool(data_config.ortholog_map)
        and policy.max_retries > 0
    )
    if retry_is_allowed:
        current_aggregation = data_config.ortholog_aggregation
        alternate_aggregation = "mean" if current_aggregation == "first" else "first"
        retry_dir = bundle / f"retry_ortholog_{alternate_aggregation}"
        event(
            "retry",
            "alternate_ortholog_projection",
            "running",
            current_aggregation=current_aggregation,
            alternate_aggregation=alternate_aggregation,
        )
        try:
            retry_annotation = annotate_to_bundle(
                checkpoint_path=checkpoint_path,
                data_path=data_path,
                output_dir=retry_dir,
                layer=layer,
                ortholog_map=ortholog_map,
                ortholog_aggregation=alternate_aggregation,
                batch_size=policy.batch_size,
                device=_device(device),
            )
            retry_quality = assess_predictions(retry_dir / "predictions.csv", policy.review_threshold)
            retry_quality["annotation"] = retry_annotation
            retry_decision = review_decision(
                retry_quality, policy.review_threshold, policy.accepted_coverage_target
            )
            retry_summary = {
                "status": "complete",
                "current_aggregation": current_aggregation,
                "alternate_aggregation": alternate_aggregation,
                "quality": retry_quality,
                "decision": retry_decision,
                "output_dir": str(retry_dir),
            }
            current_rank = (
                float(quality["accepted_coverage"]),
                float(quality["accepted_mean_confidence"]),
            )
            retry_rank = (
                float(retry_quality["accepted_coverage"]),
                float(retry_quality["accepted_mean_confidence"]),
            )
            if retry_rank > current_rank:
                shutil.copyfile(retry_dir / "predictions.csv", prediction_path)
                shutil.copyfile(retry_dir / "embeddings.npy", bundle / "embeddings_retry_selected.npy")
                quality = retry_quality
                decision = retry_decision
                retry_summary["selected"] = True
            else:
                retry_summary["selected"] = False
            retry_event = dict(retry_summary)
            retry_event["retry_status"] = retry_event.pop("status", "unknown")
            event("retry", "alternate_ortholog_projection", "complete", **retry_event)
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            retry_summary = {
                "status": "failed",
                "error": str(exc),
                "current_aggregation": current_aggregation,
                "alternate_aggregation": alternate_aggregation,
            }
            event("retry", "alternate_ortholog_projection", "failed", error=str(exc))
    else:
        event("retry", "alternate_ortholog_projection", "skipped", reason="route or quality contract did not require retry")

    quality["retry"] = retry_summary
    if force_review:
        quality = _force_review_quality(quality, "; ".join(verification["errors"]))
    decision = review_decision(quality, policy.review_threshold, policy.accepted_coverage_target)
    quality["decision"] = decision
    quality["specialist_verification"] = verification
    event("verify", "confidence_open_set_review", "complete", **quality)

    uncertainty_path = write_uncertainty_review(
        prediction_path,
        bundle / "uncertainty_review.tsv",
        policy.review_threshold,
        force_all_review=force_review,
    )
    event("verify", "export_uncertainty_review", "complete", output=str(uncertainty_path))

    try:
        marker_summary = write_predicted_marker_evidence(
            data_path=data_path,
            prediction_path=prediction_path,
            output_path=bundle / "marker_evidence.tsv",
            config=data_config,
            top_n=policy.marker_top_n,
            min_cells=policy.marker_min_cells,
        )
    except (OSError, ValueError, KeyError) as exc:
        marker_summary = {"matched_cells": 0, "marker_rows": 0, "marker_labels": 0, "status": "failed", "error": str(exc)}
        (bundle / "marker_evidence.tsv").write_text("label_key\tlabel\trank\tgene\tscore\n", encoding="utf-8")
    marker_event = dict(marker_summary)
    marker_event["marker_status"] = marker_event.pop("status", "unknown")
    event("verify", "marker_evidence_check", "complete", **marker_event)

    runtime_seconds = time.perf_counter() - started
    run_device = _device(device)
    quality["runtime_seconds"] = float(runtime_seconds)
    quality["device"] = str(run_device)
    if run_device.type == "cuda" and torch.cuda.is_available():
        quality["cuda_peak_memory_mb"] = float(torch.cuda.max_memory_allocated(run_device) / (1024**2))
    else:
        quality["cuda_peak_memory_mb"] = 0.0
    quality["marker_evidence"] = marker_summary

    metadata_path = bundle / "annotation_metadata.json"
    metadata = read_json(metadata_path) if metadata_path.exists() else {}
    metadata["agent"] = {
        "name": "PlantCell-Agent",
        "version": "0.2.0",
        "run_id": run_id,
        "central_model_id": "plant_cellfm.central_model",
        "primary_specialist_agent": specialist_plan["primary_agent"]["agent_id"],
        "route": route_decision,
        "specialist_plan": specialist_plan,
        "evidence_verification": verification,
        "quality": quality,
        "calibration": calibration,
        "marker_evidence": marker_summary,
        "retry": retry_summary,
        "runtime_seconds": runtime_seconds,
        "direct_predictions": direct_prediction_path.name,
        "checkpoint_unchanged": True,
    }
    write_json(metadata_path, metadata)

    artifacts = {
        "predictions": str(prediction_path),
        "predictions_direct": str(direct_prediction_path),
        "embeddings": str(bundle / "embeddings.npy"),
        "annotation_metadata": str(metadata_path),
        "agent_plan": str(bundle / "agent_plan.json"),
        "route_decision": str(bundle / "route_decision.json"),
        "specialist_capabilities": str(specialist_capability_path),
        "specialist_plan": str(specialist_plan_path),
        "evidence_verification": str(bundle / "evidence_verification.json"),
        "agent_trace": str(bundle / "agent_trace.jsonl"),
        "uncertainty_review": str(uncertainty_path),
        "marker_evidence": str(bundle / "marker_evidence.tsv"),
        "agent_report": str(bundle / "agent_report.md"),
    }
    if retry_dir is not None:
        artifacts["retry_output_dir"] = str(retry_dir)
        if (bundle / "embeddings_retry_selected.npy").exists():
            artifacts["embeddings_retry_selected"] = str(bundle / "embeddings_retry_selected.npy")
    result = AgentRunResult(
        run_id=run_id,
        status=decision["status"],
        route=route_decision["route"],
        output_dir=str(bundle),
        input_audit=audit,
        route_decision=route_decision,
        quality=quality,
        artifacts=artifacts,
        events=events,
    ).to_dict()
    _write_trace(bundle / "agent_trace.jsonl", events)
    write_agent_report(result, bundle / "agent_report.md")
    write_json(bundle / "agent_result.json", result)
    return result
