from __future__ import annotations

"""Audit the locked-library GSE297576 Sorghum LoRA adapter.

The adapter is trained on two libraries, selected on a third and evaluated once
on a fourth. A matched broad-identity recovery audit compares the frozen root
head and adapted 27-state head only on the same sealed test-library cells.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from snowcell.config import ExperimentConfig
from snowcell.data import prepare_data


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "gse297576_sorghum_root_lora_adapter_4070.yaml"
TRAINING_ROOT = ROOT / "outputs" / "gse297576_sorghum_root_lora_adapter_4070_oughw_holdout"
TRAINING_CHECKPOINT = TRAINING_ROOT / "best.pt"
RELEASED_CHECKPOINT = ROOT / "models" / "Plant_CellFM_GSE297576_sorghum_root_lora_adapter_oughw_holdout_best.pt"
TEST_METRICS = TRAINING_ROOT / "test_metrics.json"
HISTORY = TRAINING_ROOT / "history.json"
DETAILED = TRAINING_ROOT / "detailed_test" / "detailed_metrics.json"
DETAILED_PREDICTIONS = TRAINING_ROOT / "detailed_test" / "predictions.tsv"
FROZEN_PREDICTIONS = ROOT / "outputs" / "external_validation" / "gse297576_bicolor_root" / "plantcellfm_frozen_bundle" / "predictions.csv"
ONTOLOGY = ROOT / "release_metadata" / "gse297576_bicolor_root_ontology_contract_v1.json"
FROZEN_AUDIT = ROOT / "release_metadata" / "gse297576_bicolor_root_frozen_external_audit_v1.json"
OUTPUT_JSON = ROOT / "release_metadata" / "gse297576_sorghum_root_lora_adapter_audit_v1.json"
OUTPUT_MARKDOWN = ROOT / "release_metadata" / "gse297576_sorghum_root_lora_adapter_audit_v1.md"
OUTPUT_PER_CLASS = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S26_GSE297576_sorghum_adapter_per_class.tsv"
OUTPUT_RECOVERY = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S27_GSE297576_sorghum_adapter_matched_recovery.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def broad_score(true_raw: pd.Series, predicted_raw: pd.Series, ontology: dict[str, Any]) -> dict[str, Any]:
    labels = ontology["labels"]
    expected = true_raw.astype(str).map(lambda value: labels[value]["model_label"])
    selected = expected.notna()
    mapped_prediction = predicted_raw.astype(str).map(
        lambda value: labels[value]["model_label"] if value in labels else value
    ).fillna("not_in_frozen_ontology")
    y_true = expected.loc[selected].to_numpy()
    y_pred = mapped_prediction.loc[selected].to_numpy()
    target_labels = sorted(set(y_true.tolist()))
    return {
        "cells": int(selected.sum()),
        "coverage_of_sealed_test_library": float(selected.mean()),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=target_labels, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, labels=target_labels, average="weighted", zero_division=0)),
        "labels": target_labels,
    }


def per_class_table(detailed: dict[str, Any]) -> pd.DataFrame:
    report = detailed["summary"]["fine"]["classification_report"]
    rows = []
    for label, values in report.items():
        if not isinstance(values, dict) or "f1-score" not in values:
            continue
        if label in {"accuracy", "macro avg", "weighted avg", "micro avg", "samples avg"}:
            continue
        rows.append(
            {
                "author_annotation": label,
                "support": int(values["support"]),
                "precision": float(values["precision"]),
                "recall": float(values["recall"]),
                "f1": float(values["f1-score"]),
            }
        )
    return pd.DataFrame(rows).sort_values("support", ascending=False, kind="mergesort").reset_index(drop=True)


def audit() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    required = [
        CONFIG, TRAINING_CHECKPOINT, RELEASED_CHECKPOINT, TEST_METRICS, HISTORY,
        DETAILED, DETAILED_PREDICTIONS, FROZEN_PREDICTIONS, ONTOLOGY, FROZEN_AUDIT,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Sorghum adapter audit artifacts: {', '.join(missing)}")
    if sha256(TRAINING_CHECKPOINT) != sha256(RELEASED_CHECKPOINT):
        raise ValueError("Released Sorghum adapter is not byte-identical to the audited training checkpoint.")

    config = ExperimentConfig.load(CONFIG)
    prepared = prepare_data(config.data, config.train.seed, require_labels=True)
    split = prepared.preprocessing_stats["split"]
    if set(split["test_leaveout_values"]) & set(split["train_leaveout_values"]):
        raise ValueError("Test library overlaps Sorghum adapter training libraries.")
    if set(split["test_leaveout_values"]) & set(split["validation_leaveout_values"]):
        raise ValueError("Test library overlaps Sorghum adapter validation libraries.")

    test_metrics = json.loads(TEST_METRICS.read_text(encoding="utf-8"))
    history = json.loads(HISTORY.read_text(encoding="utf-8"))["epochs"]
    detailed = json.loads(DETAILED.read_text(encoding="utf-8"))
    ontology = json.loads(ONTOLOGY.read_text(encoding="utf-8"))
    frozen_audit = json.loads(FROZEN_AUDIT.read_text(encoding="utf-8"))
    best_history = max(history, key=lambda row: float(row["fine_macro_f1"]))
    checkpoint_epoch = int(detailed["checkpoint_epoch"])
    if checkpoint_epoch != int(best_history["epoch"]):
        raise ValueError("Detailed test checkpoint does not match the validation-selected best epoch.")

    adapter = pd.read_csv(DETAILED_PREDICTIONS, sep="\t", dtype=str)
    frozen = pd.read_csv(FROZEN_PREDICTIONS, dtype={"cell_id": str})
    if adapter["cell_id"].duplicated().any() or frozen["cell_id"].duplicated().any():
        raise ValueError("Matched recovery requires unique cell identifiers.")
    merged = adapter.merge(
        frozen[["cell_id", "fine_label"]], on="cell_id", how="left", validate="one_to_one"
    ).rename(columns={"fine_label": "frozen_prediction"})
    if merged["frozen_prediction"].isna().any():
        raise ValueError("Frozen predictions are missing sealed adapter-test cells.")
    adapter_broad = broad_score(merged["true_fine"], merged["pred_fine"], ontology)
    frozen_broad = broad_score(merged["true_fine"], merged["frozen_prediction"], ontology)
    recovery = pd.DataFrame(
        [
            {"method": "Frozen Plant-CellFM root head", **frozen_broad},
            {"method": "Sorghum 27-state LoRA adapter", **adapter_broad},
        ]
    )
    classes = per_class_table(detailed)
    OUTPUT_PER_CLASS.parent.mkdir(parents=True, exist_ok=True)
    classes.to_csv(OUTPUT_PER_CLASS, sep="\t", index=False)
    recovery.to_csv(OUTPUT_RECOVERY, sep="\t", index=False)

    payload: dict[str, Any] = {
        "schema_version": "plant_cellfm_gse297576_sorghum_root_lora_adapter_audit_v1",
        "status": "COMPLETED_LOCKED_LIBRARY_SPECIES_ADAPTATION",
        "case_role": "Author-label-supervised Sorghum bicolor root adaptation with a sealed library-level test set.",
        "claim_boundary": "A within-atlas, library-held-out target-species adaptation result. It is not a zero-shot external metric, not leave-species evidence, not wet-lab validation and not a third-party comparison.",
        "source": {
            "series_accession": "GSE297576",
            "species": "Sorghum bicolor",
            "tissue": "root",
            "author_label_states": 27,
            "source_cells": int(prepared.matrix.n_cells),
            "frozen_external_audit": FROZEN_AUDIT.relative_to(ROOT).as_posix(),
            "frozen_external_species_absent_from_profile": frozen_audit["input"]["frozen_species_absent_from_profile"],
        },
        "protocol": {
            "config": CONFIG.relative_to(ROOT).as_posix(),
            "config_sha256": sha256(CONFIG),
            "base_checkpoint": "models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt",
            "adapter_checkpoint": RELEASED_CHECKPOINT.relative_to(ROOT).as_posix(),
            "adapter_checkpoint_sha256": sha256(RELEASED_CHECKPOINT),
            "audited_training_checkpoint": TRAINING_CHECKPOINT.relative_to(ROOT).as_posix(),
            "tuning_mode": "lora",
            "lora_rank": 8,
            "parameter_report": {"total": 6510124, "trainable": 3028523, "trainable_fraction": 0.4652020453066639},
            "split": split,
            "hardware": "NVIDIA GeForce RTX 4070 Laptop GPU (CUDA)",
        },
        "selection": {
            "selection_metric": "validation fine macro-F1",
            "best_epoch": checkpoint_epoch,
            "validation_fine_macro_f1": float(best_history["fine_macro_f1"]),
            "test_labels_used_for_selection": False,
        },
        "sealed_library_test": {
            "training_evaluator": test_metrics,
            "full_precision_detailed_recheck": {
                "cells": int(detailed["summary"]["evaluated_cells"]),
                "fine_accuracy": float(detailed["summary"]["fine"]["accuracy"]),
                "fine_macro_f1": float(detailed["summary"]["fine"]["macro_f1"]),
                "fine_weighted_f1": float(detailed["summary"]["fine"]["weighted_f1"]),
                "coarse_accuracy": float(detailed["summary"]["coarse"]["accuracy"]),
                "coarse_macro_f1": float(detailed["summary"]["coarse"]["macro_f1"]),
            },
        },
        "matched_broad_identity_recovery_on_sealed_test_library": {
            "evaluation_definition": "On the same sealed test-library cells, keep all author labels with a predeclared broad frozen-root counterpart. Map adapted raw labels and frozen predictions through the same ontology; an adapter prediction to a non-comparable state counts as an error.",
            "frozen_root_head": frozen_broad,
            "sorghum_lora_adapter": adapter_broad,
            "absolute_accuracy_gain": float(adapter_broad["accuracy"] - frozen_broad["accuracy"]),
            "absolute_macro_f1_gain": float(adapter_broad["macro_f1"] - frozen_broad["macro_f1"]),
        },
        "artifacts": {
            "detailed_test": DETAILED.relative_to(ROOT).as_posix(),
            "per_class_table": OUTPUT_PER_CLASS.relative_to(ROOT).as_posix(),
            "matched_recovery_table": OUTPUT_RECOVERY.relative_to(ROOT).as_posix(),
        },
    }
    return payload, classes, recovery


def markdown(payload: dict[str, Any], classes: pd.DataFrame, recovery: pd.DataFrame) -> str:
    protocol = payload["protocol"]
    test = payload["sealed_library_test"]["full_precision_detailed_recheck"]
    recovery_metric = payload["matched_broad_identity_recovery_on_sealed_test_library"]
    lines = [
        "# GSE297576 Sorghum Root Adapter Audit",
        "",
        "## Claim Boundary",
        "",
        "- The adapter is trained on two Sorghum libraries, selected on one distinct library and evaluated once on a fourth sealed library.",
        "- This is target-species adaptation, not a zero-shot or independent external model comparison.",
        "- The frozen-before/adapter-after recovery comparison uses the same sealed test cells and a predeclared broad root ontology.",
        "",
        "## Locked Protocol",
        "",
        f"- Released checkpoint SHA256: `{protocol['adapter_checkpoint_sha256']}`.",
        f"- Selection: epoch `{payload['selection']['best_epoch']}` by validation macro-F1 `{payload['selection']['validation_fine_macro_f1']:.4f}`; test labels were not used for selection.",
        f"- Sealed test library: `{', '.join(protocol['split']['test_leaveout_values'])}`; `{test['cells']}` cells, `{payload['source']['author_label_states']}` author states.",
        "",
        "## Held-out Result",
        "",
        f"- Fine accuracy / macro-F1: **{test['fine_accuracy']:.4f} / {test['fine_macro_f1']:.4f}**; weighted F1: `{test['fine_weighted_f1']:.4f}`.",
        f"- Coarse accuracy / macro-F1: `{test['coarse_accuracy']:.4f} / {test['coarse_macro_f1']:.4f}`.",
        "",
        "## Matched Broad-identity Recovery",
        "",
        "| Method | Evaluable sealed cells | Accuracy | Macro-F1 | Weighted F1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in recovery.itertuples(index=False):
        lines.append(f"| {row.method} | {row.cells} | {row.accuracy:.4f} | {row.macro_f1:.4f} | {row.weighted_f1:.4f} |")
    lines.extend(
        [
            "",
            f"- Absolute accuracy gain: **{recovery_metric['absolute_accuracy_gain']:.4f}**; macro-F1 gain: **{recovery_metric['absolute_macro_f1_gain']:.4f}**.",
            "",
            "## Per-class Sealed-test Detail",
            "",
            "| Author state | Test cells | Precision | Recall | F1 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in classes.itertuples(index=False):
        lines.append(f"| {row.author_annotation} | {row.support} | {row.precision:.4f} | {row.recall:.4f} | {row.f1:.4f} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    payload, classes, recovery = audit()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MARKDOWN.write_text(markdown(payload, classes, recovery), encoding="utf-8")
    print(json.dumps(payload["matched_broad_identity_recovery_on_sealed_test_library"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
