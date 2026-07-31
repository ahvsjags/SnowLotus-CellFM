from __future__ import annotations

from pathlib import Path

from snowcell.config import DataConfig
from snowcell.data import load_matrix, make_demo_data, prepare_inference_data
from snowcell.vocab import LabelVocabulary, Vocabulary


def test_frozen_inference_filters_genes_absent_from_checkpoint_vocab(tmp_path: Path) -> None:
    data_path = tmp_path / "demo.npz"
    make_demo_data(data_path, n_cells=48, n_genes=96, n_samples=6, seed=7)
    config = DataConfig(path=str(data_path), min_genes_per_cell=5, min_cells_per_gene=2)
    matrix = load_matrix(data_path, config)
    gene_vocab = Vocabulary.build(matrix.genes[:12])
    species_vocab = LabelVocabulary.build(matrix.obs["species"])
    tissue_vocab = LabelVocabulary.build(matrix.obs["tissue"])

    prepared = prepare_inference_data(config, gene_vocab, species_vocab, tissue_vocab)

    assert prepared.matrix.n_genes == 12
    assert prepared.preprocessing_stats["checkpoint_vocabulary"] == {
        "source_gene_count": 96,
        "represented_gene_count": 12,
        "represented_gene_fraction": 0.125,
        "unrepresented_gene_count": 84,
    }
