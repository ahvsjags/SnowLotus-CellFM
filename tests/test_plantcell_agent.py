from __future__ import annotations

from pathlib import Path

import pandas as pd

from snowcell.adapters import PlantAdapter
from snowcell.agent_policy import choose_route, review_decision
from snowcell.agent_tools import assess_predictions, input_audit
from snowcell.config import DataConfig
from snowcell.train import create_demo_dataset


def _adapter(status: str = "validated") -> PlantAdapter:
    return PlantAdapter(
        adapter_id="adapter_test",
        species="Arabidopsis thaliana",
        aliases=("Arabidopsis",),
        status=status,
        transfer_mode="exact_gene_ids_then_ortholog_map",
        gene_id_namespace="symbol",
        ortholog_map=None,
        supervised_head=None,
        tasks=("annotation_transfer",),
        evidence={},
    )


def test_agent_route_prefers_support_then_ortholog_then_open_set() -> None:
    support_route = choose_route(_adapter(), False, False, 8)
    assert support_route["route"] == "fewshot_adapter"
    ortholog_route = choose_route(_adapter("general_backbone_ready_runtime"), False, True, 0)
    assert ortholog_route["route"] == "ortholog_stc"
    open_route = choose_route(_adapter("general_backbone_ready_runtime"), True, False, 0)
    assert open_route["route"] == "universal_open_set"


def test_review_decision_keeps_selective_metrics_explicit() -> None:
    decision = review_decision(
        {"accepted_coverage": 0.6, "mean_confidence": 0.95, "review_fraction": 0.4},
        review_threshold=0.7,
        accepted_coverage_target=0.8,
    )
    assert decision["status"] == "manual_review_required"
    assert decision["passed"] is False


def test_input_audit_and_prediction_quality(tmp_path: Path) -> None:
    data_path = create_demo_dataset(tmp_path / "demo.npz", cells=48, genes=96, samples=6, seed=3)
    audit = input_audit(data_path, DataConfig(path=str(data_path), min_genes_per_cell=1, min_cells_per_gene=1))
    assert audit["n_cells"] == 48
    assert audit["n_genes"] == 96
    assert audit["cell_id_unique_fraction"] == 1.0

    prediction_path = tmp_path / "predictions.csv"
    pd.DataFrame(
        {
            "cell_id": ["a", "b", "c"],
            "fine_label": ["root", "unknown", "leaf"],
            "fine_confidence": [0.9, 0.99, 0.4],
        }
    ).to_csv(prediction_path, index=False)
    quality = assess_predictions(prediction_path, 0.7)
    assert quality["accepted_cells"] == 1
    assert quality["open_set_cells"] == 1
    assert quality["review_cells"] == 2
