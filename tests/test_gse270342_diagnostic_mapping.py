from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_gse270342_wheat_nonoverlap_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("gse270342_diagnostic", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_direct_map_score_excludes_ambiguous_author_states() -> None:
    frame = pd.DataFrame(
        {
            "expert_annotation_raw": ["Cortex", "Cortex", "Meristems", "Root Hair"],
            "fine_label": ["Root cortex", "Unknow", "S phase", "Root hair"],
            "fine_confidence": [0.9, 0.8, 0.7, 0.6],
        }
    )
    summary, per_class, confusion = MODULE.score_mapping(frame, {"Cortex": "Root cortex", "Root Hair": "Root hair"})

    assert summary["evaluated_cells"] == 3
    assert summary["coverage_of_nonoverlap_input"] == 0.75
    assert summary["accuracy"] == 2 / 3
    assert set(per_class["model_label"]) == {"Root cortex", "Root hair"}
    assert confusion.loc["Root cortex", "Root cortex"] == 1
