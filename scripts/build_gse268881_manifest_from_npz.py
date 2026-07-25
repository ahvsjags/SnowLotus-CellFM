from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path

import numpy as np

from geo_10x_to_npz import parse_sample


def is_readable_npz(path: Path) -> bool:
    try:
        with np.load(path, allow_pickle=False) as payload:
            required = ["X_shape", "genes", "cell_id", "cell_type", "cell_type_coarse"]
            return all(key in payload for key in required)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile):
        return False


def discover_npz(input_dir: str | Path, sample_regex: str | None = None) -> list[Path]:
    paths = sorted(Path(input_dir).glob("*.npz"))
    if sample_regex:
        pattern = re.compile(sample_regex)
        paths = [path for path in paths if pattern.search(path.stem)]
    return [path for path in paths if is_readable_npz(path)]


def write_manifest(paths: list[Path], output: str | Path, dataset_id: str) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "path",
                "dataset_id",
                "species",
                "tissue",
                "layer",
                "label_key",
                "coarse_label_key",
                "sample_key",
            ]
        )
        for path in paths:
            meta = parse_sample(path.stem)
            writer.writerow(
                [
                    str(path),
                    dataset_id,
                    meta["species"],
                    meta["tissue"],
                    "",
                    "cell_type",
                    "cell_type_coarse",
                    "sample_id",
                ]
            )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GSE268881 manifest from readable NPZ files")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--sample-regex")
    parser.add_argument("--min-samples", type=int, default=1)
    args = parser.parse_args()

    paths = discover_npz(args.input_dir, args.sample_regex)
    if len(paths) < args.min_samples:
        raise ValueError(f"found {len(paths)} readable NPZ files, need at least {args.min_samples}")
    output = write_manifest(paths, args.output, args.dataset_id)
    print(output)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
