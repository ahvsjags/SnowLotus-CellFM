from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v5_blueprint_exposes_primary_claim_boundaries() -> None:
    blueprint = (ROOT / "release_metadata" / "plant_cellfm_v5_figure_blueprint.md").read_text(encoding="utf-8")
    assert "39.96% is the all-cell v17 result" in blueprint
    assert "global sensitivity analysis, not a replacement nested primary result" in blueprint
    assert "This is labelled adaptation, not zero-shot transfer" in blueprint
    assert "no external accuracy, external ranking or wet-lab validation is claimed" in blueprint


def test_v5_figure_audit_preserves_exports_and_frozen_evidence() -> None:
    report = json.loads((ROOT / "release_metadata" / "top_journal_figure_audit_v5.json").read_text(encoding="utf-8"))
    assert report["state"] == "TECHNICALLY_READY_PENDING_EDITORIAL_AND_EVIDENCE_REVIEW"
    assert report["technical_failures"] == []
    expected_evidence = {
        "v17_all_cell_accuracy": 0.39959636730575177,
        "v14_context_sensitivity_all_cell_accuracy": 0.42356205852674067,
        "v14_context_sensitivity_coverage": 0.5590312815338042,
        "external_root_input_cells": 6566,
        "external_root_label_free": True,
        "external_root_top_mean_marker_hits": 5,
        "root_candidate_rows": 200,
        "secondary_root_adapter_test_cells": 2352,
        "secondary_root_adapter_test_accuracy": 0.8397108843537415,
        "secondary_root_adapter_test_macro_f1": 0.8446817683258346,
        "secondary_root_adapter_matched_semantic_accuracy": 0.9092838196286472,
        "wheat_adapter_test_cells": 1433,
        "wheat_adapter_train_cells": 5014,
        "wheat_adapter_validation_cells": 717,
        "wheat_adapter_test_accuracy": 0.6224703419399861,
        "wheat_adapter_test_macro_f1": 0.6660112830533416,
        "wheat_adapter_matched_frozen_accuracy": 0.25933609958506226,
        "wheat_adapter_matched_adapted_accuracy": 0.5622406639004149,
    }
    for key, value in expected_evidence.items():
        assert report["frozen_evidence"][key] == value
    assert report["frozen_evidence"]["wheat_adapter_supplementary_table"] == "supplementary_tables/submission_v4/Supplementary_Table_S20_GSE270342_wheat_root_adapter_audit.tsv"
    assert len(report["figures"]["main"]) == 5
    assert len(report["figures"]["extended_data"]) == 6
    assert report["visual_contract"]["vector_font_floor_pt"] == 5.0
    for group in ("main", "extended_data"):
        for figure in report["figures"][group]:
            assert figure["minimum_svg_font_size_pt"] >= 5.0
