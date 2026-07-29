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
                    "known_adapter_count": len(state["registry"].adapters),
                    "adapter_resolution": "dynamic_all_plants",
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
            mode = str(request.get("mode", "annotation")).lower()
            if mode not in {"embedding", "annotation"}:
                raise ValueError("mode must be embedding or annotation")
            role = "backbone" if mode == "embedding" else "annotation"
            selected_checkpoint = state["checkpoints"].get(role)
            if selected_checkpoint is None:
                raise ValueError(f"{role} checkpoint is not configured")
            result = annotate_to_bundle(
                checkpoint_path=selected_checkpoint["path"],
                data_path=data_path,
                output_dir=output_dir,
                layer=request.get("layer"),
                ortholog_map=ortholog_path,
                batch_size=int(request.get("batch_size", 128)),
                device=state["device"],
            )
            selection = {
                "requested_species": request.get("species", ""),
                "mode": mode,
                "checkpoint_role": role,
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
    parser.add_argument("--checkpoint", default=None, help="Legacy single-checkpoint alias")
    parser.add_argument("--backbone-checkpoint", default=None, help="General plant MLM backbone checkpoint")
    parser.add_argument("--annotation-checkpoint", default=None, help="Optional supervised annotation checkpoint")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--data-root", default=None, help="Restrict annotation inputs to this directory")
    parser.add_argument("--project-root", default=".", help="Root for ortholog maps and release metadata")
    parser.add_argument(
        "--adapter-registry",
        default="release_metadata/plant_species_adapters.json",
        help="JSON registry containing known plant adapters; unknown species receive runtime adapters",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    backbone_value = args.backbone_checkpoint or args.checkpoint
    if not backbone_value:
        raise SystemExit("one of --backbone-checkpoint or --checkpoint is required")
    backbone_path = Path(backbone_value).expanduser().resolve()
    annotation_path = (
        Path(args.annotation_checkpoint).expanduser().resolve()
        if args.annotation_checkpoint
        else None
    )
    backbone_checkpoint = load_checkpoint(backbone_path, map_location="cpu")
    annotation_checkpoint = (
        load_checkpoint(annotation_path, map_location="cpu") if annotation_path else None
    )
    annotation_model_config = annotation_checkpoint.get("model_config", {}) if annotation_checkpoint else {}
    annotation_fine_vocab = annotation_checkpoint.get("fine_vocab", []) if annotation_checkpoint else []
    annotation_coarse_vocab = annotation_checkpoint.get("coarse_vocab", []) if annotation_checkpoint else []
    device = _device(args.device)
    registry = load_registry(args.adapter_registry)
    state = {
        "checkpoints": {
            "backbone": {"path": backbone_path, "payload": backbone_checkpoint},
            "annotation": (
                {"path": annotation_path, "payload": annotation_checkpoint}
                if annotation_path and annotation_checkpoint is not None
                else None
            ),
        },
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
            "known_adapter_count": len(registry.adapters),
            "adapter_resolution": "dynamic_all_plants",
            "runtime_adapter_policy": "materialize_a_species_adapter_for_any_named_plant",
            "snow_lotus_role": "one species adapter among all plant species",
            "primary_checkpoint_role": "backbone",
            "backbone_checkpoint": str(backbone_path),
            "annotation_checkpoint": str(annotation_path) if annotation_path else None,
            "model_config": backbone_checkpoint.get("model_config", {}),
            "backbone_model_config": backbone_checkpoint.get("model_config", {}),
            "annotation_model_config": annotation_model_config,
            "checkpoint_epoch": backbone_checkpoint.get("epoch"),
            "checkpoint_metrics": backbone_checkpoint.get("metrics", {}),
            "annotation_checkpoint_epoch": annotation_checkpoint.get("epoch") if annotation_checkpoint else None,
            "annotation_checkpoint_metrics": annotation_checkpoint.get("metrics", {}) if annotation_checkpoint else {},
            "gene_vocab_size": len(backbone_checkpoint.get("gene_vocab", [])),
            "fine_vocab_size": len(backbone_checkpoint.get("fine_vocab", [])),
            "coarse_vocab_size": len(backbone_checkpoint.get("coarse_vocab", [])),
            "annotation_fine_vocab_size": len(annotation_fine_vocab),
            "annotation_coarse_vocab_size": len(annotation_coarse_vocab),
            "annotation_head_available": annotation_checkpoint is not None,
        },
        "capabilities": {
            "status": "ok",
            "model_scope": "plant_general",
            "tasks": [
                "cross_species_embedding",
                "masked_expression_features",
                "hierarchical_cell_annotation" if annotation_checkpoint is not None else "embedding_only_until_head_attached",
                "marker_candidate_discovery",
                "species_adapter_resolution",
                "runtime_dynamic_adapter_for_any_plant_species",
            ],
            "input_formats": [".h5ad", ".npz"],
            "gene_transfer_policy": "exact gene identifiers first, then request-level or configured ortholog map with mapping statistics",
            "routes": ["GET /health", "GET /metadata", "GET /capabilities", "GET /adapters", "POST /annotate"],
            "modes": {
                "embedding": "uses the general plant backbone checkpoint",
                "annotation": "uses the supervised annotation checkpoint when configured",
            },
            "adapter_count": len(registry.adapters),
            "known_adapter_count": len(registry.adapters),
            "adapter_resolution": "dynamic_all_plants",
        },
    }
    server = ThreadingHTTPServer((args.host, args.port), PlantCellFMHandler)
    server.state = state  # type: ignore[attr-defined]
    print(json.dumps(state["metadata"], ensure_ascii=False, indent=2), flush=True)
    print(f"Serving on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
