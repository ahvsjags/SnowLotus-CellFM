import torch

from snowcell.artifacts import model_from_checkpoint
from snowcell.config import ExperimentConfig
from snowcell.model import ModelConfig, SnowCellModel
from snowcell.train import _copy_named_rows, hard_negative_margin_loss, supervised_contrastive_loss


def test_supervised_contrastive_loss_is_finite_and_uses_same_label_pairs() -> None:
    embeddings = torch.tensor(
        [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.9, 0.1],
        ]
    )
    labels = torch.tensor([0, 0, 1, 1])
    loss = supervised_contrastive_loss(embeddings, labels, temperature=0.1)
    assert torch.isfinite(loss)
    assert float(loss) > 0.0


def test_contrastive_loss_returns_zero_without_positive_pairs() -> None:
    embeddings = torch.randn(4, 8)
    labels = torch.tensor([0, 1, 2, 3])
    loss = supervised_contrastive_loss(embeddings, labels)
    assert float(loss) == 0.0


def test_hard_negative_loss_is_finite_for_same_coarse_different_fine_states() -> None:
    embeddings = torch.tensor(
        [
            [1.0, 0.0, 0.0],
            [0.95, 0.05, 0.0],
            [0.80, 0.20, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    fine_labels = torch.tensor([0, 0, 1, 2])
    coarse_labels = torch.tensor([0, 0, 0, 1])
    loss = hard_negative_margin_loss(embeddings, fine_labels, coarse_labels)
    assert torch.isfinite(loss)
    assert float(loss) >= 0.0


def test_revision_config_enables_contrastive_objective() -> None:
    config = ExperimentConfig.load("configs/revision_v19_cross_species_contrastive_4090.yaml")
    assert config.train.contrastive_loss_weight == 0.30
    assert config.train.hard_negative_loss_weight == 0.15
    assert config.train.species_balance is True
    assert config.architecture.contrastive_dim == 128


def test_old_checkpoint_without_contrastive_projection_remains_loadable() -> None:
    config = ModelConfig(
        vocab_size=16,
        num_fine_classes=3,
        num_coarse_classes=2,
        num_species=1,
        num_tissues=1,
        d_model=16,
        n_layers=1,
        n_heads=4,
        ffn_dim=32,
        value_bins=8,
        contrastive_dim=8,
    )
    model = SnowCellModel(config)
    legacy_state = {
        key: value
        for key, value in model.state_dict().items()
        if not key.startswith("contrastive_projection.")
    }
    loaded = model_from_checkpoint(
        {"model_config": config.to_dict(), "model_state": legacy_state},
        device="cpu",
    )
    assert loaded.training is False


def test_vocab_row_transfer_is_name_aligned_when_order_changes() -> None:
    target = torch.zeros(2, 1)
    source = torch.tensor([[10.0], [20.0]])
    adapted, copied = _copy_named_rows(target, source, ["b", "a"], ["a", "b"])
    assert copied == 2
    assert adapted is not None
    assert adapted[:, 0].tolist() == [20.0, 10.0]


def test_marker_prior_changes_fine_logits_only_when_contract_dimensions_match() -> None:
    config = ModelConfig(
        vocab_size=16,
        num_fine_classes=3,
        num_coarse_classes=2,
        num_species=1,
        num_tissues=1,
        d_model=16,
        n_layers=1,
        n_heads=4,
        ffn_dim=32,
        value_bins=8,
        contrastive_dim=8,
        marker_prior_weight=0.5,
    )
    model = SnowCellModel(config).eval()
    inputs = {
        "gene_ids": torch.tensor([[1, 4, 5, 0], [1, 6, 7, 0]]),
        "values": torch.ones(2, 4),
        "padding_mask": torch.tensor([[False, False, False, True], [False, False, False, True]]),
        "species_id": torch.zeros(2, dtype=torch.long),
        "tissue_id": torch.zeros(2, dtype=torch.long),
    }
    with torch.no_grad():
        baseline = model(**inputs, marker_scores=torch.zeros(2, 3))["fine_logits"]
        adjusted = model(**inputs, marker_scores=torch.tensor([[5.0, 0.0, 0.0], [0.0, 4.0, 0.0]]))["fine_logits"]
    assert not torch.allclose(baseline, adjusted)
