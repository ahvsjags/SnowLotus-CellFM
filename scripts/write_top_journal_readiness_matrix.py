from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


REQUIREMENTS = [
    {
        "id": "ssh_5090",
        "requirement": "Stable SSH alias can execute tasks on the RTX 5090 server",
        "gate": "ssh_remote_execution",
        "missing": "SSH alias or non-interactive remote execution is not available",
    },
    {
        "id": "base_training",
        "requirement": "GPU training artifacts and traceable histories exist",
        "gate": "gpu_training_active_or_artifacts_present",
        "missing": "Missing checkpoint/history artifacts or active GPU training evidence",
    },
    {
        "id": "public_data",
        "requirement": "Public plant single-cell data are ingested into manifests/corpora",
        "gate": "public_data_ingested",
        "missing": "Missing reproducible public-data manifests",
    },
    {
        "id": "data_integrity",
        "requirement": "Referenced matrix files pass integrity audit",
        "gate": "referenced_matrices_readable",
        "missing": "Missing or unreadable matrix files remain in corpus manifests",
    },
    {
        "id": "strict_split",
        "requirement": "Strict split audits are reproducible",
        "gate": "strict_split_audit_present",
        "missing": "Missing leave-out/group split audit artifacts",
    },
    {
        "id": "baseline_metric",
        "requirement": "At least one reproducible baseline benchmark metric exists",
        "gate": "baseline_benchmark_metric_present",
        "missing": "Missing metric JSON from centroid or comparable baselines",
    },
    {
        "id": "external_tools",
        "requirement": "External tool comparisons are present",
        "gate": "external_tool_benchmarks_present",
        "missing": "Missing Seurat/scPlantLLM/scPlantAnnotate benchmark outputs",
    },
    {
        "id": "snow_lotus_scrna",
        "requirement": "Snow Lotus scRNA/snRNA data exist for fine-tuning and validation",
        "gate": "snow_lotus_scRNA_present",
        "missing": "Still missing data/saussurea_involucrata.h5ad",
    },
]

HARD_GAPS = [
    "Add real `data/saussurea_involucrata.h5ad` with required cell, sample, tissue, species, batch, and label metadata.",
    "Finish pending public downloads/conversions and rebuild the public MLM corpus.",
    "Run comparable Seurat, scPlantLLM, and scPlantAnnotate benchmarks.",
    "Produce marker/regulator validation tables and independent biological validation evidence.",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def status_icon(status: str) -> str:
    return status


def requirement_status(req: dict[str, str], summary: dict[str, Any]) -> tuple[str, str]:
    gates = summary.get("publication_gates", {})
    if req["id"] == "external_tools":
        readiness = summary.get("benchmark_readiness", {})
        metric_count = int(readiness.get("external_metric_count") or 0)
        missing_methods = list(readiness.get("external_missing_methods") or [])
        present_methods = list(readiness.get("external_metric_methods") or [])
        if metric_count == 0:
            return "MISSING", req["missing"]
        if missing_methods:
            return (
                "PARTIAL",
                "Metric benchmarks present for `{}`; missing `{}`.".format(
                    ", ".join(present_methods) or "none",
                    ", ".join(missing_methods),
                ),
            )
        return "READY", "`benchmark_readiness.external_metric_methods` covers required tools"
    done = bool(gates.get(req["gate"]))
    evidence = f"`publication_gates.{req['gate']}=true`" if done else req["missing"]
    return ("READY" if done else "MISSING"), evidence


def sra_items(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in summary.get("sra_runinfo", [])
        if "Saussurea involucrata" in item.get("scientific_names", [])
    ]


def saussurea_supporting_rows(status_path: Path) -> list[dict[str, Any]]:
    payload = load_optional_json(status_path.parent / "saussurea_supporting_evidence.json")
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("rows") or payload.get("evidence") or []
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)]


def saussurea_supporting_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "saussurea_supporting_evidence_count": len(rows),
        "saussurea_supporting_runinfo_rows": sum(1 for row in rows if int(row.get("run_count") or 0) > 0),
        "saussurea_discovered_runinfo_candidate_count": sum(
            1 for row in rows if row.get("status") == "discovered_runinfo_candidate"
        ),
        "saussurea_supporting_sra_run_count": sum(int(row.get("run_count") or 0) for row in rows),
    }


