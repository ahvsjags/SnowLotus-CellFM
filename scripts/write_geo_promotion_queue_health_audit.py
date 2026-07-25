from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


JOB_RE = re.compile(r'"([^"|]+)\|([^"|]+)\|([^"|]+)\|([^"|]+)"')
PROMOTION_SESSION_RE = re.compile(r"^snowcell_geo_promotion_(gse[0-9]+)$", re.IGNORECASE)
DEFAULT_QUEUE_SESSION = "snowcell_geo_promotion_download_queue"
PROMOTION_QUEUE_SCRIPT = Path("scripts/generated_geo_promotion_downloads/queue_geo_promotion_downloads.sh")
REVIEWED_QUEUE_SCRIPT = Path("scripts/queue_reviewed_geo_downloads.sh")


def accession_from_manifest(manifest: str) -> str:
    name = Path(manifest).name
    if name.startswith("corpus_manifest.") and name.endswith(".tsv"):
        return name.removeprefix("corpus_manifest.").removesuffix(".tsv").upper()
    return ""


def read_queue_jobs(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    jobs: list[dict[str, str]] = []
    for session, manifest, command, log_path in JOB_RE.findall(path.read_text(encoding="utf-8")):
        if not manifest.startswith("data/corpus_manifest."):
            continue
        jobs.append(
            {
                "session": session,
                "manifest": manifest,
                "command": command,
                "log_path": log_path,
                "accession": accession_from_manifest(manifest),
            }
        )
    return jobs


def read_tsv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def tmux_sessions() -> set[str]:
    try:
        result = subprocess.run(
            ["tmux", "ls"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return set()
    return {line.split(":", 1)[0].strip() for line in result.stdout.splitlines() if line.strip()}


def transfer_dirs(root: Path, accession: str) -> list[Path]:
    public = root / "data" / "public"
    suffixes = [
        "10x",
        "h5",
        "h5ad",
        "mtx_tar",
        "mtx_components",
        "raw_tar",
        "rds",
    ]
    return [public / f"{accession}_{suffix}" for suffix in suffixes]


def partial_files(root: Path, accession: str) -> list[Path]:
    return sorted(
        path
        for directory in transfer_dirs(root, accession)
        for path in directory.glob("*.aria2")
    )


def unsupported_reports(root: Path, accession: str) -> list[Path]:
    return sorted(
        path
        for directory in transfer_dirs(root, accession)
        for path in directory.glob("unsupported_single_cell_matrix.json")
    )


def reviewed_status(root: Path, job: dict[str, str], active_sessions: set[str]) -> str:
    rows = read_tsv_rows(root / job["manifest"])
    if rows:
        return "complete_manifest"
    if unsupported_reports(root, job["accession"]):
        return "unsupported_expression_corpus"
    if job["session"] in active_sessions:
        return "running"
    if partial_files(root, job["accession"]):
        return "partial_without_active_session"
    return "missing_not_started"


def promotion_status(
    root: Path,
    job: dict[str, str],
    active_sessions: set[str],
    queue_supervisor_active: bool,
    reviewed_pending: bool,
) -> str:
    rows = read_tsv_rows(root / job["manifest"])
    if rows:
        return "complete_manifest"
    if unsupported_reports(root, job["accession"]):
        return "unsupported_expression_corpus"
    if job["session"] in active_sessions:
        return "running"
    if partial_files(root, job["accession"]):
        return "partial_without_active_session"
    if queue_supervisor_active and reviewed_pending:
        return "waiting_for_reviewed_queue"
    if queue_supervisor_active:
        return "queued_waiting_for_slot"
    return "queue_not_running"


def build_audit(
    project_dir: str | Path,
    queue_session: str = DEFAULT_QUEUE_SESSION,
) -> dict[str, Any]:
    root = Path(project_dir)
    active_sessions = tmux_sessions()
    reviewed_jobs = read_queue_jobs(root / REVIEWED_QUEUE_SCRIPT)
    reviewed_items = []
    for job in reviewed_jobs:
        status = reviewed_status(root, job, active_sessions)
        reviewed_items.append({**job, "status": status})
    reviewed_pending_items = [
        item
        for item in reviewed_items
        if item["status"] not in {"complete_manifest", "unsupported_expression_corpus"}
    ]
    reviewed_pending = bool(reviewed_pending_items)
    queue_supervisor_active = queue_session in active_sessions

    promotion_jobs = read_queue_jobs(root / PROMOTION_QUEUE_SCRIPT)
    promotion_items = []
    for job in promotion_jobs:
        rows = read_tsv_rows(root / job["manifest"])
        partials = partial_files(root, job["accession"])
        unsupported = unsupported_reports(root, job["accession"])
        status = promotion_status(
            root=root,
            job=job,
            active_sessions=active_sessions,
            queue_supervisor_active=queue_supervisor_active,
            reviewed_pending=reviewed_pending,
        )
        active_partial_file_count = (
            len(partials)
            if status in {"running", "partial_without_active_session"}
            else 0
        )
        residual_partial_file_count = len(partials) - active_partial_file_count
        promotion_items.append(
            {
                **job,
                "status": status,
                "active_session": job["session"] in active_sessions,
                "manifest_exists": (root / job["manifest"]).exists(),
                "manifest_rows": len(rows),
                "partial_file_count": len(partials),
                "active_partial_file_count": active_partial_file_count,
                "residual_partial_file_count": residual_partial_file_count,
                "unsupported_report_count": len(unsupported),
            }
        )

    tracked_promotion_sessions = {job["session"] for job in promotion_jobs}
    unmanaged_active_items = []
    for session in sorted(active_sessions):
        if session in tracked_promotion_sessions:
            continue
        match = PROMOTION_SESSION_RE.match(session)
        if match is None:
            continue
        accession = match.group(1).upper()
        manifest = f"data/corpus_manifest.{accession.lower()}.tsv"
        rows = read_tsv_rows(root / manifest)
        partials = partial_files(root, accession)
        unsupported = unsupported_reports(root, accession)
        if rows:
            status = "complete_manifest"
        elif unsupported:
            status = "unsupported_expression_corpus"
        else:
            status = "running_untracked"
        active_partial_file_count = (
            len(partials)
            if status in {"running_untracked", "partial_without_active_session"}
            else 0
        )
        residual_partial_file_count = len(partials) - active_partial_file_count
        unmanaged_active_items.append(
            {
                "session": session,
                "accession": accession,
                "manifest": manifest,
                "status": status,
                "active_session": True,
                "manifest_exists": (root / manifest).exists(),
                "manifest_rows": len(rows),
                "partial_file_count": len(partials),
                "active_partial_file_count": active_partial_file_count,
                "residual_partial_file_count": residual_partial_file_count,
                "unsupported_report_count": len(unsupported),
            }
        )

    counts = Counter(item["status"] for item in promotion_items)
    unmanaged_counts = Counter(item["status"] for item in unmanaged_active_items)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "queue_session": queue_session,
        "queue_supervisor_active": queue_supervisor_active,
        "job_count": len(promotion_items),
        "active_job_count": sum(1 for item in promotion_items if item["active_session"]),
        "reviewed_job_count": len(reviewed_items),
        "reviewed_pending_count": len(reviewed_pending_items),
        "reviewed_pending_accessions": [item["accession"] for item in reviewed_pending_items],
        "status_counts": dict(sorted(counts.items())),
        "waiting_for_reviewed_queue_count": counts.get("waiting_for_reviewed_queue", 0),
        "queued_waiting_for_slot_count": counts.get("queued_waiting_for_slot", 0),
        "complete_manifest_count": counts.get("complete_manifest", 0),
        "running_count": counts.get("running", 0) + unmanaged_counts.get("running_untracked", 0),
        "tracked_running_count": counts.get("running", 0),
        "unmanaged_active_promotion_count": len(unmanaged_active_items),
        "unmanaged_running_promotion_count": unmanaged_counts.get("running_untracked", 0),
        "queue_not_running_count": counts.get("queue_not_running", 0),
        "active_partial_file_count": sum(
            item["active_partial_file_count"] for item in promotion_items
        )
        + sum(item["active_partial_file_count"] for item in unmanaged_active_items),
        "residual_partial_file_count": sum(
            item["residual_partial_file_count"] for item in promotion_items
        )
        + sum(item["residual_partial_file_count"] for item in unmanaged_active_items),
    }
    return {
        "project_dir": str(root),
        "promotion_queue_script": PROMOTION_QUEUE_SCRIPT.as_posix(),
        "reviewed_queue_script": REVIEWED_QUEUE_SCRIPT.as_posix(),
        "summary": summary,
        "reviewed_jobs": reviewed_items,
        "jobs": promotion_items,
        "unmanaged_active_promotion_sessions": unmanaged_active_items,
    }


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join("---" for _ in rows[0]) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines)


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# GEO Promotion Queue Health Audit",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        markdown_table(
            [
                ["Metric", "Value"],
                ["Queue session", summary["queue_session"]],
                ["Queue supervisor active", "yes" if summary["queue_supervisor_active"] else "no"],
                ["Promotion jobs", str(summary["job_count"])],
                ["Reviewed jobs still pending", str(summary["reviewed_pending_count"])],
                ["Waiting for reviewed queue", str(summary["waiting_for_reviewed_queue_count"])],
                ["Queued waiting for slot", str(summary["queued_waiting_for_slot_count"])],
                ["Running promotion jobs", str(summary["running_count"])],
                ["Tracked running promotion jobs", str(summary["tracked_running_count"])],
                ["Untracked active promotion sessions", str(summary["unmanaged_active_promotion_count"])],
                ["Complete promotion manifests", str(summary["complete_manifest_count"])],
                ["Active partial control files", str(summary["active_partial_file_count"])],
                ["Residual control files", str(summary["residual_partial_file_count"])],
            ]
        ),
        "",
        "## Promotion Jobs",
        "",
    ]
    table = [
        [
            "Session",
            "Accession",
            "Status",
            "Rows",
            "Active partials",
            "Residual",
            "Unsupported",
            "Log",
        ]
    ]
    for item in payload["jobs"]:
        table.append(
            [
                item["session"],
                item["accession"],
                item["status"],
                str(item["manifest_rows"]),
                str(item["active_partial_file_count"]),
                str(item["residual_partial_file_count"]),
                str(item["unsupported_report_count"]),
                item["log_path"],
            ]
        )
    lines.append(markdown_table(table))
    lines.extend(["", "## Untracked Active Promotion Sessions", ""])
    if payload["unmanaged_active_promotion_sessions"]:
        unmanaged_table = [
            [
                "Session",
                "Accession",
                "Status",
                "Rows",
                "Active partials",
                "Residual",
                "Unsupported",
            ]
        ]
        for item in payload["unmanaged_active_promotion_sessions"]:
            unmanaged_table.append(
                [
                    item["session"],
                    item["accession"],
                    item["status"],
                    str(item["manifest_rows"]),
                    str(item["active_partial_file_count"]),
                    str(item["residual_partial_file_count"]),
                    str(item["unsupported_report_count"]),
                ]
            )
        lines.append(markdown_table(unmanaged_table))
    else:
        lines.append("No untracked active promotion sessions.")
    lines.extend(["", "## Reviewed Pending Gate", ""])
    if summary["reviewed_pending_accessions"]:
        lines.append(", ".join(summary["reviewed_pending_accessions"]))
    else:
        lines.append("No reviewed GEO jobs are pending.")
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Write GEO promotion queue health audit.")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--queue-session", default=DEFAULT_QUEUE_SESSION)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    payload = build_audit(args.project_dir, args.queue_session)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
