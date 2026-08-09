from __future__ import annotations

import pandas as pd

from snowcell.agent_evidence import (
    align_reference,
    calibration_curve,
    sample_expert_audit,
    score_reference_backed_audit,
    selective_curve,
)


def _aligned() -> pd.DataFrame:
    predictions = pd.DataFrame(
        {
            "cell_id": ["c1", "c2", "c3", "c4"],
            "fine_label": ["x", "x", "y", "unknown"],
            "fine_confidence": [0.95, 0.75, 0.45, 0.9],
        }
    )
    reference = pd.DataFrame({"cell_id": ["c1", "c2", "c3", "c4"], "label": ["x", "x", "z", "z"]})
    return align_reference(predictions, reference, "label")


def test_selective_curve_separates_accept_all_and_agent_review() -> None:
    curve = selective_curve(_aligned(), thresholds=(0.7,), case_id="demo")
    baseline = curve[curve["policy"] == "accept_all_baseline"].iloc[0]
    agent = curve[curve["policy"] == "agent_threshold"].iloc[0]
    assert baseline["coverage"] == 1.0
    assert agent["coverage"] == 0.5
    assert agent["accepted_accuracy"] == 1.0
    assert agent["review_risk"] > agent["accepted_risk"]


def test_calibration_curve_returns_ece() -> None:
    curve, summary = calibration_curve(_aligned(), bins=5, case_id="demo")
    assert len(curve) == 5
    assert 0.0 <= summary["expected_calibration_error"] <= 1.0


def test_reference_backed_audit_and_blinded_sample() -> None:
    aligned = _aligned()
    summary = score_reference_backed_audit(aligned, "demo", threshold=0.7)
    assert summary["review_error_rate_minus_accepted_error_rate"] > 0
    public, key = sample_expert_audit(aligned, "demo", threshold=0.7, per_group=1, seed=1)
    assert len(public) == len(key) == 2
    assert "reference_label" not in public.columns
    assert "hidden_group" not in public.columns
