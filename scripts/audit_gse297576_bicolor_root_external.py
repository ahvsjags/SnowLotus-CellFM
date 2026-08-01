from __future__ import annotations

"""Audit frozen Plant-CellFM predictions on the author-labelled GSE297576 atlas.

The script requires a predeclared label-ontology contract and checks exact cell
identity, output checksums, source-species absence from the frozen corpus and
model-input coverage before calculating a coarse external evaluation. It is a
frozen zero-shot audit, not target-species adaptation or third-party ranking.
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
DEFAULT_ATLAS = ROOT / "outputs" / "external_validation" / "gse297576_bicolor_root" / "GSE297576_bicolor_root_author_atlas.h5ad"
DEFAULT_BUNDLE = ROOT / "outputs" / "external_validation" / "gse297576_bicolor_root" / "plantcellfm_frozen_bundle"
DEFAULT_CONVERSION = ROOT / "release_metadata" / "gse297576_bicolor_root_external_conversion_v1.json"
DEFAULT_MAPPING = ROOT / "release_metadata" / "gse297576_sorghum_ortholog_map_v1.json"
DEFAULT_CONTRACT = ROOT / "release_metadata" / "gse297576_bicolor_root_ontology_contract_v1.json"
DEFAULT_MODEL_CARD = ROOT / "release_metadata" / "plant_cellfm_model_card_v4.json"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "external_validation" / "gse297576_bicolor_root" / "frozen_external_audit"
DEFAULT_RECORD = ROOT / "release_metadata" / "gse297576_bicolor_root_frozen_external_audit_v1.json"
DEFAULT_MARKDOWN = ROOT / "release_metadata" / "gse297576_bicolor_root_frozen_external_audit_v1.md"
DEFAULT_TABLE = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S25_GSE297576_frozen_external.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_contract(path: Path, author_labels: set[str]) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    declared = payload.get("labels", {})
    if set(declared) != author_labels:
        missing = sorted(author_labels - set(declared))
        extra = sorted(set(declared) - author_labels)
        raise ValueError(f"Ontology contract does not exactly cover author labels; missing={missing}, extra={extra}")
    for label, entry in declared.items():
        status = entry.get("status")
        target = entry.get("model_label")
        if status == "evaluable" and not isinstance(target, str):
            raise ValueError(f"Evaluable author label {label!r} lacks a model counterpart.")
        if status == "non_comparable" and target is not None:
            raise ValueError(f"Non-comparable author label {label!r} must not be assigned a model counterpart.")
    return declared


def join_exact(atlas_path: Path, prediction_path: Path) -> pd.DataFrame:
    atlas = ad.read_h5ad(atlas_path, backed="r")
    obs = atlas.obs.loc[:, ["cellBC", "celltype"]].reset_index(drop=True).copy()
    obs["cell_id"] = obs["cellBC"].astype(str)
    predictions = pd.read_csv(prediction_path, dtype={"cell_id": str})
    required = {"cell_id", "fine_label", "fine_confidence", "coarse_label", "coarse_confidence"}
    if not required.issubset(predictions.columns):
        raise ValueError(f"Prediction file missing columns: {sorted(required - set(predictions.columns))}")
    if obs["cell_id"].duplicated().any() or predictions["cell_id"].duplicated().any():
        raise ValueError("External audit requires unique author and prediction cell identifiers.")
    if len(obs) != len(predictions) or obs["cell_id"].tolist() != predictions["cell_id"].astype(str).tolist():
        raise ValueError("Frozen predictions do not exactly preserve author cell order and membership.")
    return pd.concat([obs, predictions.drop(columns="cell_id")], axis=1)


def evaluate(frame: pd.DataFrame, contract: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    model_labels = {label for entry in contract.values() for label in [entry["model_label"]] if label}
    frame = frame.copy()
    frame["ontology_status"] = frame["celltype"].map(lambda label: contract[str(label)]["status"])
    frame["expected_label"] = frame["celltype"].map(lambda label: contract[str(label)]["model_label"])
    selected = frame.loc[frame["ontology_status"].eq("evaluable")].copy()
    if selected.empty:
        raise ValueError("The ontology contract produced no evaluable external cells.")
    targets = sorted(model_labels)
    y_true = selected["expected_label"].to_numpy()
    y_pred = selected["fine_label"].to_numpy()
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=targets, zero_division=0)
    per_class = pd.DataFrame(
        {"model_label": targets, "support": support.astype(int), "precision": precision, "recall": recall, "f1": f1}
    )
    per_class["author_labels"] = [
        ";".join(sorted(label for label, entry in contract.items() if entry["model_label"] == target))
        for target in targets
    ]
    confusion = pd.crosstab(selected["expected_label"], selected["fine_label"], dropna=False).reindex(index=targets, fill_value=0)
    accepted = selected.loc[selected["fine_label"].ne("Unknow")]
    summary = {
        "input_cells": int(len(frame)),
        "evaluable_cells": int(len(selected)),
        "evaluable_coverage": float(len(selected) / len(frame)),
        "non_comparable_cells": int((frame["ontology_status"] == "non_comparable").sum()),
        "all_evaluable_accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1_declared_targets": float(np.mean(f1)),
        "unassigned_prediction_rate_evaluable": float(selected["fine_label"].eq("Unknow").mean()),
        "model_known_prediction_rate_evaluable": float(selected["fine_label"].ne("Unknow").mean()),
        "selective_accuracy_when_model_assigns_a_known_label": float(
            accuracy_score(accepted["expected_label"], accepted["fine_label"]) if len(accepted) else 0.0
        ),
        "selective_cells": int(len(accepted)),
        "mean_confidence_evaluable": float(selected["fine_confidence"].mean()),
        "median_confidence_evaluable": float(selected["fine_confidence"].median()),
        "unassigned_prediction_rate_non_comparable": float(
            frame.loc[frame["ontology_status"].eq("non_comparable"), "fine_label"].eq("Unknow").mean()
        ),
        "all_cell_prediction_composition": {str(label): int(count) for label, count in frame["fine_label"].value_counts().sort_index().items()},
    }
    return summary, per_class, confusion


def markdown(record: dict[str, Any]) -> str:
    metrics = record["metrics"]
    return "\n".join(
        [
            "# GSE297576 Sorghum Root Frozen External Audit",
            "",
            f"- External author-labelled input: {metrics['input_cells']:,} cells; {metrics['evaluable_cells']:,} ({metrics['evaluable_coverage']:.2%}) map to predeclared coarse identities.",
            f"- Frozen zero-shot accuracy over all evaluable cells: {metrics['all_evaluable_accuracy']:.2%}; macro-F1: {metrics['macro_f1_declared_targets']:.4f}.",
            f"- The model returned `Unknow` for {metrics['unassigned_prediction_rate_evaluable']:.2%} of evaluable cells and {metrics['unassigned_prediction_rate_non_comparable']:.2%} of non-comparable cells.",
            f"- Conditional accuracy among non-`Unknow` assignments is {metrics['selective_accuracy_when_model_assigns_a_known_label']:.2%} across {metrics['selective_cells']:,} cells; this selective quantity is not the primary accuracy.",
            "",
            "## Evidence Boundary",
            "",
            "- GSE297576 Sorghum bicolor is absent from the declared five-species frozen corpus; author labels are joined only after frozen inference.",
            "- The reported primary denominator includes every cell whose author label has a predeclared direct broad counterpart in the 13-state root vocabulary.",
            "- Non-comparable identities remain audited but are not recoded as correct, incorrect, or `Unknow` targets.",
            "- This is a Plant-CellFM frozen external audit. It is neither target-species adaptation nor a comparison against third-party methods.",
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--conversion", type=Path, default=DEFAULT_CONVERSION)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--model-card", type=Path, default=DEFAULT_MODEL_CARD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    args = parser.parse_args()
    atlas_path = args.atlas.resolve()
    bundle_dir = args.bundle.resolve()
    prediction_path = bundle_dir / "predictions.csv"
    metadata_path = bundle_dir / "annotation_metadata.json"
    if not atlas_path.is_file() or not prediction_path.is_file() or not metadata_path.is_file():
        raise FileNotFoundError("External atlas and complete frozen annotation bundle are required.")

    conversion = json.loads(args.conversion.resolve().read_text(encoding="utf-8"))
    mapping = json.loads(args.mapping.resolve().read_text(encoding="utf-8"))
    model_card = json.loads(args.model_card.resolve().read_text(encoding="utf-8"))
    bundle_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if conversion["output"]["h5ad_sha256"] != sha256(atlas_path):
        raise ValueError("Converted external atlas checksum does not match its conversion record.")
    if conversion["input"]["species"] in model_card["frozen_current_corpus"]["species_list"]:
        raise ValueError("Candidate external species appears in the declared frozen corpus.")
    if bundle_metadata["n_cells"] != int(ad.read_h5ad(atlas_path, backed="r").n_obs):
        raise ValueError("Annotation metadata does not preserve the external atlas cell count.")
    frame = join_exact(atlas_path, prediction_path)
    contract = load_contract(args.contract.resolve(), set(frame["celltype"].astype(str)))
    metrics, per_class, confusion = evaluate(frame, contract)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_dir / "cell_predictions_with_author_labels.tsv", sep="\t", index=False)
    per_class.to_csv(output_dir / "per_class_metrics.tsv", sep="\t", index=False)
    confusion.to_csv(output_dir / "confusion_matrix.tsv", sep="\t")
    args.table.resolve().parent.mkdir(parents=True, exist_ok=True)
    per_class.assign(dataset="GSE297576", species="Sorghum bicolor", evaluation="frozen_external_predeclared_coarse_ontology").to_csv(args.table.resolve(), sep="\t", index=False)

    record = {
        "schema_version": "plant_cellfm_gse297576_bicolor_root_frozen_external_audit_v1",
        "status": "COMPLETED_FROZEN_EXTERNAL_ZERO_SHOT_AUDIT",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "dataset": "GSE297576",
            "species": conversion["input"]["species"],
            "tissue": conversion["input"]["tissue"],
            "atlas": atlas_path.relative_to(ROOT).as_posix(),
            "atlas_sha256": sha256(atlas_path),
            "author_reference_label_key": "celltype",
            "cells": int(len(frame)),
            "frozen_species_absent_from_profile": True,
            "profiled_species": model_card["frozen_current_corpus"]["species_list"],
        },
        "frozen_inference": {
            "checkpoint": bundle_metadata["checkpoint_path"],
            "checkpoint_epoch": bundle_metadata["checkpoint_epoch"],
            "annotation_metadata": metadata_path.relative_to(ROOT).as_posix(),
            "annotation_metadata_sha256": sha256(metadata_path),
            "predictions": prediction_path.relative_to(ROOT).as_posix(),
            "predictions_sha256": sha256(prediction_path),
            "preprocessing_stats": bundle_metadata["preprocessing_stats"],
            "author_labels_used_for_inference": False,
        },
        "orthology_contract": {
            "mapping": mapping["output"],
            "coverage": mapping["coverage"],
            "mapping_record_sha256": sha256(args.mapping.resolve()),
        },
        "ontology_contract": {
            "path": args.contract.resolve().relative_to(ROOT).as_posix(),
            "sha256": sha256(args.contract.resolve()),
            "evaluable_author_labels": sorted(label for label, entry in contract.items() if entry["status"] == "evaluable"),
            "non_comparable_author_labels": sorted(label for label, entry in contract.items() if entry["status"] == "non_comparable"),
        },
        "metrics": metrics,
        "outputs": {
            "per_cell": (output_dir / "cell_predictions_with_author_labels.tsv").relative_to(ROOT).as_posix(),
            "per_class": (output_dir / "per_class_metrics.tsv").relative_to(ROOT).as_posix(),
            "confusion": (output_dir / "confusion_matrix.tsv").relative_to(ROOT).as_posix(),
            "supplementary_table": args.table.resolve().relative_to(ROOT).as_posix(),
        },
        "claim_boundary": "A source-pinned, author-labelled, species-held-out frozen Plant-CellFM audit with a predeclared coarse ontology. It is not a target-species adaptation result, a universal all-plant accuracy claim, or a third-party model comparison.",
    }
    args.record.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.record.resolve().write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.markdown.resolve().write_text(markdown(record), encoding="utf-8")
    print(json.dumps({"status": record["status"], "metrics": metrics}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
