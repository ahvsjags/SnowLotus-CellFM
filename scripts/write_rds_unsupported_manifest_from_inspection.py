#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST_HEADER = [
    "path",
    "dataset_id",
    "species",
    "tissue",
    "layer",
    "label_key",
    "coarse_label_key",
    "sample_key",
]

MATRIX_RE = re.compile(
    r"^(?P<key>.+)\.matrix=(?P<class>.*):(?P<rows>\d+)x(?P<cols>\d+):nnz=(?P<nnz>[^:]+)$"
)


def read_key_values(path: Path) -> dict[str, str]:
    payload: dict[str, str] = {}
    if not path.exists():
        return payload
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        payload[key.strip()] = value.strip()
    return payload


def parse_matrix_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = MATRIX_RE.match(line.strip())
        if not match:
            continue
        key = match.group("key")
        assay_match = re.search(r"\.assay\.([^.]+)\.", key)
        slot_match = re.search(r"\.slot\.([^.]+)", key)
        candidate = {
            "key": key,
            "class": match.group("class"),
            "rows": int(match.group("rows")),
            "cols": int(match.group("cols")),
            "nnz": match.group("nnz"),
            "assay": assay_match.group(1) if assay_match else "",
            "slot_or_layer": slot_match.group(1) if slot_match else "",
        }
        candidates.append(candidate)
    return candidates


def expression_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expression_assays = {"RNA", "SCT"}
    expression_slots = {"counts", "data"}
    usable: list[dict[str, Any]] = []
    for item in candidates:
        if item["rows"] <= 0 or item["cols"] <= 0:
            continue
        assay = str(item.get("assay", "")).replace(".", "_").upper()
        slot = str(item.get("slot_or_layer", "")).replace(".", "_").lower()
        if assay in expression_assays and slot in expression_slots:
            usable.append(item)
    return usable


def write_header_only_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(MANIFEST_HEADER)


def read_tail(path: Path | None, limit: int = 4000) -> str | None:
    if path is None or not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-limit:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspection-log", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--unsupported-report", required=True, type=Path)
    parser.add_argument("--accession", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--species", required=True)
    parser.add_argument("--tissue", required=True)
    parser.add_argument("--rds-path", required=True)
    parser.add_argument("--conversion-error-log", type=Path)
    args = parser.parse_args()

    inspection_text = args.inspection_log.read_text(encoding="utf-8", errors="replace")
    key_values = read_key_values(args.inspection_log)
    matrix_candidates = parse_matrix_candidates(inspection_text)
    usable_expression = expression_candidates(matrix_candidates)
    assay_names = [
        item
        for item in key_values.get("object.slot.assays.names", "").split("|")
        if item
    ]

    if usable_expression:
        payload = {
            "accession": args.accession,
            "dataset_id": args.dataset_id,
            "status": "expression_matrix_detected",
            "reason": (
                "Slot-level inspection found a non-empty RNA/SCT counts/data matrix; "
                "do not mark this RDS as unsupported."
            ),
            "expression_candidates": usable_expression,
            "inspection_log": args.inspection_log.as_posix(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        args.unsupported_report.parent.mkdir(parents=True, exist_ok=True)
        args.unsupported_report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("expression_matrix_detected")
        print(args.unsupported_report)
        return 2

    write_header_only_manifest(args.manifest_output)
    payload: dict[str, Any] = {
        "accession": args.accession,
        "dataset_id": args.dataset_id,
        "species": args.species,
        "tissue": args.tissue,
        "status": "unsupported_for_single_cell_matrix_corpus",
        "reason": (
            "The available Seurat RDS could be read, but slot-level inspection without Signac "
            "did not identify a non-empty RNA/SCT counts/data matrix suitable for the "
            "expression-only SnowLotus-CellFM corpus."
        ),
        "rds_path": args.rds_path,
        "inspection_log": args.inspection_log.as_posix(),
        "assays": assay_names,
        "matrix_candidate_count": len(matrix_candidates),
        "matrix_candidates": matrix_candidates[:50],
        "expression_candidate_count": 0,
        "corpus_manifest": args.manifest_output.as_posix(),
        "corpus_manifest_rows": 0,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    conversion_tail = read_tail(args.conversion_error_log)
    if conversion_tail:
        payload["conversion_error_tail"] = conversion_tail
    args.unsupported_report.parent.mkdir(parents=True, exist_ok=True)
    args.unsupported_report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(args.unsupported_report)
    print(args.manifest_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
