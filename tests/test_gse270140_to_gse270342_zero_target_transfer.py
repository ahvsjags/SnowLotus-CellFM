from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_gse270140_to_gse270342_zero_target_transfer as audit


def test_transfer_state_maps_are_disjoint_and_cover_the_declared_primary_states() -> None:
    source_reverse = audit._reverse_map(audit.SOURCE_STATES)
    assert set(source_reverse.values()) == {"phloem", "stele", "xylem"}
    assert audit.TARGET_PRIMARY_STATES == {"Phloem": "phloem", "Xylem": "xylem", "Provascular cells": "stele"}
    assert audit.TARGET_PERICYCLE_SENSITIVITY_STATES["Pericycle"] == "stele"


def test_l2_normalize_keeps_rows_unit_length() -> None:
    normalized = audit.l2_normalize(np.asarray([[3.0, 4.0], [0.0, 5.0]]))
    assert np.allclose(np.linalg.norm(normalized, axis=1), 1.0)


def test_metric_record_exposes_the_complete_three_state_confusion_matrix() -> None:
    record = audit._metric_record(
        np.asarray(["phloem", "stele", "xylem"], dtype=object),
        np.asarray(["phloem", "xylem", "xylem"], dtype=object),
    )
    assert record["class_counts"] == {"phloem": 1, "stele": 1, "xylem": 1}
    assert record["confusion_matrix_rows_true_columns_predicted"] == [[1, 0, 0], [0, 0, 1], [0, 0, 1]]
