"""Capability contracts and orchestration for PlantCell-Agent specialists.

The specialist layer is deliberately separate from checkpoint inference.  A
specialist declares what it can consume, what it produces, what evidence it
must leave behind and where execution falls back when its contract is not met.
This makes adapter selection an auditable agent decision rather than a renamed
weight file.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .adapters import PlantAdapter, PlantAdapterRegistry


CENTRAL_MODEL_ID = "plant_cellfm.central_model"
SPECIALIST_SCHEMA_VERSION = "plantcell-specialist-agents-v1"


@dataclass(frozen=True)
class SpecialistAgentSpec:
    """A versioned capability and execution contract for one specialist."""

    agent_id: str
    role: str
    scope: str
    route: str
    adapter_id: str | None
    capabilities: tuple[str, ...]
    required_inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    fallback_chain: tuple[str, ...]
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "capabilities",
            "required_inputs",
            "outputs",
            "evidence_requirements",
            "fallback_chain",
        ):
            payload[key] = list(payload[key])
        return payload


def _adapter_agent(adapter: PlantAdapter) -> SpecialistAgentSpec:
    capabilities = tuple(
        dict.fromkeys(
            [
                *adapter.tasks,
                "species_adapter_execution",
                "shared_embedding_inference",
            ]
        )
    )
    fallback = ("specialist.orthology_transfer", "specialist.open_set")
    return SpecialistAgentSpec(
        agent_id=f"specialist.adapter.{adapter.adapter_id}",
        role="species_adapter",
        scope=adapter.species,
        route="registered_adapter",
        adapter_id=adapter.adapter_id,
        capabilities=capabilities,
        required_inputs=("cell_expression", "species_context", "central_embedding"),
        outputs=("cell_labels", "cell_confidence", "cell_embeddings", "marker_candidates"),
        evidence_requirements=("adapter_manifest", "gene_identifier_audit", "prediction_contract"),
        fallback_chain=fallback,
    )


def build_specialist_manifest(registry: PlantAdapterRegistry) -> dict[str, Any]:
    """Build the reproducible central-model and specialist capability registry."""

    adapters = [_adapter_agent(adapter) for adapter in registry.adapters if adapter.status != "universal_fallback"]
    shared = [
        SpecialistAgentSpec(
            agent_id="specialist.support_prototype",
            role="support_calibration",
            scope="target-labelled support cells",
            route="fewshot_adapter",
            adapter_id=None,
            capabilities=("fewshot_calibration", "prototype_readout", "label_space_recovery"),
            required_inputs=("central_embedding", "support_labels", "support_cell_ids"),
            outputs=("calibrated_labels", "calibrated_confidence", "prototype_table"),
            evidence_requirements=("support_count", "support_label_count", "disjoint_query_contract"),
            fallback_chain=("specialist.open_set", "review.human"),
        ),
        SpecialistAgentSpec(
            agent_id="specialist.orthology_transfer",
            role="orthology_transfer",
            scope="species with explicit gene projection",
            route="ortholog_stc",
            adapter_id=None,
            capabilities=("orthology_projection", "cross_species_transfer", "aggregation_retry"),
            required_inputs=("cell_expression", "ortholog_map", "central_embedding"),
            outputs=("projected_expression", "cell_labels", "cell_confidence"),
            evidence_requirements=("mapped_gene_fraction", "count_retention", "aggregation_rule"),
            fallback_chain=("specialist.open_set", "review.human"),
        ),
        SpecialistAgentSpec(
            agent_id="specialist.open_set",
            role="open_set_detection",
            scope="unregistered or unsupported plant species",
            route="universal_open_set",
            adapter_id=registry.fallback_adapter,
            capabilities=("universal_inference", "open_set_detection", "unsupported_label_review"),
            required_inputs=("cell_expression", "central_embedding", "label_vocabulary"),
            outputs=("cell_labels", "cell_confidence", "open_set_flags"),
            evidence_requirements=("label_coverage", "open_set_fraction", "confidence_summary"),
            fallback_chain=("review.human",),
        ),
        SpecialistAgentSpec(
            agent_id="specialist.organ_context",
            role="organ_context",
            scope="organ and tissue metadata",
            route="context_auxiliary",
            adapter_id=None,
            capabilities=("organ_context_routing", "tissue_prior", "phylogeny_context"),
            required_inputs=("organ_metadata", "species_context", "central_embedding"),
            outputs=("context_evidence", "routing_prior"),
            evidence_requirements=("tissue_metadata_presence", "species_alias_normalization"),
            fallback_chain=("specialist.open_set",),
        ),
        SpecialistAgentSpec(
            agent_id="evidence.verification",
            role="evidence_verification",
            scope="all PlantCell-Agent runs",
            route="post_inference",
            adapter_id=None,
            capabilities=("artifact_validation", "confidence_calibration", "marker_evidence", "ontology_check"),
            required_inputs=("predictions", "embeddings", "route_decision"),
            outputs=("verification_report", "evidence_record"),
            evidence_requirements=("row_count_match", "unique_cell_ids", "confidence_bounds"),
            fallback_chain=("review.human",),
        ),
        SpecialistAgentSpec(
            agent_id="review.human",
            role="human_review",
            scope="low-confidence, open-set or failed-contract cells",
            route="manual_review",
            adapter_id=None,
            capabilities=("review_queue", "expert_audit", "abstention"),
            required_inputs=("predictions", "review_reasons", "marker_evidence"),
            outputs=("uncertainty_review", "expert_audit_sheet"),
            evidence_requirements=("review_threshold", "open_set_flags", "blinded_audit_contract"),
            fallback_chain=(),
        ),
    ]
    agents = [*adapters, *shared]
    return {
        "schema_version": SPECIALIST_SCHEMA_VERSION,
        "central_model": {
            "model_id": CENTRAL_MODEL_ID,
            "role": "shared_plant_expression_encoder",
            "embedding_dim": 256,
            "checkpoint_contract": "frozen_checkpoint_inference",
            "outputs": ["cell_embeddings", "fine_labels", "coarse_labels", "confidence"],
        },
        "orchestrator": {
            "agent_id": "plantcell.orchestrator",
            "role": "route_audit_verify",
            "selection_order": ["support_calibration", "species_adapter", "orthology_transfer", "open_set_detection"],
            "always_on": ["evidence_verification", "human_review"],
            "no_silent_fallback": True,
        },
        "fallback_policy": {
            "failed_specialist": "review.human",
            "missing_contract_evidence": "review.human",
            "open_set_label": "review.human",
            "direct_predictions_preserved": True,
        },
        "agents": [agent.to_dict() for agent in agents],
    }


def select_specialist_plan(
    registry: PlantAdapterRegistry,
    adapter: PlantAdapter,
    route_decision: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Select a primary specialist and explicit fallback chain for one run."""

    manifest = build_specialist_manifest(registry)
    by_id = {item["agent_id"]: item for item in manifest["agents"]}
    route = str(route_decision["route"])
    if route == "fewshot_adapter":
        primary_id = "specialist.support_prototype"
    elif route == "registered_adapter":
        primary_id = f"specialist.adapter.{adapter.adapter_id}"
    elif route == "ortholog_stc":
        primary_id = "specialist.orthology_transfer"
    else:
        primary_id = "specialist.open_set"
    selected = by_id[primary_id]
    tissue_values = audit.get("tissue", {}).get("values", [])
    known_tissue = [value for value in tissue_values if value not in {"unknown_tissue", "", "nan"}]
    auxiliary = ["specialist.organ_context"] if known_tissue else []
    fallback_chain = list(selected["fallback_chain"])
    return {
        "schema_version": SPECIALIST_SCHEMA_VERSION,
        "central_model_id": CENTRAL_MODEL_ID,
        "orchestrator_id": "plantcell.orchestrator",
        "primary_agent": selected,
        "auxiliary_agents": [by_id[item] for item in auxiliary],
        "fallback_chain": [by_id[item] for item in fallback_chain],
        "always_on_agents": [by_id["evidence.verification"], by_id["review.human"]],
        "selection_evidence": {
            "route": route,
            "adapter_id": adapter.adapter_id,
            "resolved_species": route_decision.get("resolved_species"),
            "has_ortholog_map": route_decision.get("has_ortholog_map", False),
            "support_count": route_decision.get("support_count", 0),
            "known_tissue_values": known_tissue,
        },
        "failure_policy": manifest["fallback_policy"],
    }


