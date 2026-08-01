from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v6_manuscript_keeps_primary_and_sensitivity_protocols_distinct() -> None:
    manuscript = (ROOT / "manuscript" / "Plant_CellFM_v6_submission_evidence_manuscript.md").read_text(encoding="utf-8")

    assert "39.96% over all 3,964 test cells" in manuscript
    assert "42.36% all-cell accuracy" in manuscript
    assert "not a replacement for the nested v17 primary result" in manuscript
    assert "not zero-shot or independent validation" in manuscript


def test_v6_manuscript_states_the_replayed_partial_scplantllm_boundary() -> None:
    manuscript = (ROOT / "manuscript" / "Plant_CellFM_v6_submission_evidence_manuscript.md").read_text(encoding="utf-8")

    assert "0.2107 accuracy and 0.2001 macro-F1" in manuscript
    assert "0.3426 accuracy and 0.2998 macro-F1" in manuscript
    assert "first five transformer blocks" in manuscript
    assert "separate replay audit" in manuscript
    assert "neither full-backbone scPlantLLM fine-tuning nor a universal model ranking" in manuscript
    assert "Extended Data Figure 8" in manuscript


def test_v6_convergence_plan_cannot_be_read_as_an_acceptance_claim() -> None:
    plan = (ROOT / "release_metadata" / "plant_cellfm_top_journal_convergence_plan_v1.md").read_text(encoding="utf-8")

    assert "does not assert editorial acceptance" in plan
    assert "39.96%" in plan
    assert "full-backbone or compute-budget-matched third-party benchmark" in plan.lower()
    assert "required for a stronger revision rather than claimed complete" in plan


def test_readme_exposes_the_current_v6_entry_points() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Current v6 Evidence-First Submission Package" in readme
    assert "Plant_CellFM_v6_submission_evidence_manuscript.md" in readme
    assert "Plant_CellFM_v6_submission_evidence_manuscript.docx" in readme
    assert "Plant_CellFM_v6_submission_evidence_manuscript.pdf" in readme
    assert "render_v6_editorial_core_figures.py" in readme
    assert "render_v6_extended_evidence_figures.py" in readme
    assert "audit_v6_submission_figure_suite.py" in readme


def test_v6_word_builder_targets_the_current_evidence_manuscript_and_figures() -> None:
    builder = (ROOT / "scripts" / "build_v6_english_manuscript_docx.js").read_text(encoding="utf-8")

    assert "Plant_CellFM_v6_submission_evidence_manuscript.md" in builder
    assert "Plant_CellFM_v6_submission_evidence_manuscript.docx" in builder
    assert "plant_cellfm_submission_v6" in builder
    assert "plant_cellfm_v6_ed_fig8_scplantllm_matched_reference" in builder
