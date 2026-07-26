#!/usr/bin/env python3
"""Add sample-level provenance fields to a sparse SnowCell NPZ corpus."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


def read_sample_metadata(path: str | Path) -> dict[str, dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows or "sample_id" not in rows[0]:
        raise ValueError("metadata TSV must contain at least one row and a sample_id column")
    return {str(row["sample_id"]): {str(k): str(v) for k, v in row.items()} for row in rows}


def enrich_npz(input_path: str | Path, metadata_path: str | Path, output_path: str | Path) -> Path:
    metadata = read_sample_metadata(metadata_path)
    source_path = Path(input_path)
    output = Path(output_path)
    with np.load(source_path, allow_pickle=False) as source:
        payload = {key: source[key] for key in source.files}
    if "sample_id" not in payload:
        raise ValueError("NPZ corpus must contain sample_id metadata")

    sample_ids = np.asarray(payload["sample_id"], dtype=str)
    unknown = sorted(set(sample_ids) - set(metadata))
    if unknown:
        raise ValueError(f"metadata missing sample IDs: {unknown[:5]}")
    fields = sorted({field for row in metadata.values() for field in row if field != "sample_id"})
    for field in fields:
        payload[field] = np.asarray([metadata[sample_id].get(field, "") for sample_id in sample_ids], dtype=str)

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **payload)
    temporary.replace(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich a sparse SnowCell NPZ with sample provenance")
    parser.add_argument("--input", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(enrich_npz(args.input, args.metadata, args.output))


if __name__ == "__main__":
    main()
