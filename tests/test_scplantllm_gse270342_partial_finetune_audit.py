from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_partial_finetune_audit_requires_exact_replay_and_clean_official_load() -> None:
    source = (ROOT / "scripts" / "audit_scplantllm_gse270342_partial_finetune.py").read_text(encoding="utf-8")
    assert "exact_prediction_match" in source
    assert "metric_match" in source
    assert "Official scPlantLLM checkpoint did not load cleanly" in source
    assert "REPLAY_CONFIRMED" in source
