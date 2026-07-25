from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ActionItem:
    id: str
    priority: str
    status: str
    owner: str
    title: str
    evidence: str
    next_action: str
    done_when: str


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


def load_inputs(project_dir: Path) -> dict[str, Any]:
    package_dir = project_dir / "outputs" / "publication_package"
    external_dir = project_dir / "outputs" / "external_benchmarks"
    return {
        "status_summary": read_json(package_dir / "status_summary.json") or {},
        "benchmark_gap": read_json(package_dir / "benchmark_gap_audit.json") or {},
        "training_health": read_json(package_dir / "training_health_audit.json") or {},
        "training_curve": read_json(package_dir / "training_curve_summary.json") or {},
        "saussurea_contract": read_json(package_dir / "saussurea_h5ad_contract.json") or {},
        "scplantannotate_access": read_json(package_dir / "scplantannotate_access_audit.json") or {},
        "scplantannotate_plan": read_json(
            external_dir / "scplantannotate_authenticated_benchmark_plan.json"
        )
        or {},
        "download_progress": read_json(package_dir / "download_progress_audit.json") or {},
        "transfer_queue": read_json(package_dir / "transfer_queue_health_audit.json") or {},
        "public_discovery_gap": read_json(
            package_dir / "public_discovery" / "public_discovery_gap_audit.json"
        )
        or {},
        "geo_promotion": read_json(
            package_dir / "public_discovery" / "geo_manifest_promotion_candidates.json"
        )
        or read_json(project_dir / "data" / "public_discovery" / "geo_manifest_promotion_candidates.json")
        or {},
        "geo_promotion_queue": read_json(
            package_dir / "public_discovery" / "geo_promotion_download_queue.json"
        )
        or read_json(project_dir / "data" / "public_discovery" / "geo_promotion_download_queue.json")
        or {},
    }


def get_requirement(benchmark_gap: dict[str, Any], item_id: str) -> dict[str, Any]:
    for item in benchmark_gap.get("requirements", []):
        if item.get("id") == item_id:
            return item
    return {}


def safe_training_run(training_health: dict[str, Any]) -> dict[str, Any]:
    for run in training_health.get("runs", []):
        if run.get("run_id") == "foundation_5090_mlm_public_late_refresh_safe":
            return run
    return {}


def active_training_runs(training_health: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        run
        for run in training_health.get("runs", [])
        if str(run.get("status", "")).startswith("running")
    ]


def target_epochs(status_summary: dict[str, Any], project_dir: Path) -> int:
    for run in status_summary.get("runs", []):
        if run.get("path", "").endswith("foundation_5090_mlm_public_late_refresh_safe"):
            run_path = Path(run.get("path", ""))
            if not run_path.is_absolute():
                run_path = project_dir / run_path
            config = read_json(run_path / "config.resolved.json")
            if isinstance(config, dict):
                return int((config.get("train") or {}).get("epochs") or 0)
    return 8


