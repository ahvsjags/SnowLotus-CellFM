"""Create a frozen, label-hidden scPlantAnnotate comparison input package."""

from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "outputs/external_validation/gse270140/GSM8335426_JWE03_author_annotated_secondary_root.h5ad")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/external_benchmarks/scplantannotate_public_sprint_input")
    parser.add_argument("--n-cells", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260810)
    args = parser.parse_args()
    source = args.source if args.source.is_absolute() else ROOT / args.source
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    data = ad.read_h5ad(source)
    label_column = "expert_annotation_raw"
    if label_column not in data.obs:
        raise ValueError(f"missing truth column: {label_column}")
    labels = data.obs[label_column].astype(str)
    chosen = labels.value_counts().head(12).index.tolist()
    rng = np.random.default_rng(args.seed)
    counts = labels.value_counts()
    total_available = int(counts.loc[chosen].sum())
    if total_available < args.n_cells:
        raise ValueError(f"selected classes contain only {total_available} cells")
    quotas = {label: max(1, int(args.n_cells * int(counts[label]) / total_available)) for label in chosen}
    while sum(quotas.values()) < args.n_cells:
        label = max(chosen, key=lambda item: int(counts[item]) - quotas[item])
        if quotas[label] >= int(counts[label]):
            break
        quotas[label] += 1
    indices: list[int] = []
    for label in chosen:
        candidates = np.flatnonzero(labels.to_numpy() == label)
        indices.extend(sorted(rng.choice(candidates, size=quotas[label], replace=False).tolist()))
    indices = sorted(indices)
    subset = data[indices].copy()
    truth = pd.DataFrame({"cell_id": subset.obs["cell_id"].astype(str), "cell_type": labels.iloc[indices].to_numpy()})
    # Remove the author label from the model input; keep only operational metadata.
    subset.obs = subset.obs.drop(columns=[label_column], errors="ignore")
    subset.obs["cell_id"] = subset.obs["cell_id"].astype(str)
    output_dir.mkdir(parents=True, exist_ok=True)
    subset.write_h5ad(output_dir / "scplantannotate_input.h5ad", compression="gzip")
    truth.to_csv(output_dir / "truth_labels.csv", index=False)
    summary = {
        "schema_version": "scplantannotate_public_sprint_input_v2",
        "source": str(source),
        "source_label_column": label_column,
        "seed": args.seed,
        "selected_cells": int(len(subset)),
        "class_count": int(truth.cell_type.nunique()),
        "labels_hidden_from_input": True,
        "label_distribution": {str(key): int(value) for key, value in truth.cell_type.value_counts().items()},
    }
    (output_dir / "summary.json").write_text(__import__("json").dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# Frozen scPlantAnnotate comparison input v2\n\n"
        "The H5AD contains expression and operational metadata only; the truth labels are stored in a separate CSV and are never uploaded.\n",
        encoding="utf-8",
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
