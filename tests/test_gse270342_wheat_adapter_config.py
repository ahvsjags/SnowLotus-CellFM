from __future__ import annotations

from pathlib import Path

from snowcell.config import ExperimentConfig


def test_gse270342_wheat_adapter_is_explicitly_orthology_aware() -> None:
    root = Path(__file__).resolve().parents[1]
    config = ExperimentConfig.load(root / "configs" / "gse270342_wheat_root_lora_adapter_4070.yaml")

    assert config.data.ortholog_map == "data/orthologs/gse270342_wheat_to_arabidopsis_author_orthogroups.tsv"
    assert config.data.ortholog_aggregation == "first"
    assert config.data.ortholog_keep_unmapped is False
    assert config.data.label_key == "expert_annotation_raw"
    assert config.train.tuning_mode == "lora"
    assert config.train.init_checkpoint == "models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt"
