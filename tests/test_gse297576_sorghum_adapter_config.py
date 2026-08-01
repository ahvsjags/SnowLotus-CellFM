from __future__ import annotations

from pathlib import Path

from snowcell.config import ExperimentConfig
from snowcell.data import prepare_data


ROOT = Path(__file__).resolve().parents[1]


def test_sorghum_adapter_uses_disjoint_library_level_splits() -> None:
    config = ExperimentConfig.load(ROOT / "configs" / "gse297576_sorghum_root_lora_adapter_4070.yaml")
    prepared = prepare_data(config.data, config.train.seed, require_labels=True)
    split = prepared.preprocessing_stats["split"]
    assert split["strategy"] == "explicit_leaveout"
    assert split["test_leaveout_values"] == ["OUGHW"]
    assert split["validation_leaveout_values"] == ["OWGSB"]
    assert set(split["train_leaveout_values"]).isdisjoint(split["test_leaveout_values"])
    assert set(split["train_leaveout_values"]).isdisjoint(split["validation_leaveout_values"])
    assert split["test_cells"] == 4150
    assert split["validation_cells"] == 1546
