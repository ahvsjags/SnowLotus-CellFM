from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


SCPLANTLLM_WEIGHT_SHA256 = "baa24dc1e686b94aa08e7e7b08df17e1bb53e479416acf7f50cd032b0fabf416"
SCPLANTLLM_WEIGHT_SIZE = 431_801_156


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def weight_status(root: Path, weight_path: Path) -> dict[str, Any]:
    path = root / weight_path
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    status = "missing"
    digest = ""
    if exists and size == SCPLANTLLM_WEIGHT_SIZE:
        digest = sha256_file(path)
        status = "ready" if digest == SCPLANTLLM_WEIGHT_SHA256 else "sha256_mismatch"
    elif exists and size > 0:
        status = "partial_or_in_progress"
    pointer = path.with_suffix(path.suffix + ".pointer")
    pointer_text = pointer.read_text(encoding="utf-8", errors="replace") if pointer.exists() else ""
    return {
        "path": str(weight_path),
        "exists": exists,
        "bytes": size,
        "expected_bytes": SCPLANTLLM_WEIGHT_SIZE,
        "sha256": digest,
        "expected_sha256": SCPLANTLLM_WEIGHT_SHA256,
        "status": status,
        "lfs_pointer_exists": pointer.exists(),
        "lfs_pointer_text": pointer_text.strip(),
    }


def probe_status(root: Path, probe_path: Path) -> dict[str, Any]:
    path = root / probe_path
    payload = read_json(path)
    metrics = payload.get("metrics", {})
    completed = bool(path.exists() and metrics.get("accuracy") is not None and metrics.get("macro_f1") is not None)
    return {
        "path": str(probe_path),
        "exists": path.exists(),
        "status": "completed_metric" if completed else "missing_or_incomplete",
        "accuracy": metrics.get("accuracy"),
        "macro_f1": metrics.get("macro_f1"),
        "method": payload.get("method"),
    }


def scplantannotate_status(root: Path, metrics_path: Path) -> dict[str, Any]:
    path = root / metrics_path
    payload = read_json(path)
    has_metrics = bool(path.exists() and payload.get("accuracy") is not None and payload.get("macro_f1") is not None)
    return {
        "path": str(metrics_path),
        "exists": path.exists(),
        "status": "completed_metric" if has_metrics else "auth_or_export_pending",
        "accuracy": payload.get("accuracy"),
        "macro_f1": payload.get("macro_f1"),
        "username_env_present": bool(os.environ.get("SCPLANTANNOTATE_USERNAME")),
        "password_env_present": bool(os.environ.get("SCPLANTANNOTATE_PASSWORD")),
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    weight = weight_status(root, args.scplantllm_weight)
    probe = probe_status(root, args.scplantllm_probe)
    annotate = scplantannotate_status(root, args.scplantannotate_metrics)
    scplantllm_metric_closed = probe["status"] == "completed_metric"
    scplantannotate_metric_closed = annotate["status"] == "completed_metric"
    if scplantllm_metric_closed and scplantannotate_metric_closed:
        overall = "third_party_metrics_closed"
    elif weight["status"] == "ready" and not scplantllm_metric_closed:
        overall = "scplantllm_weight_ready_probe_pending"
    elif weight["status"] == "partial_or_in_progress":
        overall = "scplantllm_weight_download_in_progress"
    else:
        overall = "official_metric_closure_pending"
    return {
        "schema_version": "plant_cellfm_revision_v11_third_party_closure",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M Asia/Shanghai"),
        "overall_status": overall,
        "official_sources": {
            "scPlantLLM_github": "https://github.com/compbioNJU/scPlantLLM",
            "scPlantLLM_weight_lfs_oid": SCPLANTLLM_WEIGHT_SHA256,
            "scPlantLLM_paper_doi": "10.1093/gpbjnl/qzaf024",
            "scPlantAnnotate_web": "https://scplantannotate.missouri.edu/",
            "scPlantAnnotate_paper_doi": "10.1016/j.jare.2026.01.035",
        },
        "scplantllm": {
            "weight": weight,
            "probe": probe,
            "closure_command": (
                "/root/miniconda3/envs/myconda/bin/python scripts/run_scplantllm_embedding_centroid_probe.py "
                "--chunks-dir outputs/external_benchmarks/scplantllm_public_sprint_input/reference_preprocess/chunks "
                "--scplantllm-dir external/scPlantLLM "
                "--weight-path model_params/scPlantLLM_model.pth "
                "--device cuda --batch-size 8 --max-train 2048 --max-test 2048 "
                "--output outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json"
            ),
        },
        "scplantannotate": annotate,
        "submission_rule": (
            "Only completed metric JSON files with accuracy and macro-F1 are reportable as third-party numerical "
            "comparators. Official source reachability, input readiness or partial weight downloads are evidence "
            "of closure progress, not completed superiority claims."
        ),
    }


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    weight = payload["scplantllm"]["weight"]
    probe = payload["scplantllm"]["probe"]
    annotate = payload["scplantannotate"]
    lines = [
        "# Plant-CellFM v11 Third-Party Metric Closure Audit",
        "",
        f"Generated: {payload['generated']}",
        "",
        f"Overall status: `{payload['overall_status']}`",
        "",
        "## scPlantLLM",
        "",
        f"- Weight status: `{weight['status']}`",
        f"- Weight path: `{weight['path']}`",
        f"- Weight bytes: `{weight['bytes']}` / `{weight['expected_bytes']}`",
        f"- Expected SHA256 / LFS OID: `{weight['expected_sha256']}`",
        f"- Probe status: `{probe['status']}`",
        f"- Probe accuracy: `{probe.get('accuracy')}`",
        f"- Probe macro-F1: `{probe.get('macro_f1')}`",
        "",
        "Closure command:",
        "",
        "```bash",
        payload["scplantllm"]["closure_command"],
        "```",
        "",
        "## scPlantAnnotate",
        "",
        f"- Status: `{annotate['status']}`",
        f"- Metrics path: `{annotate['path']}`",
        f"- Username env present: `{annotate['username_env_present']}`",
        f"- Password env present: `{annotate['password_env_present']}`",
        "",
        "## Submission Rule",
        "",
        payload["submission_rule"],
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write third-party metric closure audit for revision v11")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--scplantllm-weight", type=Path, default=Path("external/scPlantLLM/model_params/scPlantLLM_model.pth"))
    parser.add_argument("--scplantllm-probe", type=Path, default=Path("outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json"))
    parser.add_argument("--scplantannotate-metrics", type=Path, default=Path("outputs/external_benchmarks/scplantannotate_final_metrics.json"))
    parser.add_argument("--output-json", type=Path, default=Path("release_metadata/revision_v11_third_party_closure.json"))
    parser.add_argument("--output-md", type=Path, default=Path("release_metadata/revision_v11_third_party_closure.md"))
    args = parser.parse_args()
    payload = build_payload(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, args.output_md)
    print(args.output_json)
    print(args.output_md)


if __name__ == "__main__":
    main()
