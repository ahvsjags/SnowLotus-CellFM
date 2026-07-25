#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a SnowCell corpus manifest for NPZ files")
    parser.add_argument("--npz-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--species", required=True)
    parser.add_argument("--tissue", required=True)
    parser.add_argument("--label-key", default="cell_type")
    parser.add_argument("--coarse-label-key", default="cell_type_coarse")
    parser.add_argument("--sample-key", default="sample_id")
    args = parser.parse_args()

    paths = sorted(args.npz_dir.glob("*.npz"))
    if not paths:
        raise SystemExit(f"No .npz files found under {args.npz_dir}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
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
            writer.writerow(
                [
                    path.as_posix(),
                    args.dataset_id,
                    args.species,
                    args.tissue,
                    "",
                    args.label_key,
                    args.coarse_label_key,
                    args.sample_key,
                ]
            )
    print(args.output)


if __name__ == "__main__":
    main()
