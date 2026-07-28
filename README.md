# Plant-CellFM / SnowLotus-CellFM

Plant-CellFM is the general-plant scope of SnowLotus-CellFM: a cross-species foundation model for plant single-cell and single-nucleus expression modelling. It provides a general expression backbone, known adapters for audited public datasets, and runtime dynamic adapters for any plant species supplied at inference time. *Saussurea involucrata* (Snow Lotus) is one adapter and validation case, not the model boundary.

This snapshot is designed for rapid editorial review: it separates validated model and corpus evidence from data-promotion work that is still running on the recovered Matpool GPU host. The current replacement host exposes an RTX 4090 with 24 GB VRAM, not the originally expected 5090. The `editor-v0.3` package promotes the current best public-expansion embedding checkpoint for immediate submission while the longer continuation and public-data queues remain active in the background.

GitHub repository: https://github.com/ahvsjags/SnowLotus-CellFM

GitHub release: https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3

The repository is currently private. Grant editor/reviewer access or switch it to public before using these URLs as reviewer-facing links.

## General Plant Snapshot

- Release label: `editor-v0.3`
- Snapshot date: 2026-07-25
- Audited corpus: 48 manifests, 194 readable matrix files and 3,922,340 readable cells
- Matrix integrity: 0 missing files and 0 unreadable files in the audited snapshot
- Best annotation checkpoint: `foundation_5090_pretrain/best.pt`, macro-F1 evidence 0.8121 in the release manifest
- Best embedding checkpoint: `foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/best.pt`, SHA256 `00c1b0a1049c441585ecd7ee03e81d05704bd93100c692cc06f7bdc90f2c034a`
- Current best evidence: v0.3 epoch-7 evaluation loss 7.1917 after vocabulary-aware warm-start from the completed v0.2 continuation; v0.3 epoch-9 training is still running and will be superseded only after passing the same audit gates
- Recovered-host public MLM training has emitted epoch-6 validation loss 8.6741 on the reconstructed public MLM corpus while additional GEO/scPlantDB data queues continue in tmux
- Newly promoted public matrices after v0.2 include GSE226826, GSE240098 and GSE240102; the next plus-corpus continuation is queued behind active training on the recovered GPU host
- General-plant model card: `release_metadata/plant_general_model_card.md`
- Species adapter registry: `release_metadata/plant_species_adapters.json` with dynamic resolution for all plant species
- Species coverage table: `release_metadata/plant_general_corpus_species.tsv`
- Runtime API exposes `/capabilities` and `/adapters`, resolves a species adapter on every `/annotate` request, and accepts an optional ortholog TSV for novel plant species

## What Is Included

- A Python package for plant expression tokenization, masked-modelling training, checkpoint evaluation and prediction.
- Public-corpus manifests and audits that distinguish readable cell-by-gene matrices from unsupported public records.
- A plant species-adapter registry with exact-gene and ortholog-map transfer policies, plus a runtime dynamic adapter for every newly supplied plant species.
- Two frozen checkpoint assets for immediate editorial inspection and reproducibility checks.
- Manuscript, cover note, model card, release manifest, data-integrity audit, corpus-provenance audit and benchmark-gap audit.
- Chinese function/innovation brief for rapid editorial communication: `SnowLotus_CellFM_中文功能创新说明_v0_1.docx`.
- Focused regression tests for the core package.

## Evidence Boundary

This release supports the claim that Plant-CellFM is a reproducible, auditable cross-species plant expression foundation-model scaffold with traceable checkpoints, a callable species-adapter layer and benchmark evidence across public plant matrices.

The adapter registry records known species promoted into the public catalog and dynamically materializes a dedicated adapter record for any other plant name at request time. Each runtime adapter uses the general backbone, exact gene identifiers first, an ortholog map when supplied, and the same fine-tuning/annotation interfaces. The universal fallback is reserved for requests without a species name. Public discovery identified transcriptomic, genomic and literature support for *S. involucrata*; the Snow Lotus branch adds reference-genome and future primary single-cell adaptation assets without narrowing the general plant model.

## Quick Start

```bash
python -m pip install -e ".[singlecell,dev]"
snowcell make-demo --output data/demo.npz
snowcell train --config configs/smoke.yaml
snowcell predict --checkpoint outputs/smoke/best.pt --data data/demo.npz --output outputs/smoke/predictions.csv
```

For model inspection, keep the frozen checkpoint assets under:

```text
models/
```

Frozen editor assets:

```text
models/SnowLotus_CellFM_best_annotation.pt
models/SnowLotus_CellFM_best_embedding.pt
models/SHA256SUMS.txt
```

Validate the frozen assets after download:

```bash
cd models
sha256sum -c SHA256SUMS.txt
```

## Repository Layout

```text
src/                         Core Python package and species-adapter resolver
configs/                     Training and evaluation configurations
scripts/                     Data, training, audit and release scripts
tests/                       Focused regression tests
manuscript/                  Editor-facing manuscript and cover note
release_metadata/            Model cards, adapter registry and audit summaries
models/                      Git LFS or GitHub Release checkpoint assets
```

## Submission Note

The current GitHub-ready repository is intentionally conservative. It gives editors and reviewers a usable model package now, while leaving additional GEO promotions, v0.3/v0.4 continuation results and authenticated external benchmarks for the next revision rather than presenting them as completed evidence.

## Citation

SnowLotus-CellFM Consortium. SnowLotus-CellFM: an audited plant single-cell foundation-model scaffold for target-species transfer. Editor release v0.3, 2026.
