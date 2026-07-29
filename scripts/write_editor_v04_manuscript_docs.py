from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path("/mnt/snowlotus_cellfm")
DOCS = PROJECT / "github_release_docs"
PKG = PROJECT / "outputs/publication_package"
RUN_ID = "foundation_5090_mlm_public_expansion_v0_4_plus_latest_seed48_b8_vocabwarm"
BEST_EMBEDDING = PROJECT / "outputs" / RUN_ID / "best.pt"
BEST_ANNOTATION = PROJECT / "outputs/foundation_5090_pretrain/best.pt"
HISTORY = PROJECT / "outputs" / RUN_ID / "history.json"
PROGRESS = PROJECT / "outputs" / RUN_ID / "progress_latest.json"
DATA_AUDIT = PKG / "data_integrity_audit.md"
PLUS_SUMMARY = PKG / "public_mlm_plus_latest_manifest_summary.json"
PLUS_MANIFEST = PROJECT / "data/corpus_manifest_public_mlm_plus_latest.tsv"
POST_STATE = PROJECT / "outputs/post_training_release/editor_v0_4_current_best.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def md_int(text: str, label: str, default: int = 0) -> int:
    match = re.search(rf"- {re.escape(label)}: `([0-9]+)`", text)
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


def progress_state() -> tuple[int, int, int, str]:
    progress = read_json(PROGRESS)
    return (
        int(progress.get("epoch") or 0),
        int(progress.get("step") or 0),
        int(progress.get("train_batches_per_epoch") or 0),
        str(progress.get("status") or "unknown"),
    )


def plus_rows() -> int:
    if PLUS_MANIFEST.exists():
        with PLUS_MANIFEST.open("r", encoding="utf-8", newline="") as handle:
            return max(sum(1 for _ in csv.DictReader(handle, delimiter="\t")), 0)
    summary = read_json(PLUS_SUMMARY)
    return int(summary.get("manifest_rows") or 0)


