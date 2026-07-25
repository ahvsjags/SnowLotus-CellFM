from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


CommandRunner = Callable[[list[str], Path], dict[str, Any]]


COMMANDS = [
    ["git", "rev-parse", "--short", "HEAD"],
    ["git", "status", "--short"],
    ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
    ["nvidia-smi"],
]


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    if shutil.which(command[0]) is None:
        return {"command": command, "returncode": None, "stdout": "", "stderr": "command not found"}
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
        timeout=60,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def pip_freeze(cwd: Path, runner: CommandRunner) -> dict[str, Any]:
    return runner([sys.executable, "-m", "pip", "freeze"], cwd)


def collect_environment(project_dir: str | Path, runner: CommandRunner = run_command) -> dict[str, Any]:
    root = Path(project_dir)
    commands = [runner(command, root) for command in COMMANDS]
    return {
        "project_dir": str(root),
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "commands": commands,
        "pip_freeze": pip_freeze(root, runner),
        "reproduction_commands": [
            "python -m pip install -e \".[singlecell,dev]\"",
            "bash scripts/ensure_public_data_jobs.sh",
            "bash scripts/build_public_mlm_corpus.sh",
            "snowcell train --config configs/foundation_5090_pretrain.yaml --device cuda",
            "snowcell train --config configs/foundation_5090_mlm_public_expansion.yaml --device cuda",
            "bash scripts/start_public_mlm_continuation_training.sh",
            "bash scripts/start_public_mlm_continuation_watchdog.sh",
            "bash scripts/start_public_mlm_continuation_package_watchdog.sh",
            "bash scripts/run_strict_benchmark_audits.sh",
            "bash scripts/generate_publication_package.sh",
        ],
    }


def command_to_text(item: dict[str, Any]) -> str:
    command = " ".join(item.get("command", []))
    stdout = item.get("stdout") or ""
    stderr = item.get("stderr") or ""
    code = item.get("returncode")
    lines = [f"### `{command}`", "", f"Return code: `{code}`", ""]
    if stdout:
        lines.extend(["```text", stdout, "```", ""])
    if stderr:
        lines.extend(["stderr:", "", "```text", stderr, "```", ""])
    return "\n".join(lines).rstrip()


def write_markdown(snapshot: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SnowLotus-CellFM Environment Snapshot",
        "",
        "## Python",
        "",
        f"- Executable: `{snapshot['python']['executable']}`",
        f"- Version: `{snapshot['python']['version'].splitlines()[0]}`",
        f"- Implementation: `{snapshot['python']['implementation']}`",
        "",
        "## Platform",
        "",
        f"- System: `{snapshot['platform']['system']}`",
        f"- Release: `{snapshot['platform']['release']}`",
        f"- Machine: `{snapshot['platform']['machine']}`",
        f"- Platform: `{snapshot['platform']['platform']}`",
        "",
        "## Reproduction Commands",
        "",
        "```bash",
        *snapshot["reproduction_commands"],
        "```",
        "",
        "## Command Outputs",
        "",
    ]
    for command in snapshot["commands"]:
        lines.extend([command_to_text(command), ""])
    lines.extend(
        [
            "## Python Packages",
            "",
            "```text",
            snapshot.get("pip_freeze", {}).get("stdout", ""),
            "```",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(output_path)
    return output_path


def write_snapshot(
    project_dir: str | Path,
    output: str | Path,
    json_output: str | Path | None = None,
    runner: CommandRunner = run_command,
) -> tuple[Path, Path | None]:
    snapshot = collect_environment(project_dir, runner=runner)
    markdown_path = write_markdown(snapshot, output)
    json_path = None
    if json_output is not None:
        json_path = Path(json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json_path)
    return markdown_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a reproducibility environment snapshot")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--json-output")
    args = parser.parse_args()
    write_snapshot(args.project_dir, args.output, args.json_output)


if __name__ == "__main__":
    main()
