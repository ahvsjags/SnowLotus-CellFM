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
| Publication readiness | `docs/publication_readiness_v9.md` |
| Model card | `release_metadata/plant_cellfm_v9_model_card.md` |
| Stability audit | `release_metadata/v9_submission_stability_audit.md` |
| Peer-review preflight | `release_metadata/publication_peer_review_preflight_v9.md` |
| Server sustainability audit | `release_metadata/server_sustainability_status_v9.md` |
| Watchdog recovery audit | `release_metadata/watchdog_recovery_status_v9.md` |
| Editor issue closure | `release_metadata/v9_editor_issue_closure.md` |
| Live API runtime smoke test | `release_metadata/api_runtime_smoke_v9.md` |
| Final editor package recipe | `release_metadata/final_editor_submission_package_recipe_v9.md` |
| External benchmark panel | `release_metadata/external_benchmark_panel_v9.md` |
| Arabidopsis root biology case | `release_metadata/plant_biology_case_study_v9.md` |
| Arabidopsis root literature anchor | `release_metadata/arabidopsis_root_literature_anchor_v9.md` |
| Arabidopsis root figure package | `release_metadata/arabidopsis_root_case_figure_v9.md` |
| v9 benchmark comparison | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` |
| Development plan matching this submission | `docs/development_plan.md` |

## Stable Claims

1. Plant-CellFM v9 is a general plant expression foundation model with an all-plant adapter framework.
2. The model is not restricted to Snow Lotus; Snow Lotus is one target-species entry point under the same adapter and ortholog-map contract.
3. The frozen v9 candidate was trained and served on an RTX 4090 environment.
4. v9 improves over the frozen v3 extended baseline on the same shared-gene benchmark under leave-dataset-out, leave-sample-out and normalized leave-species-out protocols.
5. The strict leave-species-out result should be interpreted as open-set transfer evidence, not as a claim of full-coverage high-accuracy annotation for every plant species.
6. Seurat label transfer, classical centroid baselines and the v3 comparison are completed; scPlantLLM and scPlantAnnotate remain auditable comparator entry points until their official execution environments are available.
7. The Arabidopsis root case demonstrates adapter resolution, hierarchical annotation and marker-candidate mining on public data.
8. The Arabidopsis root figure package provides SVG/PDF/PNG/TIFF exports plus source data for a figure-ready biological case.

## Claims Not Used In The Current Submission

1. The current submission does not claim a completed Snow Lotus single-cell atlas.
2. The current submission does not claim universal high-accuracy annotation for all plant species.
3. The current submission does not use early RTX 5090 planning notes as the v9 hardware statement.
4. The current submission does not report scPlantLLM or scPlantAnnotate final metrics before official executable runs are frozen.
5. The current submission does not treat old `SnowLotus_CellFM_*v0_*` manuscript drafts as the current manuscript.

## Key Numbers

| Evaluation | v9 all-cell accuracy | v9 coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |
| Seurat label transfer on frozen v9 subset | 0.2207 | n/a | n/a | 0.0603 | n/a |
| Classical centroid SRP169576 sample holdout | 0.7337 | n/a | n/a | 0.4873 | n/a |

## Server Package

The server-side publication package is located at:

`/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090`

The external benchmark and biology addendum package is located at:

`/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090/addendum_methods_panel`

The service health check reports `model_scope=plant_general`, `adapter_resolution=dynamic_all_plants`, 24 known adapters and `device=cuda`.

## Notes On Historical Files

This repository keeps earlier drafts, early hardware plans and exploratory scripts for reproducibility. Some historical names include `5090` or Snow Lotus-centered wording. Those files are development history, not the v9 submission statement. For the current submission, use this index, the v9 model card, the integrated manuscript and the v9 readiness audit.
