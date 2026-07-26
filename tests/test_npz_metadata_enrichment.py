from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


def _load_module():
    path = Path(__file__).parents[1] / "scripts" / "enrich_npz_metadata.py"
    spec = importlib.util.spec_from_file_location("enrich_npz_metadata", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_enrich_npz_adds_sample_fields(tmp_path: Path) -> None:
    source = tmp_path / "source.npz"
    output = tmp_path / "output.npz"
    metadata = tmp_path / "metadata.tsv"
    np.savez_compressed(
        source,
        X_data=np.asarray([1.0], dtype=np.float32),
        X_indices=np.asarray([0], dtype=np.int32),
        X_indptr=np.asarray([0, 1, 1], dtype=np.int32),
        X_shape=np.asarray([2, 1], dtype=np.int64),
        genes=np.asarray(["gene_a"]),
        sample_id=np.asarray(["s1", "s1"]),
    )
    metadata.write_text("sample_id\tcultivar\n s1\tNip\n".replace(" s1", "s1"), encoding="utf-8")
    module = _load_module()
    module.enrich_npz(source, metadata, output)
    with np.load(output, allow_pickle=False) as loaded:
        assert loaded["cultivar"].tolist() == ["Nip", "Nip"]
        assert loaded["genes"].tolist() == ["gene_a"]
