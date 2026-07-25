from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def discover_run_dirs(root: Path, explicit: list[str] | None = None) -> list[Path]:
    if explicit:
        return [root / item for item in explicit]
    outputs = root / "outputs"
    if not outputs.exists():
        return []
    return sorted(
        {
            path.parent
            for pattern in ("*/history.json", "*/progress_latest.json", "*/config.resolved.json")
            for path in outputs.glob(pattern)
        },
        key=lambda item: item.as_posix(),
    )


def loss_delta(first: float | None, last: float | None) -> dict[str, float | None]:
    if first is None or last is None:
        return {"absolute": None, "relative_percent": None}
    relative = ((first - last) / first * 100.0) if first else None
    return {"absolute": float(first - last), "relative_percent": relative}


def nonincreasing(values: list[float]) -> bool | None:
    if len(values) < 2:
        return None
    return all(next_value <= value for value, next_value in zip(values, values[1:]))


def best_eval_epoch(epochs: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [epoch for epoch in epochs if epoch.get("eval_loss") is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda epoch: float(epoch["eval_loss"]))


def summarize_run(root: Path, run_dir: Path) -> dict[str, Any]:
    history_path = run_dir / "history.json"
    history_payload = read_json(history_path) or {}
    epochs = list(history_payload.get("epochs") or [])
    latest_progress = read_json(run_dir / "progress_latest.json") or {}
    latest_checkpoint = run_dir / "latest.pt"
    best_checkpoint = run_dir / "best.pt"
    train_losses = [
        float(epoch["train_loss"]) for epoch in epochs if epoch.get("train_loss") is not None
    ]
    eval_losses = [
        float(epoch["eval_loss"]) for epoch in epochs if epoch.get("eval_loss") is not None
    ]
    first_train = train_losses[0] if train_losses else None
    latest_train = train_losses[-1] if train_losses else None
    first_eval = eval_losses[0] if eval_losses else None
    latest_eval = eval_losses[-1] if eval_losses else None
    best_eval = best_eval_epoch(epochs)
    best_eval_loss = float(best_eval["eval_loss"]) if best_eval is not None else None
    latest_minus_best_eval = (
        float(latest_eval - best_eval_loss)
        if latest_eval is not None and best_eval_loss is not None
        else None
    )
    return {
        "run_id": run_dir.name,
        "run_dir": relpath(root, run_dir),
        "history": relpath(root, history_path),
        "history_exists": history_path.exists(),
        "epochs_recorded": len(epochs),
        "latest_epoch": epochs[-1].get("epoch") if epochs else None,
        "first_train_loss": first_train,
        "latest_train_loss": latest_train,
        "train_loss_delta": loss_delta(first_train, latest_train),
        "first_eval_loss": first_eval,
        "latest_eval_loss": latest_eval,
        "best_epoch": best_eval.get("epoch") if best_eval else None,
        "best_eval_loss": best_eval_loss,
        "best_eval_epoch_record": best_eval,
        "eval_loss_delta": loss_delta(first_eval, latest_eval),
        "best_eval_loss_delta": loss_delta(first_eval, best_eval_loss),
        "latest_minus_best_eval_loss": latest_minus_best_eval,
        "train_loss_nonincreasing": nonincreasing(train_losses),
        "eval_loss_nonincreasing": nonincreasing(eval_losses),
        "latest_progress": latest_progress,
        "latest_checkpoint": {
            "path": relpath(root, latest_checkpoint),
            "exists": latest_checkpoint.exists(),
            "bytes": latest_checkpoint.stat().st_size if latest_checkpoint.exists() else 0,
        },
        "best_checkpoint": {
            "path": relpath(root, best_checkpoint),
            "exists": best_checkpoint.exists(),
            "bytes": best_checkpoint.stat().st_size if best_checkpoint.exists() else 0,
        },
        "epochs": epochs,
    }


def build_summary(project_dir: str | Path, run_dirs: list[str] | None = None) -> dict[str, Any]:
    root = Path(project_dir)
    runs = [summarize_run(root, run_dir) for run_dir in discover_run_dirs(root, run_dirs)]
    runs_with_eval = [run for run in runs if run["latest_eval_loss"] is not None]
    improving_runs = [
        run
        for run in runs_with_eval
        if (run["eval_loss_delta"]["absolute"] or 0) > 0
    ]
    return {
        "project_dir": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "run_count": len(runs),
            "runs_with_eval_loss": len(runs_with_eval),
            "runs_with_eval_improvement": len(improving_runs),
            "checkpoint_runs": sum(
                1
                for run in runs
                if run["latest_checkpoint"]["exists"] or run["best_checkpoint"]["exists"]
            ),
        },
        "runs": runs,
    }


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "| Run | Epochs | Latest status | Train loss | Eval loss | Best eval | Best epoch | Eval delta | Checkpoint |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for run in payload["runs"]:
        progress = run.get("latest_progress") or {}
        checkpoint = "yes" if run["latest_checkpoint"]["exists"] or run["best_checkpoint"]["exists"] else "no"
        rows.append(
            "| {run_id} | {epochs} | {status} | {train} | {eval_loss} | {best_eval} | {best_epoch} | {delta} | {ckpt} |".format(
                run_id=run["run_id"],
                epochs=run["epochs_recorded"],
                status=progress.get("status") or "-",
                train=fmt(run["latest_train_loss"]),
                eval_loss=fmt(run["latest_eval_loss"]),
                best_eval=fmt(run["best_eval_loss"]),
                best_epoch=fmt(run["best_epoch"], digits=0),
                delta=fmt(run["eval_loss_delta"]["absolute"]),
                ckpt=checkpoint,
            )
        )
    lines = [
        "# SnowLotus-CellFM Training Curve Summary",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        f"- Runs with histories: `{payload['summary']['run_count']}`",
        f"- Runs with eval loss: `{payload['summary']['runs_with_eval_loss']}`",
        f"- Runs with eval improvement: `{payload['summary']['runs_with_eval_improvement']}`",
        f"- Runs with checkpoints: `{payload['summary']['checkpoint_runs']}`",
        "",
        "## Runs",
        "",
        "\n".join(rows),
        "",
    ]
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_tsv(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            delimiter="\t",
            fieldnames=["run_id", "epoch", "train_loss", "eval_loss", "eval_batches"],
        )
        writer.writeheader()
        for run in payload["runs"]:
            for epoch in run["epochs"]:
                writer.writerow(
                    {
                        "run_id": run["run_id"],
                        "epoch": epoch.get("epoch"),
                        "train_loss": epoch.get("train_loss"),
                        "eval_loss": epoch.get("eval_loss"),
                        "eval_batches": epoch.get("eval_batches"),
                    }
                )
    print(output_path)
    return output_path


def write_png(payload: dict[str, Any], output: str | Path) -> Path | None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    for run in payload["runs"]:
        epochs = [epoch.get("epoch") for epoch in run["epochs"] if epoch.get("eval_loss") is not None]
        losses = [epoch.get("eval_loss") for epoch in run["epochs"] if epoch.get("eval_loss") is not None]
        if epochs and losses:
            ax.plot(epochs, losses, marker="o", linewidth=1.5, label=run["run_id"])
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Eval loss")
    ax.set_title("SnowLotus-CellFM eval loss")
    ax.grid(True, alpha=0.25)
    if ax.lines:
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write SnowLotus-CellFM training curve summary")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--run-dir", action="append", default=None)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-tsv", required=True)
    parser.add_argument("--output-png")
    args = parser.parse_args()
    payload = build_summary(args.project_dir, args.run_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    write_tsv(payload, args.output_tsv)
    if args.output_png:
        write_png(payload, args.output_png)


if __name__ == "__main__":
    main()
