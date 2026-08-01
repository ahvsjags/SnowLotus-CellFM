from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_full_backbone_finetune_audit_requires_exact_replay_and_clean_load() -> None:
    source = (ROOT / "scripts" / "audit_scplantllm_gse270342_full_finetune.py").read_text(encoding="utf-8")

    assert "COMPLETED_MATCHED_FULL_BACKBONE_ADAPTATION" in source
    assert "full_finetune_checkpoint_sha256" in source
    assert "configure_full_backbone_adaptation" in source
    assert "restore_full_model" in source
    assert "exact_prediction_match" in source
    assert "metric_match" in source
    assert "REPLAY_CONFIRMED" in source
