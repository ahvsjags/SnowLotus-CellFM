from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("/mnt/snowlotus_cellfm")
DEFAULT_HEALTH_URL = "http://127.0.0.1:8000/health"

CRITICAL_ZIP_ENTRIES = [
    "SUBMISSION_INDEX_v9.md",
    "GITHUB_SYNC_RECOVERY.md",
    "PACKAGE_MANIFEST.json",
    "PACKAGE_README.md",
    "manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx",
    "release_metadata/plant_cellfm_v9_model_card.md",
    "release_metadata/server_sustainability_status_v9.md",
    "release_metadata/species_ontology_label_benchmark_v9.md",
    "release_metadata/species_ontology_label_benchmark_v9.json",
    "scripts/verify_v9_server_release.py",
]

CRITICAL_ROOT_FILES = [
    "SUBMISSION_INDEX_v9.md",
    "scripts/package_v9_editor_submission.py",
    "scripts/verify_v9_server_release.py",
    "release_metadata/server_sustainability_status_v9.md",
    "release_metadata/species_ontology_label_benchmark_v9.md",
    "release_metadata/species_ontology_label_benchmark_v9.json",
    "release_metadata/api_runtime_smoke_v9.md",
    "release_metadata/watchdog_recovery_status_v9.md",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], timeout: int = 15) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            args,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def check(name: str, passed: bool, detail: str, required: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "status": "pass" if passed else ("warn" if not required else "fail"),
        "required": required,
        "detail": detail,
    }


