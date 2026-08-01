from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v7_figure_renderer_and_audit_cover_the_same_source_data_contract() -> None:
    renderer = (ROOT / "scripts" / "render_v7_sorghum_external_adaptation_figure.py").read_text(encoding="utf-8")
    audit = (ROOT / "scripts" / "audit_v7_sorghum_external_figure.py").read_text(encoding="utf-8")
    for source_name in (
        "matched_recovery_bootstrap",
        "matched_recovery_metrics",
        "sealed_test_predictions_and_umap",
        "sealed_test_per_class",
        "feature_transfer_audit",
        "evidence_provenance",
        "claim_boundary",
    ):
        assert source_name in renderer
        assert source_name in audit
