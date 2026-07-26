from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DEFAULT = Path("/root/snowlotus-cellfm")
V03_RUN_ID = "foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm"
TRAIN_PROGRESS = Path("outputs") / V03_RUN_ID / "progress_latest.json"
TRAIN_HISTORY = Path("outputs") / V03_RUN_ID / "history.json"
CURRENT_BEST = Path("outputs/post_training_release/editor_v0_3_current_best.json")
RELEASE_DIR = Path("outputs/github_release/SnowLotus-CellFM")
GSE_ACCESSION = "GSE155304"
GSE_LOG = Path("logs/geo_promotion_gse155304_rds_rescue.log")
GSE_WATCHDOG_LOG = Path("logs/geo_promotion_gse155304_rds_rescue.log")
GSE_MANIFEST = Path("data/corpus_manifest.gse155304.tsv")
GSE_DOWNLOAD_DIR = Path("data/public/GSE155304_rds")


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 30, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except Exception as exc:
        return {"returncode": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def tail_text(path: Path, max_lines: int = 200) -> list[str]:
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()[-max_lines:]
    except Exception:
        return []


def parse_latest_aria2_progress(lines: list[str]) -> dict[str, Any]:
    progress: dict[str, Any] = {}
    pattern = re.compile(
        r"\[#(?P<gid>[0-9a-f]+)\s+(?P<done>[^/]+)/(?P<total>[^\(]+)\((?P<percent>\d+)%\)"
        r".*?DL:(?P<speed>[^\s\]]+)(?:\s+ETA:(?P<eta>[^\]]+))?"
    )
    for line in reversed(lines):
        match = pattern.search(line)
        if match:
            progress = match.groupdict()
            progress["percent"] = int(progress["percent"])
            break
    return progress


def manifest_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "rows": 0, "ready": False}
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    rows = max(0, len(lines) - 1)
    return {"exists": True, "rows": rows, "ready": rows > 0}


def download_status(project_dir: Path) -> dict[str, Any]:
    directory = project_dir / GSE_DOWNLOAD_DIR
    files: list[dict[str, Any]] = []
    if directory.exists():
        for path in sorted(directory.glob("*")):
            if path.is_file():
                files.append(
                    {
                        "name": path.name,
                        "size_bytes": path.stat().st_size,
                        "has_aria2_sidecar": (directory / f"{path.name}.aria2").exists()
                        if not path.name.endswith(".aria2")
                        else False,
                    }
                )
    lines = tail_text(project_dir / GSE_LOG)
    return {
        "accession": GSE_ACCESSION,
        "manifest": manifest_status(project_dir / GSE_MANIFEST),
        "download_dir": str(GSE_DOWNLOAD_DIR),
        "files": files,
        "latest_progress": parse_latest_aria2_progress(lines),
        "watchdog_tail": tail_text(project_dir / GSE_WATCHDOG_LOG, 20),
    }


def training_status(project_dir: Path) -> dict[str, Any]:
    progress = read_json(project_dir / TRAIN_PROGRESS)
    step = progress.get("step")
    total = progress.get("train_batches_per_epoch")
    if isinstance(step, int) and isinstance(total, int) and total:
        progress["epoch_progress_percent"] = round(step * 100.0 / total, 2)
    progress["run_id"] = V03_RUN_ID

    current_best = read_json(project_dir / CURRENT_BEST)
    if current_best:
        progress["best_epoch"] = current_best.get("best_epoch")
        progress["best_eval_loss"] = current_best.get("best_eval_loss")
        progress["best_checkpoint_sha256"] = current_best.get("sha256")

    history = read_json(project_dir / TRAIN_HISTORY)
    epochs = history.get("epochs") if isinstance(history, dict) else None
    if isinstance(epochs, list) and epochs:
        scored = [
            item for item in epochs
            if isinstance(item, dict) and item.get("eval_loss") is not None
        ]
        if scored and progress.get("best_epoch") is None:
            best = min(scored, key=lambda item: float(item["eval_loss"]))
            progress["best_epoch"] = best.get("epoch")
            progress["best_eval_loss"] = best.get("eval_loss")
        progress["latest_evaluated_epoch"] = epochs[-1].get("epoch")
        progress["latest_eval_loss"] = epochs[-1].get("eval_loss")
    return progress


def release_status(project_dir: Path) -> dict[str, Any]:
    release_dir = project_dir / RELEASE_DIR
    status = {
        "release_dir": str(RELEASE_DIR),
        "sha256": run(["sha256sum", "-c", "models/SHA256SUMS.txt"], cwd=release_dir),
        "lfs": run(["git", "lfs", "ls-files"], cwd=release_dir),
    }
    github_env = os.environ.copy()
    github_env["GIT_SSH_COMMAND"] = "ssh -i ~/.ssh/snowlotus_cellfm_github_ed25519 -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
    status["github_access"] = run(["git", "ls-remote", "origin", "HEAD"], cwd=release_dir, timeout=25, env=github_env)
    return status


