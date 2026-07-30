from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


def json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


def clean_label(value: Any) -> str:
    return " ".join(str(value or "").replace("_", " ").split())


def sparse_column_mean(matrix: Any) -> np.ndarray:
    mean = np.asarray(matrix.mean(axis=0)).ravel()
    return mean.astype(np.float64, copy=False)


def sparse_detection_rate(matrix: Any) -> np.ndarray:
    detected = np.asarray((matrix > 0).mean(axis=0)).ravel()
    return detected.astype(np.float64, copy=False)


def top_marker_candidates(adata: Any, groups: list[dict[str, Any]], max_genes: int) -> list[dict[str, Any]]:
    X = adata.X
    genes = np.asarray(adata.var_names.astype(str))
    labels = np.asarray([clean_label(value) for value in adata.obs["cell_type"].astype(str)])
    species = np.asarray([clean_label(value) for value in adata.obs["species"].astype(str)])
    records: list[dict[str, Any]] = []
    for group in groups:
        cell_type = group["cell_type"]
        sp = group["species"]
        mask = (labels == cell_type) & (species == sp)
        other = ~mask
        n_group = int(mask.sum())
        n_other = int(other.sum())
        if n_group < 25 or n_other < 25:
            continue
        group_mean = sparse_column_mean(X[mask])
        other_mean = sparse_column_mean(X[other])
        group_detect = sparse_detection_rate(X[mask])
        other_detect = sparse_detection_rate(X[other])
        log2fc = np.log2((group_mean + 1e-6) / (other_mean + 1e-6))
        detection_delta = group_detect - other_detect
        score = log2fc + 2.0 * detection_delta
        eligible = np.isfinite(score) & (group_detect >= 0.05) & (log2fc > 0)
        if not eligible.any():
            continue
        candidate_indices = np.flatnonzero(eligible)
        ranked = candidate_indices[np.argsort(score[candidate_indices])[::-1]][:max_genes]
        for rank, index in enumerate(ranked, start=1):
            records.append(
                {
                    "species": sp,
                    "cell_type": cell_type,
                    "rank": rank,
                    "gene": str(genes[index]),
                    "score": float(score[index]),
                    "log2fc": float(log2fc[index]),
                    "detection_delta": float(detection_delta[index]),
                    "mean_expression_group": float(group_mean[index]),
                    "mean_expression_other": float(other_mean[index]),
                    "detection_group": float(group_detect[index]),
                    "detection_other": float(other_detect[index]),
                    "n_group": n_group,
                    "n_other": n_other,
                }
            )
    return records


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "species",
        "cell_type",
        "rank",
        "gene",
        "score",
        "log2fc",
        "detection_delta",
        "mean_expression_group",
        "mean_expression_other",
        "detection_group",
        "detection_other",
        "n_group",
        "n_other",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\t".join(fields) + "\n")
        for row in rows:
            handle.write("\t".join(str(row.get(field, "")) for field in fields) + "\n")


def pct(value: Any) -> str:
    return f"{100.0 * float(value):.2f}%"


