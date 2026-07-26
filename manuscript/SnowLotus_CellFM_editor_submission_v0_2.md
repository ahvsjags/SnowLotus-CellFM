# SnowLotus-CellFM for audited plant single-cell transfer

Editor-facing manuscript draft v0.3, generated 2026-07-26 01:52 UTC

## Abstract

Plant single-cell and single-nucleus transcriptomics now span many species, tissues and stress contexts, but public reuse remains limited by fragmented formats and uneven metadata. This problem is acute for non-model medicinal plants such as *Saussurea involucrata* (Snow Lotus), where transcriptomic and genomic evidence is available but a reusable public single-cell expression matrix has not yet been identified in the current audit. Here we present SnowLotus-CellFM, an audited plant expression foundation-model scaffold for cross-species cell-state representation and target-species transfer. The current editor snapshot audits 68 manifest files, 209 readable matrix files and 4,054,536 referenced cells, with 0 missing and 0 unreadable matrices. The package separates usable expression matrices from inaccessible, incompatible or oversized records, including large GEO RAW archives that require file-level retrieval rather than whole-tar downloading. SnowLotus-CellFM uses transformer-based masked gene modelling over normalized public plant expression matrices, with gene tokens, expression-value bins and sample-level metadata. The frozen embedding asset for this submission is the current v0.3 checkpoint at epoch 7, with validation eval loss 7.1917 and SHA256 `00c1b0a1049c441585ecd7ee03e81d05704bd93100c692cc06f7bdc90f2c034a`. The supervised annotation asset remains the best current label checkpoint, with macro-F1 evidence of 0.8121 and SHA256 `ebc95ca58ffede9c9bfd2bb4f056c452b7dc43a0f799cbaf88ff77e4e9d3a4ef`. This version should be read as a reproducible model and audit resource, not as a completed Snow Lotus atlas. Its immediate contribution is to make plant single-cell foundation modelling inspectable under realistic public-data constraints. Its biological contribution is a transparent route for Snow Lotus transfer once primary or reusable single-cell matrices become available.

## Significance

SnowLotus-CellFM addresses a practical obstacle in plant single-cell biology. Public matrices are valuable but heterogeneous, and many records that appear relevant cannot be used directly for model training. The project therefore combines model development with data triage. It provides an auditable foundation-model scaffold, a frozen pair of checkpoint assets and a clear evidence boundary for Snow Lotus as a target species.

This positioning is deliberate. The manuscript does not claim that a Snow Lotus single-cell atlas has been completed. Instead, it shows how a target-species programme can proceed before a primary Snow Lotus matrix is available: assemble and audit the public plant corpus, train transferable expression representations, document what is missing and make the next experimental step explicit.

## Introduction

Plant single-cell studies are moving from isolated atlases toward reusable, cross-study resources. This shift creates a need for models that can learn from public expression matrices while preserving the provenance of each dataset. In practice, the public record is uneven. Matrix files appear as H5AD objects, 10x H5 files, Matrix Market directories, Seurat RDS files, supplementary tar archives and metadata-only accessions. Some datasets contain clear cell-by-gene expression matrices. Others contain spatial assays, multiome objects, raw archives without directly retrievable members or files that require authenticated access.

These format barriers are not only technical. They shape biological claims. A model trained on poorly audited matrices can look larger than it is, and a target-species paper can accidentally treat supporting transcriptome data as if it were single-cell evidence. Snow Lotus makes this distinction especially important. *S. involucrata* is a high-altitude medicinal plant of biological interest, but the current public-data audit did not identify a directly reusable Snow Lotus scRNA-seq or snRNA-seq expression matrix. Treating that absence honestly strengthens the study, because it prevents overclaiming while preserving a clear route to future target-species adaptation.

SnowLotus-CellFM was built to solve this combined data and modelling problem. It is a plant expression foundation-model scaffold with explicit corpus manifests, matrix-integrity checks, checkpoint manifests and submission-facing release assets. The resource is designed to answer three questions for editors and reviewers. First, what data can actually be read and traced? Second, which model assets are frozen now and how were they evaluated? Third, where does the Snow Lotus claim end, and what work remains before a primary Snow Lotus atlas can be reported?

## Results

### A public plant expression corpus with explicit integrity boundaries

The current editor package audits 68 manifest files and 209 referenced matrix files. All audited manifests are marked ready, with 0 missing files and 0 unreadable matrix files in the current integrity report. Across readable matrices, the package records 4,054,536 referenced cells. The corpus includes established plant systems such as *Arabidopsis*, rice, maize, wheat, tomato, soybean, *Medicago*, *Populus*, *Camellia* and several additional public scPlantDB-derived studies.

The audit is intentionally conservative. A record is promoted into the training corpus only when a readable expression matrix can be identified, converted and referenced by a manifest. Unsupported records are retained as evidence rather than silently discarded. Recent recovery work added usable matrix manifests for GSE226826, GSE240098 and GSE240102. In contrast, several large or incompatible GEO records are represented by header-only manifests and structured unsupported reports. This choice keeps the corpus reproducible and protects the training queue from multi-gigabyte whole-archive downloads that are unlikely to improve the editor snapshot on the submission timescale.

### Snow Lotus is treated as a transfer target, not an overclaimed source atlas

The Snow Lotus evidence audit searched public resources for *S. involucrata*, Snow Lotus and single-cell-related terms. It recovered transcriptomic, genomic and literature support, including reports relevant to Snow Lotus biology, but it did not identify a directly reusable public Snow Lotus single-cell matrix. The manuscript therefore frames Snow Lotus as a target-species transfer case. This is a stronger and more defensible claim than presenting the model as a completed Snow Lotus atlas.

