from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v6_contract_preserves_the_main_evidence_boundaries() -> None:
    contract = (ROOT / "release_metadata" / "plant_cellfm_v6_top_journal_figure_contract.md").read_text(encoding="utf-8")
    assert "39.96% all-cell accuracy" in contract
    assert "not the nested primary result" in contract
    assert "no external expert annotation" in contract
    assert "not independent external validation" in contract
    assert "zero-target-label transfer results" in contract
    assert "frozen and partial-adaptation" in contract
    assert "not a full-backbone or compute-matched ranking" in contract


def test_v6_renderer_uses_only_the_frozen_evidence_records() -> None:
    renderer = (ROOT / "scripts" / "render_v6_editorial_core_figures.py").read_text(encoding="utf-8")
    assert "revision_v17_nested_metadata_gate.json" in renderer
    assert "algorithm_innovation_v14.json" in renderer
    assert "v9_lora_vs_v3_shared_comparison.json" in renderer
    assert "historical_matched_v3_to_v9" in renderer
    assert "Sensitivity only; not nested v17" in renderer
    assert "render_fig4_external_root" in renderer
    assert "render_fig5_wheat_adapter" in renderer
    assert "not a universal transfer result" in renderer
