from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_gse297576_bicolor_root_external import evaluate, load_contract


def test_load_contract_requires_an_explicit_decision_for_every_author_label(tmp_path: Path) -> None:
    contract = tmp_path / "contract.json"
    contract.write_text('{"labels": {"cortex": {"status": "evaluable", "model_label": "Root cortex"}}}', encoding="utf-8")
    try:
        load_contract(contract, {"cortex", "xylem"})
    except ValueError as error:
        assert "missing" in str(error)
    else:
        raise AssertionError("Every author label needs an explicit evaluability decision.")


def test_evaluate_keeps_non_comparable_cells_out_of_the_primary_denominator() -> None:
    frame = pd.DataFrame(
        {
            "celltype": ["cortex", "cortex", "meristem"],
            "fine_label": ["Root cortex", "Unknow", "Unknow"],
            "fine_confidence": [0.9, 0.8, 0.99],
        }
    )
    contract = {
        "cortex": {"status": "evaluable", "model_label": "Root cortex"},
        "meristem": {"status": "non_comparable", "model_label": None},
    }
    summary, per_class, _ = evaluate(frame, contract)
    assert summary["input_cells"] == 3
    assert summary["evaluable_cells"] == 2
    assert summary["non_comparable_cells"] == 1
    assert summary["all_evaluable_accuracy"] == 0.5
    assert summary["unassigned_prediction_rate_evaluable"] == 0.5
    assert per_class.loc[0, "support"] == 2
