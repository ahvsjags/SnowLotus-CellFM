#!/usr/bin/env python3
"""Small HTTP service for reproducible Plant-CellFM inference.

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
from snowcell.adapters import load_registry
from snowcell.train import annotate_to_bundle


def _device(value: str) -> torch.device:
    if value == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(value)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


class PlantCellFMHandler(BaseHTTPRequestHandler):
    server_version = "PlantCellFM/0.1"

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
                    "service": "Plant-CellFM",
                    "model_scope": "plant_general",
                    "adapter_count": len(state["registry"].adapters),
                    "device": str(state["device"]),
                },
            )
            return
        if route == "/metadata":
            self._send(200, state["metadata"])
            return
        if route == "/capabilities":
            self._send(200, state["capabilities"])
            return
        if route == "/adapters":
            self._send(200, state["registry"].to_dict())
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
            adapter, used_fallback = state["registry"].resolve(request.get("species"))
            ortholog_map = request.get("ortholog_map")
            ortholog_path = None
            if ortholog_map:
                ortholog_path = Path(str(ortholog_map)).expanduser()
                if not ortholog_path.is_absolute():
                    ortholog_path = state["project_root"] / ortholog_path
                ortholog_path = ortholog_path.resolve()
                try:
                    ortholog_path.relative_to(state["project_root"])
                except ValueError as exc:
                    raise ValueError("ortholog_map must be under the project root") from exc
                if not ortholog_path.exists():
                    raise FileNotFoundError(ortholog_path)
            result = annotate_to_bundle(
                checkpoint_path=state["checkpoint_path"],
                data_path=data_path,
                output_dir=output_dir,
                layer=request.get("layer"),
                ortholog_map=ortholog_path,
                batch_size=int(request.get("batch_size", 128)),
                device=state["device"],
            )
            selection = {
                "requested_species": request.get("species", ""),
                "used_fallback": used_fallback,
                "ortholog_map": str(ortholog_path) if ortholog_path else None,
                "adapter": adapter.to_dict(),
            }
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "adapter_selection.json").write_text(
                json.dumps(selection, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._send(200, {"status": "ok", "adapter": selection, **result})
        except Exception as exc:  # return actionable JSON to a CLI caller
            self._send(400, {"status": "error", "error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{threading.current_thread().name}] {fmt % args}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve Plant-CellFM general-plant inference")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--data-root", default=None, help="Restrict annotation inputs to this directory")
    parser.add_argument("--project-root", default=".", help="Root for ortholog maps and release metadata")
    parser.add_argument(
        "--adapter-registry",
        default="release_metadata/plant_species_adapters.json",
        help="JSON registry containing one adapter entry per registered plant species",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    checkpoint_path = Path(args.checkpoint).expanduser().resolve()
    checkpoint = load_checkpoint(checkpoint_path, map_location="cpu")
    device = _device(args.device)
    registry = load_registry(args.adapter_registry)
    state = {
        "checkpoint_path": checkpoint_path,
        "device": device,
        "data_root": Path(args.data_root).expanduser().resolve() if args.data_root else None,
        "project_root": Path(args.project_root).expanduser().resolve(),
        "registry": registry,
        "metadata": {
            "status": "ok",
            "service": "Plant-CellFM",
            "model_scope": "plant_general",
            "model_name": "Plant-CellFM",
            "adapter_registry": str(Path(args.adapter_registry).expanduser().resolve()),
            "adapter_count": len(registry.adapters),
            "snow_lotus_role": "one species adapter among the registered plant adapters",
            "checkpoint": str(checkpoint_path),
            "model_config": checkpoint.get("model_config", {}),
            "checkpoint_epoch": checkpoint.get("epoch"),
            "checkpoint_metrics": checkpoint.get("metrics", {}),
            "gene_vocab_size": len(checkpoint.get("gene_vocab", [])),
            "fine_vocab_size": len(checkpoint.get("fine_vocab", [])),
            "coarse_vocab_size": len(checkpoint.get("coarse_vocab", [])),
        },
        "capabilities": {
            "status": "ok",
            "model_scope": "plant_general",
            "tasks": [
                "cross_species_embedding",
                "masked_expression_features",
                "hierarchical_cell_annotation",
                "marker_candidate_discovery",
                "species_adapter_resolution",
            ],
            "input_formats": [".h5ad", ".npz"],
            "gene_transfer_policy": "exact gene identifiers first, then request-level or configured ortholog map with mapping statistics",
            "routes": ["GET /health", "GET /metadata", "GET /capabilities", "GET /adapters", "POST /annotate"],
            "adapter_count": len(registry.adapters),
        },
    }
    server = ThreadingHTTPServer((args.host, args.port), PlantCellFMHandler)
    server.state = state  # type: ignore[attr-defined]
    print(json.dumps(state["metadata"], ensure_ascii=False, indent=2), flush=True)
    print(f"Serving on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
