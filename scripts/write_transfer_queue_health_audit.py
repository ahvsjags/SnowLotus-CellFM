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
DEFAULT_STALE_PARTIAL_SECONDS = 30 * 60


def read_queue_jobs(queue_script: Path) -> list[dict[str, str]]:
    if not queue_script.exists():
        return []
    text = queue_script.read_text(encoding="utf-8")
    jobs = []
    for session, manifest, command, log_path in JOB_RE.findall(text):
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


def accession_from_manifest(manifest: str) -> str:
    name = Path(manifest).name
    if name.startswith("corpus_manifest.") and name.endswith(".tsv"):
        return name.removeprefix("corpus_manifest.").removesuffix(".tsv").upper()
    return ""


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
    sessions = set()
    for line in result.stdout.splitlines():
        name = line.split(":", 1)[0].strip()
        if name:
            sessions.add(name)
    return sessions


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def file_entry(root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": relpath(root, path),
        "bytes": path.stat().st_size,
        "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def seconds_since_modified(path: Path, now: datetime) -> float:
    return max(0.0, now.timestamp() - path.stat().st_mtime)


def unsupported_reports(root: Path, accession: str) -> list[dict[str, Any]]:
    raw_dir = root / "data" / "public" / f"{accession}_raw_tar"
    paths = sorted(raw_dir.glob("unsupported_single_cell_matrix.json"))
    reports = []
    for path in paths:
        payload: dict[str, Any] = {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"parse_error": True}
        reports.append({"file": file_entry(root, path), "payload": payload})
    return reports


def transfer_files(root: Path, accession: str, now: datetime) -> dict[str, Any]:
    base = root / "data" / "public"
    dirs = [
        base / f"{accession}_raw_tar",
        base / f"{accession}_rds",
        base / f"{accession}_h5",
        base / f"{accession}_mtx_tar",
        base / f"{accession}_npz",
    ]
    files = [path for directory in dirs for path in directory.glob("*") if path.is_file()]
    partials = [path for path in files if path.name.endswith(".aria2")]
    payloads = [path for path in files if not path.name.endswith(".aria2")]
    payload_bytes = sum(path.stat().st_size for path in payloads)
    payload_bytes_are_provisional = bool(partials and payloads)
    latest_file = max(files, key=lambda p: p.stat().st_mtime) if files else None
    return {
        "file_count": len(payloads),
        "bytes": payload_bytes,
        "payload_bytes_are_provisional": payload_bytes_are_provisional,
        "provisional_payload_bytes": payload_bytes if payload_bytes_are_provisional else 0,
        "partial_file_count": len(partials),
        "partial_files": [file_entry(root, path) for path in partials],
        "latest_transfer_file": file_entry(root, latest_file) if latest_file else None,
        "latest_transfer_age_seconds": seconds_since_modified(latest_file, now)
        if latest_file
        else None,
        "largest_file": file_entry(root, max(payloads, key=lambda p: p.stat().st_size))
        if payloads
        else None,
    }


def job_status(manifest_rows: int, unsupported_count: int, active: bool, partials: int, files: int) -> str:
    if manifest_rows > 0:
        return "complete_manifest"
    if active and partials:
        return "running_partial_download"
    if active:
        return "running"
    if unsupported_count > 0:
        return "unsupported_expression_corpus"
    if partials:
        return "partial_without_active_session"
    if files:
        return "files_without_manifest"
    return "missing_not_started"


def build_audit(
    project_dir: str | Path,
    stale_partial_seconds: int = DEFAULT_STALE_PARTIAL_SECONDS,
) -> dict[str, Any]:
    root = Path(project_dir)
    jobs = read_queue_jobs(root / "scripts" / "queue_reviewed_geo_downloads.sh")
    active_sessions = tmux_sessions()
    now = datetime.now(timezone.utc)
    items = []
    for job in jobs:
        manifest_path = root / job["manifest"]
        rows = read_tsv_rows(manifest_path)
        unsupported = unsupported_reports(root, job["accession"])
        files = transfer_files(root, job["accession"], now)
        active = job["session"] in active_sessions
        stale_partial = bool(
            files["partial_file_count"]
            and files["latest_transfer_age_seconds"] is not None
            and files["latest_transfer_age_seconds"] > stale_partial_seconds
        )
        status = job_status(
            manifest_rows=len(rows),
            unsupported_count=len(unsupported),
            active=active,
            partials=files["partial_file_count"],
            files=files["file_count"],
        )
        items.append(
            {
                **job,
                "status": status,
                "active_session": active,
                "manifest_exists": manifest_path.exists(),
                "manifest_rows": len(rows),
                "manifest_bytes": manifest_path.stat().st_size if manifest_path.exists() else 0,
                "stale_partial": stale_partial,
                "stale_partial_seconds": stale_partial_seconds,
                "unsupported_report_count": len(unsupported),
                "unsupported_reports": unsupported,
                "transfer_files": files,
            }
        )
    counts = Counter(item["status"] for item in items)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "job_count": len(items),
        "active_session_count": sum(1 for item in items if item["active_session"]),
        "status_counts": dict(sorted(counts.items())),
        "complete_manifest_count": counts.get("complete_manifest", 0),
        "running_count": counts.get("running", 0) + counts.get("running_partial_download", 0),
        "unsupported_expression_corpus_count": counts.get("unsupported_expression_corpus", 0),
        "partial_without_active_session_count": counts.get("partial_without_active_session", 0),
        "stale_partial_count": sum(1 for item in items if item["stale_partial"]),
        "provisional_payload_count": sum(
            1 for item in items if item["transfer_files"]["payload_bytes_are_provisional"]
        ),
        "provisional_payload_bytes": sum(
            item["transfer_files"]["provisional_payload_bytes"] for item in items
        ),
        "missing_not_started_count": counts.get("missing_not_started", 0),
    }
    return {
        "project_dir": str(root),
        "summary": summary,
        "jobs": items,
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


def human_bytes(value: int | None) -> str:
    if value is None:
        return "-"
    size = float(value)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TiB"


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Transfer Queue Health Audit",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        markdown_table(
            [
                ["Metric", "Value"],
                ["Jobs", str(summary["job_count"])],
                ["Active sessions", str(summary["active_session_count"])],
                ["Complete manifests", str(summary["complete_manifest_count"])],
                ["Running jobs", str(summary["running_count"])],
                ["Unsupported expression-corpus targets", str(summary["unsupported_expression_corpus_count"])],
                ["Partial files without active session", str(summary["partial_without_active_session_count"])],
                ["Stale partial downloads", str(summary["stale_partial_count"])],
                ["Provisional payload byte jobs", str(summary["provisional_payload_count"])],
                ["Provisional payload bytes", human_bytes(summary["provisional_payload_bytes"])],
                ["Missing/not started", str(summary["missing_not_started_count"])],
            ]
        ),
        "",
        "## Jobs",
        "",
    ]
    table = [
        [
            "Session",
            "Accession",
            "Status",
            "Rows",
            "Partials",
            "Stale",
            "Provisional",
            "Largest",
            "Log",
        ]
    ]
    for item in payload["jobs"]:
        largest = item["transfer_files"].get("largest_file")
        table.append(
            [
                item["session"],
                item["accession"],
                item["status"],
                str(item["manifest_rows"]),
                str(item["transfer_files"]["partial_file_count"]),
                "yes" if item["stale_partial"] else "no",
                "yes" if item["transfer_files"]["payload_bytes_are_provisional"] else "no",
                human_bytes(largest["bytes"] if largest else None),
                item["log_path"],
            ]
        )
    lines.append(markdown_table(table))
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
    parser = argparse.ArgumentParser(description="Write transfer queue health audit.")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--stale-partial-seconds", default=DEFAULT_STALE_PARTIAL_SECONDS, type=int)
    args = parser.parse_args()
    payload = build_audit(args.project_dir, args.stale_partial_seconds)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