def fetch_health(url: str, timeout: int = 8) -> tuple[bool, dict[str, Any] | None, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        return True, data, payload
    except Exception as exc:
        return False, None, str(exc)


def verify(root: Path, health_url: str) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    checks: list[dict[str, Any]] = []

    output_dir = root / "outputs" / "editor_submission_v9"
    zip_path = output_dir / "Plant_CellFM_v9_editor_submission_final.zip"
    status_path = output_dir / "Plant_CellFM_v9_editor_submission_final.status.json"
    sha_path = output_dir / "Plant_CellFM_v9_editor_submission_final.zip.sha256"
    addendum_dir = root / "outputs" / "publication_package" / "v9_lora_shared_4090" / "addendum_methods_panel"

    status: dict[str, Any] = {}
    if status_path.exists():
        try:
            status = read_json(status_path)
            checks.append(check("status_json_parse", True, str(status_path)))
        except Exception as exc:
            checks.append(check("status_json_parse", False, f"{status_path}: {exc}"))
    else:
        checks.append(check("status_json_exists", False, str(status_path)))

    checks.append(check("final_zip_exists", zip_path.exists(), str(zip_path)))
    if zip_path.exists() and status:
        zip_sha = sha256_file(zip_path)
        expected = str(status.get("package_sha256", "")).strip()
        checks.append(check("final_zip_sha256_matches_status", zip_sha == expected, f"observed={zip_sha}; expected={expected}"))
        if sha_path.exists():
            sidecar = sha_path.read_text(encoding="utf-8").split()[0].strip()
            checks.append(check("final_zip_sha256_matches_sidecar", zip_sha == sidecar, f"observed={zip_sha}; sidecar={sidecar}"))
        else:
            checks.append(check("final_zip_sha256_sidecar_exists", False, str(sha_path)))

    if zip_path.exists():
        try:
            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
                bad = archive.testzip()
                checks.append(check("final_zip_integrity", bad is None, "zipfile.testzip ok" if bad is None else f"bad entry={bad}"))
                missing = [entry for entry in CRITICAL_ZIP_ENTRIES if entry not in names]
                checks.append(check("critical_zip_entries", not missing, "missing=" + ",".join(missing) if missing else f"{len(CRITICAL_ZIP_ENTRIES)} entries present"))
                if "GITHUB_SYNC_RECOVERY.md" in names and status:
                    recovery = archive.read("GITHUB_SYNC_RECOVERY.md").decode("utf-8", errors="replace")
                    source_commit = str(status.get("source_commit", ""))
                    checks.append(check("github_recovery_note_matches_source_commit", source_commit in recovery, source_commit))
        except Exception as exc:
            checks.append(check("final_zip_readable", False, str(exc)))

    if status:
        source_commit = str(status.get("source_commit", ""))
        origin_head = str(status.get("origin_branch_head", ""))
        checks.append(check("source_commit_recorded", len(source_commit) == 40 and source_commit != "unknown", source_commit))
        checks.append(check("origin_head_recorded", len(origin_head) == 40 and origin_head != "unknown", origin_head))
        checks.append(check("read_first_includes_recovery", "GITHUB_SYNC_RECOVERY.md" in status.get("read_first", []), str(status.get("read_first", []))))

    missing_root = [relative for relative in CRITICAL_ROOT_FILES if not (root / relative).exists()]
    checks.append(check("critical_project_files_on_server", not missing_root, "missing=" + ",".join(missing_root) if missing_root else f"{len(CRITICAL_ROOT_FILES)} files present"))

    addendum_recovery = addendum_dir / "GITHUB_SYNC_RECOVERY.md"
    addendum_sha = addendum_dir / "addendum_sha256sums.txt"
    checks.append(check("addendum_recovery_note_exists", addendum_recovery.exists(), str(addendum_recovery)))
    checks.append(check("addendum_sha256sums_exists", addendum_sha.exists(), str(addendum_sha)))
    if addendum_recovery.exists() and status:
        recovery_text = addendum_recovery.read_text(encoding="utf-8", errors="replace")
        checks.append(check("addendum_recovery_note_matches_source_commit", str(status.get("source_commit", "")) in recovery_text, str(status.get("source_commit", ""))))

    health_ok, health, health_detail = fetch_health(health_url)
    checks.append(check("health_endpoint_reachable", health_ok, health_detail if not health_ok else json.dumps(health, ensure_ascii=False)))
    if health:
        checks.append(check("health_status_ok", health.get("status") == "ok", str(health.get("status"))))
        checks.append(check("health_device_cuda", health.get("device") == "cuda", str(health.get("device"))))
        checks.append(check("health_model_scope_plant_general", health.get("model_scope") == "plant_general", str(health.get("model_scope"))))
        checks.append(check("health_adapter_count_24", int(health.get("adapter_count", -1)) >= 24, str(health.get("adapter_count"))))

    code, gpu_out, gpu_err = run_command(
        ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader"],
        timeout=15,
    )
    gpu_detail = gpu_out if code == 0 else gpu_err
    checks.append(check("nvidia_smi_available", code == 0, gpu_detail))
    checks.append(check("gpu_is_rtx_4090", "RTX 4090" in gpu_out, gpu_out))

    code, tmux_out, tmux_err = run_command(["tmux", "ls"], timeout=10)
    tmux_detail = tmux_out if code == 0 else tmux_err
    checks.append(check("watchdog_tmux_session_present", "plant_cellfm_watchdog" in tmux_out, tmux_detail))

    failed_required = [item for item in checks if item["required"] and item["status"] != "pass"]
    warnings = [item for item in checks if item["status"] == "warn"]

    return {
        "schema_version": "plant_cellfm_v9_server_release_verification_v1",
        "generated_at_utc": generated_at,
        "root": str(root),
        "health_url": health_url,
        "overall_status": "pass" if not failed_required else "fail",
        "failed_required_count": len(failed_required),
        "warning_count": len(warnings),
        "checks": checks,
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Plant-CellFM v9 Server Release Verification",
        "",
        f"Generated UTC: `{result['generated_at_utc']}`",
        "",
        f"Root: `{result['root']}`",
        "",
        f"Health URL: `{result['health_url']}`",
        "",
        f"Overall status: `{result['overall_status']}`",
        "",
        "| Check | Status | Required | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for item in result["checks"]:
        detail = str(item["detail"]).replace("|", "/").replace("\n", " ")
        if len(detail) > 220:
            detail = detail[:217] + "..."
        lines.append(f"| {item['name']} | {item['status']} | {item['required']} | {detail} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A `pass` result means the server-hosted final editor package is checksum-verifiable, the package contains the reviewer-facing recovery note and critical release artifacts, the project tree contains the corresponding evidence files, the live Plant-CellFM service answers `/health` on CUDA, the RTX 4090 is visible to `nvidia-smi`, and the watchdog tmux session is present.",
            "",
            "This verifier does not push to GitHub. GitHub synchronization remains controlled by workstation authentication and is documented separately in `GITHUB_SYNC_RECOVERY.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the Plant-CellFM v9 server release package and live service")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--health-url", default=DEFAULT_HEALTH_URL)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    result = verify(args.root, args.health_url)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text, encoding="utf-8")
    else:
        print(text)
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown_report(result), encoding="utf-8")
    raise SystemExit(0 if result["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
