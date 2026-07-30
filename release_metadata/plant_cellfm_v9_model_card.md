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
- 21 plant species
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

## External Comparators And Biological Case

- Submission index: `SUBMISSION_INDEX_v9.md`
- External benchmark panel: `release_metadata/external_benchmark_panel_v9.md`
- Integrated stable manuscript: `manuscript/Plant_CellFM_v9_完整主文_稳健方法版_v1.md`
- Submission stability audit: `release_metadata/v9_submission_stability_audit.md`
- Seurat label transfer on the frozen v9 subset: fine accuracy 0.2207 and fine macro-F1 0.0603 on 512 test cells.
- Classical cosine-centroid SRP169576 sample holdout: fine accuracy 0.7337 and fine macro-F1 0.4873.
- scPlantLLM: compatible input and preprocessing are present; metric completion requires an executable official checkout and weights in the release environment.
- scPlantAnnotate: official web route is reachable, but anonymous scriptable benchmark execution is not available in the current audit.
- Arabidopsis root case: `release_metadata/plant_biology_case_study_v9.md` records adapter resolution plus 260 marker-candidate rows across 13 cell states.
- Arabidopsis root literature anchor: `release_metadata/arabidopsis_root_literature_anchor_v9.md` maps the case labels to established root atlas terminology and canonical marker examples.

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
