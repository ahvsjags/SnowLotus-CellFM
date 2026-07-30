# Plant-CellFM Current Publication State After v10 Continuation

Generated: 2026-07-31 Asia/Shanghai

## Executive Position

The editor-facing release remains **Plant-CellFM v9**, a plant-general single-cell and single-nucleus expression foundation model with an all-plant adapter framework. The formal hardware statement is **NVIDIA GeForce RTX 4090, 24 GB VRAM**.

The v10 scPlantDB continuation is now a real completed server run, not only a plan. It is useful as sustainability evidence because it proves that the project can stage new public plant H5AD files, merge them into a corpus and launch LoRA continuation training on the same server environment. It is not a replacement publication model because the diagnostic test metrics are low.

## Release-Gate State

| Gate | Current value |
| --- | --- |
| Source commit | `35857f667bd277777e93373551a1e01707ce2c6d` |
| GitHub branch | `https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728` |
| Final editor zip SHA256 | `f0dbad6f437557e481c5412d3a5dc21639cbe369cc39e200ccc0762ccca65500` |
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

## Post-v9 v10 Continuation

| Item | Current value |
| --- | --- |
| Continuation state | `waiting_for_disk_budget` |
| `/mnt` free space | 692 MB, 100% used |
| `/root` free space | 61.47 GB, 70% used |
| Root staging path | `/root/snowlotus_cellfm_v10` |
| scPlantDB H5AD files | `SRP164771.h5ad`, `SRP241596.h5ad`, `SRP285040.h5ad`, `SRP386976.h5ad` |
| Merged corpus | 31,503 cells x 210,485 genes |
| Corpus diversity | 4 species, 4 tissues, 15 samples, 4 datasets, 27 fine cell-type labels |
| Training output | `/root/snowlotus_cellfm_v10_scplantdb_lora_4090` |
| Epochs | 2 completed; best epoch by eval loss: 2 |
| Diagnostic metrics | fine accuracy 0.0669, fine macro-F1 0.0128, coarse accuracy 0.0215, coarse macro-F1 0.0165 |
| Checkpoints | `best.pt` 139.88 MB; `latest.pt` 387.50 MB |

Interpretation: v10 continuation proves the ingestion/training machinery works on new public plant data under disk-aware constraints. The diagnostic metrics indicate that the new corpus needs label harmonization, sampling control, adapter calibration and a frozen benchmark before a v10 model can be promoted.

## What Is Already Strong Enough To Submit

1. The project is no longer Snow Lotus-only. The current model is Plant-CellFM, a plant-general foundation model with all-plant adapter materialization.
2. The v9 release is checksum-pinned, GitHub-synchronized and server-verified.
3. The service is callable on CUDA and has watchdog recovery evidence.
4. v9 improves over the frozen v3 baseline on the same shared-gene benchmark under leave-dataset, leave-sample and normalized leave-species protocols.
5. The low leave-species result is transparently decomposed by species-holdout failure audit, ontology coverage audit and ontology-label benchmark.
6. The external benchmark panel includes completed Seurat and centroid baselines while keeping scPlantLLM/scPlantAnnotate at their audited execution boundaries.
7. The Arabidopsis root case provides a figure-ready computational biology demonstration with 260 marker-candidate rows, 13 states and literature anchors.

## What Must Not Be Claimed

1. Do not claim universal high-accuracy annotation for all plants.
2. Do not claim the v10 continuation checkpoint is better than v9.
3. Do not claim a completed Snow Lotus single-cell atlas.
4. Do not claim official scPlantLLM or scPlantAnnotate numerical superiority until executable third-party metrics are frozen.
5. Do not cite older 5090 planning files as the current hardware statement; the model card uses RTX 4090.

## Current Venue Fit

| Venue path | Current fit | Reason |
| --- | --- | --- |
| Plant-focused method/resource journal | Ready | Strongest path: plant utility, public corpus, adapter framework, v9-v3/Seurat/centroid comparisons, Arabidopsis root case and reproducible server evidence. |
| Genome Biology-style computational genomics venue | Plausible with major-revision risk | The resource and reproducibility story is strong; official third-party model comparison would strengthen it. |
| Communications Biology-style broad biology venue | Possible with conservative framing | Works if framed as computational biology resource, not as a universal high-accuracy annotator. |
| Nature Methods / Nature Plants | Stretch | Needs stronger official third-party comparator closure and independent biological validation. |

## Recommended Submission Sentence

Plant-CellFM v9 is a reproducible plant-general single-cell expression foundation-model and all-plant adapter framework. The frozen RTX 4090 release includes checksum-pinned code and checkpoint assets, strict v9-v3 benchmarks, completed Seurat and centroid baselines, species-holdout failure and ontology audits, an Arabidopsis root marker-candidate case, a live CUDA annotation service and watchdog recovery evidence. The post-v9 v10 scPlantDB continuation demonstrates that the same server pipeline can ingest and train on additional public plant H5AD files, but it remains diagnostic and is not used as a replacement performance claim.