def build_actions(project_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    inputs = load_inputs(root)
    status_summary = inputs["status_summary"]
    benchmark_gap = inputs["benchmark_gap"]
    training_health = inputs["training_health"]
    training_curve = inputs["training_curve"]
    contract = inputs["saussurea_contract"]
    scplant = inputs["scplantannotate_access"]
    scplant_plan = inputs["scplantannotate_plan"]
    download_progress = inputs["download_progress"]
    transfer_queue = inputs["transfer_queue"]
    public_discovery_gap = inputs["public_discovery_gap"]
    geo_promotion = inputs["geo_promotion"]
    geo_promotion_queue = inputs["geo_promotion_queue"]
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
    safe_run = safe_training_run(training_health)
    safe_epochs = int(safe_run.get("epochs_recorded") or 0)
    safe_target = target_epochs(status_summary, root)
    missing_external = (
        status_summary.get("benchmark_readiness", {}).get("external_missing_methods") or []
    )
    actions: list[ActionItem] = []

    actions.append(
        ActionItem(
            id="complete_safe_mlm_refresh",
            priority="S",
            status="IN_PROGRESS" if safe_epochs < safe_target else "READY",
            owner="automation",
            title="Complete the safe public MLM refresh through the configured epoch target",
            evidence=f"safe run epochs={safe_epochs}/{safe_target}; watchdog active via tmux audit",
            next_action=(
                "Let snowcell_mlm_public_late_refresh_safe continue; watchdog resumes from latest.pt "
                "if the session exits before target completion."
            ),
            done_when=(
                "training_health_audit shows safe run epochs_recorded >= configured epochs and "
                "training_curve_summary includes the final eval-loss row."
            ),
        )
    )

    for run in active_training_runs(training_health):
        run_id = str(run.get("run_id") or "unknown_training_run")
        latest_epoch = run.get("latest_epoch") or {}
        eval_loss = latest_epoch.get("eval_loss")
        evidence_parts = [
            f"status={run.get('status')}",
            f"epochs_recorded={run.get('epochs_recorded', 0)}",
        ]
        if eval_loss is not None:
            evidence_parts.append(f"latest_eval_loss={eval_loss}")
        actions.append(
            ActionItem(
                id=f"complete_{run_id}",
                priority="S" if "continuation" in run_id else "A",
                status="IN_PROGRESS",
                owner="automation",
                title=f"Complete active training run {run_id}",
                evidence="; ".join(evidence_parts),
                next_action=(
                    "Keep the tmux session and watchdog running; regenerate the publication package "
                    "after the run exits or writes a new evaluation epoch."
                ),
                done_when=(
                    "training_health_audit marks the run completed_with_metrics or checkpoint_ready "
                    "and top_journal_readiness_matrix.json is regenerated from the final artifacts."
                ),
            )
        )

    actions.append(
        ActionItem(
            id="obtain_saussurea_h5ad",
            priority="S",
            status="BLOCKED_USER_DATA" if not contract_ready else "READY",
            owner="wet_lab_or_user_data",
            title="Provide a real labelled Saussurea involucrata scRNA/snRNA AnnData file",
            evidence=(
                "saussurea_h5ad_contract.contract_ready="
                f"{contract_ready}; input={contract_input}"
            ),
            next_action=(
                "Generate or upload data/saussurea_involucrata.h5ad with cell_type, "
                "cell_type_coarse, sample_id, species, tissue, batch, and cell_id metadata."
            ),
            done_when=(
                "validate_saussurea_h5ad_contract.py reports contract_ready=true and "
                "snow_lotus_finetune_benchmark becomes READY."
            ),
        )
    )

    scplant_summary = scplant.get("summary", {})
    scplant_gates = scplant_plan.get("readiness_gates", {})
    actions.append(
        ActionItem(
            id="run_scplantannotate_authorized_benchmark",
            priority="A",
            status=(
                "BLOCKED_AUTH"
                if "scplantannotate" in missing_external
                and not scplant_summary.get("comparison_ready")
                else "READY"
            ),
            owner="external_credentials_or_author",
            title="Run a reproducible scPlantAnnotate comparison",
            evidence=(
                "anonymous_api_accessible="
                f"{scplant_summary.get('anonymous_api_accessible')}; "
                f"auth_required_endpoint_count={scplant_summary.get('auth_required_endpoint_count')}; "
                f"input_h5ad_available={scplant_gates.get('input_h5ad_available')}; "
                f"truth_labels_available={scplant_gates.get('truth_labels_available')}; "
                f"prediction_export_available={scplant_gates.get('prediction_export_available')}"
            ),
            next_action=(
                "Use SCPLANTANNOTATE_USERNAME/SCPLANTANNOTATE_PASSWORD with "
                "scripts/run_scplantannotate_authenticated_benchmark.py --execute against "
                "outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad, "
                "or obtain an author-provided batch result export and score it against the prepared truth CSV."
            ),
            done_when=(
                "outputs/external_benchmarks contains a scplantannotate metric JSON with macro-F1 "
                "or accuracy fields, not only a dry-run plan."
            ),
        )
    )

    unsupported = [
        target
        for target in download_progress.get("targets", [])
        if target.get("download_status") == "unsupported_for_matrix_corpus"
    ]
    actions.append(
        ActionItem(
            id="curate_public_corpus_exclusions",
            priority="B",
            status="READY" if unsupported else "NOT_APPLICABLE",
            owner="automation",
            title="Keep unsupported public downloads out of the matrix corpus",
            evidence=f"unsupported_targets={','.join(item.get('dataset_id', '') for item in unsupported) or 'none'}",
            next_action=(
                "Retain unsupported_single_cell_matrix.json reports in the package and exclude "
                "quant.sf-only archives from corpus manifests."
            ),
            done_when=(
                "download_progress_audit marks unsupported targets explicitly and data_integrity_audit "
                "has missing_files=0."
            ),
        )
    )

    transfer_summary = transfer_queue.get("summary", {})
    if transfer_summary:
        running_count = int(transfer_summary.get("running_count") or 0)
        missing_not_started = int(transfer_summary.get("missing_not_started_count") or 0)
        partial_without_active = int(transfer_summary.get("partial_without_active_session_count") or 0)
        stale_partials = int(transfer_summary.get("stale_partial_count") or 0)
        provisional_payloads = int(transfer_summary.get("provisional_payload_count") or 0)
        status = (
            "IN_PROGRESS"
            if running_count > 0
            else "MISSING"
            if missing_not_started > 0 or partial_without_active > 0
            else "READY"
        )
        actions.append(
            ActionItem(
                id="complete_reviewed_geo_transfer_queue",
                priority="A",
                status=status,
                owner="automation",
                title="Complete reviewed GEO transfer and conversion queue",
                evidence=(
                    f"running={running_count}; missing_not_started={missing_not_started}; "
                    f"partial_without_active_session={partial_without_active}; "
                    f"stale_partial_count={stale_partials}; "
                    f"provisional_payload_count={provisional_payloads}; "
                    f"complete_manifest={transfer_summary.get('complete_manifest_count', 0)}"
                ),
                next_action=(
                    "Let snowcell_reviewed_geo_download_queue finish the active transfer; "
                    "after each new manifest appears, regenerate the package and let the late "
                    "public refresh queue rebuild the MLM corpus when GPU training is idle."
                ),
                done_when=(
                    "transfer_queue_health_audit has running_count=0, missing_not_started_count=0, "
                    "partial_without_active_session_count=0, and new corpus manifests are visible "
                    "in status_summary/public_discovery_gap_audit."
                ),
            )
        )

    gap_summary = public_discovery_gap.get("summary", {})
    if gap_summary:
        requires_followup = bool(
            gap_summary.get("requires_downloader_or_manifest_followup")
            or gap_summary.get("requires_manual_manifest_review")
        )
        high_priority = int(gap_summary.get("new_high_priority_candidate_count") or 0)
        review_candidates = int(gap_summary.get("new_review_candidate_count") or 0)
        unknown_geo_ready = int(gap_summary.get("geo_download_ready_unknown_manifest_count") or 0)
        unknown_geo_ready_queued = int(
            gap_summary.get("geo_download_ready_unknown_manifest_queued_count") or 0
        )
        unknown_geo_ready_unqueued = int(
            gap_summary.get("geo_download_ready_unknown_manifest_unqueued_count") or 0
        )
        queued_ready = int(gap_summary.get("manifest_download_ready_queued_count") or 0)
        unqueued_ready = int(gap_summary.get("manifest_download_ready_unqueued_count") or 0)
        promotion_summary = geo_promotion.get("summary", {}) if isinstance(geo_promotion, dict) else {}
        promotion_download = int(promotion_summary.get("promote_download_candidate_count") or 0)
        promotion_manual = int(promotion_summary.get("manual_review_count") or 0)
        promotion_queue_summary = (
            geo_promotion_queue.get("summary", {}) if isinstance(geo_promotion_queue, dict) else {}
        )
        promotion_download_jobs = int(promotion_queue_summary.get("job_count") or 0)
        actions.append(
            ActionItem(
                id="triage_public_discovery_candidates",
                priority="A" if high_priority else "B",
                status="IN_PROGRESS" if requires_followup else "READY",
                owner="automation_and_curator",
                title="Triage newly discovered public plant single-cell candidates",
                evidence=(
                    f"new_high_priority_candidate_count={high_priority}; "
                    f"new_review_candidate_count={review_candidates}; "
                    f"geo_ready_unknown_manifest_count={unknown_geo_ready}; "
                    f"geo_ready_unknown_manifest_queued_count={unknown_geo_ready_queued}; "
                    f"geo_ready_unknown_manifest_unqueued_count={unknown_geo_ready_unqueued}; "
                    f"promotion_download_candidate_count={promotion_download}; "
                    f"promotion_manual_review_count={promotion_manual}; "
                    f"promotion_download_job_count={promotion_download_jobs}; "
                    f"manifest_download_ready_without_corpus_count="
                    f"{gap_summary.get('manifest_download_ready_without_corpus_count', 0)}; "
                    f"queued_download_ready_count={queued_ready}; "
                    f"unqueued_download_ready_count={unqueued_ready}"
                ),
                next_action=(
                    "Promote confirmed expression-matrix candidates into data/public_dataset_manifest.tsv, "
                    "add download wrappers, and keep unsupported/non-expression modalities documented "
                    "instead of mixing them into the RNA expression corpus."
                ),
                done_when=(
                    "public_discovery_gap_audit reports no manual manifest review required and no "
                    "download-ready expression candidates remain outside the corpus."
                ),
            )
        )

    curve_summary = training_curve.get("summary", {})
    actions.append(
        ActionItem(
            id="include_training_curve_evidence",
            priority="A",
            status="READY" if curve_summary.get("runs_with_eval_improvement") else "IN_PROGRESS",
            owner="automation",
            title="Maintain loss-curve evidence for all trainable runs",
            evidence=(
                f"runs_with_eval_improvement={curve_summary.get('runs_with_eval_improvement')}; "
                f"checkpoint_runs={curve_summary.get('checkpoint_runs')}"
            ),
            next_action="Regenerate publication package after each completed epoch.",
            done_when="training_curve_summary.md/json/tsv/png exist and include the final safe-refresh epoch.",
        )
    )

    actions.append(
        ActionItem(
            id="final_top_journal_claim_audit",
            priority="S",
            status=(
                "READY"
                if benchmark_gap.get("summary", {}).get("top_journal_benchmark_ready")
                and contract_ready
                else "MISSING"
            ),
            owner="scientific_lead",
            title="Freeze final top-journal claims only after all hard gates pass",
            evidence=(
                "top_journal_benchmark_ready="
                f"{benchmark_gap.get('summary', {}).get('top_journal_benchmark_ready')}; "
                f"saussurea_contract_ready={contract_ready}"
            ),
            next_action=(
                "After final training, Snow Lotus h5ad validation, and external comparisons, rerun "
                "generate_publication_package.sh and lock claims to READY evidence only."
            ),
            done_when=(
                "top_journal_readiness_matrix has no MISSING/PARTIAL S/A gates and all primary-data "
                "claims point to deposited raw and processed data accessions."
            ),
        )
    )

    status_counts: dict[str, int] = {}
    for action in actions:
        status_counts[action.status] = status_counts.get(action.status, 0) + 1
    return {
        "project_dir": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "action_count": len(actions),
            "status_counts": status_counts,
            "ready_count": status_counts.get("READY", 0),
            "blocked_count": sum(
                count for status, count in status_counts.items() if status.startswith("BLOCKED")
            ),
            "missing_count": status_counts.get("MISSING", 0),
            "in_progress_count": status_counts.get("IN_PROGRESS", 0),
        },
        "actions": [asdict(action) for action in actions],
    }


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_tsv(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "priority", "status", "owner", "title", "evidence", "next_action", "done_when"]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for action in payload["actions"]:
            writer.writerow({field: action.get(field, "") for field in fields})
    print(output_path)
    return output_path


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "| ID | Priority | Status | Owner | Evidence | Next action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for action in payload["actions"]:
        rows.append(
            "| {id} | {priority} | {status} | {owner} | {evidence} | {next_action} |".format(
                id=action["id"],
                priority=action["priority"],
                status=action["status"],
                owner=action["owner"],
                evidence=action["evidence"].replace("|", "/"),
                next_action=action["next_action"].replace("|", "/"),
            )
        )
    lines = [
        "# SnowLotus-CellFM Submission Action Plan",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        f"- Actions: `{payload['summary']['action_count']}`",
        f"- Ready: `{payload['summary']['ready_count']}`",
        f"- In progress: `{payload['summary']['in_progress_count']}`",
        f"- Blocked: `{payload['summary']['blocked_count']}`",
        f"- Missing: `{payload['summary']['missing_count']}`",
        "",
        "## Action Ledger",
        "",
        "\n".join(rows),
        "",
    ]
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write SnowLotus-CellFM submission action plan")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-tsv", required=True)
    args = parser.parse_args()
    payload = build_actions(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    write_tsv(payload, args.output_tsv)


if __name__ == "__main__":
    main()
