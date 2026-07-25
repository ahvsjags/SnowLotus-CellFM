from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SAFE_RUN_ID = "foundation_5090_mlm_public_late_refresh_safe"
PUBLIC_SAFE_INIT_RUN_ID = "foundation_5090_public_safe_init"
PUBLIC_EXPANSION_CONTINUATION_RUN_ID = "foundation_5090_mlm_public_expansion_continuation"


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


_MISSING = object()


def nested_get(mapping: dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def first_non_none(mapping: dict[str, Any], *paths: str, default: Any = None) -> Any:
    for dotted_path in paths:
        value = nested_get(mapping, dotted_path, _MISSING)
        if value is not _MISSING and value is not None:
            return value
    return default


def relative_text(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def collect_detailed_evaluations(project_dir: Path) -> list[dict[str, Any]]:
    base_dir = project_dir / "outputs" / "detailed_evaluations"
    evaluations: list[dict[str, Any]] = []
    if not base_dir.exists():
        return evaluations
    for metrics_path in sorted(base_dir.glob("**/detailed_metrics.json")):
        payload = read_json(metrics_path)
        if not isinstance(payload, dict):
            continue
        summary = payload.get("summary") or {}
        fine = summary.get("fine") or {}
        coarse = summary.get("coarse") or {}
        artifacts = payload.get("artifacts") or {}
        markdown_path = metrics_path.with_name("detailed_evaluation.md")
        evaluations.append(
            {
                "run_id": metrics_path.parent.name,
                "metrics_json": relative_text(metrics_path, project_dir),
                "markdown": relative_text(markdown_path, project_dir)
                if markdown_path.exists()
                else "",
                "predictions_tsv": str(artifacts.get("predictions_tsv") or ""),
                "fine_confusion_matrix_tsv": str(
                    artifacts.get("fine_confusion_matrix_tsv") or ""
                ),
                "coarse_confusion_matrix_tsv": str(
                    artifacts.get("coarse_confusion_matrix_tsv") or ""
                ),
                "generated_at_utc": payload.get("generated_at_utc"),
                "checkpoint_path": payload.get("checkpoint_path"),
                "split": payload.get("split"),
                "evaluated_cells": summary.get("evaluated_cells"),
                "fine_accuracy": fine.get("accuracy"),
                "fine_macro_f1": fine.get("macro_f1"),
                "fine_weighted_f1": fine.get("weighted_f1"),
                "coarse_accuracy": coarse.get("accuracy"),
                "coarse_macro_f1": coarse.get("macro_f1"),
                "coarse_weighted_f1": coarse.get("weighted_f1"),
            }
        )
    return sorted(
        evaluations,
        key=lambda item: (
            str(item.get("generated_at_utc") or ""),
            str(item.get("run_id") or ""),
        ),
    )


def load_inputs(project_dir: Path) -> dict[str, Any]:
    package_dir = project_dir / "outputs" / "publication_package"
    return {
        "status_summary": read_json(package_dir / "status_summary.json") or {},
        "training_curve": read_json(package_dir / "training_curve_summary.json") or {},
        "training_health": read_json(package_dir / "training_health_audit.json") or {},
        "model_release": read_json(package_dir / "model_release_manifest.json") or {},
        "annotation_bundles": read_json(package_dir / "annotation_bundle_index.json") or {},
        "data_integrity": read_json(package_dir / "data_integrity_audit.json") or {},
        "download_progress": read_json(package_dir / "download_progress_audit.json") or {},
        "benchmark_gap": read_json(package_dir / "benchmark_gap_audit.json") or {},
        "saussurea_contract": read_json(package_dir / "saussurea_h5ad_contract.json") or {},
        "saussurea_discovery": read_json(package_dir / "saussurea_public_data_discovery.json") or {},
        "saussurea_data_request": read_json(package_dir / "saussurea_data_request_package.json") or {},
        "scplantannotate_access": read_json(package_dir / "scplantannotate_access_audit.json") or {},
        "submission_actions": read_json(package_dir / "submission_action_plan.json") or {},
        "detailed_evaluations": collect_detailed_evaluations(project_dir),
    }


def find_run(payload: dict[str, Any], run_id: str) -> dict[str, Any]:
    for run in payload.get("runs", []):
        if run.get("run_id") == run_id:
            return run
    return {}


def find_status_run(status_summary: dict[str, Any], run_id: str) -> dict[str, Any]:
    for run in status_summary.get("runs", []):
        if str(run.get("path") or "").endswith(run_id):
            return run
    return {}


def run_output_dir(project_dir: Path, run: dict[str, Any]) -> Path:
    run_path = Path(str(run.get("path") or run.get("output_dir") or ""))
    if not run_path:
        return project_dir
    return run_path if run_path.is_absolute() else project_dir / run_path


def run_target_epochs(
    status_summary: dict[str, Any],
    project_dir: Path,
    run_id: str,
    default: int,
) -> int:
    for run in status_summary.get("runs", []):
        run_path_text = str(run.get("path") or "")
        if not run_path_text.endswith(run_id):
            continue
        run_path = run_output_dir(project_dir, run)
        config = read_json(run_path / "config.resolved.json")
        if isinstance(config, dict):
            epochs = (config.get("train") or {}).get("epochs")
            if epochs:
                return int(epochs)
    return default


def best_history_epoch(project_dir: Path, run: dict[str, Any]) -> dict[str, Any]:
    output_dir = run_output_dir(project_dir, run)
    history = read_json(output_dir / "history.json")
    epochs = (history or {}).get("epochs", [])
    metric_rows = [
        row for row in epochs if isinstance(row, dict) and row.get("fine_macro_f1") is not None
    ]
    if not metric_rows:
        return {}
    return max(metric_rows, key=lambda row: float(row.get("fine_macro_f1") or 0.0))


def hard_actions(actions_payload: dict[str, Any]) -> list[dict[str, Any]]:
    hard_statuses = {"MISSING"}
    return [
        action
        for action in actions_payload.get("actions", [])
        if str(action.get("status", "")).startswith("BLOCKED")
        or str(action.get("status", "")) in hard_statuses
    ]


def in_progress_actions(actions_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        action
        for action in actions_payload.get("actions", [])
        if str(action.get("status", "")) == "IN_PROGRESS"
    ]


def running_training_actions(training_health: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for run in training_health.get("runs", []):
        status = str(run.get("status") or "")
        if not status.startswith("running"):
            continue
        run_id = str(run.get("run_id") or "training_run")
        latest_epoch = run.get("latest_epoch") or {}
        runtime = run.get("runtime") or {}
        evidence_parts = [
            f"status={status}",
            f"epochs_recorded={run.get('epochs_recorded', 0)}",
        ]
        if latest_epoch.get("fine_macro_f1") is not None:
            evidence_parts.append(f"fine_macro_f1={fmt(latest_epoch.get('fine_macro_f1'))}")
        if runtime.get("tmux_active"):
            evidence_parts.append(f"tmux={runtime.get('session')}")
        actions.append(
            {
                "id": f"continue_{run_id}",
                "priority": "A" if run_id == PUBLIC_SAFE_INIT_RUN_ID else "B",
                "status": "IN_PROGRESS",
                "evidence": "; ".join(evidence_parts),
                "next_action": "Allow the remote tmux training job to finish, then rerun publication package generation and final metrics.",
            }
        )
    return actions


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def build_dossier(project_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    inputs = load_inputs(root)
    status_summary = inputs["status_summary"]
    training_curve = inputs["training_curve"]
    training_health = inputs["training_health"]
    curve_safe_run = find_run(training_curve, SAFE_RUN_ID)
    health_safe_run = find_run(training_health, SAFE_RUN_ID)
    safe_run = curve_safe_run or health_safe_run
    safe_epochs = int(safe_run.get("epochs_recorded") or 0)
    safe_target = run_target_epochs(status_summary, root, SAFE_RUN_ID, 8)
    latest_eval_loss = safe_run.get("latest_eval_loss")
    eval_delta = nested_get(safe_run, "eval_loss_delta.absolute")
    safe_complete = bool(safe_target and safe_epochs >= safe_target)
    public_safe_init_status_run = find_status_run(status_summary, PUBLIC_SAFE_INIT_RUN_ID)
    public_safe_init_health_run = find_run(training_health, PUBLIC_SAFE_INIT_RUN_ID)
    public_safe_init_run = public_safe_init_status_run or public_safe_init_health_run
    public_safe_init_epochs = int(public_safe_init_run.get("epochs_recorded") or 0)
    public_safe_init_target = run_target_epochs(status_summary, root, PUBLIC_SAFE_INIT_RUN_ID, 12)
    public_safe_init_complete = bool(
        public_safe_init_target and public_safe_init_epochs >= public_safe_init_target
    )
    public_safe_init_best_epoch = best_history_epoch(root, public_safe_init_status_run)
    public_safe_init_test_metrics = public_safe_init_status_run.get("test_metrics") or {}
    continuation_curve_run = find_run(training_curve, PUBLIC_EXPANSION_CONTINUATION_RUN_ID)
    continuation_health_run = find_run(training_health, PUBLIC_EXPANSION_CONTINUATION_RUN_ID)
    continuation_run = continuation_curve_run or continuation_health_run
    continuation_epochs = int(continuation_run.get("epochs_recorded") or 0)
    continuation_target = run_target_epochs(
        status_summary, root, PUBLIC_EXPANSION_CONTINUATION_RUN_ID, 20
    )
    continuation_latest_eval_loss = continuation_run.get("latest_eval_loss")
    continuation_latest_train_loss = continuation_run.get("latest_train_loss")
    continuation_progress = continuation_run.get("latest_progress") or {}
    continuation_progress_epoch = continuation_progress.get("epoch")
    continuation_progress_step = continuation_progress.get("step")

    model_summary = inputs["model_release"].get("summary", {})
    bundle_summary = inputs["annotation_bundles"].get("summary", {})
    annotated_cell_count = int(
        bundle_summary.get("annotated_cells") or bundle_summary.get("total_cells") or 0
    )
    data_integrity_summary = inputs["data_integrity"].get("summary", {})
    discovery_summary = inputs["saussurea_discovery"].get("summary", {})
    saussurea_literature_report_count = int(
        discovery_summary.get("single_cell_literature_report_count") or 0
    )
    saussurea_public_matrix_found = bool(
        discovery_summary.get("public_downloadable_saussurea_single_cell_matrix_found")
    )
    saussurea_low_confidence_query_count = int(
        discovery_summary.get("low_confidence_query_count") or 0
    )
    data_request_summary = inputs["saussurea_data_request"].get("summary", {})
    saussurea_data_request_candidate_count = int(
        data_request_summary.get("request_candidate_count") or 0
    )
    saussurea_data_request_package_ready = bool(data_request_summary.get("package_ready"))
    scplant_summary = inputs["scplantannotate_access"].get("summary", {})
    benchmark_summary = inputs["benchmark_gap"].get("summary", {})
    contract = inputs["saussurea_contract"]
    actions = inputs["submission_actions"]
    detailed_evaluations = inputs["detailed_evaluations"]
    preferred_detailed = [
        item
        for item in detailed_evaluations
        if PUBLIC_SAFE_INIT_RUN_ID in str(item.get("run_id") or "")
    ]
    latest_detailed_eval = (
        preferred_detailed[-1]
        if preferred_detailed
        else detailed_evaluations[-1]
        if detailed_evaluations
        else {}
    )
    detailed_eval_cell_count = sum(
        int(item.get("evaluated_cells") or 0) for item in detailed_evaluations
    )

    contract_ready = bool(
        first_non_none(contract, "contract_ready", "summary.contract_ready", default=False)
    )
    contract_input = first_non_none(
        contract,
        "input",
        "input_path",
        "path",
        "summary.input",
        "summary.path",
        default="data/saussurea_involucrata.h5ad",
    )
    scplant_ready = bool(scplant_summary.get("comparison_ready"))
    hard_blockers = hard_actions(actions)
    progress_items = in_progress_actions(actions)
    progress_ids = {str(item.get("id")) for item in progress_items}
    for training_action in running_training_actions(training_health):
        if str(training_action.get("id")) not in progress_ids:
            progress_items.append(training_action)
            progress_ids.add(str(training_action.get("id")))
    top_journal_ready = bool(benchmark_summary.get("top_journal_benchmark_ready"))
    overall_status = (
        "READY_FOR_CLAIM_AUDIT"
        if safe_complete and contract_ready and scplant_ready and top_journal_ready and not hard_blockers
        else "IN_PROGRESS"
    )

    defensible_claims = [
        "The remote RTX 5090 pipeline can train, checkpoint, resume, and refresh the publication package."
    ]
    if model_summary.get("checkpoint_count"):
        defensible_claims.append(
            "Readable SnowLotus-CellFM checkpoints are indexed with epochs, vocab sizes, metrics, bytes, and SHA256 hashes."
        )
    if bundle_summary.get("label_ready_count"):
        defensible_claims.append(
            "At least one label-ready annotation bundle is available for inspected public plant single-cell data."
        )
    if safe_epochs:
        defensible_claims.append(
            f"The safe public MLM refresh has recorded {safe_epochs}/{safe_target} target epochs with latest eval loss {fmt(latest_eval_loss)}."
        )
    if public_safe_init_complete:
        defensible_claims.append(
            "The public safe-init hybrid run completed 12/12 epochs with a best validation fine macro-F1 of "
            f"{fmt(public_safe_init_best_epoch.get('fine_macro_f1'))} and test fine macro-F1 of "
            f"{fmt(public_safe_init_test_metrics.get('fine_macro_f1'))}."
        )
    if continuation_epochs:
        defensible_claims.append(
            "The public MLM expansion continuation has recorded "
            f"{continuation_epochs}/{continuation_target} epochs with latest eval loss "
            f"{fmt(continuation_latest_eval_loss)} while the remote continuation job keeps running."
        )
    if latest_detailed_eval:
        defensible_claims.append(
            "A deterministic detailed checkpoint evaluation is available for "
            f"`{latest_detailed_eval.get('run_id')}` on `{latest_detailed_eval.get('split')}` "
            f"with {latest_detailed_eval.get('evaluated_cells')} cells, fine macro-F1 "
            f"{fmt(latest_detailed_eval.get('fine_macro_f1'))}, and coarse macro-F1 "
            f"{fmt(latest_detailed_eval.get('coarse_macro_f1'))}."
        )
    if saussurea_literature_report_count:
        defensible_claims.append(
            "A request-only Saussurea involucrata single-cell transcriptomics literature report is recorded, "
            "but no public downloadable Snow Lotus single-cell matrix is available for training or benchmarking."
        )
    if saussurea_data_request_package_ready:
        defensible_claims.append(
            "A structured Saussurea single-cell data-request package is ready with required files, metadata fields, validation commands, and an email template."
        )

    do_not_claim_yet: list[str] = []
    if not contract_ready:
        do_not_claim_yet.append(
            f"Do not claim a primary Saussurea involucrata single-cell atlas until {contract_input} passes the h5ad contract."
        )
    if saussurea_literature_report_count and not saussurea_public_matrix_found:
        do_not_claim_yet.append(
            "Do not treat the request-only Snow Lotus single-cell literature report as reusable training or benchmark data until the matrix is obtained and licensed for analysis."
        )
    if not scplant_ready:
        do_not_claim_yet.append(
            "Do not claim head-to-head superiority over scPlantAnnotate until an authorized reproducible benchmark is present."
        )
    if not safe_complete:
        do_not_claim_yet.append(
            f"Do not present the safe public MLM refresh as final until it reaches {safe_target} epochs."
        )
    if not top_journal_ready:
        do_not_claim_yet.append(
            "Do not freeze top-journal claims until all S/A benchmark gates are READY."
        )

    reproduction_commands = [
        {
            "purpose": "Regenerate the full publication package",
            "command": "bash scripts/generate_publication_package.sh",
        },
        {
            "purpose": "Keep the package refreshing after each safe MLM epoch",
            "command": "bash scripts/start_publication_package_watchdog.sh",
        },
        {
            "purpose": "Resume or continue the safe public MLM refresh",
            "command": "bash scripts/watch_safe_mlm_refresh.sh",
        },
        {
            "purpose": "Keep the public MLM expansion continuation alive with resume support",
            "command": "bash scripts/start_public_mlm_continuation_watchdog.sh",
        },
        {
            "purpose": "Refresh the publication package after public MLM continuation epochs",
            "command": "bash scripts/start_public_mlm_continuation_package_watchdog.sh",
        },
        {
            "purpose": "Keep the GSE226097 Arabidopsis lifecycle subset download and conversion alive",
            "command": "bash scripts/start_gse226097_lifecycle_watchdog.sh",
        },
        {
            "purpose": "Create the public safe-init annotation bundle",
            "command": "bash scripts/create_public_safe_init_annotation_bundle.sh",
        },
        {
            "purpose": "Run deterministic detailed evaluation for the public safe-init checkpoint",
            "command": (
                "python scripts/evaluate_checkpoint_detailed.py "
                "--config configs/generated/foundation_5090_public_safe_init.resume.yaml "
                "--checkpoint outputs/foundation_5090_public_safe_init/best.pt "
                "--split test "
                "--output-dir outputs/detailed_evaluations/foundation_5090_public_safe_init_test "
                "--device cuda "
                "--batch-size 64"
            ),
        },
        {
            "purpose": "Validate the required Snow Lotus h5ad contract",
            "command": (
                "python scripts/validate_saussurea_h5ad_contract.py "
                "--input data/saussurea_involucrata.h5ad "
                "--output-md outputs/publication_package/saussurea_h5ad_contract.md "
                "--output-json outputs/publication_package/saussurea_h5ad_contract.json"
            ),
        },
        {
            "purpose": "Regenerate the request-only Snow Lotus single-cell data package",
            "command": (
                "python scripts/write_saussurea_data_request_package.py "
                "--project-dir . "
                "--output-md outputs/publication_package/saussurea_data_request_package.md "
                "--output-json outputs/publication_package/saussurea_data_request_package.json "
                "--output-email outputs/publication_package/saussurea_data_request_email.txt"
            ),
        },
    ]

    return {
        "project_dir": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "overall_status": overall_status,
            "safe_training_run_id": SAFE_RUN_ID,
            "safe_training_epochs": safe_epochs,
            "safe_training_target_epochs": safe_target,
            "safe_training_complete": safe_complete,
            "public_safe_init_epochs": public_safe_init_epochs,
            "public_safe_init_target_epochs": public_safe_init_target,
            "public_safe_init_complete": public_safe_init_complete,
            "public_safe_init_best_epoch": public_safe_init_best_epoch.get("epoch"),
            "public_safe_init_best_fine_macro_f1": public_safe_init_best_epoch.get("fine_macro_f1"),
            "public_safe_init_best_coarse_macro_f1": public_safe_init_best_epoch.get("coarse_macro_f1"),
            "public_safe_init_test_fine_macro_f1": public_safe_init_test_metrics.get("fine_macro_f1"),
            "public_safe_init_test_coarse_macro_f1": public_safe_init_test_metrics.get("coarse_macro_f1"),
            "public_expansion_continuation_run_id": PUBLIC_EXPANSION_CONTINUATION_RUN_ID,
            "public_expansion_continuation_epochs": continuation_epochs,
            "public_expansion_continuation_target_epochs": continuation_target,
            "public_expansion_continuation_latest_eval_loss": continuation_latest_eval_loss,
            "public_expansion_continuation_latest_train_loss": continuation_latest_train_loss,
            "public_expansion_continuation_progress_epoch": continuation_progress_epoch,
            "public_expansion_continuation_progress_step": continuation_progress_step,
            "latest_eval_loss": latest_eval_loss,
            "eval_loss_delta_absolute": eval_delta,
            "checkpoint_count": int(model_summary.get("checkpoint_count") or 0),
            "label_release_candidate_count": int(
                model_summary.get("label_release_candidate_count") or 0
            ),
            "embedding_release_candidate_count": int(
                model_summary.get("embedding_release_candidate_count") or 0
            ),
            "annotation_bundle_count": int(bundle_summary.get("bundle_count") or 0),
            "label_ready_annotation_bundle_count": int(
                bundle_summary.get("label_ready_count") or 0
            ),
            "annotated_cell_count": annotated_cell_count,
            "detailed_evaluation_count": len(detailed_evaluations),
            "detailed_evaluation_cell_count": detailed_eval_cell_count,
            "latest_detailed_evaluation_run_id": latest_detailed_eval.get("run_id"),
            "latest_detailed_evaluation_split": latest_detailed_eval.get("split"),
            "latest_detailed_evaluation_cells": latest_detailed_eval.get("evaluated_cells"),
            "latest_detailed_evaluation_fine_macro_f1": latest_detailed_eval.get("fine_macro_f1"),
            "latest_detailed_evaluation_coarse_macro_f1": latest_detailed_eval.get(
                "coarse_macro_f1"
            ),
            "data_integrity_missing_files": int(data_integrity_summary.get("missing_files") or 0),
            "saussurea_contract_ready": contract_ready,
            "saussurea_contract_input": str(contract_input),
            "snow_lotus_primary_scrna_publicly_found": bool(
                discovery_summary.get("snow_lotus_primary_scrna_publicly_found")
            ),
            "saussurea_single_cell_literature_report_count": saussurea_literature_report_count,
            "saussurea_public_downloadable_single_cell_matrix_found": saussurea_public_matrix_found,
            "saussurea_low_confidence_query_count": saussurea_low_confidence_query_count,
            "saussurea_data_request_candidate_count": saussurea_data_request_candidate_count,
            "saussurea_data_request_package_ready": saussurea_data_request_package_ready,
            "scplantannotate_comparison_ready": scplant_ready,
            "top_journal_benchmark_ready": top_journal_ready,
            "hard_blocker_count": len(hard_blockers),
            "in_progress_count": len(progress_items),
        },
        "hard_blockers": hard_blockers,
        "in_progress_items": progress_items,
        "detailed_evaluations": detailed_evaluations,
        "defensible_claims_now": defensible_claims,
        "do_not_claim_yet": do_not_claim_yet,
        "reproduction_commands": reproduction_commands,
    }


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output_path)
    return output_path


def action_table(actions: list[dict[str, Any]]) -> list[str]:
    rows = [
        "| ID | Priority | Status | Evidence | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    if not actions:
        rows.append("| - | - | - | - | - |")
        return rows
    for action in actions:
        rows.append(
            "| {id} | {priority} | {status} | {evidence} | {next_action} |".format(
                id=str(action.get("id", "")).replace("|", "/"),
                priority=str(action.get("priority", "")).replace("|", "/"),
                status=str(action.get("status", "")).replace("|", "/"),
                evidence=str(action.get("evidence", "")).replace("|", "/"),
                next_action=str(action.get("next_action", "")).replace("|", "/"),
            )
        )
    return rows


def detailed_evaluation_table(items: list[dict[str, Any]]) -> list[str]:
    rows = [
        "| Run | Split | Cells | Fine macro-F1 | Coarse macro-F1 | Metrics |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    if not items:
        rows.append("| - | - | - | - | - | - |")
        return rows
    for item in items:
        rows.append(
            "| {run_id} | {split} | {cells} | {fine} | {coarse} | `{metrics}` |".format(
                run_id=str(item.get("run_id") or "").replace("|", "/"),
                split=str(item.get("split") or "").replace("|", "/"),
                cells=int(item.get("evaluated_cells") or 0),
                fine=fmt(item.get("fine_macro_f1")),
                coarse=fmt(item.get("coarse_macro_f1")),
                metrics=str(item.get("metrics_json") or "").replace("|", "/"),
            )
        )
    return rows


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# SnowLotus-CellFM Submission Dossier",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Executive Status",
        "",
        f"- Overall status: `{summary['overall_status']}`",
        (
            f"- Safe public MLM refresh: `{summary['safe_training_epochs']}/"
            f"{summary['safe_training_target_epochs']}` epochs; latest eval loss "
            f"`{fmt(summary['latest_eval_loss'])}`; eval delta "
            f"`{fmt(summary['eval_loss_delta_absolute'])}`"
        ),
        (
            f"- Public safe-init hybrid refresh: `{summary['public_safe_init_epochs']}/"
            f"{summary['public_safe_init_target_epochs']}` epochs; best validation fine macro-F1 "
            f"`{fmt(summary['public_safe_init_best_fine_macro_f1'])}` at epoch "
            f"`{fmt(summary['public_safe_init_best_epoch'], digits=0)}`; test fine macro-F1 "
            f"`{fmt(summary['public_safe_init_test_fine_macro_f1'])}`; test coarse macro-F1 "
            f"`{fmt(summary['public_safe_init_test_coarse_macro_f1'])}`"
        ),
        (
            f"- Public MLM expansion continuation: "
            f"`{summary['public_expansion_continuation_epochs']}/"
            f"{summary['public_expansion_continuation_target_epochs']}` epochs; latest eval loss "
            f"`{fmt(summary['public_expansion_continuation_latest_eval_loss'])}`; current progress "
            f"epoch=`{fmt(summary['public_expansion_continuation_progress_epoch'], digits=0)}` "
            f"step=`{fmt(summary['public_expansion_continuation_progress_step'], digits=0)}`"
        ),
        (
            f"- Model release index: `{summary['checkpoint_count']}` checkpoints; "
            f"`{summary['label_release_candidate_count']}` label-release candidates; "
            f"`{summary['embedding_release_candidate_count']}` embedding-release candidates"
        ),
        (
            f"- Annotation bundles: `{summary['annotation_bundle_count']}` total; "
            f"`{summary['label_ready_annotation_bundle_count']}` label-ready; "
            f"`{summary['annotated_cell_count']}` cells"
        ),
        (
            f"- Detailed checkpoint evaluations: `{summary['detailed_evaluation_count']}` runs; "
            f"`{summary['detailed_evaluation_cell_count']}` evaluated cells; latest "
            f"`{summary['latest_detailed_evaluation_run_id']}` fine macro-F1 "
            f"`{fmt(summary['latest_detailed_evaluation_fine_macro_f1'])}`"
        ),
        (
            f"- Saussurea h5ad gate: contract_ready=`{summary['saussurea_contract_ready']}`; "
            f"input=`{summary['saussurea_contract_input']}`"
        ),
        (
            f"- Saussurea public single-cell evidence: literature_reports="
            f"`{summary['saussurea_single_cell_literature_report_count']}`; "
            f"public_downloadable_matrix="
            f"`{summary['saussurea_public_downloadable_single_cell_matrix_found']}`; "
            f"low_confidence_queries=`{summary['saussurea_low_confidence_query_count']}`"
        ),
        (
            f"- Saussurea data request package: candidates="
            f"`{summary['saussurea_data_request_candidate_count']}`; "
            f"ready=`{summary['saussurea_data_request_package_ready']}`"
        ),
        (
            f"- scPlantAnnotate gate: comparison_ready="
            f"`{summary['scplantannotate_comparison_ready']}`"
        ),
        f"- Hard blockers: `{summary['hard_blocker_count']}`",
        "",
        "## Hard Blockers",
        "",
        "\n".join(action_table(payload["hard_blockers"])),
        "",
        "## In Progress",
        "",
        "\n".join(action_table(payload["in_progress_items"])),
        "",
        "## Detailed Evaluations",
        "",
        "\n".join(detailed_evaluation_table(payload["detailed_evaluations"])),
        "",
        "## Defensible Claims Now",
        "",
    ]
    lines.extend(f"- {claim}" for claim in payload["defensible_claims_now"])
    lines.extend(["", "## Do Not Claim Yet", ""])
    if payload["do_not_claim_yet"]:
        lines.extend(f"- {claim}" for claim in payload["do_not_claim_yet"])
    else:
        lines.append("- No current claim holds from this automated dossier.")
    lines.extend(["", "## Reproduction Commands", ""])
    for item in payload["reproduction_commands"]:
        lines.extend(
            [
                f"### {item['purpose']}",
                "",
                "```bash",
                item["command"],
                "```",
                "",
            ]
        )
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the SnowLotus-CellFM submission dossier")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    payload = build_dossier(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