def requirement_records(summary: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for req in REQUIREMENTS:
        status, evidence = requirement_status(req, summary)
        records.append(
            {
                "id": req["id"],
                "requirement": req["requirement"],
                "gate": req["gate"],
                "status": status,
                "evidence_or_missing_item": evidence,
            }
        )
    return records


def build_matrix(status_summary: str | Path) -> dict[str, Any]:
    status_path = Path(status_summary)
    summary = load_json(status_path)
    requirements = requirement_records(summary)
    counts = Counter(item["status"] for item in requirements)
    benchmark_readiness = summary.get("benchmark_readiness", {})
    gap_audit_summary = (summary.get("public_discovery") or {}).get("gap_audit", {}).get("summary", {})
    if not gap_audit_summary:
        gap_audit_summary = (summary.get("gap_audit") or {}).get("summary", {})
    supporting_rows = saussurea_supporting_rows(status_path)
    supporting_summary = saussurea_supporting_summary(supporting_rows)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status_summary_path": str(status_path),
        "summary": {
            "requirement_count": len(requirements),
            "ready_count": counts.get("READY", 0),
            "partial_count": counts.get("PARTIAL", 0),
            "missing_count": counts.get("MISSING", 0),
            "top_journal_ready": counts.get("PARTIAL", 0) == 0 and counts.get("MISSING", 0) == 0,
            "external_metric_methods": benchmark_readiness.get("external_metric_methods", []),
            "external_missing_methods": benchmark_readiness.get("external_missing_methods", []),
            "snow_lotus_scRNA_present": summary.get("publication_gates", {}).get(
                "snow_lotus_scRNA_present", False
            ),
            "public_discovery_requires_followup": bool(
                gap_audit_summary.get("requires_downloader_or_manifest_followup")
                or gap_audit_summary.get("requires_manual_manifest_review")
            ),
            **supporting_summary,
        },
        "requirements": requirements,
        "hard_gaps": HARD_GAPS,
        "training_runs": summary.get("runs", []),
        "data_integrity": summary.get("data_integrity", {}),
        "benchmark_readiness": benchmark_readiness,
        "public_data_targets": summary.get("public_data_targets", []),
        "strict_benchmarks": summary.get("strict_benchmarks", []),
        "external_benchmarks": summary.get("external_benchmarks", []),
        "saussurea_sra_runinfo": sra_items(summary),
        "saussurea_supporting_evidence": supporting_rows,
    }


def latest_run_line(summary: dict[str, Any]) -> str:
    runs = summary.get("runs", [])
    completed = [run for run in runs if run.get("has_checkpoint")]
    if not completed:
        return "No checkpoints yet."
    lines = []
    for run in completed:
        latest = run.get("latest_epoch") or {}
        epoch = latest.get("epoch")
        fine = latest.get("fine_macro_f1")
        coarse = latest.get("coarse_macro_f1")
        metrics = []
        if epoch is not None:
            metrics.append(f"epoch={epoch}")
        if fine is not None:
            metrics.append(f"fine_macro_f1={fine:.4f}")
        if coarse is not None:
            metrics.append(f"coarse_macro_f1={coarse:.4f}")
        lines.append(f"- `{run['path']}`: checkpoint, {', '.join(metrics) or 'metrics pending'}")
    return "\n".join(lines)


