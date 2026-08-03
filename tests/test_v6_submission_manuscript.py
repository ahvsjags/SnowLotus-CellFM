from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v7_manuscript_keeps_primary_and_sensitivity_protocols_distinct() -> None:
    manuscript = (ROOT / "manuscript" / "Plant_CellFM_v7_submission_evidence_manuscript.md").read_text(encoding="utf-8")

    assert "39.96% over all 3,964 test cells" in manuscript
    assert "42.36% all-cell accuracy" in manuscript
    assert "not a replacement for the nested v17 primary result" in manuscript
    assert "not zero-shot or independent validation" in manuscript


def test_v7_manuscript_states_the_replayed_scplantllm_and_sorghum_boundaries() -> None:
    manuscript = (ROOT / "manuscript" / "Plant_CellFM_v7_submission_evidence_manuscript.md").read_text(encoding="utf-8")

    assert "0.2107 accuracy and 0.2001 macro-F1" in manuscript
    assert "0.3426 accuracy and 0.2998 macro-F1" in manuscript
    assert "first five transformer blocks" in manuscript
    assert "Separate replay audits" in manuscript
    assert "same-study adaptation comparison, not independent validation" in manuscript
    assert "Extended Data Figure 8" in manuscript
    assert "14.56% accuracy and 0.1083 macro-F1" in manuscript
    assert "76.02% 27-state accuracy and 0.7535 macro-F1" in manuscript
    assert "not a zero-shot or third-party ranking" in manuscript


def test_v7_convergence_plan_cannot_be_read_as_an_acceptance_claim() -> None:
    plan = (ROOT / "release_metadata" / "plant_cellfm_top_journal_convergence_plan_v1.md").read_text(encoding="utf-8")

    assert "does not assert editorial acceptance" in plan
    assert "39.96%" in plan
    assert "compute-budget-matched third-party benchmark" in plan.lower()
    assert "required for a stronger revision rather than claimed complete" in plan


def test_readme_exposes_the_current_plant_methods_entry_points() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Current Plant Methods v1 Submission Package" in readme
    assert "Plant_CellFM_Plant_Methods_manuscript_v1.md" in readme
    assert "Plant_CellFM_Plant_Methods_manuscript_v1.docx" in readme
    assert "Plant_CellFM_Plant_Methods_submission_v1.zip" in readme
    assert "figures/plant_cellfm_submission_v12" in readme
    assert "render_v12_system_figure.py" in readme
    assert "audit_v12_main_figure_suite.py" in readme
    assert "build_plant_methods_submission_docs.js" in readme


def test_v7_word_builder_targets_the_current_evidence_manuscript_and_figures() -> None:
    builder = (ROOT / "scripts" / "build_v6_english_manuscript_docx.js").read_text(encoding="utf-8")
    v7_builder = (ROOT / "scripts" / "build_v7_english_manuscript_docx.js").read_text(encoding="utf-8")

    assert "PLANT_CELLFM_EDITION" in builder
    assert "Plant_CellFM_${edition}_submission_evidence_manuscript.md" in builder
    assert "Plant_CellFM_${edition}_submission_evidence_manuscript.docx" in builder
    assert "plant_cellfm_submission_${edition}" in builder
    assert "plant_cellfm_v6_ed_fig8_scplantllm_matched_reference" in builder
    assert "PLANT_CELLFM_EDITION: \"v7\"" in v7_builder
