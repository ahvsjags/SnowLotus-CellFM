#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tcp_probe(host: str, port: int, timeout: float) -> dict[str, object]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"ok": True, "error": ""}
    except OSError as exc:
        return {"ok": False, "error": repr(exc)}


def ssh_probe(alias: str, timeout: int) -> dict[str, object]:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=5",
        "-o",
        "ServerAliveCountMax=1",
        alias,
        "hostname; date",
    ]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "command": cmd,
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": repr(exc), "command": cmd}


def parse_watcher_log(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "exists": False,
            "line_count": 0,
            "last_lines": [],
            "attempt_count": 0,
            "last_attempt": "",
            "last_failure": "",
            "success": False,
        }
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start_indices = [
        index for index, line in enumerate(lines) if "watcher starting" in line
    ]
    current_lines = lines[start_indices[-1] :] if start_indices else lines
    attempts = [line for line in current_lines if "attempt " in line and "probing SSH" in line]
    failures = [
        line
        for line in current_lines
        if "SSH probe failed" in line or "startup attempt failed" in line
    ]
    success = any(
        "remote full on-disk corpus watcher started successfully" in line
        for line in current_lines
    )
    total_attempts = [line for line in lines if "attempt " in line and "probing SSH" in line]
    return {
        "exists": True,
        "path": str(path),
        "line_count": len(lines),
        "last_lines": current_lines[-20:],
        "attempt_count": len(attempts),
        "total_attempt_count": len(total_attempts),
        "last_attempt": attempts[-1] if attempts else "",
        "last_failure": failures[-1] if failures else "",
        "success": success,
    }


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).resolve()
    package_dir = root / "editor_package" / "current_submit_v0.3"
    source_archive = package_dir / "snowlotus-cellfm-editor-v0.3-source-metadata.tar.gz"
    manuscript_archive = package_dir / "snowlotus-cellfm-editor-v0.3-manuscript.tar.gz"
    submit_zip = package_dir / "SnowLotus-CellFM_editor-v0.3_submit-now.zip"
    zip_sha_file = package_dir / "SnowLotus-CellFM_editor-v0.3_submit-now.zip.sha256"

    tcp = tcp_probe(args.host, args.port, args.timeout)
    ssh = ssh_probe(args.alias, args.ssh_timeout) if args.probe_ssh else {"ok": None}
    log = parse_watcher_log(Path(args.log_path))

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "alias": args.alias,
        "host": args.host,
        "port": args.port,
        "tcp_probe": tcp,
        "ssh_probe": ssh,
        "watcher": {
            "pid": args.watcher_pid,
            "log": log,
        },
        "artifacts": {
            "source_archive": {
                "path": str(source_archive),
                "sha256": sha256_file(source_archive),
            },
            "manuscript_archive": {
                "path": str(manuscript_archive),
                "sha256": sha256_file(manuscript_archive),
            },
            "submit_zip": {
                "path": str(submit_zip),
                "sha256": sha256_file(submit_zip),
                "sha256_file_text": read_text(zip_sha_file),
            },
        },
    }


def write_markdown(payload: dict[str, object], output: Path) -> None:
    tcp = payload["tcp_probe"]
    ssh = payload["ssh_probe"]
    watcher = payload["watcher"]
    log = watcher["log"]
    artifacts = payload["artifacts"]
    lines = [
        "# SSH recovery status",
        "",
        f"- Timestamp UTC: `{payload['timestamp_utc']}`",
        f"- Alias: `{payload['alias']}`",
        f"- Endpoint: `{payload['host']}:{payload['port']}`",
        f"- TCP probe ok: `{tcp.get('ok')}`",
        f"- TCP probe error: `{tcp.get('error', '')}`",
        f"- SSH probe ok: `{ssh.get('ok')}`",
        f"- SSH return code: `{ssh.get('returncode')}`",
        f"- SSH stderr: `{ssh.get('stderr', '')}`",
        f"- Watcher PID: `{watcher['pid']}`",
        f"- Watcher log exists: `{log.get('exists')}`",
        f"- Watcher attempts seen: `{log.get('attempt_count')}`",
        f"- Watcher success seen: `{log.get('success')}`",
        f"- Last watcher attempt: `{log.get('last_attempt', '')}`",
        f"- Last watcher failure: `{log.get('last_failure', '')}`",
        "",
        "## Artifacts",
        "",
    ]
    for name, item in artifacts.items():
        lines.append(f"- `{name}`: `{item.get('sha256')}`")
    lines.extend(["", "## Last Watcher Log Lines", ""])
    for line in log.get("last_lines", []):
        lines.append(f"    {line}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--alias", default="matpool-px1-jcy")
    parser.add_argument("--host", default="px1-jcy.matpool.com")
    parser.add_argument("--port", type=int, default=27683)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--ssh-timeout", type=int, default=20)
    parser.add_argument("--probe-ssh", action="store_true")
    parser.add_argument("--watcher-pid", default="")
    parser.add_argument("--log-path", default="logs/wait_and_start_remote_full_on_disk.log")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    payload = build_payload(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, output_md)
    print(output_md)
    print(output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
