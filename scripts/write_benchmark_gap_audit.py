from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkRequirement:
    id: str
    label: str
    status: str
    evidence: str
    blocker: str
    priority: str


def strict_items(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return list(summary.get("strict_benchmarks", []))


def has_baseline(items: list[dict[str, Any]], token: str | None = None) -> bool:
    for item in items:
        path = item.get("path", "")
        if item.get("kind") != "baseline":
            continue
        if token and token not in path:
            continue
        if item.get("fine_test_macro_f1") is not None or item.get("coarse_test_macro_f1") is not None:
            return True
    return False


def has_split(items: list[dict[str, Any]], token: str) -> bool:
    return any(item.get("kind") == "split_audit" and token in item.get("path", "") for item in items)


def has_marker_candidates(items: list[dict[str, Any]]) -> bool:
    return any("marker_candidates" in item.get("path", "") for item in items)


def external_files(project_dir: Path, token: str) -> list[Path]:
    external_dir = project_dir / "outputs" / "external_benchmarks"
    if not external_dir.exists():
        return []
    return sorted(path for path in external_dir.glob(f"*{token}*.json") if path.is_file())


def has_metric_payload(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if isinstance(payload.get("metrics"), dict) and payload["metrics"]:
        return True
    metric_keys = {
        "accuracy",
        "macro_f1",
        "micro_f1",
        "weighted_f1",
        "fine_test_macro_f1",
        "coarse_test_macro_f1",
    }
    return any(key in payload and payload[key] is not None for key in metric_keys)


def external_metric_files(project_dir: Path, token: str) -> list[Path]:
    excluded_name_tokens = ["access_audit", "readiness", "_input", "input_", "benchmark_plan", "_plan"]
    metric_files: list[Path] = []
    for path in external_files(project_dir, token):
        lowered = path.name.lower()
        if any(excluded in lowered for excluded in excluded_name_tokens):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if has_metric_payload(payload):
            metric_files.append(path)
    return metric_files


def build_requirements(summary: dict[str, Any], project_dir: str | Path = ".") -> list[BenchmarkRequirement]:
    root = Path(project_dir)
    items = strict_items(summary)
    public_targets = summary.get("public_data_targets", [])
    completed_public_targets = [target for target in public_targets if target.get("stage") == "manifest_ready"]
    snow_ready = bool(summary.get("publication_gates", {}).get("snow_lotus_scRNA_present"))
    return [
        BenchmarkRequirement(
            id="random_split_centroid",
            label="Random/group split nearest-centroid baseline",
            status="READY" if has_baseline(items, "public_sprint_group_random") else "MISSING",
            evidence="outputs/strict_benchmarks/public_sprint_group_random.centroid_baseline.json",
            blocker="Run scripts/run_strict_benchmark_audits.sh after a labelled corpus is available.",
            priority="A",
        ),
        BenchmarkRequirement(
            id="leave_dataset_split_audit",
            label="Leave-dataset-out split audit",
            status="READY" if has_split(items, "leaveout_brassicaceae_dataset") else "MISSING",
            evidence="outputs/strict_benchmarks/leaveout_brassicaceae_dataset.split_audit.json",
            blocker="Build the public MLM corpus and run strict benchmark audits.",
            priority="A",
        ),
        BenchmarkRequirement(
            id="leave_species_split_audit",
            label="Leave-species-out split audit",
            status="READY" if has_split(items, "leaveout_eutrema_species") else "MISSING",
            evidence="outputs/strict_benchmarks/leaveout_eutrema_species.split_audit.json",
            blocker="Build the public MLM corpus and run strict benchmark audits.",
            priority="A",
        ),
        BenchmarkRequirement(
            id="leaveout_supervised_baseline",
            label="Supervised leave-out baseline metric",
            status="READY" if has_baseline(items, "leaveout_") else "MISSING",
            evidence="outputs/strict_benchmarks/leaveout_*.centroid_baseline.json",
            blocker="Current leave-out splits need enough labelled train/validation/test cells after filtering.",
            priority="A",
        ),
        BenchmarkRequirement(
            id="marker_candidate_mining",
            label="Marker-candidate interpretability artifact",
            status="READY" if has_marker_candidates(items) else "MISSING",
            evidence="outputs/strict_benchmarks/public_sprint.marker_candidates.json",
            blocker="Run snowcell marker-candidates on a labelled benchmark corpus.",
            priority="A",
        ),
        BenchmarkRequirement(
            id="seurat_label_transfer",
            label="Seurat label-transfer benchmark",
            status="READY" if external_files(root, "seurat") else "MISSING",
            evidence="outputs/external_benchmarks/*seurat*.json",
            blocker="Export comparable train/test matrices and run Seurat label transfer in R.",
            priority="A",
        ),
        BenchmarkRequirement(
            id="scplantllm_comparison",
            label="scPlantLLM comparison",
            status="READY" if external_metric_files(root, "scplantllm") else "MISSING",
            evidence="outputs/external_benchmarks/*scplantllm*.json",
            blocker="Prepare scPlantLLM-compatible input and run its public evaluation code.",
            priority="A",
        ),
        BenchmarkRequirement(
            id="scplantannotate_comparison",
            label="scPlantAnnotate comparison",
            status="READY" if external_metric_files(root, "scplantannotate") else "MISSING",
            evidence="outputs/external_benchmarks/*scplantannotate*.json",
            blocker="Prepare matched Arabidopsis/maize/rice/soybean benchmarks and run scPlantAnnotate.",
            priority="B",
        ),
        BenchmarkRequirement(
            id="snow_lotus_finetune_benchmark",
            label="Snow Lotus fine-tune and holdout benchmark",
            status="READY" if snow_ready and has_baseline(items, "saussurea") else "MISSING",
            evidence="outputs/saussurea_lora_finetune/* and data/saussurea_involucrata.h5ad",
            blocker="Requires real data/saussurea_involucrata.h5ad with cell labels and sample metadata.",
            priority="S",
        ),
        BenchmarkRequirement(
            id="public_corpus_scale",
            label="Multi-dataset public corpus coverage",
            status="READY" if len(completed_public_targets) >= 8 else "IN_PROGRESS",
            evidence=f"{len(completed_public_targets)} manifest-ready public targets",
            blocker="Finish queued GEO downloads/conversions and rebuild the public MLM corpus.",
            priority="A",
        ),
    ]


def build_audit(summary: dict[str, Any], project_dir: str | Path = ".") -> dict[str, Any]:
    requirements = build_requirements(summary, project_dir)
    ready = sum(1 for item in requirements if item.status == "READY")
    missing = sum(1 for item in requirements if item.status == "MISSING")
    in_progress = sum(1 for item in requirements if item.status == "IN_PROGRESS")
    return {
        "summary": {
            "requirement_count": len(requirements),
            "ready": ready,
            "missing": missing,
            "in_progress": in_progress,
            "top_journal_benchmark_ready": missing == 0 and in_progress == 0,
        },
        "requirements": [asdict(item) for item in requirements],
    }


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# SnowLotus-CellFM Benchmark Gap Audit",
        "",
        f"- Requirements audited: `{summary['requirement_count']}`",
        f"- Ready: `{summary['ready']}`",
        f"- In progress: `{summary['in_progress']}`",
        f"- Missing: `{summary['missing']}`",
        f"- Top-journal benchmark ready: `{summary['top_journal_benchmark_ready']}`",
        "",
        "| ID | Priority | Status | Evidence | Blocker / next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in payload["requirements"]:
        lines.append(
            "| {id} | {priority} | {status} | `{evidence}` | {blocker} |".format(
                id=item["id"],
                priority=item["priority"],
                status=item["status"],
                evidence=item["evidence"],
                blocker=item["blocker"].replace("|", "/"),
            )
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Write benchmark gap audit for SnowLotus-CellFM")
    parser.add_argument("--status-summary", required=True, type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    status = json.loads(args.status_summary.read_text(encoding="utf-8"))
    payload = build_audit(status, args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
