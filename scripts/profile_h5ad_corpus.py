from __future__ import annotations

"""Export auditable composition tables from an AnnData H5AD without scanpy.

The training servers deliberately keep a small runtime environment.  This
reader uses only h5py and AnnData's documented categorical encoding, allowing
the exact corpus used by a checkpoint to be profiled without loading its
expression matrix into memory.
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import h5py
import numpy as np


DEFAULT_COLUMNS = ("species", "tissue", "dataset_id", "sample_id", "cell_type", "cell_type_coarse")


def as_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def read_categorical(group: h5py.Group, name: str) -> np.ndarray:
    item = group[name]
    if isinstance(item, h5py.Group) and "categories" in item and "codes" in item:
        categories = np.asarray([as_text(value) for value in item["categories"][()]])
        codes = np.asarray(item["codes"][()], dtype=np.int64)
        output = np.full(codes.shape, "<missing>", dtype=object)
        valid = (codes >= 0) & (codes < len(categories))
        output[valid] = categories[codes[valid]]
        return output.astype(str)
    values = item[()]
    return np.asarray([as_text(value) for value in values], dtype=str)


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile H5AD corpus composition using h5py")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with h5py.File(args.input, "r") as handle:
        obs = handle["obs"]
        columns = [column for column in DEFAULT_COLUMNS if column in obs]
        values = {column: read_categorical(obs, column) for column in columns}
        matrix = handle["X"]
        if isinstance(matrix, h5py.Dataset):
            shape = tuple(int(value) for value in matrix.shape)
        else:
            shape = tuple(int(value) for value in matrix.attrs["shape"])
    n_cells = shape[0]
    if any(len(value) != n_cells for value in values.values()):
        raise ValueError("obs column length does not match matrix cell count")

    summary: dict[str, Any] = {
        "schema_version": "plant_cellfm_h5ad_corpus_profile_v1",
        "input": str(args.input),
        "shape": {"cells": shape[0], "genes": shape[1]},
        "available_obs_columns": columns,
        "unique_values": {column: int(len(set(value.tolist()))) for column, value in values.items()},
    }
    composition_rows: list[dict[str, Any]] = []
    for column, column_values in values.items():
        counter = Counter(column_values.tolist())
        for value, cells in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
            composition_rows.append({"dimension": column, "value": value, "cells": int(cells), "fraction": cells / n_cells})
    write_tsv(args.output_dir / "corpus_composition.tsv", composition_rows, ["dimension", "value", "cells", "fraction"])

    for left, right, filename in (
        ("species", "tissue", "species_by_tissue.tsv"),
        ("species", "dataset_id", "species_by_dataset.tsv"),
        ("species", "cell_type", "species_by_cell_type.tsv"),
    ):
        if left not in values or right not in values:
            continue
        counter = Counter(zip(values[left].tolist(), values[right].tolist(), strict=True))
        rows = [
            {left: first, right: second, "cells": int(cells), "fraction_of_corpus": cells / n_cells}
            for (first, second), cells in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        ]
        write_tsv(args.output_dir / filename, rows, [left, right, "cells", "fraction_of_corpus"])
    (args.output_dir / "corpus_profile.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
