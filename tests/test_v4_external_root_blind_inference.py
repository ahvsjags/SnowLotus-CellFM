from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_external_root_blind_inference_record_preserves_its_evidence_boundary() -> None:
    record = json.loads(
        (ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.json").read_text(encoding="utf-8")
    )

    assert record["input_provenance"]["series_accession"] == "GSE152766"
    assert record["input_provenance"]["sample_accession"] == "GSM4626007"
    assert record["input_provenance"]["matrix"]["cells"] == 6566
    assert record["input_provenance"]["input_has_expert_cell_type_labels"] is False
    assert record["input_provenance"]["frozen_v4_corpus_profile_membership"] is False
    assert record["marker_coherence"]["predefined_expectations"] == 6
    assert record["marker_coherence"]["expected_label_is_top_mean_expression"] == 5
    assert "no external accuracy" in record["claim_boundary"].casefold()
    assert {row["marker_symbol"] for row in record["predefined_marker_coherence"]} == {
        "APL",
        "CASP1",
        "COBL9",
        "GL2",
        "MYB46",
        "WER",
    }