This evidence boundary also clarifies the next biological experiment. Once a primary Snow Lotus scRNA-seq or snRNA-seq matrix is generated or released, the current model can be used for representation learning, label transfer, marker-assisted annotation and cross-species comparison. The present release prepares that workflow and records the public-data gap that motivates it.

### Transformer masked modelling produces a frozen v0.3 embedding asset

SnowLotus-CellFM represents each cell through highly expressed genes, binned expression values and metadata fields such as species, tissue, sample and batch. The masked-modelling run uses library-size normalization to 10,000 counts, log1p transformation, a maximum of 1,536 genes per cell, masked gene prediction and auxiliary expression-value prediction. The active v0.3 configuration uses a 512-dimensional hidden state, 10 transformer layers, 8 attention heads, a 1,536-dimensional feed-forward block, dropout of 0.10, 128 expression-value bins, gradient checkpointing and bf16 mixed precision.

For the editor snapshot, the frozen embedding asset is the v0.3 best checkpoint from `outputs/foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm/best.pt`. It reached validation eval loss 7.1917 at epoch 7, and its SHA256 is `00c1b0a1049c441585ecd7ee03e81d05704bd93100c692cc06f7bdc90f2c034a`. Training remains active in epoch 8, at step 31750 of 56022 batches per epoch at the time of this manuscript refresh. The package freezes the best audited checkpoint rather than the most recent in-progress state, so the submitted model asset is reproducible even while background training continues.

### Annotation and benchmark assets define the immediate utility

The supervised annotation checkpoint remains the best current label-release asset. It is stored as `models/SnowLotus_CellFM_best_annotation.pt`, has SHA256 `ebc95ca58ffede9c9bfd2bb4f056c452b7dc43a0f799cbaf88ff77e4e9d3a4ef` and carries macro-F1 evidence of 0.8121 in the release manifest. The embedding checkpoint is stored as `models/SnowLotus_CellFM_best_embedding.pt`. The current model-release manifest lists 16 checkpoints, 0 checkpoint load errors and approximately 18.7 GB of tracked checkpoint material across training runs.

Internal evidence includes supervised checkpoint metrics, strict split audits, centroid baselines and training-curve summaries. External comparison evidence is present as a staged benchmark track. Seurat label transfer has been run on a public-sprint test set, and scPlantLLM-style embedding probes are available as additional reference points. scPlantAnnotate remains an authenticated benchmark path rather than a completed comparable metric in this editor snapshot.

### The release is designed for editorial inspection

The release directory is organized as a GitHub-ready repository. It includes source code, configuration files, generated scripts, tests, manuscript files, release metadata, model cards, data audits, training summaries and SHA256 checksums for the frozen model assets. Large checkpoints are handled through Git LFS or release-asset upload, while the full archive with models is also preserved for immediate transfer.

This structure is useful because the project is still improving. Background training and public-data promotion continue on the RTX 5090 server, but the submitted snapshot is fixed. Editors can inspect the exact assets used for the current claims, while later revisions can update the same audit trail with stronger checkpoints, additional validated public matrices and authenticated external benchmark results.

## Methods Summary

### Public data assembly and triage

Public plant single-cell resources were assembled from static dataset targets, scPlantDB-derived H5AD files and reviewed GEO candidates. Each usable dataset is represented by a tab-separated manifest with local matrix paths and dataset metadata. H5AD, 10x H5, Matrix Market, RDS and raw-tar derived files were inspected or converted into compatible matrix objects when possible. Records without a readable cell-by-gene expression matrix were retained as unsupported or deferred evidence.

Large GEO RAW archives are managed by an explicit guard. The active queue checks expected content length before whole-tar retrieval and defers archives above the configured threshold. This prevents a single 8 GB to 55 GB archive from blocking training or exhausting disk space. Deferred records remain visible through structured reports and header-only manifests, so their exclusion from the training corpus is auditable.

### Model training

Expression matrices were normalized, log transformed and converted into gene-token sequences with expression-value bins. The public masked-modelling continuation trained a transformer encoder using masked gene prediction and a small auxiliary value-prediction loss. Training was run on an RTX 5090 with persistent tmux supervision, checkpoint logging and package-refresh watchdogs. The submitted embedding checkpoint is the validation-best v0.3 asset, not the active latest checkpoint.

### Evaluation and release validation

Evaluation combines checkpoint loading, validation loss, supervised annotation metrics, split audits and external-tool readiness reports. The release package includes SHA256 checksums for frozen model files and a test suite for the packaged code path. Model assets are separated into annotation and embedding checkpoints because they serve different immediate uses.

## Limitations and Next Revision Plan

The principal biological limitation is the absence of an identified reusable public Snow Lotus single-cell matrix. This limits the current Snow Lotus claim to target-species transfer preparation and data-gap documentation. The principal computational limitation is that some external benchmark tracks and GEO promotions remain active. These limitations are recorded in the release rather than hidden.

The next revision should add three items when they pass audit: a stronger completed v0.3 or v0.4 embedding checkpoint, additional validated public matrices from the promotion queue and authenticated external benchmark results. A primary Snow Lotus matrix would convert the target-species transfer framework into a direct Snow Lotus cell-state analysis.

## Conclusion

SnowLotus-CellFM provides an audited plant single-cell foundation-model scaffold under realistic public-data constraints. The current editor snapshot freezes usable model assets, records the corpus boundary and states the Snow Lotus evidence limit plainly. Its immediate value is a reproducible plant expression representation and annotation resource. Its longer-term value is a transparent path for adapting that resource to *Saussurea involucrata* once primary single-cell data are available.
