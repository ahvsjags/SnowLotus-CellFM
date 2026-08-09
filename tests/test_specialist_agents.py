from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from snowcell.adapters import PlantAdapter, PlantAdapterRegistry
from snowcell.specialist_agents import (
    build_specialist_manifest,
    select_specialist_plan,
    verify_specialist_outputs,
    write_specialist_manifest,
)


def _registry() -> PlantAdapterRegistry:
    return PlantAdapterRegistry(
        [
            PlantAdapter(
                adapter_id="plant_universal",
                species="__unregistered_plant__",
                aliases=("unknown plant",),
                status="universal_fallback",
                transfer_mode="exact_gene_ids_then_ortholog_map",
                gene_id_namespace="dataset_defined",
                ortholog_map=None,
                supervised_head=None,
                tasks=("embedding", "annotation_transfer"),
                evidence={"source": "test"},
            ),
            PlantAdapter(
                adapter_id="plant_test_species",
                species="Test plant",
                aliases=("test",),
                status="general_backbone_ready",
                transfer_mode="exact_gene_ids_then_ortholog_map",
                gene_id_namespace="dataset_defined",
                ortholog_map=None,
                supervised_head=None,
                tasks=("embedding", "annotation_transfer"),
                evidence={"source": "test"},
            ),
        ],
        fallback_adapter="plant_universal",
    )


def test_manifest_declares_central_and_specialist_contracts() -> None:
    manifest = build_specialist_manifest(_registry())
    ids = {item["agent_id"] for item in manifest["agents"]}
    assert manifest["central_model"]["model_id"] == "plant_cellfm.central_model"
    assert "specialist.adapter.plant_test_species" in ids
    assert "specialist.orthology_transfer" in ids
    assert "evidence.verification" in ids
    assert manifest["orchestrator"]["no_silent_fallback"] is True


def test_specialist_plan_selects_adapter_and_context_agent() -> None:
    registry = _registry()
    adapter, used_fallback = registry.resolve("Test plant")
    assert used_fallback is False
    route = {
        "route": "registered_adapter",
        "adapter_id": adapter.adapter_id,
        "resolved_species": "Test plant",
        "has_ortholog_map": False,
        "support_count": 0,
    }
    plan = select_specialist_plan(
        registry,
        adapter,
        route,
        {"tissue": {"values": ["root"]}},
    )
    assert plan["primary_agent"]["agent_id"] == "specialist.adapter.plant_test_species"
    assert plan["auxiliary_agents"][0]["agent_id"] == "specialist.organ_context"
    assert plan["fallback_chain"][0]["agent_id"] == "specialist.orthology_transfer"


def test_specialist_output_contract_and_manifest_export(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    predictions = pd.DataFrame(
        {
            "cell_id": ["a", "b"],
            "fine_label": ["root", "leaf"],
            "fine_confidence": [0.9, 0.8],
        }
    )
    predictions.to_csv(bundle / "predictions.csv", index=False)
    predictions.to_csv(bundle / "predictions_direct.csv", index=False)
    np.save(bundle / "embeddings.npy", np.ones((2, 256), dtype=np.float32))
    passed = verify_specialist_outputs(bundle, expected_cells=2)
    assert passed["status"] == "passed"
    assert passed["force_review"] is False

    (bundle / "embeddings.npy").unlink()
    failed = verify_specialist_outputs(bundle, expected_cells=2)
    assert failed["status"] == "failed"
    assert failed["fallback_agent"] == "review.human"
    assert failed["force_review"] is True

    np.save(bundle / "embeddings.npy", np.ones((2, 255), dtype=np.float32))
    failed_dimension = verify_specialist_outputs(bundle, expected_cells=2)
    assert failed_dimension["status"] == "failed"
    assert failed_dimension["fallback_agent"] == "review.human"

    manifest_path = tmp_path / "specialists.json"
    write_specialist_manifest(_registry(), manifest_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "plantcell-specialist-agents-v1"
