from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_text(path: Path, max_chars: int = 20_000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:max_chars]


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    columns = sorted({key for row in rows for key in row})
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def collect_run_summary(output_dir: str | Path) -> dict[str, Any]:
    root = Path(output_dir)
    config = _read_json(root / "config.resolved.json")
    history = _read_json(root / "history.json")
    test_metrics = _read_json(root / "test_metrics.json")
    preprocessing = _read_json(root / "preprocessing_stats.json")
    return {
        "output_dir": str(root),
        "has_checkpoint": (root / "best.pt").exists(),
        "config": config,
        "history": history,
        "test_metrics": test_metrics,
        "preprocessing": preprocessing,
    }


def generate_markdown_report(
    project_dir: str | Path,
    output: str | Path,
    run_dirs: list[str] | None = None,
) -> Path:
    project = Path(project_dir)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_dirs = run_dirs or [
        "outputs/smoke",
        "outputs/foundation_5090_public_sprint",
        "outputs/foundation_5090_public_safe_init",
        "outputs/foundation_5090_pretrain",
        "outputs/foundation_5090_mlm_public_expansion",
        "outputs/foundation_5090_mlm_public_expansion_continuation",
        "outputs/foundation_5090_mlm_public_post_gse226097_refresh_safe",
        "outputs/saussurea_lora_finetune",
    ]
    summaries = [collect_run_summary(project / run_dir) for run_dir in run_dirs]

    metric_rows = []
    for summary in summaries:
        metrics = summary.get("test_metrics") or {}
        if metrics:
            row = {"run": summary["output_dir"], "checkpoint": summary["has_checkpoint"]}
            row.update({key: round(value, 5) if isinstance(value, float) else value for key, value in metrics.items()})
            metric_rows.append(row)

    manifest = _read_text(project / "data" / "public_dataset_manifest.tsv")
    strategy = _read_text(project / "docs" / "top_journal_strategy.md")
    lines = [
        "# Plant-CellFM Publication Readiness Report",
        "",
        "## Run Metrics",
        "",
        _markdown_table(metric_rows) if metric_rows else "No completed training metrics found yet.",
        "",
        "## Completed Artifacts",
        "",
    ]
    for summary in summaries:
        lines.append(f"- `{summary['output_dir']}` checkpoint: `{summary['has_checkpoint']}`")
    lines.extend(
        [
            "",
            "## Data Manifest",
            "",
            "```text",
            manifest,
            "```",
            "",
            "## Strategy Snapshot",
            "",
            strategy,
            "",
            "## Remaining Publication Gates",
            "",
            "- Real Saussurea involucrata scRNA/snRNA `.h5ad` with sample-level split metadata.",
            "- Processed public plant single-cell matrices listed in `data/corpus_manifest.tsv`.",
            "- Fair external benchmarks against scPlantLLM, scPlantAnnotate, Seurat label transfer, and marker rules.",
            "- Biological validation for at least 3-5 model-prioritized snow lotus marker/regulator candidates.",
            "- Reproducible figure scripts and frozen data provenance table.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
