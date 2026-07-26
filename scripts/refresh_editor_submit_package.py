#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path


PACKAGE_FILES = [
    "ARCHIVE_SHA256SUMS.txt",
    "SUBMISSION_STATUS_NOW.md",
    "ssh_recovery_status.local.md",
    "ssh_recovery_status.local.json",
    "matpool_candidate_port_probe.local.md",
    "matpool_candidate_port_probe.local.json",
    "matpool_ssh_recovery_runbook.md",
    "matpool_px1_next_port.example.txt",
    "matpool_px1_candidate_ports.example.txt",
    "remote_training_state.after_px2_recovery.md",
    "remote_training_state.after_px2_recovery.json",
    "README.remote.md",
    "GITHUB_PUSH_INSTRUCTIONS.remote.md",
    "EDITOR_HANDOFF.remote.md",
    "MODEL_RELEASE_NOTES_v0_3.remote.md",
    "editor_live_status_panel.remote.md",
    "public_mlm_plus_readiness.remote.md",
    "scplantannotate_access_audit.remote.md",
    "scplantllm_input_readiness.remote.md",
    "benchmark_gap_audit.remote.md",
    "models_SHA256SUMS.remote.txt",
    "SnowLotus_CellFM_editor_submission_v0_3.docx",
    "SnowLotus_CellFM_editor_submission_v0_3.md",
    "editor_cover_note_v0_3.docx",
    "editor_cover_note_v0_3.md",
    "snowlotus-cellfm-editor-v0.3-source-metadata.tar.gz",
    "snowlotus-cellfm-editor-v0.3-manuscript.tar.gz",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_recovery_status(args: argparse.Namespace, package_dir: Path) -> None:
    script = Path(args.root) / "scripts" / "write_ssh_recovery_status.py"
    cmd = [
        sys.executable,
        "-X",
        "utf8",
        str(script),
        "--root",
        str(args.root),
        "--alias",
        args.alias,
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--watcher-pid",
        str(args.watcher_pid),
        "--log-path",
        args.log_path,
        "--output-md",
        str(package_dir / "ssh_recovery_status.local.md"),
        "--output-json",
        str(package_dir / "ssh_recovery_status.local.json"),
        "--probe-ssh",
    ]
    subprocess.run(cmd, check=True)


def update_checksum_list(package_dir: Path) -> dict[str, str]:
    targets = {
        "snowlotus-cellfm-editor-v0.3-source-metadata.tar.gz": package_dir
        / "snowlotus-cellfm-editor-v0.3-source-metadata.tar.gz",
        "snowlotus-cellfm-editor-v0.3-manuscript.tar.gz": package_dir
        / "snowlotus-cellfm-editor-v0.3-manuscript.tar.gz",
        "snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz": package_dir
        / "snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz",
    }
    hashes = {
        name: sha256_file(path)
        for name, path in targets.items()
        if path.exists()
    }
    checksum_path = package_dir / "ARCHIVE_SHA256SUMS.txt"
    lines = checksum_path.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    seen: set[str] = set()
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[1] in hashes:
            updated.append(f"{hashes[parts[1]]}  {parts[1]}")
            seen.add(parts[1])
        else:
            updated.append(line)
    for name, digest in hashes.items():
        if name not in seen:
            updated.append(f"{digest}  {name}")
    checksum_path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
    return hashes


def read_recovery_payload(package_dir: Path) -> dict[str, object]:
    path = package_dir / "ssh_recovery_status.local.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def replace_once(text: str, pattern: str, replacement: str) -> str:
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"pattern did not match exactly once: {pattern}")
    return new_text


