# Plant-CellFM v5 Submission Evidence Ledger

## Purpose

This ledger is the claim-level index for the v5 submission package. Each statement in the manuscript, figures and release record must be traceable to a versioned local asset and retain its evaluation boundary.

| ID | Submission statement | Primary evidence | Reporting boundary |
| --- | --- | --- | --- |
| C01 | Plant-CellFM is a protocol-aware framework for plant single-cell annotation, target-species adaptation and deployment. | `release_metadata/plant_cellfm_model_card_v4.json`; Figure 1 contract panel | It is not an all-plants coverage claim. The frozen profile contains 5 profiled species and 9 datasets. |
| C02 | The frozen corpus profile contains 272,732 cells, 209,405 genes, 31 samples and 34 raw cell labels. | `figure_data/corpus_profile_v1/corpus_profile.json`; Figure 1 source TSVs | Historical catalogues, adapters and evaluation-only species are not counted as profile cells. |
| C03 | Primary strict leave-species transfer is 39.96% all-cell accuracy on 3,964 cells from 8 held-out species. | `release_metadata/revision_v17_nested_metadata_gate.json`; Figure 2 denominator and species TSVs | This is the sole primary strict headline. No target labels enter fitting or rule selection. |
| C04 | Source-label coverage is 55.90%; covered-label accuracy is 71.48% and macro-F1 is 0.2817. | `release_metadata/revision_v17_nested_metadata_gate.json`; Figure 2 | Conditional metrics never replace all-cell accuracy. |
| C05 | The v18 label-integrity companion retains 2,324 explicit-identity cells and audits 1,640 uninformative labels separately. | `release_metadata/revision_v18_identity_curated_strict.json`; Extended Data 1 | v18 is a companion denominator, not a revised primary headline. |
| C06 | Small labelled support sets yield repeatable target-species adaptation gains, reaching 75.89% mean query all-cell accuracy at 64 support cells per species. | `release_metadata/revision_v11_fewshot_adapter_benchmark.json`; Figure 3 source TSVs | This is labelled adaptation with non-overlapping support/query cells, not zero-shot transfer. |
| C07 | The runtime full-vocabulary head reaches 66.25% all-cell accuracy on its recorded deployment analysis. | `release_metadata/revision_v11_runtime_head_benchmark.json` | Deployment analysis is reported separately from strict leave-species transfer. |
| C08 | Frozen project checkpoints improve over the frozen v3 baseline under matched internal protocols. | `release_metadata/external_benchmark_panel_v9.json`; Extended Data 3 | This is an internal checkpoint comparison, not a third-party model ranking. |
| C09 | The frozen checkpoint executes on the external label-free GSE152766/GSM4626007 root matrix (6,566 cells) and produces 13 predicted states. | `release_metadata/gse152766_external_root_blind_inference_v4.json`; Figure 4 | The matrix lacks expert cell labels, so no external accuracy or model ranking is computed. |
| C10 | Five of six pre-specified canonical root-marker anchors are top by mean expression in their expected predicted groups; `WER` remains a positive but non-top coherence signal. | `release_metadata/gse152766_external_root_blind_inference_v4.json`; Figure 4 and Extended Data 5 | This is marker coherence of a model partition, not ground-truth validation. The phloem group has only four cells and is explicitly retained. |
| C11 | The root candidate resource covers 10 root identities with top-20 candidates per identity (200 rows); three of six literature-fixed anchors are recovered in matching top-20 programs. | `supplementary_tables/submission_v4/Supplementary_Table_S13_arabidopsis_root_marker_candidates.tsv`; `release_metadata/arabidopsis_root_literature_concordance_v4.json`; Extended Data 4 | Candidates are public-data hypotheses. This is neither an independent-matrix replication nor wet-lab validation. |
| C12 | scPlantLLM official weights execute under CUDA in a recorded official-chunk probe. | `release_metadata/scplantllm_official_execution_audit.json` | The probe does not share v17 inputs, ontology, split or score, and is not a direct rank. scPlantAnnotate matched prediction remains open. |
| C13 | A GSE270140 secondary-root LoRA-mode adapter achieves 83.97% held-out fine accuracy and 84.47% macro-F1 across 2,352 test cells; matched three-state semantic accuracy is 90.93% on 1,885 compatible held-out cells. | `release_metadata/gse270140_secondary_root_adapter_audit_v1.json`; Extended Data 6 source data; Tables S18-S19 | This is author-label-supervised, one-sample cell-level adaptation. It is neither zero-shot/leave-species evidence nor an independent external validation. |

## Release Gates

| Gate | v5 status | Evidence |
| --- | --- | --- |
| Figure exports, source data, editable SVG text and 600-dpi TIFFs | Pass | `release_metadata/top_journal_figure_audit_v5.json` |
| Figure claims expose denominators and protocol boundaries | Pass | `release_metadata/plant_cellfm_v5_figure_blueprint.md` |
| Strict primary metric frozen and automatically checked | Pass | `scripts/audit_v5_submission_figure_suite.py` |
| Root candidate-count contract automatically checked | Pass: 200 rows | `scripts/audit_v5_submission_figure_suite.py` |
| Secondary-root adaptation provenance, held-out test and figure exports | Pass | `release_metadata/gse270140_secondary_root_adapter_audit_v1.json`; Extended Data 6 |
| Matched official third-party comparison | Open | Table S12 and model-card comparison status |
| Independently expert-annotated external accuracy | Open | No label-bearing external matrix is included in v5 |
| Orthogonal or experimental validation of marker candidates | Open | Candidate resource remains a computational prioritization resource |

## Hardware Provenance

Historical training artefacts record RTX 4090 runs. The archived GSE152766 blind-execution and scPlantLLM execution records were produced on a local NVIDIA GeForce RTX 4070 Laptop GPU under CUDA; this ledger does not represent that local execution as active remote training.
