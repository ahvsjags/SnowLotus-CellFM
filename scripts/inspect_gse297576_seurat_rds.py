from __future__ import annotations

"""Inspect the author-released GSE297576 Seurat RDS before external scoring.

The inspection intentionally reports only object structure and author metadata.
It does not construct a matrix, fit a model or calculate an external metric.
"""

import argparse
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import rdata


ROOT = Path(__file__).resolve().parents[1]


def type_name(value: Any) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}"


def describe(value: Any, *, depth: int = 0) -> dict[str, Any]:
    summary: dict[str, Any] = {"type": type_name(value)}
    if isinstance(value, pd.DataFrame):
        summary.update(
            {
                "shape": [int(value.shape[0]), int(value.shape[1])],
                "columns": [str(column) for column in value.columns],
                "index_name": str(value.index.name) if value.index.name is not None else None,
            }
        )
        return summary
    if isinstance(value, Mapping):
        keys = [str(key) for key in value.keys()]
        summary["keys"] = keys
        if depth < 3:
            summary["children"] = {str(key): describe(item, depth=depth + 1) for key, item in value.items()}
        return summary
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        summary["length"] = len(value)
        if depth < 1:
            summary["first_item"] = describe(value[0], depth=depth + 1) if value else None
        return summary
    attributes = getattr(value, "__dict__", None)
    if isinstance(attributes, Mapping):
        summary["attributes"] = [str(key) for key in attributes]
        if depth < 3:
            summary["children"] = {str(key): describe(item, depth=depth + 1) for key, item in attributes.items()}
    return summary


def find_metadata(value: Any) -> pd.DataFrame | None:
    if isinstance(value, pd.DataFrame):
        expected = {"celltype", "cell_type", "seurat_clusters", "orig.ident", "CellNames"}
        if expected.intersection(map(str, value.columns)):
            return value
        return None
    if isinstance(value, Mapping):
        for key in ("meta.data", "meta_data", "metadata"):
            candidate = value.get(key)
            if isinstance(candidate, pd.DataFrame):
                return candidate
        for candidate in value.values():
            found = find_metadata(candidate)
            if found is not None:
                return found
    attributes = getattr(value, "__dict__", None)
    if isinstance(attributes, Mapping):
        for key in ("meta.data", "meta_data", "metadata"):
            candidate = attributes.get(key)
            if isinstance(candidate, pd.DataFrame):
                return candidate
        for candidate in attributes.values():
            found = find_metadata(candidate)
            if found is not None:
                return found
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    value = rdata.read_rds(input_path)
    metadata = find_metadata(value)
    payload: dict[str, Any] = {
        "schema_version": "plant_cellfm_gse297576_seurat_structure_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path),
        "object": describe(value),
        "metadata": None,
        "claim_boundary": "This is object-structure and author-metadata inspection only. It is not a converted count matrix, a frozen external evaluation or a performance result.",
    }
    if metadata is not None:
        payload["metadata"] = {
            "cells": int(metadata.shape[0]),
            "columns": [str(column) for column in metadata.columns],
            "celltype_candidates": [
                str(column)
                for column in metadata.columns
                if any(token in str(column).lower() for token in ("celltype", "cell_type", "annotation", "label", "cluster"))
            ],
            "value_counts": {
                str(column): {str(key): int(count) for key, count in metadata[column].value_counts(dropna=False).head(40).items()}
                for column in metadata.columns
                if any(token in str(column).lower() for token in ("celltype", "cell_type", "annotation", "label", "cluster"))
            },
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"metadata_detected": metadata is not None, "metadata_cells": int(metadata.shape[0]) if metadata is not None else None}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
