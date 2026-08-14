from __future__ import annotations

import json

import numpy as np
from scipy import sparse

from snowcell.config import DataConfig
from snowcell.data import ExpressionDataset, preprocess_matrix
from snowcell.ontology import canonicalize_label, load_source_only_contract, marker_prior_scores
from snowcell.vocab import LabelVocabulary, Vocabulary


CONTRACT = "release_metadata/source_only/plant_cell_state_contract_v19.json"


def test_source_only_contract_has_no_benchmark_payload() -> None:
    payload = json.loads(open(CONTRACT, encoding="utf-8").read())
    assert payload["provenance"] == "source_only_curated"
    forbidden = {"target_labels", "held_out_labels", "test_cells", "cell_counts", "benchmark_counts"}
    assert forbidden.isdisjoint(payload)
    assert len(payload["states"]) >= 15


def test_aliases_collapse_to_fixed_canonical_states() -> None:
    contract = load_source_only_contract(CONTRACT)
    assert canonicalize_label("cortex_2", contract)[0] == "Root cortex"
    assert canonicalize_label("Provascular cells", contract)[0] == "Root stele"
    assert canonicalize_label("Arabidopsis-specific-new-state", contract)[0] == "Arabidopsis-specific-new-state"


def test_preprocess_applies_ontology_without_using_expression_values(tmp_path) -> None:
    path = tmp_path / "source.npz"
    np.savez_compressed(
        path,
        X=np.asarray([[3, 0, 1], [0, 4, 1], [1, 0, 5]], dtype=np.float32),
        genes=np.asarray(["COR", "SCR", "VND6"]),
        cell_type=np.asarray(["cortex_1", "endodermis", "xylem"]),
        cell_type_coarse=np.asarray(["old", "old", "old"]),
        sample_id=np.asarray(["a", "b", "c"]),
        species=np.asarray(["sp1", "sp2", "sp3"]),
        tissue=np.asarray(["root", "root", "root"]),
        cell_id=np.asarray(["c1", "c2", "c3"]),
    )
    config = DataConfig(
        path=str(path),
        min_genes_per_cell=1,
        min_cells_per_gene=1,
        ontology_contract=CONTRACT,
    )
    matrix, stats = preprocess_matrix(config)
    assert matrix.obs["cell_type"].tolist() == ["Root cortex", "Root endodermis", "Xylem"]
    assert matrix.obs["cell_type_coarse"].tolist() == ["ground", "boundary", "vascular"]
    assert stats["source_only_ontology"]["mapped_cells"] == 3
    dataset = ExpressionDataset(
        matrix,
        np.arange(matrix.n_cells),
        config,
        Vocabulary.build(matrix.genes),
        fine_vocab=LabelVocabulary.build(matrix.obs["cell_type"]),
        coarse_vocab=LabelVocabulary.build(matrix.obs["cell_type_coarse"]),
    )
    assert dataset[0]["marker_scores"].shape[0] == 3
    assert float(dataset[0]["marker_scores"].max()) > 0.0


def test_marker_prior_is_source_only_and_sparse_aware() -> None:
    contract = load_source_only_contract(CONTRACT)
    scores, stats = marker_prior_scores(
        sparse.csr_matrix(np.asarray([[5, 0, 0], [0, 4, 0]], dtype=np.float32)),
        np.asarray(["COR", "SCR", "unused"]),
        contract,
    )
    assert scores.shape == (2, len(contract["states"]))
    assert stats["states_with_observed_markers"] >= 2
    assert float(scores.max()) > 0.0
