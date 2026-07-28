# Plant-CellFM / SnowLotus-CellFM

Plant-CellFM is the general-plant scope of SnowLotus-CellFM: a cross-species foundation model for plant single-cell and single-nucleus expression modelling. It provides a general expression backbone, known adapters for audited public datasets, and runtime dynamic adapters for any plant species supplied at inference time. *Saussurea involucrata* (Snow Lotus) is one adapter and validation case, not the model boundary.

This project is being run end-to-end on the recovered Matpool RTX 4090 host. The validated checkpoints remain available as baselines while the supervised public-plant data queue builds a new `public_plants_v1` corpus and automatically starts a fresh general-backbone continuation when the corpus is complete.

GitHub repository: https://github.com/ahvsjags/SnowLotus-CellFM

GitHub release: https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3

The repository is currently private. Grant editor/reviewer access or switch it to public before using these URLs as reviewer-facing links.

## General Plant Snapshot

- Release scope: `plant_general`
- Runtime host: NVIDIA RTX 4090, 24 GB VRAM
- Primary validated backbone: `outputs/remote_joint_scplantdb_pretrain_4090/best.pt`
- Validated annotation head: `outputs/remote_srp169576_joint_init_hybrid_4090/best.pt`
- Active continuation corpus: `data/plant_foundation_corpus_public_plants_v1.h5ad`
- Active continuation config: `configs/plant_general_foundation_public_plants_v1_4090.yaml`
- Active data supervisor: `scripts/supervise_plant_public_data_queue.sh`
- Active training watchdog: `scripts/start_plant_general_v1_training_watchdog.sh`
- General-plant model card: `release_metadata/plant_general_model_card.md`
- Species adapter registry: `release_metadata/plant_species_adapters.json` with dynamic resolution for all plant species
- Species coverage table: `release_metadata/plant_general_corpus_species.tsv`
- Runtime API exposes `/capabilities` and `/adapters`, resolves a species adapter on every `/annotate` request, and accepts an optional ortholog TSV for novel plant species

## What Is Included

- A Python package for plant expression tokenization, masked-modelling training, checkpoint evaluation and prediction.
- Public-corpus manifests and audits that distinguish readable cell-by-gene matrices from unsupported public records.
- A plant species-adapter registry with exact-gene and ortholog-map transfer policies, plus a runtime dynamic adapter for every newly supplied plant species.
- Frozen baseline checkpoints plus an isolated full-plant continuation output directory.
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

The repository distinguishes completed baseline evidence from the active full-plant continuation. New GEO datasets are promoted only after conversion, manifest validation and corpus inclusion; the new checkpoint is released only after training and cross-species evaluation finish.

## Citation

SnowLotus-CellFM Consortium. SnowLotus-CellFM: an audited plant single-cell foundation-model scaffold for target-species transfer. Editor release v0.3, 2026.
