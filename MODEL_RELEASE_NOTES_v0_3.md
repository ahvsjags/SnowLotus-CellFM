# SnowLotus-CellFM editor-v0.3 model release notes

Generated 2026-07-26 03:38 UTC

## Release Purpose

This release freezes the best current SnowLotus-CellFM assets for an urgent editorial submission. It packages the code, configuration files, manuscript draft, model files, audit metadata and checksum evidence needed to inspect the work without waiting for the longer background training run to finish.

## Frozen Checkpoint Assets

| Asset | Source checkpoint | Intended use | Evidence in this snapshot |
| --- | --- | --- | --- |
| `SnowLotus_CellFM_best_annotation.pt` | `outputs/foundation_5090_pretrain/best.pt` | Immediate annotation and label-transfer demonstrations | Macro-F1 0.8121; SHA256 `ebc95ca58ffede9c9bfd2bb4f056c452b7dc43a0f799cbaf88ff77e4e9d3a4ef` |
| `SnowLotus_CellFM_best_embedding.pt` | `outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/best.pt` | Plant expression representation and downstream transfer experiments | v0.3 epoch-7 eval loss 7.1917; SHA256 `00c1b0a1049c441585ecd7ee03e81d05704bd93100c692cc06f7bdc90f2c034a` |

The active v0.3 run remains in epoch 9, step 32250 of 56022. The release uses the validation-best audited checkpoint rather than the latest in-progress state.

## Corpus and Integrity Evidence

- Data-integrity audit: 70 manifest files and 240 referenced matrix files.
- Readable-cell evidence: 4,544,570 referenced cells across readable matrices.
- Matrix integrity: 0 missing files and 0 unreadable files.
- Public-data recovery since the previous snapshot includes GSE226826, GSE240098 and GSE240102.
- Oversized or incompatible GEO records are retained as unsupported or deferred reports rather than silently promoted.
- Model-release manifest: 16 checkpoints, 0 load errors and approximately 18.7 GB of checkpoint material.

## Checksums

The repository includes `models/SHA256SUMS.txt`. Verify the model files after cloning or downloading:

```bash
cd models
sha256sum -c SHA256SUMS.txt
```

## Evidence Boundary

The annotation checkpoint is the best current asset for immediate cell-type annotation demonstrations. The embedding checkpoint is the best current asset for foundation-model representation and transfer experiments as of this release. Neither asset should be described as a final Snow Lotus-specific model.

Snow Lotus is treated as a target-species transfer case until a reusable primary *Saussurea involucrata* single-cell or single-nucleus matrix is obtained, validated and added to the audit trail.

## Recommended Submission Wording

Use: "SnowLotus-CellFM provides an audited plant single-cell foundation-model scaffold with frozen annotation and embedding checkpoints, public-corpus integrity evidence and a transparent target-species transfer framework for Snow Lotus."

Avoid: "SnowLotus-CellFM is a completed Snow Lotus single-cell atlas" or "SnowLotus-CellFM is fully validated on primary Snow Lotus scRNA-seq data."
