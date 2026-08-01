# Plant-CellFM v6 Figure Audit

- State: `TECHNICALLY_READY_PENDING_EVIDENCE_COMPLETION`
- This is a source-data, export and claim-boundary audit. It is not a journal-acceptance assessment.

## Export Gate

| Figure | SVG/PDF/PNG/TIFF | Source TSV | Editable SVG text | Minimum SVG font (pt) | TIFF pixels |
| --- | --- | --- | --- | --- | --- |
| plant_cellfm_v6_fig1_foundation_contract | pass | 5 | True | 5.00 | 4386x3469 |
| plant_cellfm_v6_fig2_strict_transfer | pass | 5 | True | 5.00 | 4453x3915 |
| plant_cellfm_v6_fig3_target_adaptation | pass | 6 | True | 5.00 | 4385x3126 |
| plant_cellfm_v6_fig4_external_root_evidence | pass | 4 | True | 5.00 | 4332x3366 |
| plant_cellfm_v6_fig5_wheat_adapter | pass | 10 | True | 5.00 | 4365x3850 |
| plant_cellfm_v6_ed_fig7_zero_target_transfer | pass | 5 | True | 5.00 | 4430x2913 |
| plant_cellfm_v6_ed_fig8_scplantllm_matched_reference | pass | 7 | True | 5.00 | 4472x3060 |

## Evidence Still Open

- The matched scPlantLLM partial adaptation closes the frozen-reference gap, but full-backbone or compute-budget-matched scPlantLLM and a runnable scPlantAnnotate comparison remain open.
- The label-free external-root execution has no expert ground truth and no wet-lab validation; it remains a fixed-marker coherence case.
- The strict leave-species score is a transparent primary benchmark, but is not yet sufficient to claim universal high-accuracy plant annotation.

## Manual Editorial Checks

- Inspect final figure scale in the target journal template and confirm colour conversion after production export.
- Verify caption prose uses the scope boundaries shown directly in Figures 2, 4, 5 and Extended Data 7-8.
- Do not turn this technical audit into a self-assigned journal-quality or acceptance score.
