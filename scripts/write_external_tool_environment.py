from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any


CommandRunner = Callable[[list[str], Path], dict[str, Any]]
R_PACKAGES = ["Matrix", "Seurat", "SeuratObject", "jsonlite"]
SCPLANTLLM_REQUIRED_FILES = ["README.md", "scplantllm/model.py"]
SCPLANTLLM_MODEL_WEIGHT = "model_params/scPlantLLM_model.pth"


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    if shutil.which(command[0]) is None:
        return {"command": command, "returncode": None, "stdout": "", "stderr": "command not found"}
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": -124,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": f"command timed out after {exc.timeout} seconds",
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def check_r_package(package: str, project_dir: Path, runner: CommandRunner) -> dict[str, Any]:
    expression = f"cat(requireNamespace('{package}', quietly=TRUE), '\\n')"
    result = runner(["Rscript", "-e", expression], project_dir)
    available = result.get("stdout", "").strip().splitlines()[:1] == ["TRUE"]
    return {
        "package": package,
        "available": available,
        "command": result.get("command"),
        "returncode": result.get("returncode"),
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
    }


def collect_environment(project_dir: str | Path, runner: CommandRunner = run_command) -> dict[str, Any]:
    root = Path(project_dir)
    rscript_version = runner(["Rscript", "--version"], root)
    git_lfs_version = runner(["git", "lfs", "version"], root)
    r_packages = [check_r_package(package, root, runner) for package in R_PACKAGES]
    scplantllm_dir = root / "external" / "scPlantLLM"
    scplantllm_required = [scplantllm_dir / path for path in SCPLANTLLM_REQUIRED_FILES]
    scplantllm_model_weight = scplantllm_dir / SCPLANTLLM_MODEL_WEIGHT
    scplantllm_complete = scplantllm_dir.exists() and all(path.exists() for path in scplantllm_required)
    scplantllm_benchmark_ready = scplantllm_complete and scplantllm_model_weight.exists()
    scplantllm_git = (
        runner(["git", "-C", str(scplantllm_dir), "rev-parse", "--short", "HEAD"], root)
        if scplantllm_dir.exists()
        else {"command": ["git", "-C", str(scplantllm_dir), "rev-parse", "--short", "HEAD"], "returncode": None, "stdout": "", "stderr": "directory not found"}
    )
    return {
        "project_dir": str(root),
        "rscript": {
            "available": rscript_version.get("returncode") == 0,
            "version_stdout": rscript_version.get("stdout", ""),
            "version_stderr": rscript_version.get("stderr", ""),
        },
        "r_packages": r_packages,
        "seurat_ready": all(item["available"] for item in r_packages),
        "git_lfs": {
            "available": git_lfs_version.get("returncode") == 0,
            "version_stdout": git_lfs_version.get("stdout", ""),
            "version_stderr": git_lfs_version.get("stderr", ""),
        },
        "scplantllm": {
            "path": str(scplantllm_dir),
            "exists": scplantllm_dir.exists(),
            "checkout_complete": scplantllm_complete,
            "benchmark_ready": scplantllm_benchmark_ready,
            "required_files": SCPLANTLLM_REQUIRED_FILES,
            "missing_required_files": [
                path.relative_to(scplantllm_dir).as_posix()
                for path in scplantllm_required
                if not path.exists()
            ],
            "model_weight": SCPLANTLLM_MODEL_WEIGHT,
            "model_weight_exists": scplantllm_model_weight.exists(),
            "model_weight_bytes": scplantllm_model_weight.stat().st_size if scplantllm_model_weight.exists() else 0,
            "git_head": scplantllm_git.get("stdout", ""),
            "git_error": scplantllm_git.get("stderr", ""),
        },
        "recommended_actions": recommended_actions(
            r_packages,
            scplantllm_complete,
            scplantllm_model_weight.exists(),
            git_lfs_version.get("returncode") == 0,
        ),
    }


def recommended_actions(
    r_packages: list[dict[str, Any]],
    scplantllm_exists: bool,
    scplantllm_model_weight_exists: bool,
    git_lfs_available: bool,
) -> list[str]:
    actions = []
    missing_r = [item["package"] for item in r_packages if not item["available"]]
    if missing_r:
        actions.append(
            "Run scripts/install_r_singlecell_tools.sh to install missing R packages: "
            + ", ".join(missing_r)
        )
    if not scplantllm_exists:
        actions.append("Run SNOWCELL_CLONE_REFERENCES=1 bash scripts/collect_public_data.sh to clone scPlantLLM.")
    if scplantllm_exists and not scplantllm_model_weight_exists:
        if git_lfs_available:
            actions.append(
                "Fetch external/scPlantLLM/model_params/scPlantLLM_model.pth with git-lfs "
                "before reporting scPlantLLM model-comparison metrics."
            )
        else:
            actions.append(
                "Install git-lfs, then fetch external/scPlantLLM/model_params/scPlantLLM_model.pth "
                "before reporting scPlantLLM model-comparison metrics."
            )
    if not actions:
        actions.append("External benchmark environment checks passed for currently configured tools.")
    return actions


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SnowLotus-CellFM External Tool Environment",
        "",
        f"- Rscript available: `{payload['rscript']['available']}`",
        f"- Seurat benchmark environment ready: `{payload['seurat_ready']}`",
        f"- git-lfs available: `{payload['git_lfs']['available']}`",
        f"- scPlantLLM checkout exists: `{payload['scplantllm']['exists']}`",
        f"- scPlantLLM checkout complete: `{payload['scplantllm']['checkout_complete']}`",
        f"- scPlantLLM model weight present: `{payload['scplantllm']['model_weight_exists']}`",
        f"- scPlantLLM benchmark-ready environment: `{payload['scplantllm']['benchmark_ready']}`",
        "",
        "## R Packages",
        "",
        "| Package | Available |",
        "| --- | --- |",
    ]
    for item in payload["r_packages"]:
        lines.append(f"| {item['package']} | {item['available']} |")
    lines.extend(
        [
            "",
            "## scPlantLLM",
            "",
            f"- Path: `{payload['scplantllm']['path']}`",
            f"- Git head: `{payload['scplantllm']['git_head']}`",
            f"- Git error: `{payload['scplantllm']['git_error']}`",
            f"- Missing required files: `{', '.join(payload['scplantllm']['missing_required_files'])}`",
            f"- Model weight: `{payload['scplantllm']['model_weight']}`",
            f"- Model weight bytes: `{payload['scplantllm']['model_weight_bytes']}`",
            "",
            "## Recommended Actions",
            "",
        ]
    )
    lines.extend(f"- {action}" for action in payload["recommended_actions"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit external single-cell benchmark tool environment")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    payload = collect_environment(args.project_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
