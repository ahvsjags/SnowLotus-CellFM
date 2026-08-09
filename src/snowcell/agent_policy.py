"""Deterministic routing policy for Plant-CellFM agent runs."""

from __future__ import annotations

from typing import Any

from .adapters import PlantAdapter


def choose_route(
    adapter: PlantAdapter,
    used_fallback: bool,
    has_ortholog_map: bool,
    support_count: int,
    fewshot_min_support: int = 8,
) -> dict[str, Any]:
    """Choose an execution route without silently changing the model.

    ``fewshot_adapter`` means embedding-prototype calibration from labelled
    support cells. It is intentionally distinct from gradient-based training.
    """

    if support_count >= fewshot_min_support:
        route = "fewshot_adapter"
        rationale = "labelled support meets the minimum prototype-calibration contract"
        execution = "frozen_checkpoint_plus_embedding_prototypes"
    elif not used_fallback and adapter.status != "general_backbone_ready_runtime":
        route = "registered_adapter"
        rationale = "species resolves to a registered plant adapter"
        execution = "frozen_checkpoint_inference"
    elif has_ortholog_map:
        route = "ortholog_stc"
        rationale = "unregistered species has an explicit ortholog projection"
        execution = "frozen_checkpoint_inference_with_ortholog_projection"
    else:
        route = "universal_open_set"
        rationale = "no registered adapter or ortholog projection was supplied"
        execution = "frozen_checkpoint_inference_with_open_set_review"

    return {
        "route": route,
        "rationale": rationale,
        "execution_contract": execution,
        "adapter_id": adapter.adapter_id,
        "adapter_status": adapter.status,
        "used_fallback": bool(used_fallback),
        "has_ortholog_map": bool(has_ortholog_map),
        "support_count": int(support_count),
        "fewshot_min_support": int(fewshot_min_support),
    }


def review_decision(
    quality: dict[str, Any],
    review_threshold: float,
    accepted_coverage_target: float,
) -> dict[str, Any]:
    """Turn confidence and coverage into an explicit human-review decision."""

    coverage = float(quality.get("accepted_coverage", 0.0))
    mean_confidence = float(quality.get("mean_confidence", 0.0))
    review_fraction = float(quality.get("review_fraction", 1.0))
    passed = coverage >= accepted_coverage_target and mean_confidence >= review_threshold
    return {
        "status": "auto_annotation_pass" if passed else "manual_review_required",
        "passed": passed,
        "review_threshold": float(review_threshold),
        "accepted_coverage_target": float(accepted_coverage_target),
        "accepted_coverage": coverage,
        "mean_confidence": mean_confidence,
        "review_fraction": review_fraction,
        "reason": (
            "accepted cells meet the configured coverage and confidence contract"
            if passed
            else "low-confidence or open-set cells remain and are exported for review"
        ),
    }
