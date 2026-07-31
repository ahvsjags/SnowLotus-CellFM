from __future__ import annotations

"""Audit a blinded external Arabidopsis root inference case for Plant-CellFM v4.

The GEO matrix has no expert cell-type annotations.  This script therefore
records model execution and a fixed, literature-defined marker-coherence check;
it deliberately does not calculate or imply external accuracy.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "outputs" / "external_validation" / "gse152766_gsm4626007"
INPUT_PATH = CASE_ROOT / "GSM4626007_sc_52_spliced_external_root.h5ad"
BUNDLE = CASE_ROOT / "annotation_bundle"
PREDICTIONS = BUNDLE / "predictions.csv"
BUNDLE_METADATA = BUNDLE / "annotation_metadata.json"
ACQUISITION = ROOT / "release_metadata" / "gse152766_external_input_acquisition_v4.json"
OUTPUT_JSON = ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.json"
OUTPUT_MARKDOWN = ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.md"

# These six marker-to-identity expectations are fixed before inspecting the
# external input, and match the anchor list used in the v4 literature audit.
MARKER_EXPECTATIONS: tuple[dict[str, str], ...] = (
    {
        "expected_label": "Root hair",
        "marker_symbol": "COBL9",
        "gene_id": "AT5G49270",
        "literature_key": "jean_baptiste_2019",
    },
    {
        "expected_label": "Non-hair",
        "marker_symbol": "WER",
        "gene_id": "AT5G14750",
        "literature_key": "jean_baptiste_2019",
    },
    {
        "expected_label": "Non-hair",
        "marker_symbol": "GL2",
        "gene_id": "AT1G79840",
        "literature_key": "jean_baptiste_2019",
    },
    {
        "expected_label": "Root endodermis",
        "marker_symbol": "CASP1",
        "gene_id": "AT2G36100",
        "literature_key": "shahan_2022",
    },
    {
        "expected_label": "Phloem",
        "marker_symbol": "APL",
        "gene_id": "AT1G79430",
        "literature_key": "jean_baptiste_2019",
    },
    {
        "expected_label": "Xylem",
        "marker_symbol": "MYB46",
        "gene_id": "AT5G12870",
        "literature_key": "jean_baptiste_2019",
    },
)

SOURCES: dict[str, dict[str, str]] = {
    "jean_baptiste_2019": {
        "citation": "Jean-Baptiste et al. Dynamics of Gene Expression in Single Root Cells of Arabidopsis thaliana. Plant Cell 31, 993-1011 (2019).",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8516002/",
    },
    "shahan_2022": {
        "citation": "Shahan et al. A single cell Arabidopsis root atlas reveals developmental trajectories in wild-type and cell identity mutants. Developmental Cell 57, 543-560.e9 (2022).",
        "url": "https://doi.org/10.1016/j.devcel.2022.01.008",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalised_log_expression(adata: ad.AnnData, genes: list[str]) -> np.ndarray:
    gene_positions = pd.Index(adata.var_names.astype(str)).get_indexer(genes)
    if (gene_positions < 0).any():
        missing = [gene for gene, position in zip(genes, gene_positions, strict=True) if position < 0]
        raise ValueError(f"External root matrix is missing required markers: {missing}")
    raw = adata.X
    if not sparse.issparse(raw):
        raw = sparse.csr_matrix(raw)
    raw = raw.tocsr().astype(np.float64)
    library_size = np.asarray(raw.sum(axis=1)).ravel()
    if (library_size <= 0).any():
        raise ValueError("External root matrix contains a zero-library cell.")
    # This matches the published annotation bundle preprocessing contract.
    selected = raw[:, gene_positions].toarray()
    return np.log1p(selected * (10_000.0 / library_size[:, None]))


def rank_descending(values: pd.Series, target: str) -> int:
    ordered = values.sort_values(ascending=False, kind="mergesort")
    matches = np.flatnonzero(ordered.index.to_numpy() == target)
    if len(matches) != 1:
        raise ValueError(f"Expected a single expected-label rank for {target!r}.")
    return int(matches[0] + 1)


def audit() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    for path in (INPUT_PATH, PREDICTIONS, BUNDLE_METADATA, ACQUISITION):
        if not path.exists():
            raise FileNotFoundError(f"Required external-case artifact is missing: {path}")
    adata = ad.read_h5ad(INPUT_PATH)
    predictions = pd.read_csv(PREDICTIONS)
    metadata = json.loads(BUNDLE_METADATA.read_text(encoding="utf-8"))
    acquisition = json.loads(ACQUISITION.read_text(encoding="utf-8"))
    if len(predictions) != adata.n_obs:
        raise ValueError("Prediction count does not equal external input cell count.")
    if predictions["cell_id"].astype(str).tolist() != adata.obs_names.astype(str).tolist():
        raise ValueError("Prediction row order does not match external input cell identifiers.")
    if any(column in adata.obs.columns for column in ("cell_type", "celltype", "cell_type_coarse")):
        raise ValueError("External input unexpectedly contains a cell-label field; blind-case boundary must be reviewed.")
    if int(metadata["n_cells"]) != int(adata.n_obs):
        raise ValueError("Annotation metadata cell count does not equal external input cell count.")
    if not metadata["preprocessing_stats"]["quality_control"]["log1p"]:
        raise ValueError("Expected log1p preprocessing contract is missing from annotation metadata.")

    labels = predictions["fine_label"].astype(str)
    label_summary = (
        predictions.assign(fine_label=labels)
        .groupby("fine_label", as_index=False)
        .agg(
            cells=("cell_id", "size"),
            fraction=("cell_id", lambda values: len(values) / len(predictions)),
            mean_confidence=("fine_confidence", "mean"),
            median_confidence=("fine_confidence", "median"),
        )
        .sort_values("cells", ascending=False, kind="mergesort")
        .reset_index(drop=True)
    )
    markers = [entry["gene_id"] for entry in MARKER_EXPECTATIONS]
    expression = normalised_log_expression(adata, markers)
    marker_rows: list[dict[str, Any]] = []
    label_order = label_summary["fine_label"].tolist()
    for marker_position, expectation in enumerate(MARKER_EXPECTATIONS):
        values = expression[:, marker_position]
        all_label_rows: list[dict[str, Any]] = []
        for label in label_order:
            mask = labels.to_numpy() == label
            all_label_rows.append(
                {
                    "label": label,
                    "mean_expression": float(values[mask].mean()),
                    "detection_fraction": float((values[mask] > 0).mean()),
                    "cells": int(mask.sum()),
                }
            )
        by_label = pd.DataFrame(all_label_rows).set_index("label")
        target = expectation["expected_label"]
        if target not in by_label.index:
            raise ValueError(f"Expected label {target!r} was absent from the annotation output.")
        target_mask = labels.to_numpy() == target
        background_mask = ~target_mask
        target_mean = float(values[target_mask].mean())
        background_mean = float(values[background_mask].mean())
        target_detection = float((values[target_mask] > 0).mean())
        background_detection = float((values[background_mask] > 0).mean())
        marker_rows.append(
            {
                **expectation,
                "predicted_label_cells": int(target_mask.sum()),
                "target_mean_log1p_normalised_expression": target_mean,
                "outside_mean_log1p_normalised_expression": background_mean,
                "mean_expression_delta": target_mean - background_mean,
                "target_detection_fraction": target_detection,
                "outside_detection_fraction": background_detection,
                "detection_fraction_delta": target_detection - background_detection,
                "rank_among_predicted_labels_by_mean_expression": rank_descending(by_label["mean_expression"], target),
                "rank_among_predicted_labels_by_detection_fraction": rank_descending(by_label["detection_fraction"], target),
                "is_top_mean_expression_label": bool(rank_descending(by_label["mean_expression"], target) == 1),
                "is_top_detection_label": bool(rank_descending(by_label["detection_fraction"], target) == 1),
            }
        )
    marker_summary = pd.DataFrame(marker_rows)
    checkpoint_path = ROOT / str(metadata["checkpoint_path"])
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Recorded checkpoint is unavailable for hashing: {checkpoint_path}")
    top_mean = int(marker_summary["is_top_mean_expression_label"].sum())
    top_detection = int(marker_summary["is_top_detection_label"].sum())
    payload: dict[str, Any] = {
        "schema_version": "plant_cellfm_v4_gse152766_external_root_blind_inference_v1",
        "case_role": "Blinded external Arabidopsis root-matrix inference and predefined marker-coherence audit.",
        "claim_boundary": "The downloaded matrix has no expert cell-type labels. This record contains no external accuracy, no head-to-head model comparison and no claim of independent experimental validation. Marker coherence tests whether fixed canonical loci are enriched in their corresponding model-predicted groups.",
        "input_provenance": {
            "series_accession": acquisition["series_accession"],
            "sample_accession": acquisition["sample_accession"],
            "source_url": acquisition["source_url"],
            "archive_sha256": acquisition["archive_sha256"],
            "prepared_h5ad": INPUT_PATH.relative_to(ROOT).as_posix(),
            "prepared_h5ad_sha256": sha256(INPUT_PATH),
            "frozen_v4_corpus_profile_membership": acquisition["gse152766_listed_in_frozen_v4_corpus_profile"],
            "frozen_v4_dataset_ids": acquisition["frozen_v4_dataset_ids"],
            "input_has_expert_cell_type_labels": False,
            "matrix": {"cells": int(adata.n_obs), "genes": int(adata.n_vars), "nonzero_counts": int(adata.X.nnz)},
        },
        "execution": {
            "annotation_bundle": BUNDLE.relative_to(ROOT).as_posix(),
            "prediction_csv_sha256": sha256(PREDICTIONS),
            "embedding_npy_sha256": sha256(BUNDLE / str(metadata["embedding_npy"])),
            "annotation_metadata_sha256": sha256(BUNDLE_METADATA),
            "checkpoint_path": str(metadata["checkpoint_path"]),
            "checkpoint_sha256": sha256(checkpoint_path),
            "checkpoint_epoch": int(metadata["checkpoint_epoch"]),
            "device_record": "cuda (NVIDIA GeForce RTX 4070 Laptop GPU at execution)",
            "preprocessing": metadata["preprocessing_stats"]["quality_control"],
            "n_cells": int(metadata["n_cells"]),
            "embedding_dimension": int(metadata["embedding_dim"]),
        },
        "prediction_summary": {
            "predicted_labels": int(label_summary.shape[0]),
            "fine_confidence_quantiles": {
                key: float(value)
                for key, value in zip(
                    ("min", "q05", "q25", "median", "q75", "q95", "max"),
                    np.quantile(predictions["fine_confidence"].to_numpy(dtype=float), (0, .05, .25, .5, .75, .95, 1)),
                    strict=True,
                )
            },
        },
        "marker_coherence": {
            "normalisation": "raw spliced UMI counts per cell were scaled to 10,000 and log1p transformed, matching the recorded annotation preprocessing contract",
            "predefined_expectations": len(MARKER_EXPECTATIONS),
            "expected_label_is_top_mean_expression": top_mean,
            "expected_label_is_top_detection_fraction": top_detection,
            "sources": SOURCES,
            "interpretation": "A positive delta or rank is a coherence statistic of the model-predicted partition and the external expression matrix; it is not a ground-truth accuracy measure and may be affected by marker specificity, dropout and label granularity.",
        },
        "prediction_distribution": label_summary.astype(object).where(pd.notna(label_summary), None).to_dict(orient="records"),
        "predefined_marker_coherence": marker_summary.astype(object).where(pd.notna(marker_summary), None).to_dict(orient="records"),
    }
    return payload, label_summary, marker_summary


def render_markdown(payload: dict[str, Any], labels: pd.DataFrame, markers: pd.DataFrame) -> str:
    root = payload["input_provenance"]
    execution = payload["execution"]
    marker = payload["marker_coherence"]
    lines = [
        "# GSE152766 Blind External Root Inference Audit",
        "",
        "## Scope",
        "",
        f"- GEO input: `{root['series_accession']}` / `{root['sample_accession']}`; `{root['matrix']['cells']}` cells and `{root['matrix']['genes']}` TAIR10 genes.",
        f"- Frozen-v4 corpus-profile membership: `{root['frozen_v4_corpus_profile_membership']}`. This is only a statement about the documented frozen v4 dataset list.",
        f"- Execution: checkpoint epoch `{execution['checkpoint_epoch']}`, `{execution['embedding_dimension']}`-dimensional embedding, `{execution['device_record']}`.",
        f"- Predicted states: `{payload['prediction_summary']['predicted_labels']}`; no cell-type labels were present in the downloaded input.",
        "",
        "## Evidence Boundary",
        "",
        "- This is blinded external inference, not an external accuracy estimate: the input matrix has no expert cell-type labels.",
        "- It is not a numerical comparison with scPlantLLM, scPlantAnnotate or any other tool.",
        "- The marker test is deliberately restricted to six loci fixed from primary literature before external-expression lookup. It tests coherence of model-predicted groups with expression, not causal biology or experimental validation.",
        "",
        "## Prediction Distribution",
        "",
        "| Predicted state | Cells | Fraction | Mean confidence | Median confidence |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in labels.itertuples(index=False):
        lines.append(
            f"| {row.fine_label} | {row.cells} | {row.fraction:.3f} | {row.mean_confidence:.3f} | {row.median_confidence:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Predefined Marker Coherence",
            "",
            f"- Expected group had highest mean marker expression: **{marker['expected_label_is_top_mean_expression']}/{len(markers)}** anchors.",
            f"- Expected group had highest marker detection fraction: **{marker['expected_label_is_top_detection_fraction']}/{len(markers)}** anchors.",
            "",
            "| Expected model state | Marker | Locus | n predicted cells | Mean-expression delta | Detection delta | Mean rank | Detection rank |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in markers.itertuples(index=False):
        lines.append(
            f"| {row.expected_label} | {row.marker_symbol} | {row.gene_id} | {row.predicted_label_cells} | {row.mean_expression_delta:.3f} | {row.detection_fraction_delta:.3f} | {row.rank_among_predicted_labels_by_mean_expression} | {row.rank_among_predicted_labels_by_detection_fraction} |"
        )
    lines.extend(["", "## Primary Sources", ""])
    for key, source in marker["sources"].items():
        lines.append(f"- `{key}`: {source['citation']} {source['url']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    payload, labels, markers = audit()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MARKDOWN.write_text(render_markdown(payload, labels, markers), encoding="utf-8")
    print(
        json.dumps(
            {
                "cells": payload["input_provenance"]["matrix"]["cells"],
                "predicted_labels": payload["prediction_summary"]["predicted_labels"],
                "top_mean_expression_anchors": payload["marker_coherence"]["expected_label_is_top_mean_expression"],
                "top_detection_anchors": payload["marker_coherence"]["expected_label_is_top_detection_fraction"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
