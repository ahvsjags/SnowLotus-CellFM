#!/usr/bin/env python3
"""Merge validated plant corpus manifests with deterministic duplicate auditing."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {
    "path",
    "dataset_id",
    "species",
    "tissue",
    "layer",
    "label_key",
    "coarse_label_key",
    "sample_key",
}


def read_manifest(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - set(fieldnames)
        if missing:
            raise ValueError(f"{path} is missing manifest columns: {sorted(missing)}")
        return fieldnames, [dict(row) for row in reader]


def resolve_path(raw_path: str, project_root: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    return candidate if candidate.is_absolute() else project_root / candidate


def row_key(row: dict[str, str]) -> tuple[str, str]:
    # GEO conversions can be staged once under /mnt and once under data/; the
    # dataset plus sample basename identifies that duplicate deterministically.
    return row.get("dataset_id", ""), Path(row.get("path", "")).name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary-output", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--require-files", action="store_true")
    parser.add_argument("--fail-on-missing", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    headers: list[str] | None = None
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    duplicates: list[dict[str, Any]] = []
    missing_files: list[str] = []

    for source in args.manifest:
        source_path = Path(source).expanduser().resolve()
        source_headers, source_rows = read_manifest(source_path)
        if headers is None:
            headers = source_headers
        elif source_headers != headers:
            raise ValueError(f"manifest header mismatch: {source_path}")
        for row in source_rows:
            key = row_key(row)
            if key in seen:
                duplicates.append({"key": list(key), "source": str(source_path)})
                continue
            seen.add(key)
            rows.append(row)
            if args.require_files and not resolve_path(row["path"], project_root).exists():
                missing_files.append(row["path"])

    if headers is None:
        raise ValueError("no manifest rows were supplied")
    if args.fail_on_missing and missing_files:
        raise FileNotFoundError(f"missing manifest files: {missing_files[:10]}")

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "manifest_sources": [str(Path(item).expanduser()) for item in args.manifest],
        "manifest_rows": len(rows),
        "dataset_count": len({row["dataset_id"] for row in rows}),
        "species_count": len({row["species"] for row in rows}),
        "duplicate_count": len(duplicates),
        "missing_file_count": len(missing_files),
        "duplicates": duplicates,
        "missing_files": missing_files,
    }
    summary_path = Path(args.summary_output).expanduser()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
