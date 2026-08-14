from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from evaluate_revision_v19_strict_replay import _metrics  # noqa: E402


def test_v19_metrics_include_bootstrap_for_coverage_and_macro_f1() -> None:
    frame = pd.DataFrame(
        {
            "reference_label": ["Xylem", "Xylem", "Phloem", "Unknown"],
            "predicted_label": ["Xylem", "Phloem", "Phloem", "Xylem"],
        }
    )
    metrics = _metrics(
        frame,
        {"Xylem", "Phloem", "Unknown"},
        bootstrap_seed=7,
        bootstrap_replicates=25,
    )
    assert metrics["n_test"] == 4
    assert len(metrics["coverage_ci95"]) == 2
    assert len(metrics["macro_f1_all_ci95"]) == 2
    assert len(metrics["covered_label_macro_f1_ci95"]) == 2
    assert len(metrics["actionable_macro_f1_ci95"]) == 2
