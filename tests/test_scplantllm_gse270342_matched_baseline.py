from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import sparse


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_scplantllm_gse270342_matched_baseline as baseline


def test_build_sequences_collapses_duplicate_ortholog_targets_and_pads() -> None:
    matrix = sparse.csr_matrix(np.asarray([[3.0, 2.0, 4.0], [0.0, 5.0, 0.0]]))
    gids, values, stats = baseline.build_sequences(
        matrix,
        np.asarray([7, 7, 9]),
        np.asarray([0, 1]),
        sequence_length=6,
        max_tokens=4,
        value_pad=101,
        seed=17,
    )
    assert gids.tolist()[0][:2] == [7, 9]
    assert values.tolist()[0][:2] == [5, 4]
    assert values.tolist()[1][:2] == [5, -2]
    assert stats["cells"] == 2


def test_metric_payload_reports_per_class_support() -> None:
    metrics, per_class = baseline.metric_payload(
        np.asarray(["Cortex", "Cortex", "Xylem"], dtype=object),
        np.asarray(["Cortex", "Xylem", "Xylem"], dtype=object),
    )
    assert metrics["accuracy"] == 2 / 3
    assert set(per_class.author_label) == {"Cortex", "Xylem"}
    assert int(per_class.support.sum()) == 3
