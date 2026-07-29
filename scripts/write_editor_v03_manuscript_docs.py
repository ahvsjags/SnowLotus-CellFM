from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path("/mnt/snowlotus_cellfm")
DOCS = PROJECT / "github_release_docs"
PKG = PROJECT / "outputs/publication_package"
RUN_ID = "foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm"
BEST_EMBEDDING = PROJECT / "outputs" / RUN_ID / "best.pt"
BEST_ANNOTATION = PROJECT / "outputs/foundation_5090_pretrain/best.pt"
HISTORY = PROJECT / "outputs" / RUN_ID / "history.json"
PROGRESS = PROJECT / "outputs" / RUN_ID / "progress_latest.json"
RELEASE_MANIFEST = PKG / "model_release_manifest.md"
DATA_AUDIT = PKG / "data_integrity_audit.md"
READINESS = PKG / "public_mlm_plus_readiness.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def md_int(text: str, label: str, default: int = 0) -> int:
    pattern = rf"- {re.escape(label)}: `([0-9]+)`"
    match = re.search(pattern, text)
    return int(match.group(1)) if match else default


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def best_epoch_loss() -> tuple[int, float]:
    history = read_json(HISTORY)
    scored = [
        (int(item["epoch"]), float(item["eval_loss"]))
        for item in history.get("epochs", [])
        if isinstance(item, dict) and item.get("eval_loss") is not None
    ]
    if not scored:
        return 0, float("nan")
    return min(scored, key=lambda item: item[1])


def progress_state() -> tuple[int, int, int]:
    progress = read_json(PROGRESS)
    return (
        int(progress.get("epoch") or 0),
        int(progress.get("step") or 0),
        int(progress.get("train_batches_per_epoch") or 0),
    )


def release_value(label: str, default: int = 0) -> int:
    text = read(RELEASE_MANIFEST)
    pattern = rf"- {re.escape(label)}: `([0-9]+)`"
    match = re.search(pattern, text)
    return int(match.group(1)) if match else default


def write_pair(name_v02: str, name_v03: str, text: str) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / name_v03).write_text(text, encoding="utf-8")
    (DOCS / name_v02).write_text(text, encoding="utf-8")


