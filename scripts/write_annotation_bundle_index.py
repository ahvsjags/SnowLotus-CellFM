from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AnnotationBundle:
    bundle: str
    status: str
    checkpoint_path: str
    data_path: str
    checkpoint_epoch: int | None
    n_cells: int
    embedding_dim: int
    fine_vocab_size: int
    coarse_vocab_size: int
    prediction_rows: int
    top_fine_labels: str
    metadata_json: str
    prediction_csv: str
    embedding_npy: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def summarize_predictions(path: Path) -> tuple[int, str]:
    if not path.exists():
        return 0, ""
    counts: dict[str, int] = {}
    rows = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            label = row.get("fine_label") or "unknown"
            counts[label] = counts.get(label, 0) + 1
    top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]
    return rows, ";".join(f"{label}:{count}" for label, count in top)


def collect_bundles(project_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    base = root / "outputs" / "annotation_bundles"
    bundles: list[AnnotationBundle] = []
    for metadata_path in sorted(base.glob("*/annotation_metadata.json")):
        metadata = read_json(metadata_path)
        bundle_dir = metadata_path.parent
        prediction_path = bundle_dir / str(metadata.get("prediction_csv", "predictions.csv"))
        embedding_path = bundle_dir / str(metadata.get("embedding_npy", "embeddings.npy"))
        prediction_rows, top_labels = summarize_predictions(prediction_path)
        fine_vocab_size = int(metadata.get("fine_vocab_size") or 0)
        coarse_vocab_size = int(metadata.get("coarse_vocab_size") or 0)
        status = "label_ready" if fine_vocab_size > 1 and coarse_vocab_size > 1 else "embedding_only"
        bundles.append(
            AnnotationBundle(
                bundle=relpath(root, bundle_dir),
                status=status,
                checkpoint_path=str(metadata.get("checkpoint_path", "")),
                data_path=str(metadata.get("data_path", "")),
                checkpoint_epoch=metadata.get("checkpoint_epoch"),
                n_cells=int(metadata.get("n_cells") or 0),
                embedding_dim=int(metadata.get("embedding_dim") or 0),
                fine_vocab_size=fine_vocab_size,
                coarse_vocab_size=coarse_vocab_size,
                prediction_rows=prediction_rows,
                top_fine_labels=top_labels,
                metadata_json=relpath(root, metadata_path),
                prediction_csv=relpath(root, prediction_path),
                embedding_npy=relpath(root, embedding_path),
            )
        )
    status_counts: dict[str, int] = {}
    for bundle in bundles:
        status_counts[bundle.status] = status_counts.get(bundle.status, 0) + 1
    return {
        "project_dir": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "bundle_count": len(bundles),
            "label_ready_count": status_counts.get("label_ready", 0),
            "embedding_only_count": status_counts.get("embedding_only", 0),
            "annotated_cells": sum(bundle.n_cells for bundle in bundles),
        },
        "bundles": [asdict(bundle) for bundle in bundles],
    }


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "| Bundle | Status | Cells | Dim | Fine vocab | Coarse vocab | Checkpoint | Data | Top fine labels |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for item in payload["bundles"]:
        rows.append(
            "| {bundle} | {status} | {cells} | {dim} | {fine} | {coarse} | {ckpt} | {data} | {labels} |".format(
                bundle=item["bundle"],
                status=item["status"],
                cells=item["n_cells"],
                dim=item["embedding_dim"],
                fine=item["fine_vocab_size"],
                coarse=item["coarse_vocab_size"],
                ckpt=item["checkpoint_path"],
                data=item["data_path"],
                labels=item["top_fine_labels"].replace("|", "/"),
            )
        )
    lines = [
        "# SnowLotus-CellFM Annotation Bundle Index",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        f"- Bundles: `{payload['summary']['bundle_count']}`",
        f"- Label-ready bundles: `{payload['summary']['label_ready_count']}`",
        f"- Embedding-only bundles: `{payload['summary']['embedding_only_count']}`",
        f"- Annotated cells: `{payload['summary']['annotated_cells']}`",
        "",
        "## Bundles",
        "",
        "\n".join(rows),
        "",
    ]
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Index SnowLotus-CellFM annotation bundles")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    payload = collect_bundles(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
