from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT_CELL_TYPES = {
    "Columella root cap",
    "Lateral root cap",
    "Root cap",
    "Root cortex",
    "Root endodermis",
    "Root hair",
    "Root stele",
    "Phloem",
    "Xylem",
    "Non-hair",
}


DISPLAY_LABEL_FIXES = {
    "Unknow": "Unknown",
    "unknow": "Unknown",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_marker_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parsed: dict[str, Any] = dict(row)
            for key in [
                "rank",
                "score",
                "log2fc",
                "mean_in",
                "mean_out",
                "detection_in",
                "detection_out",
                "n_cells_in",
                "n_cells_out",
            ]:
                if key in parsed and parsed[key] != "":
                    try:
                        parsed[key] = int(parsed[key]) if key.startswith("n_") or key == "rank" else float(parsed[key])
                    except ValueError:
                        pass
            rows.append(parsed)
    return rows


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def adapter_summary(adapters_path: Path) -> dict[str, Any]:
    payload = read_json(adapters_path)
    adapters = payload.get("adapters", [])
    arabidopsis = [
        adapter for adapter in adapters if str(adapter.get("species", "")).lower() == "arabidopsis thaliana"
    ]
    universal = [
        adapter for adapter in adapters if adapter.get("adapter_id") == payload.get("fallback_adapter", "plant_universal")
    ]
    return {
        "registry": adapters_path.as_posix(),
        "scope": payload.get("scope"),
        "dynamic_adapter_resolution": payload.get("dynamic_adapter_resolution"),
        "adapter_count": len(adapters),
        "arabidopsis_adapter": arabidopsis[0] if arabidopsis else None,
        "fallback_adapter": universal[0] if universal else None,
    }


def display_label(label: str) -> str:
    return DISPLAY_LABEL_FIXES.get(label, label)


def summarize_markers(rows: list[dict[str, Any]], top_n: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_label[str(row.get("label", ""))].append(row)

    summaries: list[dict[str, Any]] = []
    top_rows: list[dict[str, Any]] = []
    for raw_label, label_rows in sorted(by_label.items()):
        label = display_label(raw_label)
        ranked = sorted(label_rows, key=lambda item: (int(item.get("rank", 999999)), -float(item.get("score", 0))))
        selected = ranked[:top_n]
        top_rows.extend(selected)
        scores = [float(row["score"]) for row in selected if isinstance(row.get("score"), (int, float))]
        log2fc = [float(row["log2fc"]) for row in selected if isinstance(row.get("log2fc"), (int, float))]
        detection_delta = [
            float(row["detection_in"]) - float(row["detection_out"])
            for row in selected
            if isinstance(row.get("detection_in"), (int, float))
            and isinstance(row.get("detection_out"), (int, float))
        ]
        summaries.append(
            {
                "label": label,
                "source_label": raw_label,
                "category": "root_cell_identity" if label in ROOT_CELL_TYPES else "cell_cycle_or_other",
                "top_genes": [row.get("gene") for row in selected],
                "top_n": len(selected),
                "median_score": statistics.median(scores) if scores else None,
                "median_log2fc": statistics.median(log2fc) if log2fc else None,
                "median_detection_delta": statistics.median(detection_delta) if detection_delta else None,
                "n_cells_in": selected[0].get("n_cells_in") if selected else None,
                "n_cells_out": selected[0].get("n_cells_out") if selected else None,
            }
        )
    return summaries, top_rows


def write_top_marker_tsv(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "label_key",
        "label",
        "rank",
        "gene",
        "score",
        "log2fc",
        "mean_in",
        "mean_out",
        "detection_in",
        "detection_out",
        "n_cells_in",
        "n_cells_out",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_case(args: argparse.Namespace) -> dict[str, Any]:
    root = args.project_dir.resolve()
    marker_json_path = (root / args.marker_json).resolve()
    marker_tsv_path = (root / args.marker_tsv).resolve()
    adapters_path = (root / args.adapters).resolve()
    marker_meta = read_json(marker_json_path)
    marker_rows = read_marker_rows(marker_tsv_path)
    label_summaries, top_rows = summarize_markers(marker_rows, args.top_n)
    top_tsv = (root / args.output_top_tsv).resolve()
    write_top_marker_tsv(top_rows, top_tsv)

    root_labels = [row for row in label_summaries if row["category"] == "root_cell_identity"]
    return {
        "schema_version": "plant-cellfm-biology-case-study-v1",
        "case_id": "arabidopsis_root_marker_adapter_case",
        "title": "Arabidopsis root cell-identity marker and adapter case",
        "scope": (
            "A complete public-plant biological case demonstrating adapter resolution, "
            "hierarchical annotation evidence and marker-candidate mining on root cell states."
        ),
        "evidence_files": {
            "marker_json": rel(marker_json_path, root),
            "marker_tsv": rel(marker_tsv_path, root),
            "top_marker_tsv": rel(top_tsv, root),
            "adapter_registry": rel(adapters_path, root),
        },
        "adapter_layer": adapter_summary(adapters_path),
        "marker_overview": {
            "labels": marker_meta.get("labels"),
            "n_labels": marker_meta.get("n_labels"),
            "n_marker_rows": marker_meta.get("n_rows"),
            "root_identity_labels": [row["label"] for row in root_labels],
            "root_identity_label_count": len(root_labels),
            "top_n_per_label": args.top_n,
        },
        "label_marker_summaries": label_summaries,
        "biological_workflow": [
            "Resolve the input species to the Arabidopsis adapter, with plant_universal as fallback.",
            "Run the Plant-CellFM backbone and annotation head to obtain cell embeddings and fine/coarse labels.",
            "Mine marker candidates per predicted or reference cell state using expression enrichment, log2 fold-change and detection-rate separation.",
            "Review root identity labels such as root cap, cortex, endodermis, stele, phloem, xylem and root hair as a coherent plant biology case.",
        ],
        "manuscript_claim": (
            "The Arabidopsis root case provides a complete public-data demonstration of Plant-CellFM v9: "
            "the same plant-general model resolves a species adapter, produces annotation-ready "
            "representations and returns marker candidates for major root cell identities."
        ),
    }


def write_json(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    adapter = payload["adapter_layer"].get("arabidopsis_adapter") or {}
    overview = payload["marker_overview"]
    lines = [
        "# Plant-CellFM v9 Biology Case Study",
        "",
        f"## {payload['title']}",
        "",
        payload["scope"],
        "",
        "## Evidence",
        "",
        f"- Adapter registry scope: `{payload['adapter_layer'].get('scope')}`",
        f"- Dynamic adapter resolution: `{payload['adapter_layer'].get('dynamic_adapter_resolution')}`",
        f"- Total adapters: `{payload['adapter_layer'].get('adapter_count')}`",
        f"- Arabidopsis adapter: `{adapter.get('adapter_id', '-')}`",
        f"- Arabidopsis evidence: `{adapter.get('evidence', {})}`",
        f"- Marker labels: `{overview.get('n_labels')}`",
        f"- Marker rows: `{overview.get('n_marker_rows')}`",
        f"- Root identity labels: `{overview.get('root_identity_label_count')}`",
        "",
        "## Top Marker Summary",
        "",
        "| Cell state | Category | Top genes | Median score | Median log2FC | Median detection delta |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in payload["label_marker_summaries"]:
        lines.append(
            "| {label} | {category} | {genes} | {score} | {log2fc} | {det} |".format(
                label=str(row["label"]).replace("|", "/"),
                category=row["category"],
                genes=", ".join(str(gene) for gene in row["top_genes"]),
                score=fmt(row["median_score"]),
                log2fc=fmt(row["median_log2fc"]),
                det=fmt(row["median_detection_delta"]),
            )
        )
    lines.extend(
        [
            "",
            "## Manuscript-Ready Case Statement",
            "",
            payload["manuscript_claim"],
            "",
            "## Reproducible Workflow",
            "",
        ]
    )
    for index, item in enumerate(payload["biological_workflow"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(
        [
            "",
            "## Files",
            "",
        ]
    )
    for key, value in payload["evidence_files"].items():
        lines.append(f"- `{key}`: `{value}`")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write Plant-CellFM v9 biology case study")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument(
        "--marker-json",
        default="release_metadata/strict_benchmarks/public_sprint.marker_candidates.json",
        type=Path,
    )
    parser.add_argument(
        "--marker-tsv",
        default="release_metadata/strict_benchmarks/public_sprint.marker_candidates.tsv",
        type=Path,
    )
    parser.add_argument(
        "--adapters",
        default="release_metadata/plant_species_adapters.json",
        type=Path,
    )
    parser.add_argument("--top-n", default=5, type=int)
    parser.add_argument(
        "--output-json",
        default="release_metadata/plant_biology_case_study_v9.json",
        type=Path,
    )
    parser.add_argument(
        "--output-md",
        default="release_metadata/plant_biology_case_study_v9.md",
        type=Path,
    )
    parser.add_argument(
        "--output-top-tsv",
        default="release_metadata/plant_biology_case_study_top_markers_v9.tsv",
        type=Path,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top_n < 1:
        raise ValueError("--top-n must be >= 1")
    payload = build_case(args)
    root = args.project_dir.resolve()
    json_path = (root / args.output_json).resolve()
    md_path = (root / args.output_md).resolve()
    write_json(payload, json_path)
    write_markdown(payload, md_path)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
