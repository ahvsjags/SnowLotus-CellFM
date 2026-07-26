#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
from datetime import datetime, timezone
from pathlib import Path


def resolve_ports_file(path: Path) -> tuple[Path, bool]:
    if path.exists():
        return path, False
    if path.name == "matpool_px1_candidate_ports.txt":
        example = path.with_name("matpool_px1_candidate_ports.example.txt")
        if example.exists():
            return example, True
    raise FileNotFoundError(f"candidate ports file not found: {path}")


def parse_port_token(token: str, allow_ranges: bool) -> list[int]:
    token = token.strip()
    if not token:
        return []
    if "-" in token:
        if not allow_ranges:
            raise ValueError(f"port range requires --allow-ranges: {token}")
        left, right = token.split("-", 1)
        start = int(left)
        end = int(right)
        if start > end:
            raise ValueError(f"invalid descending port range: {token}")
        return list(range(start, end + 1))
    return [int(token)]


def read_candidate_ports(path: Path, allow_ranges: bool, max_ports: int) -> list[int]:
    ports: list[int] = []
    seen: set[int] = set()
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.split("#", 1)[0].replace(",", " ").strip()
        if not line:
            continue
        for token in line.split():
            for port in parse_port_token(token, allow_ranges=allow_ranges):
                if port < 1 or port > 65535:
                    raise ValueError(f"port out of range at {path}:{line_number}: {port}")
                if port not in seen:
                    ports.append(port)
                    seen.add(port)
                if len(ports) > max_ports:
                    raise ValueError(f"too many candidate ports; max allowed is {max_ports}")
    if not ports:
        raise ValueError(f"no candidate ports found in {path}")
    return ports


def tcp_probe(host: str, port: int, timeout: float) -> dict[str, object]:
    started = datetime.now(timezone.utc)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            ok = True
            error = ""
    except OSError as exc:
        ok = False
        errno = getattr(exc, "errno", None)
        winerror = getattr(exc, "winerror", None)
        parts = [exc.__class__.__name__]
        if errno is not None:
            parts.append(f"errno={errno}")
        if winerror is not None:
            parts.append(f"winerror={winerror}")
        error = " ".join(parts)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    return {"port": port, "ok": ok, "error": error, "elapsed_seconds": round(elapsed, 3)}


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    requested_ports_file = Path(args.ports_file)
    ports_file, used_example = resolve_ports_file(requested_ports_file)
    ports = read_candidate_ports(
        ports_file,
        allow_ranges=args.allow_ranges,
        max_ports=args.max_ports,
    )
    results = [tcp_probe(args.host, port, args.timeout) for port in ports]
    open_ports = [item["port"] for item in results if item["ok"]]
    selected_open_port = open_ports[0] if open_ports else None
    hint_written = False
    if selected_open_port is not None and args.write_hint_if_open:
        hint_path = Path(args.write_hint_if_open)
        hint_path.parent.mkdir(parents=True, exist_ok=True)
        hint_path.write_text(f"{selected_open_port}\n", encoding="ascii")
        hint_written = True
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": args.host,
        "requested_ports_file": str(requested_ports_file),
        "ports_file": str(ports_file),
        "used_example_ports_file": used_example,
        "allow_ranges": args.allow_ranges,
        "max_ports": args.max_ports,
        "timeout_seconds": args.timeout,
        "candidate_ports": ports,
        "results": results,
        "open_ports": open_ports,
        "selected_open_port": selected_open_port,
        "hint_path": args.write_hint_if_open or "",
        "hint_written": hint_written,
    }


def write_markdown(payload: dict[str, object], path: Path) -> None:
    lines = [
        "# Matpool candidate port probe",
        "",
        f"- Timestamp UTC: `{payload['timestamp_utc']}`",
        f"- Host: `{payload['host']}`",
        f"- Ports file: `{payload['ports_file']}`",
        f"- Used example file: `{payload['used_example_ports_file']}`",
        f"- Candidate count: `{len(payload['candidate_ports'])}`",
        f"- Open ports: `{payload['open_ports']}`",
        f"- Selected open port: `{payload['selected_open_port']}`",
        f"- Hint written: `{payload['hint_written']}`",
        f"- Hint path: `{payload['hint_path']}`",
        "",
        "| port | ok | elapsed_s | error |",
        "| --- | --- | ---: | --- |",
    ]
    for item in payload["results"]:
        error = str(item.get("error", "")).replace("|", "\\|")
        lines.append(
            f"| {item['port']} | {item['ok']} | {item['elapsed_seconds']} | `{error}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe only explicitly listed Matpool SSH candidate ports and optionally "
            "write config/matpool_px1_next_port.txt for the recovery watcher."
        )
    )
    parser.add_argument("--host", default="px2-jcy.matpool.com")
    parser.add_argument("--ports-file", default="config/matpool_px1_candidate_ports.txt")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--max-ports", type=int, default=64)
    parser.add_argument("--allow-ranges", action="store_true")
    parser.add_argument("--write-hint-if-open", default="")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--fail-if-none-open", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        write_markdown(payload, Path(args.output_md))
    print(json.dumps(payload, ensure_ascii=False))
    if args.fail_if_none_open and payload["selected_open_port"] is None:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
