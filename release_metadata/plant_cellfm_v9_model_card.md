# Plant-CellFM v9 Model Card

## Identity

- Model: `Plant-CellFM v9 LoRA`
- Scope: general plant single-cell and single-nucleus expression modelling
- Checkpoint role: shared-gene backbone with hierarchical annotation head
- Hardware: NVIDIA GeForce RTX 4090, 24 GB VRAM
- Training mode: hybrid masked-expression modelling and supervised hierarchical annotation
- Adapter policy: known catalog adapters plus runtime adapter materialization for any named plant species

## Training Corpus

- 56 manifest rows
- 29 public datasets
- 20 normalized plant species labels and 21 raw species strings before alias canonicalization
- Approximately 13.78 million cells
- Approximately 1.53 million source genes before shared-gene filtering
- Shared checkpoint vocabulary: 280,747 genes

The public corpus contains Arabidopsis, rice, tomato, soybean, maize, cotton, tea, poplar, Medicago, Brassicaceae and additional plant taxa. Snow Lotus is a target adapter and validation case, not the boundary of the model.

## Functions

- Cross-species expression embeddings
- Masked-expression feature extraction
- Hierarchical fine/coarse cell-state annotation
- Marker-candidate discovery
- Exact-gene transfer and optional ortholog-map transfer
- Runtime species-adapter resolution
- Reproducible prediction and embedding output bundles

## Evaluation

The candidate and v3 baseline were evaluated on the same v9 shared-gene subset.

| Protocol | v9 all-cell accuracy | v9 coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |

The internal held-out test reports fine accuracy 0.8113, coarse accuracy 0.8298 and fine macro-F1 0.3833. Known-label metrics are conditional on the reference label occurring in the training fold; all-cell accuracy counts unseen labels as errors. Species labels are canonicalized before species holdout, so `Arabidopsis_thaliana` and `Arabidopsis thaliana` are evaluated as one species group. Therefore, for cross-species generalization, the primary normalized species-holdout result is 23.54% all-cell accuracy at 55.90% coverage, while 42.10% and 0.1918 are conditional metrics.

The species-holdout failure audit decomposes this result into label coverage, known-label transfer and per-species revision targets. It reports 1,748 / 3,964 open-set cells without train-fold label overlap, accounting for an estimated 57.67% of all-cell errors. This audit supports a transparent open-set generalization claim rather than a universal high-accuracy claim for every plant species.

The paired species ontology coverage audit maps 106 observed fine labels to a conservative plant cell-state ontology. After aligning server-exported `obs` labels to the frozen 3,964 leave-species test cells, exact-label coverage is reconstructed as 2,246 cells, within 30 cells of the frozen JSON. Actionable ontology coverage is 1,794 / 3,964 cells (45.26%) after excluding 1,384 unknown or unannotated cells. This is a label-harmonization audit and does not revise the frozen accuracy or macro-F1 metrics.

The ontology-label species-holdout benchmark reuses the frozen 3,964 x 256 runtime-smoke embeddings and reruns nearest-centroid transfer after ontology mapping. Exact-label recomputation matches the frozen benchmark closely. Under the ontology-actionable protocol, 1,640 unknown or unannotated cells are excluded, 2,324 cells remain actionable, ontology-label coverage is 74.44%, actionable all-cell accuracy is 14.97%, known-label accuracy is 20.12% and known-label macro-F1 is 0.1395. This provides a stricter diagnostic of remaining representation-transfer error after label harmonization.

The v10 Species-Transfer Calibration (STC) benchmark adds a classifier-side improvement on the same frozen runtime-smoke embeddings and the same leave-species split. The best `knn_cosine_k9` calibrated layer improves exact-label all-cell accuracy from the centroid baseline 23.64% to 30.10%, known-label accuracy from 42.28% to 53.84%, and known-label macro-F1 from 0.1922 to 0.2663, without training on held-out species labels. Coverage remains 55.90%, so the result is reported as measured species-transfer calibration rather than a universal high-accuracy claim.

The v13/v14 zero-shot STC revision closes the stricter reviewer concern under the same frozen embeddings and same 3,964 aligned cells. v13 shows that a generic z-scored neural calibration head reaches only 31.84% all-cell and 56.95% known-label accuracy. v14 then adds a context-aware phylogeny/organ gate estimated only from training species metadata; `phylo_organ_gate_v1` reaches 42.36% strict all-cell accuracy, 75.77% known-label accuracy and 0.3045 known-label macro-F1 at unchanged 55.90% coverage, without using held-out species labels for training, calibration or prior construction.

