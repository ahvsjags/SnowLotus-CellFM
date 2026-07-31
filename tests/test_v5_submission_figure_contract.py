from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v5_blueprint_exposes_primary_claim_boundaries() -> None:
    blueprint = (ROOT / "release_metadata" / "plant_cellfm_v5_figure_blueprint.md").read_text(encoding="utf-8")
    assert "39.96% is the all-cell v17 result" in blueprint
    assert "This is labelled adaptation, not zero-shot transfer" in blueprint
    assert "no external accuracy, external ranking or wet-lab validation is claimed" in blueprint


def test_v5_figure_audit_preserves_exports_and_frozen_evidence() -> None:
    report = json.loads((ROOT / "release_metadata" / "top_journal_figure_audit_v5.json").read_text(encoding="utf-8"))
    assert report["state"] == "TECHNICALLY_READY_PENDING_EDITORIAL_AND_EVIDENCE_REVIEW"
    assert report["technical_failures"] == []
    assert report["frozen_evidence"] == {
        "v17_all_cell_accuracy": 0.39959636730575177,
        "external_root_input_cells": 6566,
        "external_root_label_free": True,
        "external_root_top_mean_marker_hits": 5,
        "root_candidate_rows": 200,
    }
    assert len(report["figures"]["main"]) == 4
    assert len(report["figures"]["extended_data"]) == 5
