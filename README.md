# Plant-CellFM / SnowLotus-CellFM

Plant-CellFM is the general-plant branch of SnowLotus-CellFM, a cross-species foundation model for plant single-cell and single-nucleus expression data. The model is not restricted to *Saussurea involucrata* (Snow Lotus): Snow Lotus is a target-species adapter and application scenario within a broader plant model.

## Frozen v9 Release

The current publication candidate is the v9 LoRA checkpoint trained on an audited public plant corpus with an NVIDIA RTX 4090. The release is frozen for reproducibility; later v10 data-expansion jobs are not part of this candidate.

Reviewer-facing entry point: `SUBMISSION_INDEX_v9.md`. That file lists the current manuscript, model card, benchmark panel and stable claim boundaries for the frozen v9 package.

- Corpus: 56 manifest rows, 29 datasets and 21 plant species.
- Training corpus: 13.78 million cells after corpus construction.
- Architecture: 256-dimensional model, 4 transformer layers, 8 attention heads, LoRA rank 8.
- Training: six epochs, hybrid masked-expression modelling and hierarchical annotation objectives, CUDA mixed precision.
- Checkpoint: `best.pt` in the GitHub release asset and on the Matpool host at `/root/snowlotus_cellfm_v9_lora_shared_4090/best.pt`.
- Service: Plant-CellFM inference service with embedding, annotation, ortholog-map transfer and runtime species-adapter resolution.

## Evaluation Snapshot

The release reports both an internal held-out test and stricter cross-group evaluations. The latter are the appropriate evidence for cross-species generalization.

| Evaluation | All-cell accuracy | Label coverage | Known-label conditional accuracy | Known-label conditional macro-F1 |
| --- | ---: | ---: | ---: | ---: |
| Internal held-out test | 0.8113 | n/a | n/a | 0.3833 |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 |

The known-label conditional columns evaluate only test cells whose reference labels occur in the training fold. The all-cell accuracy column counts cells with unseen labels as errors, which is the appropriate open-set view for species holdout. The species-holdout protocol canonicalizes species aliases such as `Arabidopsis_thaliana` and `Arabidopsis thaliana` before splitting, reducing the selected benchmark from 9 raw species labels to 8 normalized species groups. Against the frozen v3 extended baseline on the same shared-gene benchmark, v9 all-cell accuracy improved by 24.70, 20.45 and 4.41 percentage points for leave-dataset, leave-sample and normalized leave-species evaluation, respectively. All benchmark JSON, model checksums, training history and the 256-cell benchmark subset are included in the release package.

The extended methods panel also includes transparent non-Plant-CellFM comparators and a biological case-study asset. Seurat anchor-based label transfer was run on the frozen v9 subset export with 2,940 train cells and 512 test cells, obtaining fine accuracy 0.2207 and macro-F1 0.0603. The classical cosine-centroid SRP169576 sample-holdout baseline reports fine accuracy 0.7337 and macro-F1 0.4873. The scPlantLLM input path is prepared and audited, but the frozen metric is reported only when its official checkout and weights are locally available. The Arabidopsis root case study contains 260 marker-candidate rows across 13 cell states and demonstrates adapter resolution, marker mining and root cell-identity interpretation.

## Repositories and Release

- Repository: https://github.com/ahvsjags/SnowLotus-CellFM
- Frozen v9 release: https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora
- Code branch used for the release: `agent/remote-pipeline-20260728`

The repository contains the source package, training configurations, public-data manifests, audit scripts, benchmark code, model card, manuscript materials and service watchdog. The large checkpoint is distributed as a GitHub Release asset rather than committed to Git history.

## Model Functions

- Cross-species expression embeddings from `.h5ad` or `.npz` input.
- Masked-expression feature extraction and annotation inference.
- Hierarchical fine/coarse cell-state prediction when a supervised head is available.
- Exact-gene transfer followed by an optional ortholog TSV for species with different gene identifiers.
- Known adapter registry plus runtime adapter materialization for any named plant species.
- Reproducible output bundles containing predictions, embeddings, metadata and adapter-selection records.

## Quick Start

```bash
python -m pip install -e ".[singlecell,dev]"
snowcell make-demo --output data/demo.npz
snowcell train --config configs/smoke.yaml
snowcell predict --checkpoint outputs/smoke/best.pt --data data/demo.npz --output outputs/smoke/predictions.csv
```

For the frozen model, download the v9 release asset and use the packaged configuration and scripts. The server-side API exposes `GET /health`, `GET /metadata`, `GET /capabilities`, `GET /adapters` and `POST /annotate`.

## Reproducibility Evidence

- `SUBMISSION_INDEX_v9.md`
- `release_metadata/plant_cellfm_v9_model_card.md`
- `release_metadata/v9_data_card.md`
- `release_metadata/data_integrity_audit.md`
- `release_metadata/corpus_provenance_audit.md`
- `release_metadata/benchmark_gap_audit.md`
- `release_metadata/external_benchmark_status_v9.md`
- `release_metadata/external_benchmark_panel_v9.md`
- `release_metadata/plant_biology_case_study_v9.md`
- `release_metadata/third_party_comparator_sources_v9.md`
- `release_metadata/v9_submission_stability_audit.md`
- `release_metadata/server_sustainability_status_v9.md`
- `release_metadata/watchdog_recovery_status_v9.md`
- `release_metadata/v9_editor_issue_closure.md`
- `release_metadata/api_runtime_smoke_v9.md`
- `manuscript/Plant_CellFM_v9_完整主文_稳健方法版_v1.md`
- `docs/publication_readiness_v9.md`
- `scripts/package_v9_release.sh`
- `tests/`

The local regression suite passes with `PYTHONPATH=src pytest -q`. The release package also includes a SHA256 manifest that was verified on the server.

## Evidence Boundary

This release supports the claim that Plant-CellFM is a reproducible, auditable cross-species plant expression foundation-model implementation with a callable adapter layer and measured gains over the v3 extended baseline on public plant matrices. The normalized leave-species-out result should be reported with both its 55.90% label coverage and 23.54% all-cell accuracy; the 42.10% and 0.1918 values are conditional on labels being present in the training fold. The internal held-out accuracy should not be presented as universal accuracy for every plant species.

## Citation

SnowLotus-CellFM Consortium. *Plant-CellFM: a cross-species foundation model and adapter layer for plant single-cell expression annotation*. Frozen v9 release, 2026.
