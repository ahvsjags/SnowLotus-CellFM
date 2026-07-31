from __future__ import annotations

"""Audit frozen GSE270342 predictions against a predeclared coarse root map.

This is deliberately a same-study, non-overlapping-cell diagnostic. It reports a
small direct label map and an expanded stele-sensitive sensitivity map separately;
neither is an independent benchmark or a replacement for strict leave-species
evaluation.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse270342"
    / "GSE270342_wheat_root_author_annotated_nonoverlap_diagnostic.h5ad"
)
DEFAULT_FIRST = ROOT / "outputs" / "external_validation" / "gse270342" / "annotation_bundle_nonoverlap_author_orthogroups"
DEFAULT_MEAN = ROOT / "outputs" / "external_validation" / "gse270342" / "annotation_bundle_nonoverlap_author_orthogroup_mean"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "external_validation" / "gse270342" / "diagnostic_audit"
DEFAULT_RECORD = ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_frozen_diagnostic_v1.json"
DEFAULT_MARKDOWN = ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_frozen_diagnostic_v1.md"

# Declared before inspecting the frozen-prediction scores. The map keeps only
# anatomical labels with an explicit counterpart in the 13-state root checkpoint.
DIRECT_AUTHOR_TO_MODEL = {
    "Unknown": "Unknow",
    "Epidermis": "Non-hair",
    "Cortex": "Root cortex",
    "Root Hair": "Root hair",
    "Endodermis": "Root endodermis",
    "Xylem": "Xylem",
    "Phloem": "Phloem",
    "Root Cap": "Root cap",
}
EXTENDED_STELE_MAP = {
    **DIRECT_AUTHOR_TO_MODEL,
    "Pericycle": "Root stele",
    "Provascular cells": "Root stele",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frame(input_path: Path, prediction_path: Path) -> pd.DataFrame:
    adata = ad.read_h5ad(input_path, backed="r")
    obs = adata.obs.loc[:, ["cell_id", "expert_annotation_raw"]].reset_index(drop=True).copy()
    predictions = pd.read_csv(prediction_path, dtype={"cell_id": str})
    required = {"cell_id", "fine_label", "fine_confidence"}
    if not required.issubset(predictions.columns):
        raise ValueError(f"Prediction file missing columns: {sorted(required - set(predictions.columns))}")
    if len(obs) != len(predictions) or obs["cell_id"].tolist() != predictions["cell_id"].astype(str).tolist():
        raise ValueError("Prediction cell order does not exactly match the declared non-overlap input.")
    obs["fine_label"] = predictions["fine_label"].astype(str).to_numpy()
    obs["fine_confidence"] = pd.to_numeric(predictions["fine_confidence"], errors="raise").to_numpy()
    return obs


def score_mapping(frame: pd.DataFrame, label_map: dict[str, str]) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    selected = frame.loc[frame["expert_annotation_raw"].isin(label_map)].copy()
    selected["expected_label"] = selected["expert_annotation_raw"].map(label_map)
    targets = sorted(set(label_map.values()))
    y_true = selected["expected_label"].to_numpy()
    y_pred = selected["fine_label"].to_numpy()
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=targets,
        zero_division=0,
    )
    per_class = pd.DataFrame(
        {
            "model_label": targets,
            "support": support.astype(int),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    )
    per_class["author_labels"] = [
        ";".join(sorted(label for label, target in label_map.items() if target == model_label))
        for model_label in targets
    ]
    confusion = pd.crosstab(
        selected["expected_label"],
        selected["fine_label"],
        dropna=False,
    ).reindex(index=targets, fill_value=0)
    summary = {
        "evaluated_cells": int(len(selected)),
        "coverage_of_nonoverlap_input": float(len(selected) / len(frame)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1_declared_targets": float(np.mean(f1)),
        "mean_confidence": float(selected["fine_confidence"].mean()),
        "median_confidence": float(selected["fine_confidence"].median()),
        "author_labels": sorted(label_map),
        "model_labels": targets,
    }
    return summary, per_class, confusion


def run_mode(name: str, input_path: Path, bundle_dir: Path, output_dir: Path) -> dict[str, Any]:
    prediction_path = bundle_dir / "predictions.csv"
    metadata_path = bundle_dir / "annotation_metadata.json"
    if not prediction_path.is_file() or not metadata_path.is_file():
        raise FileNotFoundError(f"Missing annotation bundle files in {bundle_dir}")
    frame = load_frame(input_path, prediction_path)
    bundle_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    direct, direct_per_class, direct_confusion = score_mapping(frame, DIRECT_AUTHOR_TO_MODEL)
    extended, extended_per_class, extended_confusion = score_mapping(frame, EXTENDED_STELE_MAP)
    mode_dir = output_dir / name
    mode_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(mode_dir / "cell_predictions_with_author_labels.tsv", sep="\t", index=False)
    direct_per_class.to_csv(mode_dir / "direct_per_class.tsv", sep="\t", index=False)
    direct_confusion.to_csv(mode_dir / "direct_confusion.tsv", sep="\t")
    extended_per_class.to_csv(mode_dir / "extended_stele_per_class.tsv", sep="\t", index=False)
    extended_confusion.to_csv(mode_dir / "extended_stele_confusion.tsv", sep="\t")
    return {
        "mode": name,
        "prediction_path": prediction_path.relative_to(ROOT).as_posix(),
        "prediction_sha256": sha256(prediction_path),
        "annotation_metadata_path": metadata_path.relative_to(ROOT).as_posix(),
        "annotation_metadata_sha256": sha256(metadata_path),
        "preprocessing_stats": bundle_metadata.get("preprocessing_stats", {}),
        "all_cells_prediction_composition": frame["fine_label"].value_counts().sort_index().to_dict(),
        "all_cells_mean_confidence": float(frame["fine_confidence"].mean()),
        "direct_anatomical_map": direct,
        "extended_stele_sensitivity_map": extended,
    }


def markdown(record: dict[str, Any]) -> str:
    lines = [
        "# GSE270342 Frozen Wheat Root Diagnostic",
        "",
        f"- Non-overlapping author-labelled cells: {record['input']['cells']}.",
        "- Primary readout: direct coarse anatomical correspondence only.",
        "- Sensitivity readout: adds Pericycle and Provascular cells as broad Root stele; reported separately.",
        "",
        "| Ortholog projection | Direct cells | Direct accuracy | Direct macro-F1 | Extended cells | Extended accuracy |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode in record["modes"]:
        direct = mode["direct_anatomical_map"]
        extended = mode["extended_stele_sensitivity_map"]
        lines.append(
            f"| {mode['mode']} | {direct['evaluated_cells']} | {direct['accuracy']:.2%} | "
            f"{direct['macro_f1_declared_targets']:.4f} | {extended['evaluated_cells']} | {extended['accuracy']:.2%} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Boundary",
            "",
            "- Exact barcodes recorded in the earlier GSE270342 replicate-1 strict-transfer subset were removed before prediction.",
            "- The retained cells remain from the same study and are not independent external validation.",
            "- No author labels entered frozen inference, mapping-policy selection, checkpoint selection, or calibration.",
            "- This stress test does not replace the v17 nested leave-species primary metric or provide third-party model ranking.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--first-bundle", type=Path, default=DEFAULT_FIRST)
    parser.add_argument("--mean-bundle", type=Path, default=DEFAULT_MEAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Missing declared non-overlap input: {input_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    modes = [
        run_mode("first", input_path, args.first_bundle.resolve(), output_dir),
        run_mode("mean", input_path, args.mean_bundle.resolve(), output_dir),
    ]
    comparison = pd.DataFrame(
        [
            {
                "ortholog_aggregation": mode["mode"],
                "direct_evaluated_cells": mode["direct_anatomical_map"]["evaluated_cells"],
                "direct_accuracy": mode["direct_anatomical_map"]["accuracy"],
                "direct_macro_f1": mode["direct_anatomical_map"]["macro_f1_declared_targets"],
                "extended_evaluated_cells": mode["extended_stele_sensitivity_map"]["evaluated_cells"],
                "extended_accuracy": mode["extended_stele_sensitivity_map"]["accuracy"],
                "extended_macro_f1": mode["extended_stele_sensitivity_map"]["macro_f1_declared_targets"],
            }
            for mode in modes
        ]
    )
    comparison.to_csv(output_dir / "projection_mode_comparison.tsv", sep="\t", index=False)
    record = {
        "schema_version": "plant_cellfm_gse270342_frozen_wheat_nonoverlap_diagnostic_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": input_path.relative_to(ROOT).as_posix(),
            "sha256": sha256(input_path),
            "cells": int(ad.read_h5ad(input_path, backed="r").n_obs),
        },
        "declared_maps": {
            "direct_anatomical": DIRECT_AUTHOR_TO_MODEL,
            "extended_stele_sensitivity": EXTENDED_STELE_MAP,
        },
        "modes": modes,
        "claim_boundary": (
            "A same-study, barcode-non-overlap frozen-model diagnostic. No author labels entered inference or "
            "policy selection. It is not independent external validation, a zero-shot headline, or a third-party ranking."
        ),
    }
    record_path = args.record.resolve()
    markdown_path = args.markdown.resolve()
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown(record), encoding="utf-8")
    print(comparison.to_json(orient="records"))


if __name__ == "__main__":
    main()
