from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import h5py
import numpy as np


REQUIRED_OBS_FIELDS = [
    "cell_type",
    "cell_type_coarse",
    "sample_id",
    "species",
    "tissue",
    "batch",
    "cell_id",
]
UNKNOWN_LABELS = {"", "unknown", "unknow", "unannotated", "nan", "none", "na"}


def json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


def decode_values(values: Any) -> list[str]:
    array = np.asarray(values)
    if array.dtype.kind in {"S", "O"}:
        return [
            item.decode("utf-8", errors="replace") if isinstance(item, bytes) else str(item)
            for item in array.tolist()
        ]
    return [str(item) for item in array.tolist()]


def h5ad_shape(handle: h5py.File) -> tuple[int, int]:
    if "X" not in handle:
        return (0, 0)
    x = handle["X"]
    if isinstance(x, h5py.Dataset):
        return (int(x.shape[0]), int(x.shape[1]))
    if "shape" in x:
        shape = np.asarray(x["shape"]).astype(int).tolist()
        return (int(shape[0]), int(shape[1]))
    shape_attr = x.attrs.get("shape")
    if shape_attr is not None:
        shape = np.asarray(shape_attr).astype(int).tolist()
        return (int(shape[0]), int(shape[1]))
    return (0, 0)


def obs_keys(handle: h5py.File) -> list[str]:
    if "obs" not in handle or not isinstance(handle["obs"], h5py.Group):
        return []
    return sorted(key for key in handle["obs"].keys() if not key.startswith("_"))


def read_obs_column(handle: h5py.File, column: str) -> list[str]:
    obs = handle["obs"]
    if column not in obs:
        return []
    node = obs[column]
    if isinstance(node, h5py.Dataset):
        return decode_values(node[()])
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"]).astype(int)
        categories = decode_values(node["categories"][()])
        values = []
        for code in codes:
            values.append(categories[code] if 0 <= code < len(categories) else "")
        return values
    return []


def value_counts(values: list[str], limit: int = 30) -> dict[str, int]:
    return dict(Counter(values).most_common(limit))


def non_unknown(values: list[str]) -> list[str]:
    return [value for value in values if value.strip().lower() not in UNKNOWN_LABELS]


