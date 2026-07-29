#!/usr/bin/env python3
"""Compare two all-plant benchmark artifacts and write a promotion-oriented audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROTOCOLS = (
    "leave_dataset_out",
    "leave_sample_out",
    "leave_species_out",
)
METRICS = ("accuracy", "macro_f1", "coverage")


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"benchmark must be an object: {path}")
    return payload


def record_key(protocol: str, label: str) -> str:
    return f"{protocol}_{label}"


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for protocol in PROTOCOLS:
        result[protocol] = {}
        for label in ("fine", "coarse"):
            metrics = payload.get(record_key(protocol, label), {})
            result[protocol][label] = {
                metric: metrics.get(metric) for metric in METRICS if metric in metrics
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args()

    baseline = load(args.baseline)
    candidate = load(args.candidate)
    comparison: dict[str, Any] = {
        "schema_version": "plant-general-checkpoint-comparison-v1",
        "baseline": {
            "path": str(args.baseline),
            "checkpoint": baseline.get("checkpoint"),
            "checkpoint_sha256": baseline.get("checkpoint_sha256"),
            "summary": summarize(baseline),
        },
        "candidate": {
            "path": str(args.candidate),
            "checkpoint": candidate.get("checkpoint"),
            "checkpoint_sha256": candidate.get("checkpoint_sha256"),
            "summary": summarize(candidate),
        },
        "delta": {},
        "gates": {
            "candidate_embedding_finite": candidate.get("embedding", {}).get("nan_count", 1) == 0
            and candidate.get("embedding", {}).get("infinite_count", 1) == 0,
            "annotation_head_promotion": "manual_review_required",
        },
    }

    for protocol in PROTOCOLS:
        comparison["delta"][protocol] = {}
        for label in ("fine", "coarse"):
            base_metrics = baseline.get(record_key(protocol, label), {})
            cand_metrics = candidate.get(record_key(protocol, label), {})
            comparison["delta"][protocol][label] = {
                metric: (
                    float(cand_metrics[metric]) - float(base_metrics[metric])
                    if metric in cand_metrics and metric in base_metrics
                    else None
                )
                for metric in METRICS
            }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# All-Plant Checkpoint Comparison",
        "",
        "This audit compares the same cross-species protocols. It does not promote a checkpoint to the annotation service by itself.",
        "",
        "| Protocol | Label level | Baseline accuracy | Candidate accuracy | Delta |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for protocol in PROTOCOLS:
        for label in ("fine", "coarse"):
            base = baseline.get(record_key(protocol, label), {}).get("accuracy")
            cand = candidate.get(record_key(protocol, label), {}).get("accuracy")
            delta = comparison["delta"][protocol][label]["accuracy"]
            fmt = lambda value: "NA" if value is None else f"{float(value):.4f}"
            lines.append(f"| {protocol} | {label} | {fmt(base)} | {fmt(cand)} | {fmt(delta)} |")
    lines.extend(
        [
            "",
            f"- Baseline checkpoint: `{baseline.get('checkpoint')}`",
            f"- Candidate checkpoint: `{candidate.get('checkpoint')}`",
            "- Candidate embedding finite-value gate: **PASS**" if comparison["gates"]["candidate_embedding_finite"] else "- Candidate embedding finite-value gate: **FAIL**",
            "- Annotation-head promotion: **manual review required**",
        ]
    )
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
