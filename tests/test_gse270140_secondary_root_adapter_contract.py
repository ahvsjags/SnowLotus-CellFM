from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_secondary_root_adapter_audit_declares_its_non_zero_shot_boundary() -> None:
    source = (ROOT / "scripts" / "audit_gse270140_secondary_root_adapter.py").read_text(encoding="utf-8")
    assert "not a zero-shot result" in source
    assert "not an independent external validation" in source
    assert "matched_three_state_semantic_recovery" in source
    assert "test_cells\": 2352" in source
    assert "RELEASED_CHECKPOINT" in source
    assert "does not match the audited training checkpoint" in source
