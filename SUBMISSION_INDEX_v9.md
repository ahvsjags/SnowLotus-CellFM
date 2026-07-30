# Plant-CellFM v9 Submission Index

This file is the reviewer-facing entry point for the frozen v9 submission package.

## Current Submission Identity

- Project: Plant-CellFM / SnowLotus-CellFM
- Current model scope: general plant single-cell and single-nucleus expression annotation
- Current release: `v0.9.0-plant-general-lora`
- Current hardware statement: NVIDIA GeForce RTX 4090, 24 GB VRAM
- Current checkpoint: `SnowLotus-CellFM-v9-lora-4090-best.pt`
- Repository: https://github.com/ahvsjags/SnowLotus-CellFM
- Release asset: https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora

## Files To Read First

| Purpose | File |
| --- | --- |
| Repository overview | `README.md` |
| Full Chinese manuscript | `manuscript/Plant_CellFM_v9_完整主文_稳健方法版_v1.md` |
| Full Chinese manuscript, ASCII path | `manuscript/Plant_CellFM_v9_final_submission_zh_v1.md` |
| Full Chinese manuscript, Word | `manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx` |
| Final handoff summary | `release_metadata/final_handoff_summary_v9.md` |
| Cover letter | `manuscript/Plant_CellFM_v9_cover_letter.docx` |
| English synopsis, abstract and highlights | `manuscript/Plant_CellFM_v9_english_submission_synopsis.docx` |
| Submission highlights and headline numbers | `release_metadata/submission_highlights_v9.md` |
| Data and code availability | `release_metadata/data_code_availability_v9.md` |
| Publication readiness | `docs/publication_readiness_v9.md` |
| Model card | `release_metadata/plant_cellfm_v9_model_card.md` |
| Stability audit | `release_metadata/v9_submission_stability_audit.md` |
| Peer-review preflight | `release_metadata/publication_peer_review_preflight_v9.md` |
| Publication target readiness matrix | `release_metadata/top_journal_readiness_matrix.md` |
| Server sustainability audit | `release_metadata/server_sustainability_status_v9.md` |
| Release gate completion audit script | `scripts/write_release_gate_completion_audit_v9.py` |
| Server release verification script | `scripts/verify_v9_server_release.py` |
| GitHub sync recovery note | `GITHUB_SYNC_RECOVERY.md` inside the final editor zip |
| Watchdog recovery audit | `release_metadata/watchdog_recovery_status_v9.md` |
| Editor issue closure | `release_metadata/v9_editor_issue_closure.md` |
| Live API runtime smoke test | `release_metadata/api_runtime_smoke_v9.md` |
| Final editor package recipe | `release_metadata/final_editor_submission_package_recipe_v9.md` |
| External benchmark panel | `release_metadata/external_benchmark_panel_v9.md` |
| Third-party benchmark contract | `release_metadata/third_party_benchmark_contract_v10.md` |
| Arabidopsis root biology case | `release_metadata/plant_biology_case_study_v9.md` |
| Arabidopsis root literature anchor | `release_metadata/arabidopsis_root_literature_anchor_v9.md` |
| Arabidopsis root figure package | `release_metadata/arabidopsis_root_case_figure_v9.md` |
| Multi-species scPlantDB biology case | `release_metadata/multispecies_scplantdb_case_v10.md` |
| Species-holdout failure audit | `release_metadata/species_holdout_failure_audit_v9.md` |
| Species ontology coverage audit | `release_metadata/species_ontology_coverage_audit_v9.md` |
| Species ontology-label benchmark | `release_metadata/species_ontology_label_benchmark_v9.md` |
| Species-transfer calibration benchmark | `release_metadata/cross_species_classifier_benchmark_v10.md` |
| Algorithmic innovation note | `release_metadata/algorithm_innovation_v10.md` |
| Open-set calibration and selective annotation | `release_metadata/open_set_calibration_v9.md` |
| Submission scorecard | `release_metadata/submission_scorecard_v11.md` |
| Plant cell-state ontology mapping | `release_metadata/plant_cell_state_ontology_mapping_v9.tsv` |
| v9 benchmark comparison | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` |
| Current publication strategy | `docs/top_journal_strategy.md` |
| Development plan matching this submission | `docs/development_plan.md` |

## Stable Claims

1. Plant-CellFM v9 is a general plant expression foundation model with an all-plant adapter framework.
2. The model is not restricted to Snow Lotus; Snow Lotus is one target-species entry point under the same adapter and ortholog-map contract.
3. The frozen v9 candidate was trained and served on an RTX 4090 environment.
4. v9 improves over the frozen v3 extended baseline on the same shared-gene benchmark under leave-dataset-out, leave-sample-out and normalized leave-species-out protocols.
5. The strict leave-species-out result should be interpreted as open-set transfer evidence, not as a claim of full-coverage high-accuracy annotation for every plant species.
6. Seurat label transfer, classical centroid baselines and the v3 comparison are completed; scPlantLLM and scPlantAnnotate are now official-source benchmark contracts until their official execution environments produce frozen metrics.
7. The open-set calibration audit shows that API fine-confidence top-30/top-40 selective annotation reaches 96.64%/92.81% accuracy while low-confidence cells are routed to review.
8. The Arabidopsis root case demonstrates adapter resolution, hierarchical annotation and marker-candidate mining on public data.
9. The multi-species scPlantDB case adds a second public-data biology case spanning 31,503 cells, 4 species, 4 tissues and 96 marker-candidate records.
10. The Arabidopsis root figure package provides SVG/PDF/PNG/TIFF exports plus source data for a figure-ready biological case.
11. The species-holdout failure audit decomposes the strict normalized leave-species-out result into label-coverage gaps, known-label errors and per-species revision targets.
12. The species ontology coverage audit maps 106 observed fine labels into a conservative plant cell-state ontology and separates actionable ontology coverage from unknown or unannotated labels.
13. The ontology-label species-holdout benchmark reruns nearest-centroid evaluation on frozen v9 embeddings after ontology mapping, reporting 74.44% actionable coverage and 14.97% actionable all-cell accuracy.
14. The v10 Species-Transfer Calibration layer improves strict frozen leave-species all-cell accuracy from 23.64% to 30.10% and known-label accuracy from 42.28% to 53.84% without training on held-out species labels.
15. The algorithmic innovation note frames the method as all-plant adapter materialization plus STC calibration, open-set reliability control, ontology-aware benchmark audit and reproducible CUDA release.
16. The submission scorecard records all fixable evidence-readiness dimensions at 90+ while explicitly not inflating raw leave-species accuracy or unfinished official third-party metrics.
17. The publication target readiness matrix ranks the current package as strongest for plant-focused method/resource submission, plausible for genomics computational-method submission with major-revision risk, and stretch for top general methods venues until official third-party numerical closure and stronger validation are added.
18. The English synopsis file provides an abstract, significance statement, highlights, graphical abstract text and editorial positioning that use the same claim boundaries as the full manuscript.

## Claims Not Used In The Current Submission

1. The current submission does not claim a completed Snow Lotus single-cell atlas.
2. The current submission does not claim universal high-accuracy annotation for all plant species.
3. The current submission uses the model-card hardware statement: NVIDIA GeForce RTX 4090, 24 GB VRAM.
4. The current submission does not report scPlantLLM or scPlantAnnotate final metrics before official executable runs are frozen.
5. The current submission does not treat old `SnowLotus_CellFM_*v0_*` manuscript drafts as the current manuscript.
6. The current submission keeps exploratory post-v9 continuation checkpoints outside the editor-facing evidence package.
7. The current submission does not treat the 90+ evidence-readiness scorecard as 90+ raw cross-species accuracy.

## Key Numbers

| Evaluation | v9 all-cell accuracy | v9 coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |
| STC `knn_cosine_k9` on frozen leave-species embeddings | 0.3010 | 0.5590 | 0.5384 | 0.2663 | centroid 0.2364 |
| Seurat label transfer on frozen v9 subset | 0.2207 | n/a | n/a | 0.0603 | n/a |
| Classical centroid SRP169576 sample holdout | 0.7337 | n/a | n/a | 0.4873 | n/a |
| API confidence top-30 selective annotation | 0.9664 | 0.3000 accepted | n/a | n/a | n/a |
| API confidence top-40 selective annotation | 0.9281 | 0.4000 accepted | n/a | n/a | n/a |

## Server Package

The server-side publication package is located at:

`/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090`

The external benchmark and biology addendum package is located at:

`/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090/addendum_methods_panel`

The service health check reports `model_scope=plant_general`, `adapter_resolution=dynamic_all_plants`, 24 known adapters and `device=cuda`.

## Notes On Historical Files

This repository keeps earlier drafts and exploratory scripts for reproducibility. Historical files are development history, not the v9 submission statement. For the current submission, use this index, the v9 model card, the integrated manuscript and the v9 readiness audit.
