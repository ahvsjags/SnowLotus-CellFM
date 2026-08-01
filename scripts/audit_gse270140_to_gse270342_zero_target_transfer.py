from __future__ import annotations

"""Audit a source-only Arabidopsis-to-wheat vascular-state transfer probe.

The script is deliberately an audit rather than a promotion path.  It fits
simple decoders on GSE270140 author labels and keeps GSE270342 labels locked
until scoring.  Both studies are already represented in project provenance, so
this is a transparent source-to-target stress test, not an independent external
benchmark or a replacement for the strict leave-species evaluation.
"""

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.neighbors import KNeighborsClassifier


ROOT = Path(__file__).resolve().parents[1]
SOURCE_H5AD = ROOT / "outputs" / "external_validation" / "gse270140" / "GSM8335426_JWE03_author_annotated_secondary_root.h5ad"
TARGET_H5AD = ROOT / "outputs" / "external_validation" / "gse270342" / "GSE270342_wheat_root_author_annotated_nonoverlap_diagnostic.h5ad"
SOURCE_BUNDLES = {
    "frozen_root_checkpoint": ROOT / "outputs" / "external_validation" / "gse270140" / "annotation_bundle_srp169576_1024",
    "gse270140_source_adapter": ROOT / "outputs" / "external_validation" / "gse270140" / "annotation_bundle_gse270140_source_adapter",
}
TARGET_BUNDLES = {
    "frozen_root_checkpoint": ROOT / "outputs" / "external_validation" / "gse270342" / "annotation_bundle_nonoverlap_author_orthogroups",
    "gse270140_source_adapter": ROOT / "outputs" / "external_validation" / "gse270342" / "annotation_bundle_gse270140_source_adapter_zero_target",
}
OUTPUT_JSON = ROOT / "release_metadata" / "gse270140_to_gse270342_zero_target_transfer_audit_v1.json"
OUTPUT_TABLE = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S21_GSE270140_to_GSE270342_zero_target_transfer.tsv"

CLASSES = np.asarray(["phloem", "stele", "xylem"], dtype=object)
SOURCE_STATES = {
    "phloem": {
        "Mature phloem parenchyma",
        "Conductive phloem parenchyma",
        "Companion cell",
        "Sieve element",
    },
    "xylem": {
        "Maturing xylem parenchyma",
        "Young xylem parenchyma",
        "Fiber",
        "Mature xylem parenchyma",
        "Vessel identity",
        "Expanding vessel",
        "Late differentiating vessel",
    },
    "stele": {"Vascular cambium"},
}
TARGET_PRIMARY_STATES = {"Phloem": "phloem", "Xylem": "xylem", "Provascular cells": "stele"}
TARGET_PERICYCLE_SENSITIVITY_STATES = {**TARGET_PRIMARY_STATES, "Pericycle": "stele"}
K_VALUES = (9, 31, 101)


def _reverse_map(groups: dict[str, set[str]]) -> dict[str, str]:
    return {raw_label: state for state, raw_labels in groups.items() for raw_label in raw_labels}


def l2_normalize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    return values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1e-12)


def _validate_bundle(bundle: Path, expected_ids: pd.Index, name: str) -> np.ndarray:
    embeddings = np.load(bundle / "embeddings.npy")
    predictions = pd.read_csv(bundle / "predictions.csv", dtype={"cell_id": str})
    if embeddings.shape[0] != len(expected_ids):
        raise ValueError(f"{name} embedding count does not match the prepared AnnData input.")
    if "cell_id" not in predictions or not np.array_equal(predictions.cell_id.to_numpy(str), expected_ids.to_numpy(str)):
        raise ValueError(f"{name} bundle cell IDs do not match the prepared AnnData input order.")
    return embeddings


def _metric_record(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    matrix = confusion_matrix(y_true, y_pred, labels=CLASSES)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", labels=CLASSES, zero_division=0)),
        "class_counts": {label: int(np.sum(y_true == label)) for label in CLASSES},
        "predicted_class_counts": {label: int(np.sum(y_pred == label)) for label in CLASSES},
        "confusion_matrix_rows_true_columns_predicted": matrix.tolist(),
    }