def inspect_h5ad(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": path.as_posix(),
            "summary": {
                "exists": False,
                "readable": False,
                "contract_ready": False,
                "top_journal_primary_data_ready": False,
            },
            "errors": [f"Missing required file: {path.as_posix()}"],
        }
    try:
        with h5py.File(path, "r") as handle:
            n_cells, n_genes = h5ad_shape(handle)
            keys = obs_keys(handle)
            missing_obs = [field for field in REQUIRED_OBS_FIELDS if field not in keys]
            columns = {
                field: read_obs_column(handle, field)
                for field in REQUIRED_OBS_FIELDS
                if field in keys
            }
    except Exception as exc:
        return {
            "path": path.as_posix(),
            "summary": {
                "exists": True,
                "readable": False,
                "contract_ready": False,
                "top_journal_primary_data_ready": False,
            },
            "errors": [f"{type(exc).__name__}: {exc}"],
        }

    fine_labels = non_unknown(columns.get("cell_type", []))
    coarse_labels = non_unknown(columns.get("cell_type_coarse", []))
    samples = non_unknown(columns.get("sample_id", []))
    tissues = non_unknown(columns.get("tissue", []))
    batches = non_unknown(columns.get("batch", []))
    species_values = non_unknown(columns.get("species", []))
    species_norm = {value.replace("_", " ").strip().lower() for value in species_values}
    species_ok = "saussurea involucrata" in species_norm if species_norm else False

    gates = {
        "file_exists": True,
        "readable": True,
        "has_X_shape": n_cells > 0 and n_genes > 0,
        "required_obs_fields_present": not missing_obs,
        "species_is_saussurea_involucrata": species_ok,
        "min_cells": n_cells >= args.min_cells,
        "min_genes": n_genes >= args.min_genes,
        "min_labelled_cells": len(fine_labels) >= args.min_labelled_cells,
        "min_fine_cell_types": len(set(fine_labels)) >= args.min_fine_cell_types,
        "min_samples": len(set(samples)) >= args.min_samples,
        "min_tissues": len(set(tissues)) >= args.min_tissues,
        "min_batches": len(set(batches)) >= args.min_batches,
    }
    contract_ready = all(gates.values())
    top_journal_gates = {
        **gates,
        "top_journal_cells": n_cells >= args.top_journal_min_cells,
        "top_journal_samples": len(set(samples)) >= args.top_journal_min_samples,
        "top_journal_tissues": len(set(tissues)) >= args.top_journal_min_tissues,
        "top_journal_fine_cell_types": len(set(fine_labels)) >= args.top_journal_min_cell_types,
    }
    top_journal_ready = all(top_journal_gates.values())
    return {
        "path": path.as_posix(),
        "summary": {
            "exists": True,
            "readable": True,
            "contract_ready": contract_ready,
            "top_journal_primary_data_ready": top_journal_ready,
            "n_cells": n_cells,
            "n_genes": n_genes,
            "required_obs_present": len(REQUIRED_OBS_FIELDS) - len(missing_obs),
            "required_obs_total": len(REQUIRED_OBS_FIELDS),
            "labelled_cell_count": len(fine_labels),
            "fine_cell_type_count": len(set(fine_labels)),
            "coarse_cell_type_count": len(set(coarse_labels)),
            "sample_count": len(set(samples)),
            "tissue_count": len(set(tissues)),
            "batch_count": len(set(batches)),
        },
        "gates": gates,
        "top_journal_gates": top_journal_gates,
        "missing_obs_fields": missing_obs,
        "obs_fields": keys,
        "label_counts": {
            "cell_type": value_counts(fine_labels),
            "cell_type_coarse": value_counts(coarse_labels),
            "sample_id": value_counts(samples),
            "tissue": value_counts(tissues),
            "batch": value_counts(batches),
            "species": value_counts(species_values),
        },
        "errors": [],
    }


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Saussurea h5ad Contract Validation",
        "",
        f"- Input: `{payload['path']}`",
        f"- Exists: `{summary.get('exists')}`",
        f"- Readable: `{summary.get('readable')}`",
        f"- Contract ready: `{summary.get('contract_ready')}`",
        f"- Top-journal primary-data ready: `{summary.get('top_journal_primary_data_ready')}`",
        f"- Cells: `{summary.get('n_cells', 0)}`",
        f"- Genes: `{summary.get('n_genes', 0)}`",
        f"- Fine cell types: `{summary.get('fine_cell_type_count', 0)}`",
        f"- Samples: `{summary.get('sample_count', 0)}`",
        f"- Tissues: `{summary.get('tissue_count', 0)}`",
        "",
        "## Gates",
        "",
        "| Gate | Pass |",
        "| --- | --- |",
    ]
    for key, value in payload.get("gates", {}).items():
        lines.append(f"| `{key}` | `{value}` |")
    if payload.get("missing_obs_fields"):
        lines.extend(["", "## Missing obs Fields", ""])
        lines.extend(f"- `{field}`" for field in payload["missing_obs_fields"])
    if payload.get("errors"):
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in payload["errors"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the Snow Lotus primary h5ad data contract.")
    parser.add_argument("--input", default="data/saussurea_involucrata.h5ad", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--min-cells", default=5000, type=int)
    parser.add_argument("--min-genes", default=1000, type=int)
    parser.add_argument("--min-labelled-cells", default=1000, type=int)
    parser.add_argument("--min-fine-cell-types", default=5, type=int)
    parser.add_argument("--min-samples", default=2, type=int)
    parser.add_argument("--min-tissues", default=1, type=int)
    parser.add_argument("--min-batches", default=1, type=int)
    parser.add_argument("--top-journal-min-cells", default=20000, type=int)
    parser.add_argument("--top-journal-min-samples", default=6, type=int)
    parser.add_argument("--top-journal-min-tissues", default=3, type=int)
    parser.add_argument("--top-journal-min-cell-types", default=10, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = inspect_h5ad(args.input, args)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
