# Plant-CellFM / SnowLotus-CellFM

Plant-CellFM is the general-plant branch of SnowLotus-CellFM for plant single-cell and single-nucleus expression annotation. The active release is the Plant Methods v1 submission package with v12 main figures.

## Current Plant Methods v1 Submission Package

The reviewer-facing package frames Plant-CellFM as a coverage-aware plant single-cell annotation method that separates frozen-encoder downstream decoder transfer, source-context routing and target-supervised sparse adaptation. The primary transfer result is 39.96% all-cell accuracy on a 3,964-cell complete denominator with 55.90% source-label coverage and 71.48% covered-label accuracy. The context-gate 42.36% result is retained as a global sensitivity analysis, while wheat and Sorghum results are reported as target-supervised adaptation.

- **Main manuscript**: [`Plant_CellFM_Plant_Methods_manuscript_v1.md`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_manuscript_v1.md) and [`Word version`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_manuscript_v1.docx).
- **Supporting Information**: [`Plant_CellFM_Plant_Methods_supporting_information_v1.md`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_supporting_information_v1.md) and [`Word version`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_supporting_information_v1.docx).
- **Cover letter and QA**: [`cover letter`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_cover_letter_v1.md), [`claim map`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_claim_figure_map_v1.md) and [`QA report`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_QA_report_v1.md).
- **Main figures**: seven upload-ready PDFs in [`submission_files/main_figures`](manuscript/plant_methods_submission_v1/submission_files/main_figures), with editable SVG/PDF/PNG source exports, 600-dpi local TIFF exports and panel-level TSV source data in [`figures/plant_cellfm_submission_v12`](figures/plant_cellfm_submission_v12).
- **Submission zip**: [`Plant_CellFM_Plant_Methods_submission_v1.zip`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_submission_v1.zip), SHA256 `c7240194f5d6be1a1a9827420e6055db640cd60ecbaaab006d49609a140929a8`.
- **Figure policy**: v12 main figures use table-driven quantitative panels and scripted vector schematics; no generative-image assets are included in the active package.

## Build And Audit

Rebuild the active figure suite and Word files with:

```bash
python scripts/render_v12_system_figure.py
python scripts/render_v12_strict_transfer_figure.py
python scripts/render_v12_context_stc_hero.py
python scripts/render_v12_target_adaptation_figure.py
python scripts/render_v12_root_biology_figure.py
python scripts/render_v12_wheat_benchmark_figure.py
python scripts/render_v12_sorghum_recovery_figure.py
python scripts/assemble_v12_main_figure_suite.py
python scripts/audit_v12_main_figure_suite.py
node scripts/build_plant_methods_submission_docs.js
```

The exact upload bundle is:

```text
manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_submission_v1.zip
```

Public repository tag:

```text
plant-methods-submission-v1-20260803
```