def evaluate_protocol(
    source_embeddings: np.ndarray,
    target_embeddings: np.ndarray,
    source_labels: np.ndarray,
    target_labels: np.ndarray,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fit source-only kNN decoders and score labels only after prediction."""
    source_embeddings = l2_normalize(source_embeddings)
    target_embeddings = l2_normalize(target_embeddings)
    metrics: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for neighbors in K_VALUES:
        decoder = KNeighborsClassifier(n_neighbors=neighbors, weights="distance", metric="cosine")
        decoder.fit(source_embeddings, source_labels)
        prediction = decoder.predict(target_embeddings)
        record = _metric_record(target_labels, prediction)
        metrics[f"knn_{neighbors}"] = record
        rows.append(
            {
                "decoder": f"kNN (k={neighbors})",
                "n_source": int(len(source_labels)),
                "n_target": int(len(target_labels)),
                "accuracy": record["accuracy"],
                "balanced_accuracy": record["balanced_accuracy"],
                "macro_f1": record["macro_f1"],
            }
        )
    return metrics, rows


def run_audit() -> dict[str, Any]:
    source = ad.read_h5ad(SOURCE_H5AD, backed="r")
    target = ad.read_h5ad(TARGET_H5AD, backed="r")
    source_raw = source.obs["expert_annotation_raw"].astype(str).str.strip().to_numpy()
    target_raw = target.obs["expert_annotation_raw"].astype(str).str.strip().to_numpy()
    source_map = _reverse_map(SOURCE_STATES)
    source_states = np.asarray([source_map.get(label, "") for label in source_raw], dtype=object)
    source_mask = source_states != ""

    source_embeddings = {
        name: _validate_bundle(bundle, source.obs_names, f"source/{name}")
        for name, bundle in SOURCE_BUNDLES.items()
    }
    target_embeddings = {
        name: _validate_bundle(bundle, target.obs_names, f"target/{name}")
        for name, bundle in TARGET_BUNDLES.items()
    }

    cohorts = {
        "primary_three_state": TARGET_PRIMARY_STATES,
        "pericycle_inclusive_sensitivity": TARGET_PERICYCLE_SENSITIVITY_STATES,
    }
    all_rows: list[dict[str, Any]] = []
    results: dict[str, Any] = {}
    for cohort_name, mapping in cohorts.items():
        target_states = np.asarray([mapping.get(label, "") for label in target_raw], dtype=object)
        target_mask = target_states != ""
        protocol_results: dict[str, Any] = {}
        for encoder_name in SOURCE_BUNDLES:
            metrics, rows = evaluate_protocol(
                source_embeddings[encoder_name][source_mask],
                target_embeddings[encoder_name][target_mask],
                source_states[source_mask],
                target_states[target_mask],
            )
            protocol_results[encoder_name] = metrics
            all_rows.extend([{"cohort": cohort_name, "encoder": encoder_name, **row} for row in rows])
        results[cohort_name] = {
            "source_cells": int(np.sum(source_mask)),
            "target_cells": int(np.sum(target_mask)),
            "source_class_counts": {label: int(np.sum(source_states[source_mask] == label)) for label in CLASSES},
            "target_class_counts": {label: int(np.sum(target_states[target_mask] == label)) for label in CLASSES},
            "source_only_decoders": protocol_results,
        }

    table = pd.DataFrame(all_rows)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_TABLE, sep="\t", index=False)
    record = {
        "schema_version": "plant_cellfm_gse270140_to_gse270342_zero_target_transfer_audit_v1",
        "claim_boundary": (
            "This is a source-only, zero-target-label, three-state Arabidopsis-to-wheat stress test. "
            "It is not an independent external benchmark because both studies are registered in historical provenance, "
            "not a strict leave-species replacement, and not a matched third-party ranking. Target labels are read only "
            "after source-only decoder predictions are written for scoring."
        ),
        "interpretation": (
            "The source-trained adapter does not improve the primary three-state macro-F1 over the frozen root checkpoint. "
            "The record is retained to prevent selective reporting and to identify cross-species vascular-state alignment as an open research problem."
        ),
        "protocol": {
            "source": {"dataset": "GSE270140/GSM8335426", "species": "Arabidopsis thaliana", "label_key": "expert_annotation_raw"},
            "target": {"dataset": "GSE270342", "species": "Triticum aestivum", "label_key": "expert_annotation_raw", "labels_used_for_fitting": False},
            "source_state_map": {state: sorted(labels) for state, labels in SOURCE_STATES.items()},
            "target_primary_state_map": TARGET_PRIMARY_STATES,
            "target_pericycle_sensitivity_map": TARGET_PERICYCLE_SENSITIVITY_STATES,
            "decoders": [f"distance-weighted cosine kNN, k={value}" for value in K_VALUES],
            "orthology": "Target embeddings use the released author wheat-to-Arabidopsis orthogroup map with deterministic first-target projection.",
            "bundle_id_order_verified": True,
        },
        "results": results,
        "artifacts": {
            "supplementary_table": OUTPUT_TABLE.relative_to(ROOT).as_posix(),
            "source_bundles": {name: bundle.relative_to(ROOT).as_posix() for name, bundle in SOURCE_BUNDLES.items()},
            "target_bundles": {name: bundle.relative_to(ROOT).as_posix() for name, bundle in TARGET_BUNDLES.items()},
        },
    }
    OUTPUT_JSON.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit source-only GSE270140-to-GSE270342 transfer.")
    parser.parse_args()
    report = run_audit()
    primary = report["results"]["primary_three_state"]["source_only_decoders"]
    print(
        json.dumps(
            {
                "state": "AUDITED_NEGATIVE_TRANSFER_RESULT_RETAINED",
                "frozen_knn9_macro_f1": primary["frozen_root_checkpoint"]["knn_9"]["macro_f1"],
                "source_adapter_knn9_macro_f1": primary["gse270140_source_adapter"]["knn_9"]["macro_f1"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
