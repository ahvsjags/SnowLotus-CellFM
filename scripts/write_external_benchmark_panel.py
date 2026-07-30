from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROTOCOL_LABELS = {
    "leave_dataset_out": "Leave-dataset-out",
    "leave_sample_out": "Leave-sample-out",
    "leave_species_out": "Leave-species-out, species labels normalized",
}


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def metric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: Any, digits: int = 4) -> str:
    value = metric(value)
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def load_v9_rows(path: Path, root: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    if not payload:
        return []
    candidate = payload.get("candidate", {}).get("summary", {})
    baseline = payload.get("baseline", {}).get("summary", {})
    delta = payload.get("delta", {})
    rows: list[dict[str, Any]] = []
    for protocol, label in PROTOCOL_LABELS.items():
        cand = candidate.get(protocol, {}).get("fine", {})
        base = baseline.get(protocol, {}).get("fine", {})
        gain = delta.get(protocol, {}).get("fine", {})
        rows.append(
            {
                "comparison": "Plant-CellFM v9 vs frozen v3 extended",
                "protocol": label,
                "status": "completed",
                "formal_comparison": True,
                "evidence": rel(path, root),
                "candidate_all_cell_accuracy": metric(cand.get("accuracy_all")),
                "candidate_all_cell_macro_f1_weighted": metric(
                    cand.get("macro_f1_all_weighted_by_cells")
                ),
                "candidate_coverage": metric(cand.get("coverage")),
                "candidate_known_label_accuracy": metric(cand.get("accuracy")),
                "candidate_known_label_macro_f1": metric(cand.get("macro_f1")),
                "baseline_all_cell_accuracy": metric(base.get("accuracy_all")),
                "baseline_known_label_accuracy": metric(base.get("accuracy")),
                "delta_all_cell_accuracy": metric(gain.get("accuracy_all")),
                "delta_known_label_accuracy": metric(gain.get("accuracy")),
                "interpretation": (
                    "Frozen v9 and frozen v3 extended are evaluated on the same "
                    "shared-gene public-plant benchmark using the same protocol."
                ),
            }
        )
    return rows


def load_centroid_baseline(path: Path, root: Path, label: str, formal: bool) -> dict[str, Any]:
    payload = read_json(path)
    if not payload:
        return {
            "comparison": label,
            "status": "missing",
            "formal_comparison": False,
            "evidence": rel(path, root),
        }
    return {
        "comparison": label,
        "protocol": payload.get("split", {}).get("strategy", "configured split"),
        "status": "completed",
        "formal_comparison": formal,
        "evidence": rel(path, root),
        "method": payload.get("method", "cosine_nearest_centroid"),
        "test_cells": payload.get("split", {}).get("test_cells"),
        "train_cells": payload.get("split", {}).get("train_cells"),
        "fine_accuracy": metric(payload.get("fine_test_accuracy")),
        "fine_macro_f1": metric(payload.get("fine_test_macro_f1")),
        "coarse_accuracy": metric(payload.get("coarse_test_accuracy")),
        "coarse_macro_f1": metric(payload.get("coarse_test_macro_f1")),
        "interpretation": (
            "A transparent classical baseline using the same labelled corpus family; "
            "included as a sanity and reproducibility comparator."
        ),
    }


def load_scplantllm(
    probe_path: Path,
    readiness_path: Path,
    root: Path,
) -> dict[str, Any]:
    probe = read_json(probe_path)
    if probe and isinstance(probe.get("metrics"), dict):
        metrics = probe["metrics"]
        data = probe.get("data", {})
        return {
            "comparison": "scPlantLLM frozen embedding nearest-centroid probe",
            "protocol": "public sprint train/test chunks",
            "status": "completed",
            "formal_comparison": True,
            "evidence": rel(probe_path, root),
            "method": probe.get("method"),
            "train_cells": data.get("selected_train_cells"),
            "test_cells": data.get("selected_test_cells"),
            "accuracy": metric(metrics.get("accuracy")),
            "macro_f1": metric(metrics.get("macro_f1")),
            "micro_f1": metric(metrics.get("micro_f1")),
            "weighted_f1": metric(metrics.get("weighted_f1")),
            "interpretation": probe.get(
                "interpretation",
                "Frozen scPlantLLM embeddings evaluated with a local centroid probe.",
            ),
        }

    readiness = read_json(readiness_path) or {}
    return {
        "comparison": "scPlantLLM frozen embedding nearest-centroid probe",
        "protocol": "public sprint train/test chunks",
        "status": "input_ready_metric_missing",
        "formal_comparison": False,
        "evidence": rel(readiness_path, root),
        "selected_cells": readiness.get("selected_cells"),
        "retained_genes": readiness.get("retained_genes"),
        "gene_vocab_overlap_rate": readiness.get("gene_vocab_overlap_rate"),
        "interpretation": (
            "The scPlantLLM-compatible input and reference preprocessing are ready, "
            "but a metric JSON is not present in the current release tree."
        ),
    }


def load_seurat(path: Path, root: Path) -> dict[str, Any]:
    payload = read_json(path)
    if not payload:
        return {
            "comparison": "Seurat label transfer",
            "status": "runner_available_metric_missing",
            "formal_comparison": False,
            "evidence": "scripts/run_seurat_label_transfer_benchmark.R",
            "interpretation": (
                "The Seurat runner is included, but the current release tree does not "
                "contain a metric JSON for this comparator."
            ),
        }
    return {
        "comparison": "Seurat label transfer",
        "protocol": "exported train/test split",
        "status": "completed",
        "formal_comparison": True,
        "evidence": rel(path, root),
        "method": payload.get("method", "seurat_label_transfer"),
        "test_cells": payload.get("test_cells"),
        "fine_accuracy": metric(payload.get("fine_test_accuracy")),
        "fine_macro_f1": metric(payload.get("fine_test_macro_f1")),
        "coarse_accuracy": metric(payload.get("coarse_test_accuracy")),
        "coarse_macro_f1": metric(payload.get("coarse_test_macro_f1")),
        "interpretation": "Seurat anchor-based label transfer on an exported matching split.",
    }


def load_scplantannotate(path: Path, root: Path) -> dict[str, Any]:
    payload = read_json(path) or {}
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    web_server_reachable = payload.get("web_server_reachable", summary.get("web_server_reachable"))
    scriptable_batch_api_detected = payload.get(
        "scriptable_batch_api_detected",
        summary.get("batch_api_detected"),
    )
    anonymous_api_accessible = payload.get(
        "anonymous_api_accessible",
        summary.get("anonymous_api_accessible"),
    )
    comparison_ready = payload.get(
        "reproducible_comparison_ready",
        summary.get("comparison_ready"),
    )
    status = "completed" if comparison_ready else "web_api_auth_required"
    return {
        "comparison": "scPlantAnnotate",
        "protocol": "official web/API route audit",
        "status": status if anonymous_api_accessible is False else payload.get("status", status),
        "formal_comparison": False,
        "evidence": rel(path, root),
        "web_server_reachable": web_server_reachable,
        "scriptable_batch_api_detected": scriptable_batch_api_detected,
        "anonymous_api_accessible": anonymous_api_accessible,
        "interpretation": (
            "The official web server is reachable, but anonymous scriptable benchmark "
            "execution is not available in the current audit. This is kept as an "
            "access-limited comparator rather than reported as a completed result."
        ),
    }


def build_panel(args: argparse.Namespace) -> dict[str, Any]:
    root = args.project_dir.resolve()
    rows: list[dict[str, Any]] = []
    rows.extend(load_v9_rows((root / args.v9_comparison).resolve(), root))
    rows.append(
        load_centroid_baseline(
            (root / args.group_random_centroid).resolve(),
            root,
            "Classical cosine centroid, group-random split",
            formal=False,
        )
    )
    rows.append(
        load_centroid_baseline(
            (root / args.srp169576_centroid).resolve(),
            root,
            "Classical cosine centroid, SRP169576 sample holdout",
            formal=True,
        )
    )
    rows.append(
        load_scplantllm(
            (root / args.scplantllm_probe).resolve(),
            (root / args.scplantllm_readiness).resolve(),
            root,
        )
    )
    rows.append(load_seurat((root / args.seurat_result).resolve(), root))
    rows.append(load_scplantannotate((root / args.scplantannotate_audit).resolve(), root))

    completed_formal = [
        row for row in rows if row.get("formal_comparison") and row.get("status") == "completed"
    ]
    completed_metric_rows = [row for row in rows if row.get("status") == "completed"]
    missing_formal = [
        row for row in rows if row.get("formal_comparison") is False and "missing" in str(row.get("status"))
    ]
    return {
        "schema_version": "plant-cellfm-external-benchmark-panel-v1",
        "scope": "frozen_v9_methods_submission",
        "summary": {
            "rows": len(rows),
            "completed_metric_rows": len(completed_metric_rows),
            "completed_formal_comparisons": len(completed_formal),
            "metric_missing_or_access_limited": len(missing_formal),
            "claim_safe_position": (
                "Plant-CellFM v9 has a completed frozen v3 comparison and a classical "
                "sample-holdout baseline. Seurat label transfer is included as a "
                "completed traditional external baseline. scPlantLLM remains "
                "input-ready until a metric JSON is present; scPlantAnnotate remains "
                "access-limited until an authenticated reproducible execution path is available."
            ),
        },
        "comparisons": rows,
    }


def write_json(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Plant-CellFM v9 External Benchmark Panel",
        "",
        "This panel separates completed metrics from input-ready or access-limited comparators.",
        "",
        f"- Rows: `{payload['summary']['rows']}`",
        f"- Completed metric rows: `{payload['summary']['completed_metric_rows']}`",
        f"- Completed formal comparisons: `{payload['summary']['completed_formal_comparisons']}`",
        f"- Claim-safe position: {payload['summary']['claim_safe_position']}",
        "",
        "| Comparator | Protocol | Status | Main accuracy | Macro-F1 | Evidence |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["comparisons"]:
        acc = (
            row.get("candidate_all_cell_accuracy")
            if row.get("candidate_all_cell_accuracy") is not None
            else row.get("fine_accuracy", row.get("accuracy"))
        )
        f1 = (
            row.get("candidate_known_label_macro_f1")
            if row.get("candidate_known_label_macro_f1") is not None
            else row.get("fine_macro_f1", row.get("macro_f1"))
        )
        lines.append(
            "| {comparison} | {protocol} | {status} | {acc} | {f1} | `{evidence}` |".format(
                comparison=str(row.get("comparison", "")).replace("|", "/"),
                protocol=str(row.get("protocol", "")).replace("|", "/"),
                status=row.get("status", ""),
                acc=fmt(acc),
                f1=fmt(f1),
                evidence=row.get("evidence", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The strongest completed comparison remains the frozen v9 versus frozen v3 extended benchmark on the same shared-gene public-plant subset. The SRP169576 sample-holdout centroid baseline provides a transparent classical comparator, and the Seurat label-transfer run adds a completed traditional external baseline. scPlantLLM and scPlantAnnotate are included only at the evidence level supported by files present in the release tree.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write Plant-CellFM v9 external benchmark panel")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument(
        "--v9-comparison",
        default="release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json",
        type=Path,
    )
    parser.add_argument(
        "--group-random-centroid",
        default="release_metadata/strict_benchmarks/public_sprint_group_random.centroid_baseline.json",
        type=Path,
    )
    parser.add_argument(
        "--srp169576-centroid",
        default="release_metadata/strict_benchmarks/leaveout_srp169576_sample.centroid_baseline.json",
        type=Path,
    )
    parser.add_argument(
        "--scplantllm-probe",
        default="outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json",
        type=Path,
    )
    parser.add_argument(
        "--scplantllm-readiness",
        default="release_metadata/scplantllm_input_readiness.json",
        type=Path,
    )
    parser.add_argument(
        "--seurat-result",
        default="release_metadata/external_benchmarks/seurat_v9_subset.json",
        type=Path,
    )
    parser.add_argument(
        "--scplantannotate-audit",
        default="release_metadata/scplantannotate_access_audit.json",
        type=Path,
    )
    parser.add_argument(
        "--output-json",
        default="release_metadata/external_benchmark_panel_v9.json",
        type=Path,
    )
    parser.add_argument(
        "--output-md",
        default="release_metadata/external_benchmark_panel_v9.md",
        type=Path,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_panel(args)
    root = args.project_dir.resolve()
    json_path = (root / args.output_json).resolve()
    md_path = (root / args.output_md).resolve()
    write_json(payload, json_path)
    write_markdown(payload, md_path)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
