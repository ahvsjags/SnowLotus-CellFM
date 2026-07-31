from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from scipy import sparse
from scipy.io import mmwrite


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from prepare_gse270140_external_validation import build_anndata, canonical_tair_gene_id


def test_canonical_tair_gene_id_keeps_unmapped_features() -> None:
    assert canonical_tair_gene_id("AT1G01010-NAC001") == "AT1G01010"
    assert canonical_tair_gene_id("NewGene-Venus") == "NewGene-Venus"


def test_build_anndata_preserves_rds_cell_order_and_annotations(tmp_path: Path) -> None:
    mmwrite(tmp_path / "matrix_cells_by_genes.mtx", sparse.csr_matrix([[1, 0], [0, 2]]))
    (tmp_path / "genes.txt").write_text("AT1G01010-NAC001\nAT2G02020-XYZ\n", encoding="utf-8")
    (tmp_path / "cells.txt").write_text("cell_a\ncell_b\n", encoding="utf-8")
    pd.DataFrame(
        {
            "cell_id": ["cell_a", "cell_b"],
            "annotation": ["Mature xylem parenchyma", "Periderm"],
            "orig.ident": ["JWE3", "JWE3"],
            "seurat_clusters": ["1", "2"],
        }
    ).to_csv(tmp_path / "metadata.csv", index=False)

    adata = build_anndata(tmp_path)

    assert adata.shape == (2, 2)
    assert adata.obs_names.tolist() == ["cell_a", "cell_b"]
    assert adata.obs["expert_annotation_raw"].tolist() == ["Mature xylem parenchyma", "Periderm"]
    assert adata.var_names.tolist() == ["AT1G01010", "AT2G02020"]
    assert adata.obs["Organ"].unique().tolist() == ["Root"]
    assert adata.obs["Tissue"].unique().tolist() == ["Whole root"]
