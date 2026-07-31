from __future__ import annotations

from pathlib import Path

from snowcell.config import ExperimentConfig


ROOT = Path(__file__).resolve().parents[1]


def test_secondary_root_adapter_is_a_labelled_lora_protocol() -> None:
    config = ExperimentConfig.load(ROOT / "configs" / "gse270140_secondary_root_lora_adapter_4070.yaml")
    assert config.data.label_key == "expert_annotation_raw"
    assert config.data.group_key == "cell_id"
    assert config.data.test_fraction == 0.20
    assert config.architecture.lora_rank == 8
    assert config.train.tuning_mode == "lora"
    assert config.train.stage == "supervised"
    assert config.train.init_checkpoint == "models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt"
