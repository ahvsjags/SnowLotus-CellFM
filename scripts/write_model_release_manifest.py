from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CheckpointRecord:
    run_id: str
    checkpoint_kind: str
    path: str
    status: str
    bytes: int
    sha256: str
    checkpoint_epoch: int | None
    stage: str
    model_d_model: int | None
    model_layers: int | None
    model_heads: int | None
    gene_vocab_size: int
    fine_vocab_size: int
    coarse_vocab_size: int
    species_vocab_size: int
    tissue_vocab_size: int
    train_loss: float | None
    eval_loss: float | None
    fine_macro_f1: float | None
    coarse_macro_f1: float | None
    history_epochs: int
    config: str
    release_note: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def metric(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    return float(value) if isinstance(value, int | float) else None


def checkpoint_status(fine_vocab_size: int, coarse_vocab_size: int, stage: str) -> tuple[str, str]:
    if fine_vocab_size > 1 and coarse_vocab_size > 1:
        return "label_release_candidate", "Supervised labels available for annotation."
    if stage == "pretrain":
        return "embedding_release_candidate", "Pretraining checkpoint: embeddings/MLM evidence, not label annotation."
    return "model_release_candidate", "Checkpoint readable, but label readiness needs manual review."


def summarize_checkpoint(root: Path, path: Path) -> CheckpointRecord:
    import torch

    run_dir = path.parent
    history = read_json(run_dir / "history.json") or {}
    config_path = run_dir / "config.resolved.json"
    config = read_json(config_path) or {}
    payload = torch.load(path, map_location="cpu", weights_only=False)
    model_config = payload.get("model_config") or {}
    exp_config = payload.get("experiment_config") or {}
    train_config = exp_config.get("train") or config.get("train") or {}
    metrics = payload.get("metrics") or {}
    fine_vocab_size = len(payload.get("fine_vocab") or [])
    coarse_vocab_size = len(payload.get("coarse_vocab") or [])
    stage = str(train_config.get("stage") or "")
    status, release_note = checkpoint_status(fine_vocab_size, coarse_vocab_size, stage)
    return CheckpointRecord(
        run_id=run_dir.name,
        checkpoint_kind=path.stem,
        path=relpath(root, path),
        status=status,
        bytes=path.stat().st_size,
        sha256=sha256_file(path),
        checkpoint_epoch=payload.get("epoch"),
        stage=stage,
        model_d_model=model_config.get("d_model"),
        model_layers=model_config.get("n_layers"),
        model_heads=model_config.get("n_heads"),
        gene_vocab_size=len(payload.get("gene_vocab") or []),
        fine_vocab_size=fine_vocab_size,
        coarse_vocab_size=coarse_vocab_size,
        species_vocab_size=len(payload.get("species_vocab") or []),
        tissue_vocab_size=len(payload.get("tissue_vocab") or []),
        train_loss=metric(metrics, "train_loss"),
        eval_loss=metric(metrics, "eval_loss"),
        fine_macro_f1=metric(metrics, "fine_macro_f1"),
        coarse_macro_f1=metric(metrics, "coarse_macro_f1"),
        history_epochs=len(history.get("epochs") or []),
        config=relpath(root, config_path) if config_path.exists() else "",
        release_note=release_note,
    )


def collect_manifest(project_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    records: list[CheckpointRecord] = []
    errors: list[dict[str, str]] = []
    paths = sorted(
        {path for pattern in ["outputs/*/best.pt", "outputs/*/latest.pt"] for path in root.glob(pattern)},
        key=lambda item: item.as_posix(),
    )
    for path in paths:
        try:
            records.append(summarize_checkpoint(root, path))
        except Exception as exc:  # pragma: no cover - corrupted checkpoints are environment-specific
            errors.append(
                {
                    "path": relpath(root, path),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    status_counts: dict[str, int] = {}
    for record in records:
        status_counts[record.status] = status_counts.get(record.status, 0) + 1
    return {
        "project_dir": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "checkpoint_count": len(records),
            "label_release_candidate_count": status_counts.get("label_release_candidate", 0),
            "embedding_release_candidate_count": status_counts.get("embedding_release_candidate", 0),
            "error_count": len(errors),
            "total_checkpoint_bytes": sum(record.bytes for record in records),
        },
        "checkpoints": [asdict(record) for record in records],
        "errors": errors,
    }


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def fmt_float(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "| Run | Kind | Status | Epoch | Stage | Bytes | Gene vocab | Fine vocab | Coarse vocab | Eval loss | Macro-F1 | SHA256 |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in payload["checkpoints"]:
        macro_f1 = item["fine_macro_f1"] if item["fine_macro_f1"] is not None else item["coarse_macro_f1"]
        rows.append(
            "| {run} | {kind} | {status} | {epoch} | {stage} | {bytes} | {gene} | {fine} | {coarse} | {eval_loss} | {macro_f1} | `{sha}` |".format(
                run=item["run_id"],
                kind=item["checkpoint_kind"],
                status=item["status"],
                epoch=item["checkpoint_epoch"] or "",
                stage=item["stage"],
                bytes=item["bytes"],
                gene=item["gene_vocab_size"],
                fine=item["fine_vocab_size"],
                coarse=item["coarse_vocab_size"],
                eval_loss=fmt_float(item["eval_loss"]),
                macro_f1=fmt_float(macro_f1),
                sha=str(item["sha256"])[:16],
            )
        )
    lines = [
        "# SnowLotus-CellFM Model Release Manifest",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        f"- Checkpoints: `{payload['summary']['checkpoint_count']}`",
        f"- Label-release candidates: `{payload['summary']['label_release_candidate_count']}`",
        f"- Embedding-release candidates: `{payload['summary']['embedding_release_candidate_count']}`",
        f"- Checkpoint load errors: `{payload['summary']['error_count']}`",
        f"- Total checkpoint bytes: `{payload['summary']['total_checkpoint_bytes']}`",
        "",
        "## Checkpoints",
        "",
        "\n".join(rows),
        "",
    ]
    if payload["errors"]:
        lines.extend(["## Errors", ""])
        lines.extend(f"- `{item['path']}`: {item['error']}" for item in payload["errors"])
        lines.append("")
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write SnowLotus-CellFM model release manifest")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    payload = collect_manifest(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