def num(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Plant-CellFM v10 Multi-Species scPlantDB Biology Case",
        "",
        "This report adds an independent, non-Arabidopsis-only public-data biology case to the Plant-CellFM package. It is used as public-data biological evidence and does not replace the frozen v9 performance claims.",
        "",
        "## Corpus",
        "",
        "| Item | Value |",
        "| --- | ---: |",
        f"| Cells | {payload['corpus']['cells']} |",
        f"| Genes | {payload['corpus']['genes']} |",
        f"| Species | {payload['corpus']['species']} |",
        f"| Tissues | {payload['corpus']['tissues']} |",
        f"| Samples | {payload['corpus']['samples']} |",
        f"| Datasets | {payload['corpus']['datasets']} |",
        f"| Fine cell-type labels | {payload['corpus']['cell_types']} |",
        "",
        "## Species And Tissue Coverage",
        "",
        "| Species | Cells | Tissues | Cell-type labels | Dominant tissue | Dominant label |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["species_summary"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["species"],
                    str(row["cells"]),
                    str(row["tissues"]),
                    str(row["cell_types"]),
                    row["dominant_tissue"],
                    row["dominant_cell_type"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Marker-Candidate Examples",
            "",
            "| Species | Cell type | n | Top genes | Median score | Median log2FC | Median detection delta |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for row in payload["marker_summary"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["species"],
                    row["cell_type"],
                    str(row["n_group"]),
                    ", ".join(row["top_genes"]),
                    num(row["median_score"]),
                    num(row["median_log2fc"]),
                    num(row["median_detection_delta"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The case broadens the biological demonstration beyond the Arabidopsis root figure. It shows that the same continuation machinery can organize public data from several plant species, recover species/tissue/cell-type structure and produce marker-candidate tables. The results are computational candidates and should be used as a second public-data biology case, not as wet-lab validation.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a multi-species scPlantDB biology case report")
    parser.add_argument("--h5ad", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-tsv", type=Path, required=True)
    parser.add_argument("--top-cell-types-per-species", type=int, default=3)
    parser.add_argument("--top-genes", type=int, default=8)
    args = parser.parse_args()

    import anndata as ad

    adata = ad.read_h5ad(args.h5ad)
    obs = adata.obs.copy()
    for column in ["species", "tissue", "sample_id", "dataset_id", "cell_type"]:
        if column not in obs:
            raise KeyError(f"{args.h5ad} missing obs column {column!r}")
        obs[column] = obs[column].astype(str).map(clean_label)

    species_summary = []
    marker_groups: list[dict[str, Any]] = []
    for species, species_obs in obs.groupby("species", sort=True):
        cell_type_counts = species_obs["cell_type"].value_counts()
        tissue_counts = species_obs["tissue"].value_counts()
        species_summary.append(
            {
                "species": species,
                "cells": int(species_obs.shape[0]),
                "tissues": int(species_obs["tissue"].nunique()),
                "cell_types": int(species_obs["cell_type"].nunique()),
                "dominant_tissue": str(tissue_counts.index[0]),
                "dominant_cell_type": str(cell_type_counts.index[0]),
            }
        )
        for cell_type, count in cell_type_counts.head(args.top_cell_types_per_species).items():
            marker_groups.append({"species": species, "cell_type": str(cell_type), "n": int(count)})

    marker_records = top_marker_candidates(adata, marker_groups, args.top_genes)
    marker_summary = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in marker_records:
        grouped.setdefault((row["species"], row["cell_type"]), []).append(row)
    for (species, cell_type), rows in sorted(grouped.items()):
        marker_summary.append(
            {
                "species": species,
                "cell_type": cell_type,
                "n_group": int(rows[0]["n_group"]),
                "top_genes": [row["gene"] for row in sorted(rows, key=lambda item: item["rank"])[:5]],
                "median_score": float(np.median([row["score"] for row in rows])),
                "median_log2fc": float(np.median([row["log2fc"] for row in rows])),
                "median_detection_delta": float(np.median([row["detection_delta"] for row in rows])),
            }
        )

    payload = {
        "schema_version": "plant_cellfm_v10_multispecies_scplantdb_case_v1",
        "claim_boundary": "Post-v9 public-data computational biology case; not a replacement for frozen v9 performance and not wet-lab validation.",
        "source_h5ad": str(args.h5ad),
        "corpus": {
            "cells": int(adata.n_obs),
            "genes": int(adata.n_vars),
            "species": int(obs["species"].nunique()),
            "tissues": int(obs["tissue"].nunique()),
            "samples": int(obs["sample_id"].nunique()),
            "datasets": int(obs["dataset_id"].nunique()),
            "cell_types": int(obs["cell_type"].nunique()),
        },
        "species_summary": species_summary,
        "top_cell_type_counts": [
            {"cell_type": str(key), "cells": int(value)}
            for key, value in Counter(obs["cell_type"].tolist()).most_common(30)
        ],
        "marker_record_count": len(marker_records),
        "marker_summary": marker_summary,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )
    write_tsv(args.output_tsv, marker_records)
    write_markdown(args.output_md, payload)
    print(args.output_json)
    print(args.output_md)
    print(args.output_tsv)


if __name__ == "__main__":
    main()
