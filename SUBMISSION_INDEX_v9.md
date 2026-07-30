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
| v13 neural zero-shot STC audit | `release_metadata/revision_v13_neural_zero_shot_stc.md` |
| v14 context-aware zero-shot STC benchmark | `release_metadata/revision_v14_context_stc_benchmark.md` |
| v11 few-shot target adapter benchmark | `release_metadata/revision_v11_fewshot_adapter_benchmark.md` |
| v11 runtime-head cross-species benchmark | `release_metadata/revision_v11_runtime_head_benchmark.md` |
| v11 third-party metric closure audit | `release_metadata/revision_v11_third_party_closure.md` |
| Algorithmic innovation note | `release_metadata/algorithm_innovation_v10.md` |
| v14 algorithmic innovation note | `release_metadata/algorithm_innovation_v14.md` |
| Open-set calibration and selective annotation | `release_metadata/open_set_calibration_v9.md` |
| Submission scorecard | `release_metadata/submission_scorecard_v11.md` |
| v14 submission scorecard | `release_metadata/submission_scorecard_v14.md` |
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
15. The v13 neural STC audit shows that a generic neural calibration head reaches 31.84% all-cell and 56.95% known-label accuracy, indicating that classifier capacity alone does not solve the cross-species bottleneck.
16. The v14 context-aware STC layer adds a phylogeny/organ gate and improves the same strict zero-shot leave-species denominator to 42.36% all-cell accuracy and 75.77% known-label accuracy without using held-out species labels for training, calibration or prior construction.
17. The algorithmic innovation note frames the method as all-plant adapter materialization plus expression STC, neural STC audit, context-aware phylo-organ STC, open-set reliability control, ontology-aware benchmark audit and reproducible CUDA release.
18. The submission scorecard records all fixable evidence-readiness dimensions at 90+ while explicitly not presenting evidence-readiness as universal all-species accuracy.
19. The publication target readiness matrix ranks the current package as strongest for plant-focused method/resource submission, plausible for genomics computational-method submission with major-revision risk, and stretch for top general methods venues until official third-party numerical closure and stronger validation are added.
20. The English synopsis file provides an abstract, significance statement, highlights, graphical abstract text and editorial positioning that use the same claim boundaries as the full manuscript.
21. The v11 few-shot target-adapter benchmark is the revision result for the all-plant adapter claim: with 8 random labeled support cells per target species, query all-cell accuracy is 59.21% across 10 seeds, and larger support budgets reach 67.34-75.89%.
22. The v11 runtime-head benchmark reports 66.25% exact-label all-cell accuracy on the same 3,964 aligned cross-species cells, decomposed into 62.86% covered-label accuracy and 70.54% open-set-label accuracy.
23. The v11 third-party closure audit records scPlantLLM official-weight download status, expected SHA256/LFS OID and scPlantAnnotate authentication status; it still does not report final third-party numerical superiority before metric JSON exists.

## Claims Not Used In The Current Submission

1. The current submission does not claim a completed Snow Lotus single-cell atlas.
2. The current submission does not claim universal high-accuracy annotation for all plant species.
3. The current submission uses the model-card hardware statement: NVIDIA GeForce RTX 4090, 24 GB VRAM.
4. The current submission does not report scPlantLLM or scPlantAnnotate final metrics before official executable runs are frozen.
5. The current submission does not treat old `SnowLotus_CellFM_*v0_*` manuscript drafts as the current manuscript.
6. The current submission keeps exploratory post-v9 continuation checkpoints outside the editor-facing evidence package.
7. The current submission does not treat the 90+ evidence-readiness scorecard as 90+ raw cross-species accuracy.
8. The current submission does not present the v11 few-shot target-adapter benchmark as a zero-shot leave-species result; it is a labeled-support species-adaptation protocol.

## Key Numbers

| Evaluation | v9 all-cell accuracy | v9 coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |
| STC `knn_cosine_k9` on frozen leave-species embeddings | 0.3010 | 0.5590 | 0.5384 | 0.2663 | centroid 0.2364 |
| v13 neural STC on frozen leave-species embeddings | 0.3184 | 0.5590 | 0.5695 | 0.3079 | STC 0.3010 |
| v14 context-aware STC `phylo_organ_gate_v1` | 0.4236 | 0.5590 | 0.7577 | 0.3045 | STC 0.3010 |
| v11 few-shot adapter, 8 random support cells/species | 0.5921 query accuracy | support cells excluded | n/a | 0.2195 | zero-shot STC 0.3010 |
| v11 few-shot adapter, 16 random support cells/species | 0.6734 query accuracy | support cells excluded | n/a | 0.2904 | zero-shot STC 0.3010 |
| v11 full-vocabulary runtime head | 0.6625 | n/a | covered-label 0.6286; open-set-label 0.7054 | n/a | strict STC 0.3010 |
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
