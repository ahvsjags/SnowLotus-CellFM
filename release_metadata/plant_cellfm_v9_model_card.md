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

## External Comparators And Biological Case

- Submission index: `SUBMISSION_INDEX_v9.md`
- External benchmark panel: `release_metadata/external_benchmark_panel_v9.md`
- Species-holdout failure audit: `release_metadata/species_holdout_failure_audit_v9.md`
- Species ontology coverage audit: `release_metadata/species_ontology_coverage_audit_v9.md`
- Species ontology-label benchmark: `release_metadata/species_ontology_label_benchmark_v9.md`
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
