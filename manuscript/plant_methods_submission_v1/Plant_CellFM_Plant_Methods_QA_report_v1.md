# Plant-CellFM Plant Methods QA Report v1

## Status

**Plant Methods submission package: PASS after four-blocker repair and specialist-agent upgrade.** The scientific text, main figures, source manifests and Word files are now aligned around a coverage-aware cross-species annotation claim with a central Plant-CellFM model and capability-scoped specialist agents. Author names, affiliations and corresponding-author details still need to be entered by the submitting author.

## Four-blocker repair log

| Blocker | Repair | Verification |
| --- | --- | --- |
| Overstated source-only generalization | Reframed the primary result as frozen-encoder leave-species downstream decoder transfer; removed claims that target labels were absent from encoder fitting. | Manuscript and Supporting Information now state that the encoder is fixed and target exclusion applies to downstream decoder fitting, selection, thresholding and calibration. |
| Unsupported-label terminology | Replaced overbroad recognition language with coverage-aware transfer, source-label coverage and unsupported-label accounting. | Final source scan found no residual high-risk terminology in the manuscript, support file, cover letter, claim map, figure manifest or v12 renderer scripts. |
| Generative-image figure policy risk | Replaced Fig. 1, Fig. 3, Fig. 4, Fig. 5, Fig. 6 and Fig. 7 generated raster mechanism layers with scripted vector schematics. Removed retired generated assets from the v12 figure folder and manifest. | `scripts/audit_v12_main_figure_suite.py` reports PASS for seven figures; manifest records `assets: []` and scripted vector schematics. |
| Public reproducibility package | Rebuilt DOCX files, submission PDFs, manifest and zip; recorded the planned public tag and repository. | Zip integrity PASS with 14 entries; new submission SHA256 is `c7240194f5d6be1a1a9827420e6055db640cd60ecbaaab006d49609a140929a8`. |

## Specialist-agent upgrade checks

- Central model and specialist capability manifest: `release_metadata/plantcell_specialist_agents_v1.json`.
- Each real Agent run exports `specialist_capabilities.json`, `specialist_plan.json` and `evidence_verification.json`.
- Specialist output checks cover prediction columns, audited row count, unique cell IDs, confidence bounds, embedding row count and preservation of direct predictions.
- A failed specialist contract forces the Review Agent path and preserves the direct prediction table.
- Arabidopsis end-to-end v0.2 smoke replay passed with registered species specialist `specialist.adapter.plant_arabidopsis_thaliana` and evidence status `passed`.
- Supplementary Fig. S12 now uses the central-model specialist-agent architecture; the final supplementary PDF is `Plant_CellFM_Plant_Methods_supplementary_figures_v4.pdf` with 13 pages.

## Scientific claim checks

- Primary transfer result: 39.96% all-cell accuracy, 55.90% source-label coverage and 71.48% covered-label accuracy on the same 3,964-cell denominator.
- Context gate: 42.36% all-cell accuracy and 75.77% covered-label accuracy, labelled as a global sensitivity analysis rather than the nested primary estimate.
- Sparse target support: query accuracy increases from 59.21% to 75.89% when support rises from 8 to 64 cells per species.
- Wheat benchmark: Plant-CellFM LoRA reaches 62.25% accuracy and 0.6660 macro-F1 on the same 1,433 locked cells used for the scPlantLLM reference.
- Sorghum sealed library: 76.02% fine-state accuracy on 4,150 OUGHW test cells; broad-root recovery increases from 14.79% to 84.98% on matched cells.
- Blind Arabidopsis root evidence is described as marker coherence rather than expert-label accuracy.
- scPlantAnnotate numerical comparison remains omitted because authenticated batch prediction export is unavailable.

## File engineering checks

- Main DOCX rebuilt: `Plant_CellFM_Plant_Methods_manuscript_v1.docx`, 36,231 bytes.
- Supporting DOCX rebuilt: `Plant_CellFM_Plant_Methods_supporting_information_v1.docx`, 24,580 bytes.
- Cover letter DOCX rebuilt: `Plant_CellFM_Plant_Methods_cover_letter_v1.docx`, 10,801 bytes.
- Native Word mathematics: 66 OMML objects in the main manuscript and 65 OMML objects in Supporting Information.
- Equation placeholder scan: zero `[[EQUATION:...]]` placeholders and zero residual LaTeX display or inline markers in both DOCX files.
- Main figures: seven PDF files in `submission_files/main_figures`, all rebuilt from v12 outputs and all below 300 KB except Fig. 7 at 297,743 bytes.
- v12 main-figure audit: PASS for editable SVG/PDF, 600-dpi PNG/TIFF exports, source-table counts, row counts and scripted-vector mechanism panels.
- Submission ZIP: `Plant_CellFM_Plant_Methods_submission_v1.zip`, 2,316,251 bytes, 14 entries, `zipfile.testzip()` PASS.

## Remaining author actions

1. Enter final author names, affiliations and corresponding-author contact information in the manuscript and submission system.
2. Confirm author contributions and all-author approval.
3. Create or link the public repository release for tag `plant-methods-submission-v1-20260803`.
4. Add a persistent archive DOI after Zenodo or another archive issues it.