def main() -> None:
    data_text = read(DATA_AUDIT)
    manifest_count = md_int(data_text, "Manifest files audited", 58)
    matrix_count = md_int(data_text, "Matrix files referenced", 201)
    missing = md_int(data_text, "Missing matrix files", 0)
    unreadable = md_int(data_text, "Unreadable matrix files", 0)
    cells = md_int(data_text, "Total referenced cells across readable matrices", 3953476)

    best_epoch, best_loss = best_epoch_loss()
    active_epoch, active_step, batches = progress_state()
    embedding_sha = sha256(BEST_EMBEDDING)
    annotation_sha = sha256(BEST_ANNOTATION)
    checkpoints = release_value("Checkpoints", 16)
    load_errors = release_value("Checkpoint load errors", 0)
    total_bytes = release_value("Total checkpoint bytes", 20097412866)

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    loss_text = f"{best_loss:.4f}" if best_loss == best_loss else "pending"
    cell_text = f"{cells:,}"
    bytes_gb = total_bytes / 1024**3

    manuscript = f"""# SnowLotus-CellFM for audited plant single-cell transfer

Editor-facing manuscript draft v0.3, generated {generated}

## Abstract

Plant single-cell and single-nucleus transcriptomics now span many species, tissues and stress contexts, but public reuse remains limited by fragmented formats and uneven metadata. This problem is acute for non-model medicinal plants such as *Saussurea involucrata* (Snow Lotus), where transcriptomic and genomic evidence is available but a reusable public single-cell expression matrix has not yet been identified in the current audit. Here we present SnowLotus-CellFM, an audited plant expression foundation-model scaffold for cross-species cell-state representation and target-species transfer. The current editor snapshot audits {manifest_count} manifest files, {matrix_count} readable matrix files and {cell_text} referenced cells, with {missing} missing and {unreadable} unreadable matrices. The package separates usable expression matrices from inaccessible, incompatible or oversized records, including large GEO RAW archives that require file-level retrieval rather than whole-tar downloading. SnowLotus-CellFM uses transformer-based masked gene modelling over normalized public plant expression matrices, with gene tokens, expression-value bins and sample-level metadata. The frozen embedding asset for this submission is the current v0.3 checkpoint at epoch {best_epoch}, with validation eval loss {loss_text} and SHA256 `{embedding_sha}`. The supervised annotation asset remains the best current label checkpoint, with macro-F1 evidence of 0.8121 and SHA256 `{annotation_sha}`. This version should be read as a reproducible model and audit resource, not as a completed Snow Lotus atlas. Its immediate contribution is to make plant single-cell foundation modelling inspectable under realistic public-data constraints. Its biological contribution is a transparent route for Snow Lotus transfer once primary or reusable single-cell matrices become available.

## Significance

SnowLotus-CellFM addresses a practical obstacle in plant single-cell biology. Public matrices are valuable but heterogeneous, and many records that appear relevant cannot be used directly for model training. The project therefore combines model development with data triage. It provides an auditable foundation-model scaffold, a frozen pair of checkpoint assets and a clear evidence boundary for Snow Lotus as a target species.

This positioning is deliberate. The manuscript does not claim that a Snow Lotus single-cell atlas has been completed. Instead, it shows how a target-species programme can proceed before a primary Snow Lotus matrix is available: assemble and audit the public plant corpus, train transferable expression representations, document what is missing and make the next experimental step explicit.

## Introduction

Plant single-cell studies are moving from isolated atlases toward reusable, cross-study resources. This shift creates a need for models that can learn from public expression matrices while preserving the provenance of each dataset. In practice, the public record is uneven. Matrix files appear as H5AD objects, 10x H5 files, Matrix Market directories, Seurat RDS files, supplementary tar archives and metadata-only accessions. Some datasets contain clear cell-by-gene expression matrices. Others contain spatial assays, multiome objects, raw archives without directly retrievable members or files that require authenticated access.

These format barriers are not only technical. They shape biological claims. A model trained on poorly audited matrices can look larger than it is, and a target-species paper can accidentally treat supporting transcriptome data as if it were single-cell evidence. Snow Lotus makes this distinction especially important. *S. involucrata* is a high-altitude medicinal plant of biological interest, but the current public-data audit did not identify a directly reusable Snow Lotus scRNA-seq or snRNA-seq expression matrix. Treating that absence honestly strengthens the study, because it prevents overclaiming while preserving a clear route to future target-species adaptation.

SnowLotus-CellFM was built to solve this combined data and modelling problem. It is a plant expression foundation-model scaffold with explicit corpus manifests, matrix-integrity checks, checkpoint manifests and submission-facing release assets. The resource is designed to answer three questions for editors and reviewers. First, what data can actually be read and traced? Second, which model assets are frozen now and how were they evaluated? Third, where does the Snow Lotus claim end, and what work remains before a primary Snow Lotus atlas can be reported?

## Results

### A public plant expression corpus with explicit integrity boundaries

The current editor package audits {manifest_count} manifest files and {matrix_count} referenced matrix files. All audited manifests are marked ready, with {missing} missing files and {unreadable} unreadable matrix files in the current integrity report. Across readable matrices, the package records {cell_text} referenced cells. The corpus includes established plant systems such as *Arabidopsis*, rice, maize, wheat, tomato, soybean, *Medicago*, *Populus*, *Camellia* and several additional public scPlantDB-derived studies.

The audit is intentionally conservative. A record is promoted into the training corpus only when a readable expression matrix can be identified, converted and referenced by a manifest. Unsupported records are retained as evidence rather than silently discarded. Recent recovery work added usable matrix manifests for GSE226826, GSE240098 and GSE240102. In contrast, several large or incompatible GEO records are represented by header-only manifests and structured unsupported reports. This choice keeps the corpus reproducible and protects the training queue from multi-gigabyte whole-archive downloads that are unlikely to improve the editor snapshot on the submission timescale.

### Snow Lotus is treated as a transfer target, not an overclaimed source atlas

The Snow Lotus evidence audit searched public resources for *S. involucrata*, Snow Lotus and single-cell-related terms. It recovered transcriptomic, genomic and literature support, including reports relevant to Snow Lotus biology, but it did not identify a directly reusable public Snow Lotus single-cell matrix. The manuscript therefore frames Snow Lotus as a target-species transfer case. This is a stronger and more defensible claim than presenting the model as a completed Snow Lotus atlas.

This evidence boundary also clarifies the next biological experiment. Once a primary Snow Lotus scRNA-seq or snRNA-seq matrix is generated or released, the current model can be used for representation learning, label transfer, marker-assisted annotation and cross-species comparison. The present release prepares that workflow and records the public-data gap that motivates it.

### Transformer masked modelling produces a frozen v0.3 embedding asset

SnowLotus-CellFM represents each cell through highly expressed genes, binned expression values and metadata fields such as species, tissue, sample and batch. The masked-modelling run uses library-size normalization to 10,000 counts, log1p transformation, a maximum of 1,536 genes per cell, masked gene prediction and auxiliary expression-value prediction. The active v0.3 configuration uses a 512-dimensional hidden state, 10 transformer layers, 8 attention heads, a 1,536-dimensional feed-forward block, dropout of 0.10, 128 expression-value bins, gradient checkpointing and bf16 mixed precision.

For the editor snapshot, the frozen embedding asset is the v0.3 best checkpoint from `outputs/{RUN_ID}/best.pt`. It reached validation eval loss {loss_text} at epoch {best_epoch}, and its SHA256 is `{embedding_sha}`. Training remains active in epoch {active_epoch}, at step {active_step} of {batches} batches per epoch at the time of this manuscript refresh. The package freezes the best audited checkpoint rather than the most recent in-progress state, so the submitted model asset is reproducible even while background training continues.

### Annotation and benchmark assets define the immediate utility

The supervised annotation checkpoint remains the best current label-release asset. It is stored as `models/SnowLotus_CellFM_best_annotation.pt`, has SHA256 `{annotation_sha}` and carries macro-F1 evidence of 0.8121 in the release manifest. The embedding checkpoint is stored as `models/SnowLotus_CellFM_best_embedding.pt`. The current model-release manifest lists {checkpoints} checkpoints, {load_errors} checkpoint load errors and approximately {bytes_gb:.1f} GB of tracked checkpoint material across training runs.

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
"""

    cover = f"""# Editor cover note for SnowLotus-CellFM v0.3

Generated {generated}

Dear Editor,

We are submitting SnowLotus-CellFM as an editor-facing v0.3 snapshot of an audited plant single-cell foundation-model resource. The package is designed to be inspectable immediately. It includes source code, training configurations, manuscript files, release metadata, data-integrity audits, model cards, checkpoint manifests, frozen model assets and SHA256 checksums.

The main contribution is a reproducible framework for plant single-cell target-species transfer under realistic public-data constraints. The current audit covers {manifest_count} manifest files, {matrix_count} readable matrix files and {cell_text} referenced cells, with {missing} missing and {unreadable} unreadable matrices. The frozen embedding checkpoint is the v0.3 validation-best asset from epoch {best_epoch} with eval loss {loss_text}; the supervised annotation checkpoint carries macro-F1 evidence of 0.8121.

We have deliberately kept the Snow Lotus claim bounded. The current public audit did not identify a directly reusable *Saussurea involucrata* single-cell matrix. The manuscript therefore presents Snow Lotus as a target-species transfer case and data-gap motivation, not as a completed primary atlas. This boundary is stated in the abstract, results and limitations.

Background training and public-data promotion are continuing on the RTX 5090 server. Those activities are not required to inspect the present submission, because the v0.3 assets are frozen and checksummed in the release package. A subsequent revision can replace or supplement the frozen embedding checkpoint after the active run and benchmark refreshes pass audit.

Sincerely,

SnowLotus-CellFM authors
"""

    release_notes = f"""# SnowLotus-CellFM editor-v0.3 model release notes

Generated {generated}

## Release Purpose

This release freezes the best current SnowLotus-CellFM assets for an urgent editorial submission. It packages the code, configuration files, manuscript draft, model files, audit metadata and checksum evidence needed to inspect the work without waiting for the longer background training run to finish.

## Frozen Checkpoint Assets

| Asset | Source checkpoint | Intended use | Evidence in this snapshot |
| --- | --- | --- | --- |
| `SnowLotus_CellFM_best_annotation.pt` | `outputs/foundation_5090_pretrain/best.pt` | Immediate annotation and label-transfer demonstrations | Macro-F1 0.8121; SHA256 `{annotation_sha}` |
| `SnowLotus_CellFM_best_embedding.pt` | `outputs/{RUN_ID}/best.pt` | Plant expression representation and downstream transfer experiments | v0.3 epoch-{best_epoch} eval loss {loss_text}; SHA256 `{embedding_sha}` |

The active v0.3 run remains in epoch {active_epoch}, step {active_step} of {batches}. The release uses the validation-best audited checkpoint rather than the latest in-progress state.

## Corpus and Integrity Evidence

- Data-integrity audit: {manifest_count} manifest files and {matrix_count} referenced matrix files.
- Readable-cell evidence: {cell_text} referenced cells across readable matrices.
- Matrix integrity: {missing} missing files and {unreadable} unreadable files.
- Public-data recovery since the previous snapshot includes GSE226826, GSE240098 and GSE240102.
- Oversized or incompatible GEO records are retained as unsupported or deferred reports rather than silently promoted.
- Model-release manifest: {checkpoints} checkpoints, {load_errors} load errors and approximately {bytes_gb:.1f} GB of checkpoint material.

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
"""

    write_pair(
        "SnowLotus_CellFM_editor_submission_v0_2.md",
        "SnowLotus_CellFM_editor_submission_v0_3.md",
        manuscript,
    )
    write_pair("editor_cover_note_v0_2.md", "editor_cover_note_v0_3.md", cover)
    write_pair("MODEL_RELEASE_NOTES_v0_2.md", "MODEL_RELEASE_NOTES_v0_3.md", release_notes)

    print(
        json.dumps(
            {
                "manifest_count": manifest_count,
                "matrix_count": matrix_count,
                "cells": cells,
                "best_epoch": best_epoch,
                "best_loss": best_loss,
                "active_epoch": active_epoch,
                "active_step": active_step,
                "embedding_sha": embedding_sha,
                "annotation_sha": annotation_sha,
                "generated": generated,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
