from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNS = [
    {
        "run_id": "smoke",
        "output_dir": "outputs/smoke",
        "log_glob": "logs/smoke*.log",
        "session": "",
        "process_token": "configs/smoke.yaml",
    },
    {
        "run_id": "foundation_5090_pretrain",
        "output_dir": "outputs/foundation_5090_pretrain",
        "log_glob": "logs/foundation_long*.log",
        "session": "snowcell_foundation_long",
        "process_token": "configs/foundation_5090_pretrain.yaml",
    },
    {
        "run_id": "foundation_5090_public_sprint",
        "output_dir": "outputs/foundation_5090_public_sprint",
        "log_glob": "logs/*public_sprint*.log",
        "session": "",
        "process_token": "configs/foundation_5090_public_sprint.yaml",
    },
    {
        "run_id": "foundation_5090_public_safe_init",
        "output_dir": "outputs/foundation_5090_public_safe_init",
        "log_glob": "logs/public_safe_init*.log",
        "session": "snowcell_public_safe_init",
        "process_token": "configs/foundation_5090_public_safe_init.yaml",
        "process_tokens": [
            "configs/foundation_5090_public_safe_init.yaml",
            "configs/generated/foundation_5090_public_safe_init.resume.yaml",
        ],
    },
    {
        "run_id": "foundation_5090_mlm_public_expansion",
        "output_dir": "outputs/foundation_5090_mlm_public_expansion",
        "log_glob": "logs/mlm_public_expansion_*.log",
        "session": "snowcell_mlm_public_expansion",
        "process_token": "configs/foundation_5090_mlm_public_expansion.yaml",
    },
    {
        "run_id": "foundation_5090_mlm_public_expansion_continuation",
        "output_dir": "outputs/foundation_5090_mlm_public_expansion_continuation",
        "log_glob": "logs/mlm_public_expansion_continuation_*.log",
        "session": "snowcell_mlm_public_expansion_continuation",
        "process_token": "configs/generated/foundation_5090_mlm_public_expansion_continuation.yaml",
    },
    {
        "run_id": "foundation_5090_mlm_public_late_refresh",
        "output_dir": "outputs/foundation_5090_mlm_public_late_refresh",
        "log_glob": "logs/mlm_public_late_refresh_*.log",
        "session": "snowcell_mlm_public_late_refresh",
        "process_token": "configs/foundation_5090_mlm_public_late_refresh.yaml",
    },
    {
        "run_id": "foundation_5090_mlm_public_late_refresh_safe",
        "output_dir": "outputs/foundation_5090_mlm_public_late_refresh_safe",
        "log_glob": "logs/mlm_public_late_refresh_safe_*.log",
        "session": "snowcell_mlm_public_late_refresh_safe",
        "process_token": "configs/foundation_5090_mlm_public_late_refresh_safe.yaml",
    },
    {
        "run_id": "foundation_5090_mlm_public_post_gse226097_refresh_safe",
        "output_dir": "outputs/foundation_5090_mlm_public_post_gse226097_refresh_safe",
        "log_glob": "logs/mlm_public_post_gse226097_refresh_safe_*.log",
        "session": "snowcell_mlm_public_post_gse226097_refresh_safe",
        "process_token": "configs/foundation_5090_mlm_public_post_gse226097_refresh_safe.yaml",
    },
]

OOM_RE = re.compile(r"(?:CUDA out of memory|OOM|memory allocation failed)", re.IGNORECASE)
ERROR_RE = re.compile(r"(?:Traceback|RuntimeError|Exception|failed|error:)", re.IGNORECASE)