The v11 revision benchmark adds two clearly separated cross-species usage protocols. First, the deployable full-vocabulary runtime annotation head reaches 66.25% exact-label all-cell accuracy on the same 3,964 aligned runtime-smoke cells; within the strict leave-species train-label partition this decomposes into 62.86% covered-label accuracy and 70.54% open-set-label accuracy. Second, the few-shot target-species adapter protocol uses a small labeled support set from each held-out species for adapter/classifier calibration and excludes support cells from query evaluation. Under this species-adaptation protocol, 8 random support cells per target species reach 59.21% mean query all-cell accuracy across 10 seeds, while 16, 32 and 64 support cells reach 67.34%, 72.30% and 75.89%. These v11 results do not replace the zero-shot STC benchmark; they document the practical adapter path for new plant species.

## External Comparators And Biological Case

- Submission index: `SUBMISSION_INDEX_v9.md`
- External benchmark panel: `release_metadata/external_benchmark_panel_v9.md`
- Species-holdout failure audit: `release_metadata/species_holdout_failure_audit_v9.md`
- Species ontology coverage audit: `release_metadata/species_ontology_coverage_audit_v9.md`
- Species ontology-label benchmark: `release_metadata/species_ontology_label_benchmark_v9.md`
- Species-transfer calibration benchmark: `release_metadata/cross_species_classifier_benchmark_v10.md`
- v13 neural zero-shot STC audit: `release_metadata/revision_v13_neural_zero_shot_stc.md`
- v14 context-aware zero-shot STC benchmark: `release_metadata/revision_v14_context_stc_benchmark.md`
- v11 few-shot target adapter benchmark: `release_metadata/revision_v11_fewshot_adapter_benchmark.md`
- v11 runtime-head benchmark: `release_metadata/revision_v11_runtime_head_benchmark.md`
- v11 third-party closure audit: `release_metadata/revision_v11_third_party_closure.md`
- Algorithmic innovation note: `release_metadata/algorithm_innovation_v14.md`
- Plant cell-state ontology mapping: `release_metadata/plant_cell_state_ontology_mapping_v9.tsv`
- Integrated stable manuscript: `manuscript/Plant_CellFM_v9_final_submission_zh_v1.md` and `manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx`
- Submission stability audit: `release_metadata/v9_submission_stability_audit.md`
- Seurat label transfer on the frozen v9 subset: fine accuracy 0.2207 and fine macro-F1 0.0603 on 512 test cells.
- Classical cosine-centroid SRP169576 sample holdout: fine accuracy 0.7337 and fine macro-F1 0.4873.
- scPlantLLM: compatible input and preprocessing are present; metric completion requires an executable official checkout and weights in the release environment.
- scPlantAnnotate: official web route is reachable, but anonymous scriptable benchmark execution is not available in the current audit.
- Arabidopsis root case: `release_metadata/plant_biology_case_study_v9.md` records adapter resolution plus 260 marker-candidate rows across 13 cell states.
- Arabidopsis root literature anchor: `release_metadata/arabidopsis_root_literature_anchor_v9.md` maps the case labels to established root atlas terminology and canonical marker examples.
- Multi-species scPlantDB case: `release_metadata/multispecies_scplantdb_case_v10.md` adds 31,503 public-data cells across 4 plant species, 4 tissues and 96 marker-candidate records.

## Reproduction and Integrity

- Frozen checkpoint: GitHub Release asset `SnowLotus-CellFM-v9-lora-4090-best.pt`
- SHA256: `9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`
- Configuration: `configs/generated/foundation_public_plants_v9_lora_4090.yaml`
- Benchmark comparison: `/root/snowlotus_cellfm_v9_lora_shared_4090/v9_lora_vs_v3_shared_comparison.json`
- Service: `http://127.0.0.1:8000` on the Matpool host
- Live API smoke evidence: `release_metadata/api_runtime_smoke_v9.md`
- Watchdog recovery evidence: `release_metadata/watchdog_recovery_status_v9.md`
- Server sustainability evidence: `release_metadata/server_sustainability_status_v9.md`
- Release package checksum verification: passed on the server

## Scope Boundary

The model card describes the frozen v9 publication checkpoint only. Exploratory post-v9 continuation checkpoints and refresh logs are not used as v9 performance evidence and are kept outside the editor-facing package.
