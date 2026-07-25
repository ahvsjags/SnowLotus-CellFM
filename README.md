# SnowLotus-CellFM

SnowLotus-CellFM is an editor-ready research release for audited plant single-cell and single-nucleus expression modelling, with a target-species transfer path for *Saussurea involucrata* (Snow Lotus). The repository freezes the best current annotation and embedding checkpoints, the code needed to reproduce smoke training and prediction, and the audit trail that defines exactly which public plant matrices were usable at submission time.

This snapshot is designed for rapid editorial review: it separates validated model and corpus evidence from data-promotion work that is still running on the RTX 5090 server. The `editor-v0.3` package promotes the current best public-expansion embedding checkpoint for immediate submission while the longer continuation queue remains active in the background.

## Editor Snapshot

- Release label: `editor-v0.3`
- Snapshot date: 2026-07-25
- Audited corpus: 48 manifests, 194 readable matrix files and 3,922,340 readable cells
- Matrix integrity: 0 missing files and 0 unreadable files in the audited snapshot
- Best annotation checkpoint: `foundation_5090_pretrain/best.pt`, macro-F1 evidence 0.8121 in the release manifest
- Best embedding checkpoint: `foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/best.pt`, SHA256 `649448b2071816856cd5f92a43985c6d865d115d45d91274db94cb5f9348d577`
- Current best evidence: v0.3 epoch-5 evaluation loss 7.2156 after vocabulary-aware warm-start from the completed v0.2 continuation; v0.3 epoch-6 training is still running and will be superseded only after passing the same audit gates
- Newly promoted public matrices after v0.2 include GSE226826, GSE240098 and GSE240102; the v0.4 plus-corpus continuation is queued behind active v0.3 training on the RTX 5090 server

## What Is Included

- A Python package for plant expression tokenization, masked-modelling training, checkpoint evaluation and prediction.
- Public-corpus manifests and audits that distinguish readable cell-by-gene matrices from unsupported public records.
- Two frozen checkpoint assets for immediate editorial inspection and reproducibility checks.
- Manuscript, cover note, model card, release manifest, data-integrity audit, corpus-provenance audit and benchmark-gap audit.
- Focused regression tests for the core package.

## Evidence Boundary

This release supports the claim that SnowLotus-CellFM is a reproducible plant expression foundation-model scaffold with auditable data provenance, traceable checkpoints and benchmark evidence across public plant matrices.

It does not claim that a reusable public Snow Lotus single-cell matrix already exists. The Snow Lotus component is therefore framed as a target-species transfer and data-gap case. Public discovery identified transcriptomic, genomic and literature support for *S. involucrata*, but no directly reusable public *S. involucrata* cell-by-gene scRNA-seq or snRNA-seq matrix in the current audit.

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
src/                         Core Python package
configs/                     Training and evaluation configurations
scripts/                     Data, training, audit and release scripts
tests/                       Focused regression tests
manuscript/                  Editor-facing manuscript and cover note
release_metadata/            Model card, release manifest and audit summaries
models/                      Git LFS or GitHub Release checkpoint assets
```

## Submission Note

The current GitHub-ready repository is intentionally conservative. It gives editors and reviewers a usable model package now, while leaving additional GEO promotions, v0.3/v0.4 continuation results and authenticated external benchmarks for the next revision rather than presenting them as completed evidence.

## Citation

SnowLotus-CellFM Consortium. SnowLotus-CellFM: an audited plant single-cell foundation-model scaffold for target-species transfer. Editor release v0.3, 2026.
