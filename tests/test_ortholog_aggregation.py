from __future__ import annotations

import numpy as np

from snowcell.data import MatrixData, collapse_by_ortholog


def test_mean_ortholog_projection_preserves_expression_and_relationships() -> None:
    matrix = MatrixData(
        X=np.asarray([[10.0, 4.0], [6.0, 8.0]], dtype=np.float32),
        genes=np.asarray(["wheat_a", "wheat_b"], dtype=str),
        obs={},
    )
    collapsed, stats = collapse_by_ortholog(
        matrix,
        {"wheat_a": ("ath_a", "ath_b"), "wheat_b": ("ath_b",)},
        aggregation="mean",
    )

    assert collapsed.genes.tolist() == ["ath_a", "ath_b"]
    assert np.allclose(collapsed.X, [[5.0, 9.0], [3.0, 11.0]])
    assert np.allclose(np.asarray(collapsed.X).sum(axis=1), matrix.X.sum(axis=1))
    assert stats["aggregation"] == "mean"
    assert stats["mapping_relationship_count"] == 3
    assert stats["mean_targets_per_mapped_source"] == 1.5
