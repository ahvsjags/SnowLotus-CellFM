# Plant-CellFM v6 Submission Evidence Ledger

## Purpose

This ledger separates the evidence that can be displayed as a main conclusion from the evidence that belongs in Extended Data, source tables or a future revision. It is the guardrail for a high-impact visual package: visual polish may clarify the record, but cannot expand its scope.

## Main-Figure Claims

| Figure | Permitted conclusion | Frozen evidence | Scope retained in the same figure |
| --- | --- | --- | --- |
| Fig. 1 | Plant-CellFM links a deterministic gene/orthology input contract, shared cell representation and species-adaptation output record. | 272,732 frozen-profile cells, five profiled species, 3,964 strict-panel cells and 24 registered adaptation modules. | The frozen profile is not an all-plant atlas. |
| Fig. 2 | Locked leave-species transfer reaches 39.96% all-cell accuracy across 3,964 held-out cells, while 55.90% source-label coverage makes heterogeneity visible. | `revision_v17_nested_metadata_gate.json`; 2,216 covered and 1,748 open/unavailable cells. | The 42.36% context-gate number is a sensitivity result, not the nested primary score. |
| Fig. 3 | Target-labelled support produces a repeatable adaptation dose response, reaching 75.89% mean all-cell query accuracy at 64 support cells per held-out species. | Ten fixed support draws per budget, support/query isolation and the retained low-information rows. | This is labelled adaptation, not zero-shot transfer. |
| Fig. 4 | The frozen model produces an inspectable 13-state partition on a 6,566-cell label-free external root matrix; five of six prespecified marker anchors peak in their expected predicted group. | `gse152766_external_root_blind_inference_v4.json` and fixed-marker source data. | This is biological coherence, not external accuracy or wet-lab validation. |
| Fig. 5 | With barcode-overlap exclusion and a fixed 13-class test, wheat LoRA reaches 62.25% accuracy and 0.6660 macro-F1; direct-root accuracy rises from 25.93% frozen to 56.22% after target-supervised adaptation. | `gse270342_wheat_lora_adapter_audit_v1.json`, locked 1,433-cell test and released checkpoint checksum. | One public author-labelled study with a same-study cell-level split; adaptation, not independent validation. |

## Extended Evidence

| Asset | What it resolves | What it does not resolve |
| --- | --- | --- |
| Extended Data 7 and Table S21 | Source-only Arabidopsis-to-wheat three-state transfer. The frozen root checkpoint reaches macro-F1 0.4231 while the GSE270140 source adapter reaches 0.4036 under k=9, so the adapter is not promoted. | It is not strict leave-species replacement, independent external validation or third-party comparison. |
| Extended Data 8 and Tables S22-S24 | Matched GSE270342 scPlantLLM references with the same prepared object, author first-target mapping and exact 1,433-cell locked test. Frozen encoder plus train-only centroid readout reaches 0.2107 accuracy and 0.2001 macro-F1; final-block-plus-new-head partial adaptation reaches 0.3426 accuracy and 0.2998 macro-F1; full-backbone-plus-new-head adaptation reaches 0.4501 accuracy and 0.4588 macro-F1 after validation-only epoch selection. Both adapted prediction tables replay exactly from their recorded checksums. | All runs are same-study adaptation references. They are not independent validation, strict leave-species transfer or a compute-matched universal model-ranking claim. |
| Extended Data 1-6 and Tables S1-S20 | Identity, nested-selection, historical checkpoint, marker, label-free root and secondary-root adaptation audits. | These do not replace an independent multi-study ground-truth benchmark. |

## Reproducibility Assets

- Main suite: `figures/plant_cellfm_submission_v6/main/` with five SVG, PDF, PNG and 600-dpi TIFF figure sets.
- Extended suite: `figures/plant_cellfm_submission_v6/extended_data/` with Extended Data 7 and 8 in the same four formats.
- Tidy source data: `figures/plant_cellfm_submission_v6/source_data/`.
- Formal visual contract: `release_metadata/plant_cellfm_v6_top_journal_figure_contract.md`.
- Export and evidence audit: `scripts/audit_v6_submission_figure_suite.py` and its generated JSON/Markdown reports.

## Evidence Still Needed for a Stronger Revision

1. A compute-budget-matched scPlantLLM comparison and an executable scPlantAnnotate benchmark under a shared label/open-set protocol. The full-backbone matched-data scPlantLLM run is now complete and replayed.
2. At least one independently labelled multi-species external cohort, ideally accompanied by orthogonal biological validation for a selected root or stress trajectory.
3. A strict leave-species improvement that survives the retained open-set denominator and improves macro-F1, not only accuracy on a filtered label subset.

## Editorial Rule

Use the main figures to make the five bounded conclusions above legible. Use Extended Data to show the audits, sensitivity analyses and matched scPlantLLM adaptation reference. Do not claim universal high-accuracy plant annotation, third-party superiority, independent external accuracy or experimental validation until those evidence assets exist.
