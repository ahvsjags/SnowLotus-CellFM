#!/usr/bin/env python3
"""Small HTTP service for reproducible SnowLotus-CellFM inference.

The service intentionally accepts server-side dataset paths instead of file
uploads. This keeps large single-cell matrices out of request bodies and
makes each annotation run auditable through its output directory.
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import torch

from snowcell.artifacts import load_checkpoint
from snowcell.train import annotate_to_bundle


def _device(value: str) -> torch.device:
    if value == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(value)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


class SnowLotusHandler(BaseHTTPRequestHandler):
    server_version = "SnowLotusCellFM/0.1"

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        route = urlparse(self.path).path
        state = self.server.state  # type: ignore[attr-defined]
        if route == "/health":
            self._send(
                200,
                {
                    "status": "ok",
                    "service": "SnowLotus-CellFM",
                    "device": str(state["device"]),
                },
            )
            return
        if route == "/metadata":
            self._send(200, state["metadata"])
            return
        self._send(404, {"error": "unknown route"})

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        route = urlparse(self.path).path
        if route != "/annotate":
            self._send(404, {"error": "unknown route"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(request, dict):
                raise ValueError("request body must be a JSON object")
            state = self.server.state  # type: ignore[attr-defined]
            data_path = Path(str(request["data_path"])).expanduser().resolve()
            output_dir = Path(str(request["output_dir"])).expanduser().resolve()
            data_root = state["data_root"]
            if data_root is not None:
                try:
                    data_path.relative_to(data_root)
                except ValueError as exc:
                    raise ValueError(f"data_path must be under {data_root}") from exc
            if not data_path.exists():
                raise FileNotFoundError(data_path)
            result = annotate_to_bundle(
                checkpoint_path=state["checkpoint_path"],
                data_path=data_path,
                output_dir=output_dir,
                layer=request.get("layer"),
                batch_size=int(request.get("batch_size", 128)),
                device=state["device"],
            )
            self._send(200, {"status": "ok", **result})
        except Exception as exc:  # return actionable JSON to a CLI caller
            self._send(400, {"status": "error", "error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{threading.current_thread().name}] {fmt % args}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve SnowLotus-CellFM inference")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--data-root", default=None, help="Restrict annotation inputs to this directory")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    checkpoint_path = Path(args.checkpoint).expanduser().resolve()
    checkpoint = load_checkpoint(checkpoint_path, map_location="cpu")
    device = _device(args.device)
    state = {
        "checkpoint_path": checkpoint_path,
        "device": device,
        "data_root": Path(args.data_root).expanduser().resolve() if args.data_root else None,
        "metadata": {
            "status": "ok",
            "service": "SnowLotus-CellFM",
            "checkpoint": str(checkpoint_path),
            "model_config": checkpoint.get("model_config", {}),
            "checkpoint_epoch": checkpoint.get("epoch"),
            "checkpoint_metrics": checkpoint.get("metrics", {}),
            "gene_vocab_size": len(checkpoint.get("gene_vocab", [])),
            "fine_vocab_size": len(checkpoint.get("fine_vocab", [])),
            "coarse_vocab_size": len(checkpoint.get("coarse_vocab", [])),
        },
    }
    server = ThreadingHTTPServer((args.host, args.port), SnowLotusHandler)
    server.state = state  # type: ignore[attr-defined]
    print(json.dumps(state["metadata"], ensure_ascii=False, indent=2), flush=True)
    print(f"Serving on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
