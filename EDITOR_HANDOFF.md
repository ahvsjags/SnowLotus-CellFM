# SnowLotus-CellFM editor handoff

## One-paragraph position

SnowLotus-CellFM is submitted as an audited plant single-cell foundation-model scaffold for cell-state representation, annotation benchmarking and target-species transfer to *Saussurea involucrata* (Snow Lotus). The current `editor-v0.3` release is intentionally conservative: it freezes the strongest validated annotation checkpoint and the current best public-expansion embedding checkpoint available on 2026-07-25, documents the public plant matrix corpus that is actually readable, and treats Snow Lotus as a target-species transfer case because no directly reusable public Snow Lotus scRNA-seq or snRNA-seq matrix was found in the audit.

## Frozen editor evidence

- Audited corpus: 48 manifests, 194 readable matrix files and 3,922,340 readable cells.
- Matrix integrity: 0 missing files and 0 unreadable referenced matrices.
- Annotation checkpoint: `models/SnowLotus_CellFM_best_annotation.pt`, macro-F1 evidence 0.8121.
- Embedding checkpoint: `models/SnowLotus_CellFM_best_embedding.pt`, promoted from `outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/best.pt`; current best v0.3 epoch-5 eval loss 7.2156, SHA256 `649448b2071816856cd5f92a43985c6d865d115d45d91274db94cb5f9348d577`.
- Data expansion after v0.2: GSE226826, GSE240098 and GSE240102 were recovered into usable NPZ/manifests; v0.4 plus-corpus training is queued behind v0.3.
- Release manifest: 11 checkpoint entries with no load errors.
- External references: Seurat label transfer and scPlantLLM-style embedding probes are included; scPlantAnnotate remains an authenticated benchmark pending final access.

## What to tell the editor

This is not being oversold as a completed Snow Lotus single-cell atlas. It is a reproducible plant single-cell modelling resource plus a transparent transfer framework for a target medicinal plant with limited public single-cell data. The package includes manuscript text, cover note, model card, release manifest, data-integrity audit, corpus-provenance audit, benchmark-gap audit, environment snapshot and SHA256 checksums for the frozen model assets.

## Repository publication status

The GitHub-ready repository is staged at `/root/snowlotus-cellfm/outputs/github_release/SnowLotus-CellFM` on the RTX 5090 server. The two frozen model files are present in `models/` and verified against `models/SHA256SUMS.txt`. The completed v0.2 run remains the stable baseline; `editor-v0.3` promotes the stronger v0.3 best checkpoint for the submission package while training continues. GitHub publication is blocked only by repository/key authorization: GitHub currently rejects the server deploy key with `Permission denied (publickey)`. Once the repository `ahvsjags/SnowLotus-CellFM` exists and the deploy key in `GITHUB_PUSH_INSTRUCTIONS.md` has write access, the staged repository can be pushed as-is.

## Next revision

The next revision should add GEO promotions that pass the matrix-integrity gate, complete authenticated external benchmarks, refresh the release manifest and model card, and replace local repository placeholders with stable public URLs.
