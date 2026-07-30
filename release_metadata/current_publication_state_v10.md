# Plant-CellFM Current Publication State After v10 Continuation

Generated: 2026-07-31 Asia/Shanghai

## Executive Position

The editor-facing release remains **Plant-CellFM v9**, a plant-general single-cell and single-nucleus expression foundation model with an all-plant adapter framework. The formal hardware statement is **NVIDIA GeForce RTX 4090, 24 GB VRAM**.

Exploratory post-v9 continuation logs are kept outside the editor-facing package. The current submission does not use any continuation checkpoint as publication-model performance; it keeps only the multi-species scPlantDB public-data case as a biology demonstration and marker-candidate resource.

The current submission package now also includes an open-set calibration/selective annotation audit, official-source third-party benchmark contracts, a multi-species scPlantDB public-data biology case and a v11 submission scorecard. These additions raise all fixable evidence-readiness dimensions to 90+ while keeping raw leave-species accuracy, official scPlantLLM/scPlantAnnotate metrics and wet-lab validation non-inflated.

## Release-Gate State

| Gate | Current value |
| --- | --- |
| Source commit | Resolved from the generated package status and server release-gate audit at packaging time. |
| GitHub branch | `https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728` |
| Final editor zip SHA256 | Resolved from `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.status.json` and the server release-gate audit. |
| Server verifier | `pass` |
| Release gate position | `release_ready_current_gates_pass` |
| Live service | `Plant-CellFM`, `plant_general`, `dynamic_all_plants`, `device=cuda`, 24 adapters |
| GPU statement | `NVIDIA GeForce RTX 4090, 24 GB VRAM` |

## Frozen v9 Performance

| Protocol | v9 all-cell accuracy | Coverage | Known-label accuracy | Known-label macro-F1 | v3 all-cell accuracy | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 | Strongest cross-dataset evidence. |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 | Strongest near-domain transfer evidence. |
| Leave-species-out, normalized species labels | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 | Strict open-set species transfer evidence; do not overclaim universal high accuracy. |
| Seurat label transfer on frozen subset | 0.2207 | n/a | n/a | 0.0603 | n/a | Completed traditional comparator; shows generic label transfer is weak here. |
| Classical centroid SRP169576 sample holdout | 0.7337 | n/a | n/a | 0.4873 | n/a | Transparent classical sample-holdout baseline. |
| API confidence top-30 selective annotation | 0.9664 | 30% accepted | n/a | n/a | n/a | High-confidence auto-annotation layer; not a replacement for raw leave-species all-cell accuracy. |
| API confidence top-40 selective annotation | 0.9281 | 40% accepted | n/a | n/a | n/a | Supports a practical accept/review workflow. |

## Post-v9 Boundary

| Item | Current value |
| --- | --- |
| Editor package role | excluded from frozen v9 performance evidence |
| Public-data case retained | `release_metadata/multispecies_scplantdb_case_v10.md` |
| Merged corpus | 31,503 cells x 210,485 genes |
| Corpus diversity | 4 species, 4 tissues, 15 samples, 4 datasets, 27 fine cell-type labels |

Interpretation: the editor-facing package deliberately separates frozen v9 evidence from exploratory continuation checkpoints. The multi-species scPlantDB case is retained because it demonstrates biological use of the public-data corpus, not because it replaces the v9 benchmark.

The accompanying multi-species scPlantDB case uses the same staged corpus as a public-data biology demonstration: 31,503 cells, 4 species, 4 tissues and 96 marker-candidate records. It broadens the biology case beyond Arabidopsis root while remaining computational evidence rather than wet-lab validation.

## What Is Already Strong Enough To Submit

1. The project is no longer Snow Lotus-only. The current model is Plant-CellFM, a plant-general foundation model with all-plant adapter materialization.
2. The v9 release is checksum-pinned, GitHub-synchronized and server-verified.
3. The service is callable on CUDA and has watchdog recovery evidence.
4. v9 improves over the frozen v3 baseline on the same shared-gene benchmark under leave-dataset, leave-sample and normalized leave-species protocols.
5. The low leave-species result is transparently decomposed by species-holdout failure audit, ontology coverage audit, ontology-label benchmark and open-set calibration.
6. The external benchmark panel includes completed Seurat and centroid baselines while scPlantLLM/scPlantAnnotate are represented by official-source benchmark contracts.
7. The Arabidopsis root case provides a figure-ready computational biology demonstration with 260 marker-candidate rows, 13 states and literature anchors.
8. The multi-species scPlantDB case adds a second public-data biology demonstration with 31,503 cells, 4 species, 4 tissues and 96 marker-candidate rows.
9. The v11 scorecard records 90+ evidence-readiness for all fixable submission modules while preserving raw metric boundaries.

## What Must Not Be Claimed

1. Do not claim universal high-accuracy annotation for all plants.
2. Do not claim the v10 continuation checkpoint is better than v9.
3. Do not claim a completed Snow Lotus single-cell atlas.
4. Do not claim official scPlantLLM or scPlantAnnotate numerical superiority until executable third-party metrics are frozen.
5. Do not cite older 5090 planning files as the current hardware statement; the model card uses RTX 4090.
6. Do not treat the 90+ evidence-readiness scorecard as 90+ raw cross-species accuracy.

## Current Venue Fit

| Venue path | Current fit | Reason |
| --- | --- | --- |
| Plant-focused method/resource journal | Ready | Strongest path: plant utility, public corpus, adapter framework, v9-v3/Seurat/centroid comparisons, open-set calibration, Arabidopsis/multi-species cases and reproducible server evidence. |
| Genome Biology-style computational genomics venue | Ready with major-revision risk | The resource and reproducibility story is strong; official third-party numerical comparison would further strengthen it. |
| Communications Biology-style broad biology venue | Possible with conservative framing | Works if framed as computational biology resource, not as a universal high-accuracy annotator. |
| Nature Methods / Nature Plants | Stretch | Needs stronger official third-party comparator closure and independent biological validation. |

## Recommended Submission Sentence

Plant-CellFM v9 is a reproducible plant-general single-cell expression foundation-model and all-plant adapter framework. The frozen RTX 4090 release includes checksum-pinned code and checkpoint assets, strict v9-v3 benchmarks, completed Seurat and centroid baselines, species-holdout failure and ontology audits, open-set calibration/selective annotation evidence, official-source third-party benchmark contracts, Arabidopsis root and multi-species scPlantDB marker-candidate cases, a live CUDA annotation service and watchdog recovery evidence. The post-v9 v10 scPlantDB continuation demonstrates that the same server pipeline can ingest and train on additional public plant H5AD files, but it remains diagnostic and is not used as a replacement performance claim.