def update_status_page(
    package_dir: Path,
    hashes: dict[str, str],
    payload: dict[str, object],
    generated: str,
    github_commit: str,
) -> None:
    path = package_dir / "SUBMISSION_STATUS_NOW.md"
    text = path.read_text(encoding="utf-8")
    watcher = payload.get("watcher", {}) if isinstance(payload, dict) else {}
    log = watcher.get("log", {}) if isinstance(watcher, dict) else {}
    watcher_pid = str(watcher.get("pid", ""))
    attempt_count = str(log.get("attempt_count", ""))
    tcp = payload.get("tcp_probe", {}) if isinstance(payload, dict) else {}
    ssh = payload.get("ssh_probe", {}) if isinstance(payload, dict) else {}
    watcher_success = str(log.get("success", ""))

    text = replace_once(text, r"^Generated: .+$", f"Generated: {generated} Asia/Shanghai")
    if "snowlotus-cellfm-editor-v0.3-source-metadata.tar.gz" in hashes:
        text = replace_once(
            text,
            r"- Source/metadata archive: `[^`]+`",
            f"- Source/metadata archive: `{hashes['snowlotus-cellfm-editor-v0.3-source-metadata.tar.gz']}`",
        )
    if "snowlotus-cellfm-editor-v0.3-manuscript.tar.gz" in hashes:
        text = replace_once(
            text,
            r"- Manuscript/editor archive: `[^`]+`",
            f"- Manuscript/editor archive: `{hashes['snowlotus-cellfm-editor-v0.3-manuscript.tar.gz']}`",
        )
    if "snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz" in hashes:
        text = replace_once(
            text,
            r"- Local full archive with current best models: `[^`]+`",
            f"- Local full archive with current best models: `{hashes['snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz']}`",
        )
    text = re.sub(
        r"Subsequent SSH/TCP checks through [^`]+? Asia/Shanghai returned",
        f"Subsequent SSH/TCP checks through {generated} Asia/Shanghai returned",
        text,
        count=1,
    )
    if watcher_pid:
        text = replace_once(
            text,
            r"It is currently running locally as PID `[^`]+`",
            f"It is currently running locally as PID `{watcher_pid}`",
        )
    if attempt_count:
        audit_line = (
            "- Local recovery status is generated by `scripts/write_ssh_recovery_status.py`; "
            "the current audit files are `ssh_recovery_status.local.md/json`. "
            f"The latest audit observed TCP probe ok=`{tcp.get('ok')}`, "
            f"SSH probe ok=`{ssh.get('ok')}`, watcher success=`{watcher_success}`, "
            f"watcher PID=`{watcher_pid}`, and current watcher attempt `{attempt_count}/240`."
        )
        text = replace_once(
            text,
            r"- Local recovery status is generated by `scripts/write_ssh_recovery_status\.py`; .+$",
            audit_line,
        )
    if github_commit:
        text = replace_once(
            text,
            r"GitHub source tree is synchronized from the local authenticated GitHub account at commit `[^`]+`;",
            f"GitHub source tree is synchronized from the local authenticated GitHub account at commit `{github_commit}`;",
        )
        text = replace_once(
            text,
            r"- Source commit: `[^`]+`",
            f"- Source commit: `{github_commit}`",
        )
    path.write_text(text, encoding="utf-8")


def rebuild_zip(package_dir: Path) -> str:
    zip_path = package_dir / "SnowLotus-CellFM_editor-v0.3_submit-now.zip"
    sha_path = package_dir / "SnowLotus-CellFM_editor-v0.3_submit-now.zip.sha256"
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if zip_path.exists():
        shutil.move(str(zip_path), str(package_dir / f"{zip_path.stem}.before-refresh-{stamp}.zip"))
    if sha_path.exists():
        shutil.move(str(sha_path), str(package_dir / f"{zip_path.stem}.before-refresh-{stamp}.zip.sha256"))
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in PACKAGE_FILES:
            path = package_dir / relative
            if not path.exists():
                raise FileNotFoundError(f"missing package file: {path}")
            archive.write(path, arcname=relative)
    digest = sha256_file(zip_path)
    sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="ascii")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--package-dir", default="editor_package/current_submit_v0.3")
    parser.add_argument("--alias", default="matpool-px1-jcy")
    parser.add_argument("--host", default="px2-jcy.matpool.com")
    parser.add_argument("--port", type=int, default=29153)
    parser.add_argument("--watcher-pid", default="")
    parser.add_argument("--log-path", default="logs/wait_and_start_remote_full_on_disk.log")
    parser.add_argument("--github-commit", default="")
    args = parser.parse_args()

    args.root = Path(args.root).resolve()
    package_dir = (args.root / args.package_dir).resolve()
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    run_recovery_status(args, package_dir)
    hashes = update_checksum_list(package_dir)
    payload = read_recovery_payload(package_dir)
    update_status_page(
        package_dir=package_dir,
        hashes=hashes,
        payload=payload,
        generated=generated,
        github_commit=args.github_commit,
    )
    zip_digest = rebuild_zip(package_dir)
    print(json.dumps({
        "package_dir": str(package_dir),
        "generated": generated,
        "github_commit": args.github_commit,
        "zip_sha256": zip_digest,
        "hashes": hashes,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
