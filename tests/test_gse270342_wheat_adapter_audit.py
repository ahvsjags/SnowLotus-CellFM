from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_gse270342_wheat_lora_adapter.py"
SPEC = importlib.util.spec_from_file_location("gse270342_wheat_adapter_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_matched_direct_score_only_uses_declared_anatomical_labels() -> None:
    frame = pd.DataFrame(
        {
            "true_fine": ["Cortex", "Root Hair", "Meristems"],
            "pred_fine": ["Cortex", "Epidermis", "Meristems"],
            "frozen_fine_label": ["Root cortex", "Root hair", "S phase"],
        }
    )
    summary, selected = MODULE.score_matched_direct(frame)

    assert summary["evaluated_cells"] == 2
    assert summary["frozen_first_projection_accuracy"] == 1.0
    assert summary["adapted_lora_accuracy"] == 0.5
    assert selected["expected_root_label"].tolist() == ["Root cortex", "Root hair"]


def test_wheat_adapter_release_path_is_a_versioned_model_asset() -> None:
    assert MODULE.DEFAULT_RELEASED_CHECKPOINT.relative_to(MODULE.ROOT).as_posix() == (
        "models/Plant_CellFM_GSE270342_wheat_root_lora_adapter_best.pt"
    )