def tmux_status() -> dict[str, Any]:
    sessions = run(["tmux", "ls"], timeout=10)
    interesting = []
    for line in sessions.get("stdout", "").splitlines():
        if any(token in line for token in ["snowcell_mlm", "geo_promotion", "github_release"]):
            interesting.append(line)
    return {"all_query": sessions, "interesting_sessions": interesting}


def gpu_status() -> dict[str, Any]:
    return run(
        [
            "nvidia-smi",
            "--query-gpu=timestamp,utilization.gpu,memory.used,memory.total",
            "--format=csv,noheader",
        ],
        timeout=10,
    )


def render_md(panel: dict[str, Any]) -> str:
    training = panel.get("training", {})
    gse = panel.get("gse226826", {})
    release = panel.get("release", {})
    github = release.get("github_access", {})
    sha = release.get("sha256", {})
    progress = gse.get("latest_progress", {})
    manifest = gse.get("manifest", {})
    lfs_stdout = release.get("lfs", {}).get("stdout", "")
    lfs_count = len([line for line in lfs_stdout.splitlines() if line.strip()])

    lines = [
        "# SnowLotus-CellFM live editor status panel",
        "",
        f"- Generated UTC: `{panel['generated_utc']}`",
        f"- Project directory: `{panel['project_dir']}`",
        "",
        "## RTX 5090 training",
        "",
        f"- Run ID: `{training.get('run_id', 'unknown')}`",
        f"- Status: `{training.get('status', 'unknown')}`",
        f"- Epoch: `{training.get('epoch', 'unknown')}`",
        f"- Step: `{training.get('step', 'unknown')}/{training.get('train_batches_per_epoch', 'unknown')}`",
        f"- Epoch progress: `{training.get('epoch_progress_percent', 'unknown')}%`",
        f"- Optimizer updates: `{training.get('optimizer_updates', 'unknown')}`",
        f"- Running loss: `{training.get('running_train_losses', {}).get('loss', training.get('train_loss', 'unknown'))}`",
        f"- Best evaluated epoch: `{training.get('best_epoch', 'unknown')}`",
        f"- Best eval loss: `{training.get('best_eval_loss', 'unknown')}`",
        f"- GPU: `{panel.get('gpu', {}).get('stdout', 'unknown')}`",
        "",
        "## Public data promotion",
        "",
        f"- Focus accession: `{gse.get('accession', GSE_ACCESSION)}`",
        f"- Manifest ready: `{manifest.get('ready', False)}`",
        f"- Manifest rows: `{manifest.get('rows', 0)}`",
        f"- Latest download progress: `{progress.get('done', 'unknown')}/{progress.get('total', 'unknown')} ({progress.get('percent', 'unknown')}%)`",
        f"- Latest speed: `{progress.get('speed', 'unknown')}`",
        f"- Latest ETA: `{progress.get('eta', 'unknown')}`",
        "",
        "## Release package",
        "",
        f"- Release directory: `{release.get('release_dir', RELEASE_DIR)}`",
        f"- Git LFS model files: `{lfs_count}`",
        f"- SHA256 check return code: `{sha.get('returncode')}`",
        "",
        "## GitHub publication status",
        "",
        f"- Remote check return code: `{github.get('returncode')}`",
        f"- Remote check stderr: `{github.get('stderr', '')}`",
        "",
        "## Active tmux sessions",
        "",
    ]
    for session in panel.get("tmux", {}).get("interesting_sessions", []):
        lines.append(f"- `{session}`")
    if not panel.get("tmux", {}).get("interesting_sessions"):
        lines.append("- No matching tmux sessions reported.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=PROJECT_DEFAULT)
    parser.add_argument("--output-md", type=Path, default=Path("outputs/publication_package/editor_live_status_panel.md"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/publication_package/editor_live_status_panel.json"))
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    panel = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(project_dir),
        "training": training_status(project_dir),
        "gpu": gpu_status(),
        "gse226826": download_status(project_dir),
        "release": release_status(project_dir),
        "tmux": tmux_status(),
    }

    output_json = args.output_json if args.output_json.is_absolute() else project_dir / args.output_json
    output_md = args.output_md if args.output_md.is_absolute() else project_dir / args.output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(panel, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_md(panel), encoding="utf-8")
    print(output_md)
    print(output_json)


if __name__ == "__main__":
    main()
