from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_v6_submission_figure_suite as audit


def test_v6_audit_keeps_export_and_evidence_boundaries_separate() -> None:
    report = audit.audit()
    assert report["state"] == "TECHNICALLY_READY_PENDING_EVIDENCE_COMPLETION"
    assert not report["technical_failures"]
    assert len(report["figures"]["main"]) == 5
    assert len(report["figures"]["extended_data"]) == 2
    assert report["frozen_evidence"]["zero_target_source_adapter_k9_macro_f1"] < report["frozen_evidence"]["zero_target_frozen_k9_macro_f1"]
    assert report["frozen_evidence"]["scplantllm_frozen_reference_accuracy"] == 0.2107466852756455
    assert report["frozen_evidence"]["scplantllm_partial_reference_accuracy"] == 0.34263782274947663
    assert report["frozen_evidence"]["scplantllm_partial_best_validation_epoch"] == 4
