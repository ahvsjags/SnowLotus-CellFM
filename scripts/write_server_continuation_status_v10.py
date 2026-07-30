from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release_metadata"
OUTPUTS = ROOT / "outputs" / "editor_submission_v9"


QUEUE_SESSIONS = [
    "snowcell_public_queues_when_space",
    "snowcell_public_mlm_queue",
    "snowcell_late_public_refresh_queue",
    "snowcell_scplantdb_budgeted_h5ad_queue",
    "snowcell_scplantdb_root_budgeted_h5ad_queue",
    "snowcell_mlm_public_expansion",
    "snowcell_mlm_public_available_expansion",
    "snowcell_mlm_public_expansion_continuation",
    "snowcell_mlm_public_post_gse226097_refresh_safe",
]


def run(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except Exception as exc:
        return {"returncode": -1, "stdout": "", "stderr": str(exc)}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def df_bytes(path: str) -> dict[str, Any]:
    result = run(["df", "-PB1", path], timeout=10)
    lines = result["stdout"].splitlines()
    if len(lines) < 2:
        return {"path": path, "available_bytes": None, "raw": result}
    parts = lines[1].split()
    available = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else None
    return {
        "path": path,
        "filesystem": parts[0] if parts else "",
        "size_bytes": int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None,
        "used_bytes": int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else None,
        "available_bytes": available,
        "use_percent": parts[4] if len(parts) >= 5 else "",
        "mount": parts[5] if len(parts) >= 6 else "",
    }


def count_tsv_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        line_count = sum(1 for _ in handle)
    return max(0, line_count - 1)


def root_stage_progress(root_stage: Path) -> dict[str, Any]:
    if not root_stage.exists():
        return {"exists": False}
    manifest = root_stage / "data" / "corpus_manifest.scplantdb.tsv"
    h5ad_dir = root_stage / "data" / "public" / "scPlantDB_h5ad"
    audit_paths = [
        root_stage / "outputs" / "publication_package" / "scplantdb_manifest_audit.md",
        root_stage / "outputs" / "publication_package" / "data_integrity_audit.md",
        root_stage / "outputs" / "publication_package" / "pending_corpus_additions.md",
    ]
    h5ad_files = sorted(h5ad_dir.glob("*.h5ad")) if h5ad_dir.exists() else []
    return {
        "exists": True,
        "manifest": str(manifest),
        "manifest_rows": count_tsv_rows(manifest),
        "h5ad_file_count": len(h5ad_files),
        "h5ad_total_bytes": sum(path.stat().st_size for path in h5ad_files),
        "h5ad_files": [path.name for path in h5ad_files],
        "audits": {
            path.name: {
                "path": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
            for path in audit_paths
        },
    }


def file_summary(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def root_v10_training_progress(output_dir: Path) -> dict[str, Any]:
    if not output_dir.exists():
        return {"exists": False, "output_dir": str(output_dir)}
    history = read_json(output_dir / "history.json")
    test_metrics = read_json(output_dir / "test_metrics.json")
    progress_latest = read_json(output_dir / "progress_latest.json")
    checkpoints = {
        name: file_summary(output_dir / name)
        for name in ["best.pt", "latest.pt", "epoch_0001.pt", "epoch_0002.pt"]
    }
    epochs = history.get("epochs") or []
    best_epoch = None
    if epochs:
        best_epoch = min(
            epochs,
            key=lambda item: float(item.get("eval_loss", float("inf"))),
        ).get("epoch")
    return {
        "exists": True,
        "output_dir": str(output_dir),
        "history_epochs": len(epochs),
        "best_epoch_by_eval_loss": best_epoch,
        "latest_status": progress_latest.get("status", "not_available"),
        "latest_epoch": progress_latest.get("epoch"),
        "latest_step": progress_latest.get("step"),
        "train_loss_last_epoch": epochs[-1].get("train_loss") if epochs else None,
        "eval_loss_last_epoch": epochs[-1].get("eval_loss") if epochs else None,
        "eval_fine_accuracy_last_epoch": epochs[-1].get("fine_accuracy") if epochs else None,
        "eval_coarse_accuracy_last_epoch": epochs[-1].get("coarse_accuracy") if epochs else None,
        "test_metrics": test_metrics,
        "checkpoints": checkpoints,
    }


def tmux_sessions() -> list[str]:
    result = run(["tmux", "ls"], timeout=10)
    if result["returncode"] != 0:
        return []
    return [line.split(":", 1)[0].strip() for line in result["stdout"].splitlines() if line.strip()]


def health() -> dict[str, Any]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return {"status": "unreachable", "detail": str(exc)}


def nvidia() -> dict[str, Any]:
    result = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,utilization.gpu",
            "--format=csv,noheader",
        ],
        timeout=10,
    )
    return {"returncode": result["returncode"], "output": result["stdout"] or result["stderr"]}


def build_status(min_free_bytes: int) -> dict[str, Any]:
    sessions = tmux_sessions()
    active_queue_sessions = [session for session in QUEUE_SESSIONS if session in sessions]
    disk_project = df_bytes(str(ROOT))
    disk_root = df_bytes("/root")
    root_stage = Path("/root/snowlotus_cellfm_v10")
    root_training_dir = Path("/root/snowlotus_cellfm_v10_scplantdb_lora_4090")
    disk_root_stage = df_bytes(str(root_stage)) if root_stage.exists() else {}
    root_stage_scplantdb = root_stage_progress(root_stage)
    root_v10_training = root_v10_training_progress(root_training_dir)
    available = disk_project.get("available_bytes")
    disk_ok = available is not None and available >= min_free_bytes
    package_status = read_json(OUTPUTS / "Plant_CellFM_v9_editor_submission_final.status.json")
    verifier = read_json(RELEASE / "server_release_verification_v9.json")
    gate = read_json(RELEASE / "release_gate_completion_audit_v9.json")

    if "snowcell_scplantdb_root_budgeted_h5ad_queue" in sessions:
        continuation_state = "root_staging_scplantdb_queue_running"
    elif "snowcell_public_queues_when_space" in sessions and not disk_ok:
        continuation_state = "waiting_for_disk_budget"
    elif any(session in sessions for session in QUEUE_SESSIONS if session != "snowcell_public_queues_when_space"):
        continuation_state = "public_queues_running"
    elif disk_ok:
        continuation_state = "disk_ready_queues_not_running"
    else:
        continuation_state = "paused_no_queue_watcher"

    return {
        "schema_version": "plant_cellfm_server_continuation_status_v10",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "min_free_bytes": min_free_bytes,
        "disk_project": disk_project,
        "disk_root": disk_root,
        "root_stage_exists": root_stage.exists(),
        "root_stage": str(root_stage),
        "disk_root_stage": disk_root_stage,
        "root_stage_scplantdb": root_stage_scplantdb,
        "root_v10_training": root_v10_training,
        "disk_budget_ok": disk_ok,
        "tmux_sessions": sessions,
        "active_queue_sessions": active_queue_sessions,
        "continuation_state": continuation_state,
        "health": health(),
        "nvidia_smi": nvidia(),
        "package_source_commit": package_status.get("source_commit", "unknown"),
        "package_sha256": package_status.get("package_sha256", "unknown"),
        "server_verifier_status": verifier.get("overall_status", "not_available"),
        "release_gate_completion_position": gate.get("completion_position", "not_available"),
    }


def fmt_bytes(value: Any) -> str:
    if value is None:
        return "unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{value} B"


def markdown(status: dict[str, Any]) -> str:
    disk = status["disk_project"]
    root_disk = status["disk_root"]
    stage_disk = status.get("disk_root_stage", {})
    root_scplantdb = status.get("root_stage_scplantdb", {})
    root_training = status.get("root_v10_training", {})
    health = status["health"]
    lines = [
        "# Plant-CellFM v10 Continuation Status",
        "",
        f"Generated UTC: `{status['generated_at_utc']}`",
        "",
        f"Project root: `{status['project_root']}`",
        "",
        f"Continuation state: `{status['continuation_state']}`",
        "",
        f"Disk budget OK: `{status['disk_budget_ok']}`",
        "",
        f"Required free space: `{fmt_bytes(status['min_free_bytes'])}`",
        "",
        f"Project disk free: `{fmt_bytes(disk.get('available_bytes'))}` on `{disk.get('mount', '')}` ({disk.get('use_percent', '')} used)",
        "",
        f"Root disk free: `{fmt_bytes(root_disk.get('available_bytes'))}` on `{root_disk.get('mount', '')}` ({root_disk.get('use_percent', '')} used)",
        "",
        f"Root staging exists: `{status.get('root_stage_exists')}` at `{status.get('root_stage')}`",
        "",
        f"Root staging disk free: `{fmt_bytes(stage_disk.get('available_bytes'))}` on `{stage_disk.get('mount', '')}` ({stage_disk.get('use_percent', '')} used)",
        "",
        f"Root staging scPlantDB manifest rows: `{root_scplantdb.get('manifest_rows', 'not_available')}`",
        "",
        f"Root staging scPlantDB H5AD files: `{root_scplantdb.get('h5ad_file_count', 'not_available')}`; total size `{fmt_bytes(root_scplantdb.get('h5ad_total_bytes'))}`",
        "",
        f"Root v10 scPlantDB training exists: `{root_training.get('exists')}` at `{root_training.get('output_dir', '')}`",
        "",
        f"Root v10 scPlantDB training epochs: `{root_training.get('history_epochs', 'not_available')}`; best epoch by eval loss `{root_training.get('best_epoch_by_eval_loss', 'not_available')}`",
        "",
        f"Root v10 scPlantDB test fine accuracy: `{root_training.get('test_metrics', {}).get('fine_accuracy', 'not_available')}`; coarse accuracy `{root_training.get('test_metrics', {}).get('coarse_accuracy', 'not_available')}`",
        "",
        f"Health: `{health.get('status')}`; scope `{health.get('model_scope')}`; device `{health.get('device')}`; adapters `{health.get('adapter_count')}`",
        "",
        f"GPU: `{status['nvidia_smi']['output']}`",
        "",
        f"Final package commit: `{status['package_source_commit']}`",
        "",
        f"Final package SHA256: `{status['package_sha256']}`",
        "",
        f"Server verifier status: `{status['server_verifier_status']}`",
        "",
        f"Release gate position: `{status['release_gate_completion_position']}`",
        "",
        "## Active Queue Sessions",
        "",
    ]
    if status["active_queue_sessions"]:
        lines.extend(f"- `{session}`" for session in status["active_queue_sessions"])
    else:
        lines.append("- none")
    lines.extend(["", "## All tmux Sessions", ""])
    if status["tmux_sessions"]:
        lines.extend(f"- `{session}`" for session in status["tmux_sessions"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Root Staging scPlantDB Files",
            "",
        ]
    )
    h5ad_files = root_scplantdb.get("h5ad_files") or []
    if h5ad_files:
        lines.extend(f"- `{name}`" for name in h5ad_files)
    else:
        lines.append("- none")
    lines.extend(["", "## Root v10 scPlantDB Training", ""])
    if root_training.get("exists"):
        lines.extend(
            [
                f"- Output: `{root_training.get('output_dir')}`",
                f"- Epochs recorded: `{root_training.get('history_epochs')}`",
                f"- Last train loss: `{root_training.get('train_loss_last_epoch')}`",
                f"- Last eval loss: `{root_training.get('eval_loss_last_epoch')}`",
                f"- Last eval fine accuracy: `{root_training.get('eval_fine_accuracy_last_epoch')}`",
                f"- Last eval coarse accuracy: `{root_training.get('eval_coarse_accuracy_last_epoch')}`",
                f"- Test fine accuracy: `{root_training.get('test_metrics', {}).get('fine_accuracy')}`",
                f"- Test coarse accuracy: `{root_training.get('test_metrics', {}).get('coarse_accuracy')}`",
                f"- Best checkpoint exists: `{root_training.get('checkpoints', {}).get('best.pt', {}).get('exists')}`; size `{fmt_bytes(root_training.get('checkpoints', {}).get('best.pt', {}).get('size_bytes'))}`",
                f"- Latest checkpoint exists: `{root_training.get('checkpoints', {}).get('latest.pt', {}).get('exists')}`; size `{fmt_bytes(root_training.get('checkpoints', {}).get('latest.pt', {}).get('size_bytes'))}`",
            ]
        )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report is for post-v9 continuation work. It does not change the frozen v9 editor package. "
            "When the project disk has less free space than the configured budget, public data download and GPU retraining queues should remain paused or waiting. "
            "Once disk budget is restored, the queue watcher can start `scripts/start_public_queues.sh` to continue public plant data acquisition and v10 training refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    min_free_bytes = int(__import__("os").environ.get("SNOWCELL_MIN_FREE_BYTES", "21474836480"))
    status = build_status(min_free_bytes)
    RELEASE.mkdir(parents=True, exist_ok=True)
    json_path = RELEASE / "server_continuation_status_v10.json"
    md_path = RELEASE / "server_continuation_status_v10.md"
    json_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown(status), encoding="utf-8")
    print(json_path)
    print(md_path)
    print(status["continuation_state"])


if __name__ == "__main__":
    main()
