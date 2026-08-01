from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_gse297576_sorghum_root_adapter import broad_score


def test_broad_score_counts_predictions_to_noncomparable_states_as_errors() -> None:
    ontology = {
        "labels": {
            "cortex": {"model_label": "Root cortex", "status": "evaluable"},
            "meristem": {"model_label": None, "status": "non_comparable"},
        }
    }
    score = broad_score(
        pd.Series(["cortex", "cortex", "meristem"]),
        pd.Series(["cortex", "meristem", "cortex"]),
        ontology,
    )
    assert score["cells"] == 2
    assert score["accuracy"] == 0.5
    assert score["macro_f1"] == 2 / 3
