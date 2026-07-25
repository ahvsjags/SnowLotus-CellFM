from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_bytes(value: int | float | None) -> str:
    size = float(value or 0)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def metric_value(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return ""
    return str(value)


def run_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for run in summary.get("runs", []):
        latest = run.get("latest_epoch") or {}
        test_metrics = run.get("test_metrics") or {}
        rows.append(
            {
                "run": run.get("path"),
                "checkpoint": bool(run.get("has_checkpoint")),
                "checkpoint_size": fmt_bytes(run.get("checkpoint_bytes")),
                "epochs_recorded": run.get("epochs_recorded", 0),
                "latest_epoch": latest.get("epoch", ""),
                "fine_macro_f1": metric_value(latest, "fine_macro_f1")
                or metric_value(test_metrics, "fine_macro_f1"),
                "coarse_macro_f1": metric_value(latest, "coarse_macro_f1")
                or metric_value(test_metrics, "coarse_macro_f1"),
                "eval_loss": metric_value(latest, "eval_loss"),
            }
        )
    return rows


def corpus_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "path": item.get("path"),
            "exists": bool(item.get("exists")),
            "size": fmt_bytes(item.get("bytes")),
        }
        for item in summary.get("corpora", [])
    ]


def data_target_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for target in summary.get("public_data_targets", []):
        manifest_rows = target.get("manifest", {}).get("rows", 0) or (
            target.get("available_manifest") or {}
        ).get("rows", 0)
        rows.append(
            {
                "dataset_id": target.get("dataset_id"),
                "priority": target.get("priority"),
                "status": target.get("status"),
                "stage": target.get("stage"),
                "manifest_rows": manifest_rows,
                "raw_files": target.get("raw_files", {}).get("file_count", 0),
                "npz_files": target.get("npz_files", {}).get("file_count", 0),
            }
        )
    return rows


def pending_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return summary.get("pending_corpus_additions", {}).get("pending_manifests", [])


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    if not rows:
        lines.append("| " + " | ".join([""] * len(columns)) + " |")
        return lines
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def build_card(summary: dict[str, Any]) -> dict[str, Any]:
    gates = summary.get("publication_gates", {})
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_dir": summary.get("project_dir"),
        "intended_use": (
            "Plant single-cell and single-nucleus foundation annotation, public cross-species "
            "pretraining, and Snow Lotus transfer once primary Saussurea data are available."
        ),
        "model_family": "Transformer-based expression foundation model with MLM-style pretraining and hierarchical labels.",
        "runs": run_rows(summary),
        "corpora": corpus_rows(summary),
        "public_data_targets": data_target_rows(summary),
        "pending_corpus_additions": pending_rows(summary),
        "publication_gates": gates,
        "known_limitations": [
            "Real Snow Lotus scRNA/snRNA primary data are not yet present as data/saussurea_involucrata.h5ad.",
            "Current public foundation training uses heterogeneous public plant matrices with incomplete harmonized labels.",
            "Several newly reviewed GEO datasets are still downloading or pending conversion.",
            "External tool benchmarks and wet-lab validation are required before top-journal biological claims.",
            "The current model card is a living project artifact and should be frozen with final checksums before submission.",
        ],
        "recommended_next_actions": [
            "Let public MLM training finish, then allow late-refresh to rebuild the corpus with GSE243419.",
            "Continue reviewed GEO downloads and add converted manifests to the public MLM corpus.",
            "Add primary Saussurea involucrata scRNA/snRNA h5ad and run Snow Lotus fine-tuning.",
            "Run strict external benchmarks and produce marker/regulator validation tables.",
            "Deposit final raw and processed data with stable accessions and update Data Availability.",
        ],
    }


def write_markdown(card: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SnowLotus-CellFM Model and Data Card",
        "",
        f"- Generated UTC: `{card['generated_at_utc']}`",
        f"- Project directory: `{card.get('project_dir')}`",
        f"- Model family: {card['model_family']}",
        f"- Intended use: {card['intended_use']}",
        "",
        "## Model Artifacts",
        "",
        *markdown_table(
            card["runs"],
            [
                "run",
                "checkpoint",
                "checkpoint_size",
                "epochs_recorded",
                "latest_epoch",
                "fine_macro_f1",
                "coarse_macro_f1",
                "eval_loss",
            ],
        ),
        "",
        "## Corpus Artifacts",
        "",
        *markdown_table(card["corpora"], ["path", "exists", "size"]),
        "",
        "## Public Data Targets",
        "",
        *markdown_table(
            card["public_data_targets"],
            ["dataset_id", "priority", "status", "stage", "manifest_rows", "raw_files", "npz_files"],
        ),
        "",
        "## Pending Corpus Additions",
        "",
        *markdown_table(
            card["pending_corpus_additions"],
            ["manifest", "dataset_ids", "rows_missing_from_public_mlm_manifest"],
        ),
        "",
        "## Known Limitations",
        "",
        *[f"- {item}" for item in card["known_limitations"]],
        "",
        "## Recommended Next Actions",
        "",
        *[f"- {item}" for item in card["recommended_next_actions"]],
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)
    return output


def write_json(card: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a SnowLotus-CellFM model/data card")
    parser.add_argument("--status-summary", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    summary = read_json(args.status_summary)
    card = build_card(summary)
    write_markdown(card, args.output_md)
    write_json(card, args.output_json)


if __name__ == "__main__":
    main()
