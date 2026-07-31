# Plant-CellFM v4 Figure Audit

- State: `EVIDENCE_STRONG_DRAFT_NOT_SUBMISSION_APPROVED`
- Visual review: `90.0/100` (expert_reviewed_v4_data_first_draft)
- v17 strict all-cell accuracy: `0.3996`
- v18 curated identity cohort: `2324` cells after excluding `1640` unknown/unannotated labels.

## Export and Source-Data Gate

| Figure | SVG/PDF/PNG/TIFF | Source TSV | Editable SVG text | TIFF pixels |
| --- | --- | --- | --- | --- |
| plant_cellfm_v4_fig1_cross_species_atlas | pass | 3 | True | 4487x3430 |
| plant_cellfm_v4_fig2_nested_strict_transfer | pass | 5 | True | 4762x3622 |
| plant_cellfm_v4_fig3_fewshot_target_adaptation | pass | 3 | True | 4356x3409 |
| plant_cellfm_v4_fig4_arabidopsis_root_candidate_resource | pass | 3 | True | 4243x3515 |
| plant_cellfm_v4_ed_fig1_label_integrity | pass | 4 | True | 4352x2636 |
| plant_cellfm_v4_ed_fig2_nested_selection_audit | pass | 2 | True | 4455x2567 |
| plant_cellfm_v4_ed_fig3_matched_checkpoint_comparison | pass | 2 | True | 4609x2749 |
| plant_cellfm_v4_ed_fig4_literature_marker_concordance | pass | 2 | True | 4649x2314 |
| plant_cellfm_v4_ed_fig5_external_root_blind_inference | pass | 3 | True | 4679x4152 |

## Remaining Submission Blockers

- A matched official scPlantLLM/scPlantAnnotate benchmark is not closed. scPlantLLM has an auditable CUDA execution on its own official chunks, not a shared v17 input and scoring contract.
- The biology package now includes literature-anchor concordance and a label-free external root-matrix marker-coherence execution, but it still lacks independently annotated test labels or wet-lab validation.
- The frozen corpus supports a defined public cohort, not universal all-plant performance.

## Per-Figure Review

| Asset | Score | Review |
| --- | ---: | --- |
| Fig. 1 | 90/100 | Dominant cell-level embedding, matched ontology view and compact corpus context make the biological scale visible without a decorative dashboard. |
| Fig. 2 | 89/100 | The strict protocol, held-out-cell view, all-species outcomes and label-integrity cascade form a connected causal argument; v17 and v18 remain explicitly separated. |
| Fig. 3 | 91/100 | All independent support draws, dose response, macro-F1 and species heterogeneity are visible. Single-label public records are explicitly marked. |
| Fig. 4 | 91/100 | The compact root taxonomy now joins four biological compartments, ten identity nodes and their public-data evidence scale with ranked programs, effect size and detection separation. The resource remains explicitly computational pending independent validation. |
| Extended Data 1 | 90/100 | The identity denominator and excluded labels are directly auditable at species resolution. |
| Extended Data 2 | 89/100 | Nested candidate selection is visible rather than asserted in prose. |
| Extended Data 3 | 90/100 | Frozen checkpoint gains are shown only on matched protocols, with the hardest species transfer setting left visible. |
| Extended Data 4 | 90/100 | All six literature-defined root anchors are visible, with recovered and unrecovered entries shown together and the non-experimental scope made explicit. |
| Extended Data 5 | 92/100 | A full external label-free root-matrix execution exposes its manifold, all 13 output states, confidence distribution and all six fixed marker checks without substituting marker coherence for accuracy. |
