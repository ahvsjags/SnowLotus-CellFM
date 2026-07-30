# Plant-CellFM / SnowLotus-CellFM

Plant-CellFM is the general-plant branch of SnowLotus-CellFM, a cross-species foundation model for plant single-cell and single-nucleus expression data. The model is not restricted to *Saussurea involucrata* (Snow Lotus): Snow Lotus is one species adapter and one biological validation case within a broader plant model.

## Frozen v9 Release

The current publication candidate is the v9 LoRA checkpoint trained on an audited public plant corpus with an NVIDIA RTX 4090. The release is frozen for reproducibility; later v10 data-expansion jobs are not part of this candidate.

- Corpus: 56 manifest rows, 29 datasets and 21 plant species.
- Training corpus: 13.78 million cells after corpus construction.
- Architecture: 256-dimensional model, 4 transformer layers, 8 attention heads, LoRA rank 8.
- Training: six epochs, hybrid masked-expression modelling and hierarchical annotation objectives, CUDA mixed precision.
- Checkpoint: `best.pt` in the GitHub release asset and on the Matpool host at `/root/snowlotus_cellfm_v9_lora_shared_4090/best.pt`.
- Service: Plant-CellFM inference service with embedding, annotation, ortholog-map transfer and runtime species-adapter resolution.

## Evaluation Snapshot

The release reports both an internal held-out test and stricter cross-group evaluations. The latter are the appropriate evidence for cross-species generalization.

| Evaluation | Fine accuracy | Fine macro-F1 |
| --- | ---: | ---: |
| Internal held-out test | 0.8113 | 0.3833 |
| Leave-dataset-out | 0.5601 | 0.3485 |
| Leave-sample-out | 0.6281 | 0.4902 |
| Leave-species-out | 0.5282 | 0.2897 |

Against the frozen v3 baseline on the same shared-gene benchmark, fine accuracy improved by 30.81, 20.72 and 28.26 percentage points for leave-dataset, leave-sample and leave-species evaluation, respectively. All benchmark JSON, model checksums, training history and the 256-cell benchmark subset are included in the release package.

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

- `release_metadata/plant_general_model_card.md`
- `release_metadata/model_data_card.md`
- `release_metadata/data_integrity_audit.md`
- `release_metadata/corpus_provenance_audit.md`
- `release_metadata/benchmark_gap_audit.md`
- `docs/publication_readiness_v9.md`
- `scripts/package_v9_release.sh`
- `tests/`

The local regression suite passes with `PYTHONPATH=src pytest -q`. The release package also includes a SHA256 manifest that was verified on the server.

## Evidence Boundary

This release supports the claim that Plant-CellFM is a reproducible, auditable cross-species plant expression foundation-model implementation with a callable adapter layer and measured gains over the v3 baseline on public plant matrices. The reported leave-species-out result is the principal generalization result; the internal held-out accuracy should not be presented as universal accuracy for every plant species.

## Citation

SnowLotus-CellFM Consortium. *Plant-CellFM: a cross-species foundation model and adapter layer for plant single-cell expression annotation*. Frozen v9 release, 2026.
