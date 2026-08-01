from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v6_extended_renderer_keeps_negative_and_partial_comparator_boundaries() -> None:
    renderer = (ROOT / "scripts" / "render_v6_extended_evidence_figures.py").read_text(encoding="utf-8")
    assert "gse270140_to_gse270342_zero_target_transfer_audit_v1.json" in renderer
    assert "scplantllm_gse270342_matched_embedding_probe_v1.json" in renderer
    assert "scplantllm_gse270342_partial_finetune_v1.json" in renderer
    assert "not a universal ranking" in renderer
    assert "Partial adaptation leaves the first five transformer blocks frozen" in renderer
    assert "Source adaptation does not improve zero-target macro-F1" in renderer
