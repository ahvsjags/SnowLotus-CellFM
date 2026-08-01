from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from prepare_gse297576_bicolor_root_external import coordinate_names, sparse_counts


class MiniLogMap:
    def __init__(self, names: list[str]) -> None:
        self.dims = ("dim_0", "dim_1")
        self.coords = {"dim_0": SimpleNamespace(values=np.asarray(names, dtype=str))}


def test_sparse_counts_requires_exact_author_cell_order_and_preserves_raw_shape() -> None:
    metadata = pd.DataFrame({"cellBC": ["c1", "c2"], "celltype": ["cortex", "xylem"]})
    counts = SimpleNamespace(
        i=np.asarray([0, 1, 0], dtype=np.int32),
        p=np.asarray([0, 2, 3], dtype=np.int32),
        Dim=np.asarray([2, 2], dtype=np.int32),
        x=np.asarray([1, 2, 3], dtype=np.int32),
    )
    rna = SimpleNamespace(layers={"counts": counts}, cells=MiniLogMap(["c1", "c2"]), features=MiniLogMap(["g1", "g2"]))
    object_ = SimpleNamespace(**{"meta.data": metadata, "assays": {"RNA": rna}})
    matrix, observed_metadata, genes = sparse_counts(object_)
    assert matrix.shape == (2, 2)
    assert matrix.toarray().tolist() == [[1, 2], [3, 0]]
    assert observed_metadata["celltype"].tolist() == ["cortex", "xylem"]
    assert genes.tolist() == ["g1", "g2"]


def test_coordinate_names_rejects_duplicate_identifiers() -> None:
    try:
        coordinate_names(MiniLogMap(["c1", "c1"]))
    except ValueError as error:
        assert "unique" in str(error)
    else:
        raise AssertionError("Duplicate cell identifiers must fail the external contract.")
