from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_top_journal_figure_suite import find_numbered_ids, has_required_claims


def test_find_numbered_ids_reports_missing_entries() -> None:
    report = find_numbered_ids("Figure 1\nFigure 3\nFigure 3", "Figure", 3)
    assert report["found"] == [1, 3]
    assert report["missing"] == [2]
    assert report["complete"] is False


def test_required_claims_are_case_insensitive() -> None:
    present, missing = has_required_claims("Strict zero-shot 42.36% and scPlantLLM", ["42.36%", "scplantllm", "60.09%"])
    assert present == ["42.36%", "scplantllm"]
    assert missing == ["60.09%"]
