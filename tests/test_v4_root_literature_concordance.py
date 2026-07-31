from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_v4_root_literature_concordance import build_concordance


def test_root_literature_anchor_lookup_is_complete_and_claim_safe() -> None:
    table, payload = build_concordance()

    assert payload["summary"]["anchors_tested"] == 6
    assert payload["summary"]["matching_program_hits"] == 3
    assert payload["summary"]["recovered_marker_symbols"] == ["CASP1", "APL", "MYB46"]
    assert set(table.loc[table.recovered_in_matching_program, "candidate_rank"]) == {4, 7, 12}
    assert "wet-lab validation" in payload["claim_boundary"]