def write_specialist_manifest(registry: PlantAdapterRegistry, output: str | Path) -> Path:
    """Export the versioned capability manifest used by a release."""

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_specialist_manifest(registry), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def verify_specialist_outputs(
    bundle: str | Path,
    expected_cells: int,
    expected_embedding_dim: int = 256,
) -> dict[str, Any]:
    """Verify the specialist output contract before release or review routing."""

    root = Path(bundle)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    prediction_path = root / "predictions.csv"
    embedding_path = root / "embeddings.npy"
    direct_path = root / "predictions_direct.csv"
    required = {"cell_id", "fine_label", "fine_confidence"}
    if not prediction_path.is_file():
        errors.append("predictions.csv is missing")
    else:
        predictions = pd.read_csv(prediction_path)
        missing = sorted(required - set(predictions.columns))
        checks.append({"check": "prediction_columns", "passed": not missing, "missing": missing})
        if missing:
            errors.append(f"prediction columns missing: {missing}")
        checks.append({"check": "prediction_row_count", "passed": len(predictions) == expected_cells, "observed": len(predictions), "expected": expected_cells})
        if len(predictions) != expected_cells:
            errors.append("prediction row count does not match audited cells")
        unique = bool(predictions["cell_id"].astype(str).is_unique) if "cell_id" in predictions else False
        checks.append({"check": "unique_cell_ids", "passed": unique})
        if not unique:
            errors.append("prediction cell IDs are not unique")
        if "fine_confidence" in predictions:
            confidence = pd.to_numeric(predictions["fine_confidence"], errors="coerce")
            bounded = bool(confidence.notna().all() and confidence.between(0.0, 1.0).all())
            checks.append({"check": "confidence_bounds", "passed": bounded})
            if not bounded:
                errors.append("fine_confidence contains missing or out-of-range values")
    if not embedding_path.is_file():
        errors.append("embeddings.npy is missing")
    else:
        embeddings = np.asarray(np.load(embedding_path), dtype=np.float32)
        shape_ok = (
            embeddings.ndim == 2
            and embeddings.shape[0] == expected_cells
            and embeddings.shape[1] == expected_embedding_dim
        )
        checks.append(
            {
                "check": "embedding_shape",
                "passed": shape_ok,
                "shape": list(embeddings.shape),
                "expected_cells": expected_cells,
                "expected_embedding_dim": expected_embedding_dim,
            }
        )
        if not shape_ok:
            errors.append("embedding shape does not match the central model contract")
    checks.append({"check": "direct_prediction_preserved", "passed": direct_path.is_file()})
    if not direct_path.is_file():
        errors.append("predictions_direct.csv is missing")
    return {
        "status": "passed" if not errors else "failed",
        "checks": checks,
        "errors": errors,
        "fallback_agent": "review.human" if errors else None,
        "force_review": bool(errors),
    }