def data_target_table(summary: dict[str, Any]) -> str:
    rows = [
        "| Dataset | Stage | Manifest rows | Raw files | NPZ files |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for target in summary.get("public_data_targets", []):
        manifest_rows = target.get("manifest", {}).get("rows", 0)
        available_rows = (target.get("available_manifest") or {}).get("rows", 0)
        rows.append(
            "| {dataset} | {stage} | {rows} | {raw} | {npz} |".format(
                dataset=target.get("dataset_id"),
                stage=target.get("stage"),
                rows=manifest_rows or available_rows,
                raw=target.get("raw_files", {}).get("file_count", 0),
                npz=target.get("npz_files", {}).get("file_count", 0),
            )
        )
    return "\n".join(rows)


def strict_benchmark_lines(summary: dict[str, Any]) -> str:
    items = summary.get("strict_benchmarks", [])
    if not items:
        return "No strict benchmark artifacts yet."
    lines = []
    for item in items:
        metric = ""
        if item.get("fine_test_macro_f1") is not None:
            metric = f", fine_test_macro_f1={item['fine_test_macro_f1']:.4f}"
        lines.append(
            f"- `{item['path']}`: {item.get('kind')}, "
            f"supervised_ready={item.get('supervised_benchmark_ready')}{metric}"
        )
    return "\n".join(lines)


def benchmark_readiness_lines(summary: dict[str, Any]) -> str:
    readiness = summary.get("benchmark_readiness", {})
    if not readiness:
        return "Benchmark readiness summary has not been generated yet."
    lines = [
        f"- Baseline metric artifacts: `{readiness.get('baseline_metric_count', 0)}`",
        f"- Split audit artifacts: `{readiness.get('split_audit_count', 0)}`",
        f"- Supervised-ready split audits: `{readiness.get('supervised_split_audit_count', 0)}`",
        f"- Marker candidate artifact present: `{readiness.get('marker_candidate_artifact_present')}`",
        f"- External benchmark files: `{readiness.get('external_benchmark_count', 0)}`",
        f"- External metric benchmark files: `{readiness.get('external_metric_count', 0)}`",
        "- External metric methods present: `{}`".format(
            ", ".join(readiness.get("external_metric_methods") or []) or "none"
        ),
        "- External metric methods missing: `{}`".format(
            ", ".join(readiness.get("external_missing_methods") or []) or "none"
        ),
    ]
    return "\n".join(lines)


def external_benchmark_lines(summary: dict[str, Any]) -> str:
    items = summary.get("external_benchmarks", [])
    if not items:
        return "No external benchmark metric artifacts yet."
    lines = []
    for item in items:
        metric = ""
        if item.get("fine_test_macro_f1") is not None:
            metric = f", fine_test_macro_f1={item['fine_test_macro_f1']:.4f}"
        if item.get("coarse_test_macro_f1") is not None:
            metric += f", coarse_test_macro_f1={item['coarse_test_macro_f1']:.4f}"
        lines.append(
            f"- `{item['path']}`: {item.get('method')}, "
            f"metric={item.get('has_metric')}, test_cells={item.get('test_cells')}{metric}"
        )
    return "\n".join(lines)


def data_integrity_lines(summary: dict[str, Any]) -> str:
    integrity = summary.get("data_integrity", {})
    if not integrity.get("exists"):
        return "Data integrity audit has not been generated yet."
    return "\n".join(
        [
            f"- Manifests audited: `{integrity.get('manifest_count', 0)}`",
            f"- Matrix files audited: `{integrity.get('matrix_count', 0)}`",
            f"- Missing files: `{integrity.get('missing_files', 0)}`",
            f"- Unreadable files: `{integrity.get('unreadable_files', 0)}`",
            f"- Total readable cells: `{integrity.get('total_cells', 0)}`",
        ]
    )


def sra_lines(summary: dict[str, Any]) -> str:
    supporting = summary.get("saussurea_supporting_evidence") or []
    if supporting:
        lines = []
        for item in supporting:
            lines.append(
                "- `{dataset}`: status={status}, accession={accession}, runs={runs}, "
                "strategies={strategies}, total_size_mb={size:.1f}, source_page={source_page}".format(
                    dataset=item.get("dataset_id", "unknown"),
                    status=item.get("status", "unknown"),
                    accession=item.get("accession_or_doi", ""),
                    runs=int(item.get("run_count") or 0),
                    strategies=item.get("library_strategies") or "unknown",
                    size=float(item.get("total_size_mb") or 0),
                    source_page=item.get("source_page_present"),
                )
            )
        return "\n".join(lines)

    items = summary.get("sra_runinfo", [])
    if not items:
        return "No Saussurea SRA runinfo files found yet."
    lines = []
    for item in items:
        lines.append(
            f"- `{item['path']}`: {item['rows']} runs, "
            f"strategies={','.join(item.get('library_strategies', []))}, "
            f"total_size_mb={item.get('total_size_mb', 0):.1f}"
        )
    return "\n".join(lines)


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    summary = {
        "runs": payload.get("training_runs", []),
        "data_integrity": payload.get("data_integrity", {}),
        "benchmark_readiness": payload.get("benchmark_readiness", {}),
        "public_data_targets": payload.get("public_data_targets", []),
        "strict_benchmarks": payload.get("strict_benchmarks", []),
        "external_benchmarks": payload.get("external_benchmarks", []),
        "sra_runinfo": payload.get("saussurea_sra_runinfo", []),
        "saussurea_supporting_evidence": payload.get("saussurea_supporting_evidence", []),
    }
    lines = [
        "# SnowLotus-CellFM Top-Journal Readiness Matrix",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Gate Matrix",
        "",
        "| ID | Requirement | Status | Evidence / Missing item |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["requirements"]:
        lines.append(
            "| {id} | {requirement} | {status} | {evidence} |".format(
                id=item["id"],
                requirement=item["requirement"],
                status=status_icon(item["status"]),
                evidence=item["evidence_or_missing_item"],
            )
        )
    lines.extend(
        [
            "",
            "## Current Training Evidence",
            "",
            latest_run_line(summary),
            "",
            "## Data Integrity Evidence",
            "",
            data_integrity_lines(summary),
            "",
            "## Benchmark Readiness Evidence",
            "",
            benchmark_readiness_lines(summary),
            "",
            "## Public Data Targets",
            "",
            data_target_table(summary),
            "",
            "## Strict Benchmark Evidence",
            "",
            strict_benchmark_lines(summary),
            "",
            "## External Benchmark Evidence",
            "",
            external_benchmark_lines(summary),
            "",
            "## Saussurea Supporting Transcriptome Evidence",
            "",
            sra_lines(summary),
            "",
            "## Remaining Hard Gaps",
            "",
            *[f"- {item}" for item in payload["hard_gaps"]],
            "",
        ]
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(output_path)
    return output_path


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output_path)
    return output_path


def write_matrix(status_summary: str | Path, output: str | Path, output_json: str | Path | None = None) -> Path:
    payload = build_matrix(status_summary)
    output_path = write_markdown(payload, output)
    if output_json is not None:
        write_json(payload, output_json)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a top-journal readiness matrix from status_summary.json")
    parser.add_argument("--status-summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--output-json")
    args = parser.parse_args()
    write_matrix(args.status_summary, args.output, args.output_json)


if __name__ == "__main__":
    main()
