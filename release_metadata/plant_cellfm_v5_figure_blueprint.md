# Plant-CellFM v5 Figure Blueprint

## Target

Build a methods-and-resource figure sequence suitable for high-impact editorial review. The target is not a decorative restyle: every main figure must carry one falsifiable claim, expose its denominator, and link to versioned source data.

## Main Story

| Figure | Core claim | Data evidence | Boundary retained in the figure |
| --- | --- | --- | --- |
| Fig. 1 | Plant-CellFM is a protocol-aware plant single-cell framework rather than a single opaque classifier. | Frozen corpus profile, 3,964-cell evaluation embedding, species-organ matrix and recorded annotation contract. | The frozen profile has 5 profiled species and 9 datasets; it is not a claim of all-plant coverage. |
| Fig. 2 | Strict leave-species transfer must report open-set coverage alongside accuracy. | Eight-species v17 held-out records, 3,964-cell denominator, 3,000 fixed-seed bootstrap resamples and an explicit nested-selection trace. | 39.96% is the all-cell v17 result; conditional accuracy is never substituted for it. |
| Fig. 3 | A small labelled support set gives repeatable target-species adaptation gains. | Ten non-overlapping draws at four support budgets, macro-F1 and species-by-budget outcomes. | This is labelled adaptation, not zero-shot transfer. |
| Fig. 4 | A frozen model can execute on a label-free external root matrix and yield auditable marker coherence. | 6,566 external cells, all 13 output states, confidence distribution and six fixed literature anchors. | The input has no expert labels; no external accuracy, external ranking or wet-lab validation is claimed. |

## Extended Data and Tables

| Asset | Role |
| --- | --- |
| Extended Data 1 | Label-integrity denominator and audit-only labels. |
| Extended Data 2 | Inner-fold candidate selection audit. |
| Extended Data 3 | Frozen v3-to-v9 matched checkpoint comparison. |
| Extended Data 4 | Predefined root-marker literature concordance. |
| Extended Data 5 | Full external blind-inference audit. |
| Extended Data 6 | GSE270140 author-label-supervised secondary-root LoRA-mode adaptation, including a matched three-state recovery audit, 14-class held-out confusion matrix and per-class F1. |
| Tables S1-S19 | Corpus provenance, ontology, splits, adapter registry, benchmarks, root candidates, external-root audit and GSE270140 secondary-root adapter detail. |

## Presentation Rules

- Main figures use a data-first layout with direct observations occupying the majority of the canvas.
- Workflow elements are restrained, rectangular and subordinate to the data rather than presented as dashboard cards.
- Colours retain a stable semantic role: teal for primary measured performance, blue for conditional or structural quantities, orange for coverage/support, purple for fine-label or adapter effects, and grey for audit-only context.
- Every quantitative panel has a TSV source-data companion. SVG text stays editable and TIFF exports are 600 dpi.
- No self-scored visual number is presented as editorial evidence. Final readability remains a human editorial review item.

## Open Evidence Needed for a Higher Claim Tier

1. A raw, independently expert-annotated external matrix with a frozen label-mapping contract.
2. Matched official scPlantLLM and scPlantAnnotate predictions on the same input, ontology mapping, split and open-set score.
3. Independent experimental or orthogonal biological validation of the candidate marker resource.

## Post-hoc Adaptation Evidence

GSE270140/GSM8335426 supplies 11,760 author-annotated secondary-root cells across 14 states. It is used here only for a labelled, one-sample, cell-level split adaptation exercise: 8,232 training cells, 1,176 validation cells and 2,352 locked test cells. The LoRA-mode adapter reaches 83.97% primary test-evaluator fine accuracy and 84.47% macro-F1; the detailed full-precision recheck is 84.18% / 84.64%. On 1,885 held-out cells whose author labels map to the frozen three-state vascular ontology, semantic accuracy rises from 2.02% for the frozen base checkpoint to 90.93% after adaptation. This is not a zero-shot or leave-species result, and it does not close the independent external validation gate.
