from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_gse270140_mapping_is_complete_frozen_and_separates_uncovered_states() -> None:
    mapping = pd.read_csv(
        ROOT / "release_metadata" / "gse270140_external_label_mapping_v1.tsv",
        sep="\t",
        dtype=str,
    ).fillna("")
    assert len(mapping) == 14
    assert mapping["source_label"].is_unique
    assert set(mapping["mapping_frozen_before_inference"]) == {"true"}
    assert set(mapping["evaluation_tier"]) == {"shared_state", "no_direct_model_state"}
    assert set(mapping.loc[mapping["evaluation_tier"] == "shared_state", "mapped_model_label"]) == {
        "Phloem",
        "Root stele",
        "Xylem",
    }
    assert set(mapping.loc[mapping["evaluation_tier"] == "no_direct_model_state", "mapped_model_label"]) == {""}
