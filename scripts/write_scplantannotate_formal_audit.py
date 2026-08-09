"""Write a fail-closed formal scPlantAnnotate comparison audit packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad"
DEFAULT_TRUTH = ROOT / "outputs/external_benchmarks/scplantannotate_public_sprint_input/truth_labels.csv"
DEFAULT_ACCESS = ROOT / "release_metadata/scplantannotate_access_audit.json"
DEFAULT_METRICS = ROOT / "outputs/external_benchmarks/scplantannotate_final_metrics.json"
DEFAULT_OUTPUT = ROOT / "release_metadata/scplantannotate_formal_benchmark_v1.json"
DEFAULT_MARKDOWN = ROOT / "release_metadata/scplantannotate_formal_benchmark_v1.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-h5ad", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--truth-csv", type=Path, default=DEFAULT_TRUTH)
    parser.add_argument("--access-audit", type=Path, default=DEFAULT_ACCESS)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--username-env", default="SCPLANTANNOTATE_USERNAME")
    parser.add_argument("--password-env", default="SCPLANTANNOTATE_PASSWORD")
    args = parser.parse_args()
    for name in ("input_h5ad", "truth_csv", "access_audit", "metrics", "output", "markdown"):
        path = getattr(args, name)
        if not path.is_absolute():
            setattr(args, name, ROOT / path)
    truth = pd.read_csv(args.truth_csv) if args.truth_csv.exists() else pd.DataFrame()
    credentials = bool(os.environ.get(args.username_env, "") and os.environ.get(args.password_env, ""))
    metrics_payload: dict[str, Any] | None = None
    if args.metrics.exists():
        try:
            candidate = json.loads(args.metrics.read_text(encoding="utf-8"))
            if candidate.get("status") == "metrics_ready" and candidate.get("accuracy") is not None:
                metrics_payload = candidate
        except json.JSONDecodeError:
            metrics_payload = None
    access = json.loads(args.access_audit.read_text(encoding="utf-8")) if args.access_audit.exists() else {}
    if metrics_payload is not None:
        status = "completed_formal_numeric_comparison"
        counts_as_completed = True
    elif credentials:
        status = "authorized_execution_ready"
        counts_as_completed = False
    else:
        status = "auth_required_not_counted"
        counts_as_completed = False
    payload: dict[str, Any] = {
        "schema_version": "scplantannotate_formal_benchmark_v1",
        "status": status,
        "counts_as_completed_metric": counts_as_completed,
        "method": "scPlantAnnotate official web/API execution on a frozen 5,000-cell Arabidopsis input",
        "official_publication": {
            "doi": "10.1016/j.jare.2026.01.035",
            "url": "https://pubmed.ncbi.nlm.nih.gov/41554477/",
        },
        "input": {
            "h5ad": str(args.input_h5ad),
            "h5ad_exists": args.input_h5ad.exists(),
            "h5ad_sha256": sha256(args.input_h5ad) if args.input_h5ad.exists() else None,
            "truth_csv": str(args.truth_csv),
            "truth_exists": args.truth_csv.exists(),
            "truth_sha256": sha256(args.truth_csv) if args.truth_csv.exists() else None,
            "test_cells": int(len(truth)),
            "classes": int(truth["cell_type"].nunique()) if "cell_type" in truth else 0,
        },
        "access_audit": {
            "web_server_reachable": access.get("summary", {}).get("web_server_reachable"),
            "anonymous_api_accessible": access.get("summary", {}).get("anonymous_api_accessible"),
            "auth_required_endpoint_count": access.get("summary", {}).get("auth_required_endpoint_count"),
        },
        "credentials": {
            "username_env": args.username_env,
            "password_env": args.password_env,
            "present": credentials,
        },
        "metric_acceptance": {
            "required_fields": ["status=metrics_ready", "test_cells", "accuracy", "macro_f1", "prediction_csv", "truth_csv"],
            "same_input_truth_required": True,
            "dry_run_or_published_context_not_counted": True,
        },
        "execution_command": (
            f"{args.username_env}=<user> {args.password_env}=<password> python scripts/run_scplantannotate_authenticated_benchmark.py "
            f"--input-h5ad {args.input_h5ad} --dataset-name snowcell_public_sprint_scplantannotate_probe "
            "--organism-id 1 --predictor-id 1 --execute --wait "
            "--output outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json"
        ),
        "metrics": metrics_payload,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# scPlantAnnotate formal benchmark audit v1",
        "",
        f"Status: **{status}**",
        f"Counts as completed metric: **{counts_as_completed}**",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| Frozen cells | {len(truth):,} |",
        f"| Frozen classes | {int(truth['cell_type'].nunique()) if 'cell_type' in truth else 0} |",
        f"| Input SHA256 | `{payload['input']['h5ad_sha256']}` |",
        f"| Truth SHA256 | `{payload['input']['truth_sha256']}` |",
        f"| Official numerical output | {'available' if metrics_payload else 'not available'} |",
        "",
        "This packet is a formal comparison contract, not a substitute for the official numerical output. The result is counted only after the authenticated job or an official exported prediction file is scored against the frozen truth CSV.",
        "",
        "## Reproduction",
        "",
        "```text",
        payload["execution_command"],
        "```",
    ]
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