def run_command(command: list[str], cwd: Path, timeout: int = 10) -> dict[str, Any]:
    if shutil.which(command[0]) is None:
        return {"command": command, "returncode": None, "stdout": "", "stderr": "command not found"}
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def file_summary(root: Path, path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": relpath(root, path),
            "exists": False,
            "bytes": 0,
            "modified_utc": None,
        }
    stat = path.stat()
    return {
        "path": relpath(root, path),
        "exists": True,
        "bytes": stat.st_size,
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def log_summary(root: Path, pattern: str) -> dict[str, Any]:
    paths = sorted(root.glob(pattern), key=lambda item: item.as_posix())
    items = []
    oom_count = 0
    error_count = 0
    excerpts: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        log_oom_count = sum(1 for line in lines if OOM_RE.search(line))
        log_error_count = sum(1 for line in lines if ERROR_RE.search(line))
        oom_count += log_oom_count
        error_count += log_error_count
        if log_oom_count or log_error_count:
            for line in lines:
                if OOM_RE.search(line) or ERROR_RE.search(line):
                    excerpts.append(line.strip()[:240])
                    if len(excerpts) >= 8:
                        break
        items.append(
            {
                **file_summary(root, path),
                "oom_count": log_oom_count,
                "error_count": log_error_count,
            }
        )
    return {
        "pattern": pattern,
        "files": items,
        "file_count": len(items),
        "oom_count": oom_count,
        "error_count": error_count,
        "issue_excerpts": excerpts[:8],
    }


def runtime_summary(root: Path, run: dict[str, Any]) -> dict[str, Any]:
    session = run.get("session") or ""
    process_token = run.get("process_token") or ""
    process_tokens = [
        str(token)
        for token in (run.get("process_tokens") or [process_token])
        if str(token or "").strip()
    ]
    tmux_result = (
        run_command(["tmux", "has-session", "-t", f"={session}"], root)
        if session
        else {"returncode": None, "stdout": "", "stderr": "no session configured"}
    )
    process_results = [
        run_command(["pgrep", "-af", token], root)
        for token in process_tokens
    ]
    if not process_results:
        process_results = [{"returncode": None, "stdout": "", "stderr": "no process token configured"}]
    process_lines = []
    for token, process_result in zip(process_tokens, process_results):
        process_lines.extend(
            line
            for line in process_result.get("stdout", "").splitlines()
            if "pgrep -af" not in line
            and "tmux new-session" not in line
            and token in line
        )
    return {
        "session": session,
        "process_token": process_token,
        "process_tokens": process_tokens,
        "tmux_active": tmux_result.get("returncode") == 0,
        "process_active": bool(process_lines),
        "process_lines": process_lines[:10],
        "tmux_probe": {
            "returncode": tmux_result.get("returncode"),
            "stderr": tmux_result.get("stderr", ""),
        },
        "process_probe": {
            "returncode": 0 if process_lines else process_results[0].get("returncode"),
            "stderr": "; ".join(
                str(result.get("stderr", "")) for result in process_results if result.get("stderr")
            ),
        },
    }


def run_status(
    checkpoint: dict[str, Any],
    history: dict[str, Any],
    test_metrics: dict[str, Any],
    logs: dict[str, Any],
    runtime: dict[str, Any],
) -> str:
    if logs["oom_count"] and not checkpoint["exists"]:
        return "oom_incomplete"
    active = bool(runtime.get("tmux_active") or runtime.get("process_active"))
    if active and not history["exists"] and not checkpoint["exists"]:
        return "running_no_epoch_yet"
    if active and checkpoint["exists"] and not test_metrics["exists"]:
        return "running_with_checkpoint"
    if active and history["exists"] and not test_metrics["exists"]:
        return "running_with_history"
    if checkpoint["exists"] and test_metrics["exists"]:
        return "completed_with_metrics"
    if checkpoint["exists"]:
        return "checkpoint_ready"
    if history["exists"] or test_metrics["exists"]:
        return "partial_artifacts"
    if logs["file_count"] or logs["error_count"]:
        return "log_only"
    return "not_started"


def summarize_run(root: Path, run: dict[str, str]) -> dict[str, Any]:
    output_dir = root / run["output_dir"]
    best_checkpoint = file_summary(root, output_dir / "best.pt")
    latest_checkpoint = file_summary(root, output_dir / "latest.pt")
    checkpoint = dict(best_checkpoint if best_checkpoint["exists"] else latest_checkpoint)
    checkpoint["kind"] = "best" if best_checkpoint["exists"] else "latest"
    history = file_summary(root, output_dir / "history.json")
    test_metrics = file_summary(root, output_dir / "test_metrics.json")
    resolved_config = file_summary(root, output_dir / "config.resolved.json")
    history_payload = read_json(output_dir / "history.json")
    epochs = (history_payload or {}).get("epochs", [])
    latest_epoch = epochs[-1] if epochs else None
    logs = log_summary(root, run["log_glob"])
    runtime = runtime_summary(root, run)
    status = run_status(checkpoint, history, test_metrics, logs, runtime)
    return {
        "run_id": run["run_id"],
        "output_dir": run["output_dir"],
        "status": status,
        "checkpoint": checkpoint,
        "best_checkpoint": best_checkpoint,
        "latest_checkpoint": latest_checkpoint,
        "history": history,
        "test_metrics": test_metrics,
        "resolved_config": resolved_config,
        "epochs_recorded": len(epochs),
        "latest_epoch": latest_epoch,
        "logs": logs,
        "runtime": runtime,
    }


def build_audit(project_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    runs = [summarize_run(root, run) for run in RUNS]
    status_counts: dict[str, int] = {}
    for run in runs:
        status_counts[run["status"]] = status_counts.get(run["status"], 0) + 1
    return {
        "project_dir": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "run_count": len(runs),
            "status_counts": status_counts,
            "oom_issue_count": sum(run["logs"]["oom_count"] for run in runs),
            "completed_metric_runs": sum(1 for run in runs if run["test_metrics"]["exists"]),
            "checkpoint_runs": sum(1 for run in runs if run["checkpoint"]["exists"]),
            "running_runs": sum(
                1
                for run in runs
                if run["runtime"]["tmux_active"] or run["runtime"]["process_active"]
            ),
        },
        "runs": runs,
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
    rows = [["Run", "Status", "Active", "Checkpoint", "Metrics", "Epochs", "OOM warnings"]]
    for run in payload["runs"]:
        active = run["runtime"]["tmux_active"] or run["runtime"]["process_active"]
        rows.append(
            [
                run["run_id"],
                run["status"],
                "yes" if active else "no",
                "yes" if run["checkpoint"]["exists"] else "no",
                "yes" if run["test_metrics"]["exists"] else "no",
                str(run["epochs_recorded"]),
                str(run["logs"]["oom_count"]),
            ]
        )
    lines = [
        "# SnowLotus-CellFM Training Health Audit",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        markdown_table(
            [
                ["Metric", "Value"],
                ["Runs tracked", str(payload["summary"]["run_count"])],
                ["Checkpoint runs", str(payload["summary"]["checkpoint_runs"])],
                ["Completed metric runs", str(payload["summary"]["completed_metric_runs"])],
                ["Running runs", str(payload["summary"]["running_runs"])],
                ["OOM warning count", str(payload["summary"]["oom_issue_count"])],
            ]
        ),
        "",
        "## Runs",
        "",
        markdown_table(rows),
        "",
    ]
    issue_runs = [
        run
        for run in payload["runs"]
        if run["status"] in {"oom_incomplete", "log_only"} or run["logs"]["issue_excerpts"]
    ]
    lines.extend(["## Issues", ""])
    if not issue_runs:
        lines.append("No training log issues were detected in tracked runs.")
    else:
        for run in issue_runs:
            lines.append(f"### {run['run_id']}")
            lines.append("")
            lines.append(f"- Status: `{run['status']}`")
            lines.append(f"- Log pattern: `{run['logs']['pattern']}`")
            if run["logs"]["issue_excerpts"]:
                lines.append("- Excerpts:")
                for excerpt in run["logs"]["issue_excerpts"]:
                    lines.append(f"  - `{excerpt}`")
            if run["status"] == "oom_incomplete":
                lines.append(
                    "- Recovery route: relaunch with the memory-safe late refresh config "
                    "`configs/foundation_5090_mlm_public_late_refresh.yaml`."
                )
            lines.append("")
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write SnowCell training health audit")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    payload = build_audit(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