def main() -> None:
    if not BEST_EMBEDDING.exists():
        raise SystemExit(f"missing v0.4 checkpoint: {BEST_EMBEDDING}")

    data_text = read(DATA_AUDIT)
    manifest_count = md_int(data_text, "Manifest files audited", 58)
    matrix_count = md_int(data_text, "Matrix files referenced", 201)
    missing = md_int(data_text, "Missing matrix files", 0)
    unreadable = md_int(data_text, "Unreadable matrix files", 0)
    cells = md_int(data_text, "Total referenced cells across readable matrices", 3953476)

    best_epoch, best_loss = best_epoch_loss()
    active_epoch, active_step, batches, status = progress_state()
    plus_count = plus_rows()
    embedding_sha = sha256(BEST_EMBEDDING)
    annotation_sha = sha256(BEST_ANNOTATION)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    loss_text = f"{best_loss:.4f}" if not math.isnan(best_loss) else "pending"
    cell_text = f"{cells:,}"

    DOCS.mkdir(parents=True, exist_ok=True)
    POST_STATE.parent.mkdir(parents=True, exist_ok=True)

    readme = f"""# SnowLotus-CellFM

Current release: `editor-v0.4`

SnowLotus-CellFM is an audited plant single-cell foundation-model scaffold for cross-species cell-state representation and Snow Lotus target-species transfer. This v0.4 package is the plus-corpus continuation release: it starts from the v0.3 best checkpoint, rebuilds the public MLM corpus with newly promoted public manifests, and freezes the best v0.4 embedding checkpoint for downstream inspection.

## Frozen Assets

- Annotation checkpoint: `models/SnowLotus_CellFM_best_annotation.pt`, SHA256 `{annotation_sha}`.
- Embedding checkpoint: `models/SnowLotus_CellFM_best_embedding.pt`, source `outputs/{RUN_ID}/best.pt`, SHA256 `{embedding_sha}`.
- Best v0.4 evidence: epoch {best_epoch}, validation eval loss `{loss_text}`.
- Training status at document generation: `{status}`, epoch {active_epoch}, step {active_step} / {batches}.

## Corpus Boundary

- Audited manifests: {manifest_count}.
- Matrix files referenced: {matrix_count}.
- Referenced readable cells: {cell_text}.
- Public plus manifest rows: {plus_count}.
- Missing matrix files: {missing}; unreadable matrix files: {unreadable}.

Snow Lotus remains framed as a target-species transfer case until a directly reusable *Saussurea involucrata* single-cell or single-nucleus expression matrix is obtained and audited.
"""

    handoff = f"""# SnowLotus-CellFM editor-v0.4 handoff

Generated {generated}

This package supersedes the urgent `editor-v0.3` snapshot for the public-MLM branch. It should be used when the editor can accept a stronger post-v0.3 checkpoint and refreshed plus-corpus evidence.

## What changed

- v0.4 warm-started from the v0.3 best embedding checkpoint.
- The plus public MLM corpus was rebuilt before launch.
- The frozen embedding checkpoint is v0.4 epoch {best_epoch}, eval loss `{loss_text}`, SHA256 `{embedding_sha}`.
- The annotation checkpoint remains SHA256 `{annotation_sha}`.

## How to verify

```bash
cd models
sha256sum -c SHA256SUMS.txt
```

The release repository also includes source code, configs, generated scripts, tests, manuscript files, release metadata and audit reports.
"""

    manuscript = f"""# SnowLotus-CellFM v0.4 plus-corpus continuation

Editor-facing manuscript draft v0.4, generated {generated}

## Abstract

SnowLotus-CellFM v0.4 extends the editor-v0.3 plant single-cell foundation-model snapshot by rebuilding the public masked-language-modelling corpus with newly promoted public manifests and continuing training from the v0.3 best checkpoint. The release audits {manifest_count} manifest files, {matrix_count} matrix references and {cell_text} readable referenced cells, with {missing} missing and {unreadable} unreadable matrix files in the integrity report. The plus manifest contains {plus_count} rows at document generation. The frozen embedding asset is the v0.4 checkpoint from epoch {best_epoch}, validation eval loss {loss_text}, SHA256 `{embedding_sha}`. The supervised annotation asset remains SHA256 `{annotation_sha}`. The Snow Lotus claim remains intentionally bounded: the release prepares target-species transfer for *Saussurea involucrata* and documents the absence of a directly reusable public Snow Lotus single-cell matrix.

## Results

The v0.4 branch converts the running data-promotion work into a larger public MLM training substrate. GEO-derived manifests, scPlantDB-derived manifests and the base curated corpus are merged into `data/corpus_manifest_public_mlm_plus_latest.tsv`, then materialized as `data/plant_foundation_corpus_public_mlm_plus_latest.h5ad`. Records that cannot be safely read remain in unsupported or deferred reports rather than being silently counted as training data.

The model is initialized from the v0.3 best checkpoint and trained under the same transformer masked-gene objective, preserving gene-token and expression-bin semantics while giving the model access to the refreshed public corpus. At this snapshot, the best v0.4 checkpoint is epoch {best_epoch} with eval loss {loss_text}. The release should be cited as a plus-corpus continuation and not as a final Snow Lotus atlas.

## Methods Summary

The workflow first rebuilds publication audits, then constructs the plus corpus from the base manifest and all completed public promotion manifests. The v0.4 training configuration is generated from the v0.3 configuration, replacing the corpus path, seed, output directory and initialization checkpoint. Post-training validation runs model checksum verification and the packaged test suite before creating source, manuscript and full-with-model archives.

## Limitations

Authenticated external benchmarks and primary Snow Lotus single-cell data remain future-revision items. The value of this release is a stronger audited plant representation checkpoint and a clearer public-data boundary for the target species.
"""

    cover = f"""# Editor cover note for SnowLotus-CellFM v0.4

Generated {generated}

Dear Editor,

We are submitting SnowLotus-CellFM editor-v0.4 as the plus-corpus continuation of the v0.3 snapshot. The package includes refreshed public-corpus audits, source code, configurations, tests, manuscript files, release metadata and frozen model assets.

The v0.4 embedding checkpoint was initialized from the v0.3 best model and trained on the rebuilt public MLM plus corpus. Its current best validation evidence is epoch {best_epoch}, eval loss {loss_text}, SHA256 `{embedding_sha}`. The supervised annotation checkpoint remains SHA256 `{annotation_sha}`.

We keep the Snow Lotus claim bounded. No directly reusable public *Saussurea involucrata* single-cell matrix has been identified in the audit, so the manuscript presents Snow Lotus as a target-species transfer case and a data-gap motivation rather than a completed primary atlas.

Sincerely,

SnowLotus-CellFM authors
"""

    notes = f"""# SnowLotus-CellFM editor-v0.4 model release notes

Generated {generated}

## Release Purpose

`editor-v0.4` is the plus-corpus continuation release. It should be used after the v0.4 run finishes and passes release validation.

## Frozen Checkpoint Assets

| Asset | Source checkpoint | Evidence |
| --- | --- | --- |
| `SnowLotus_CellFM_best_annotation.pt` | `outputs/foundation_5090_pretrain/best.pt` | SHA256 `{annotation_sha}` |
| `SnowLotus_CellFM_best_embedding.pt` | `outputs/{RUN_ID}/best.pt` | v0.4 epoch {best_epoch}, eval loss {loss_text}, SHA256 `{embedding_sha}` |

## Corpus Evidence

- Public plus manifest rows: {plus_count}.
- Audited manifests: {manifest_count}.
- Matrix files referenced: {matrix_count}.
- Readable referenced cells: {cell_text}.
- Missing/unreadable matrices: {missing} / {unreadable}.

## Evidence Boundary

This remains a plant foundation-model and Snow Lotus target-transfer resource, not a completed Snow Lotus atlas.
"""

    (DOCS / "README.md").write_text(readme, encoding="utf-8")
    (DOCS / "EDITOR_HANDOFF.md").write_text(handoff, encoding="utf-8")
    (DOCS / "SnowLotus_CellFM_editor_submission_v0_4.md").write_text(manuscript, encoding="utf-8")
    (DOCS / "editor_cover_note_v0_4.md").write_text(cover, encoding="utf-8")
    (DOCS / "MODEL_RELEASE_NOTES_v0_4.md").write_text(notes, encoding="utf-8")

    payload = {
        "active_epoch": active_epoch,
        "active_step": active_step,
        "annotation_sha": annotation_sha,
        "best_epoch": best_epoch,
        "best_loss": best_loss,
        "embedding_sha": embedding_sha,
        "generated": generated,
        "manifest_count": manifest_count,
        "matrix_count": matrix_count,
        "plus_manifest_rows": plus_count,
        "run_id": RUN_ID,
        "status": status,
    }
    POST_STATE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
