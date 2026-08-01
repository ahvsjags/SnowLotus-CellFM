from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_gse297576_sorghum_arabidopsis_ortholog_map import build_map


def test_build_map_retains_all_author_relations_in_deterministic_order() -> None:
    orthogroups = pd.DataFrame(
        {
            "species": [
                "Sorghum_bicolor_RTx430",
                "Sorghum_bicolor_RTx430",
                "Arabidopsis_thaliana_Col-0",
                "Arabidopsis_thaliana_Col-0",
                "Oryza_sativa_Nipponbare",
            ],
            "orthogroup": ["OG2", "OG1", "OG2", "OG2", "OG1"],
            "gene": ["SBI2", "SBI1", "AT2", "AT1", "OS1"],
        }
    )
    mapping, coverage = build_map(pd.Index(["SBI2", "SBI1", "SBI0"]), orthogroups)
    assert mapping[["source_gene", "target_gene"]].values.tolist() == [["SBI2", "AT1"], ["SBI2", "AT2"]]
    assert coverage == {
        "source_gene_count": 3,
        "source_genes_in_author_orthogroups": 2,
        "source_genes_with_arabidopsis_target": 1,
        "mapping_relationship_count": 2,
        "arabidopsis_target_gene_count": 2,
    }


def test_build_map_rejects_an_empty_observed_mapping() -> None:
    orthogroups = pd.DataFrame(
        {
            "species": ["Sorghum_bicolor_RTx430", "Arabidopsis_thaliana_Col-0"],
            "orthogroup": ["OG1", "OG2"],
            "gene": ["SBI1", "AT1"],
        }
    )
    try:
        build_map(pd.Index(["SBI1"]), orthogroups)
    except ValueError as error:
        assert "No observed Sorghum" in str(error)
    else:
        raise AssertionError("A zero-coverage map must fail before inference.")
