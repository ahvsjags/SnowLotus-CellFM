from __future__ import annotations

"""Freeze provenance and matched semantic recovery metrics for the GSE270140 adapter."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "gse270140_secondary_root_lora_adapter_4070.yaml"
CASE_ROOT = ROOT / "outputs" / "external_validation" / "gse270140"
MAPPING = ROOT / "release_metadata" / "gse270140_external_label_mapping_v1.tsv"
BASE_PREDICTIONS = CASE_ROOT / "annotation_bundle_srp169576_1024" / "predictions.csv"
ADAPTER_ROOT = ROOT / "outputs" / "gse270140_secondary_root_lora_adapter_4070"
TRAINING_CHECKPOINT = ADAPTER_ROOT / "best.pt"
RELEASED_CHECKPOINT = ROOT / "models" / "Plant_CellFM_GSE270140_secondary_root_lora_adapter_best.pt"
TEST_METRICS = ADAPTER_ROOT / "test_metrics.json"
HISTORY = ADAPTER_ROOT / "history.json"
DETAILED = ADAPTER_ROOT / "detailed_test" / "detailed_metrics.json"
DETAILED_PREDICTIONS = ADAPTER_ROOT / "detailed_test" / "predictions.tsv"
OUTPUT_JSON = ROOT / "release_metadata" / "gse270140_secondary_root_adapter_audit_v1.json"
OUTPUT_MARKDOWN = ROOT / "release_metadata" / "gse270140_secondary_root_adapter_audit_v1.md"
OUTPUT_TABLE = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S18_GSE270140_secondary_root_adapter_per_class.tsv"
OUTPUT_SEMANTIC_TABLE = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S19_GSE270140_secondary_root_adapter_semantic_recovery.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_builtin(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_builtin(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def semantic_score(true: pd.Series, predicted: pd.Series) -> dict[str, float | int]:
    labels = ["Phloem", "Root stele", "Xylem"]
    true_values = true.astype(str).tolist()
    pred_values = predicted.fillna("not_in_frozen_ontology").astype(str).tolist()
    return {
        "cells": int(len(true_values)),
        "accuracy": float(accuracy_score(true_values, pred_values)),
        "macro_f1": float(f1_score(true_values, pred_values, labels=labels, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(true_values, pred_values, labels=labels, average="weighted", zero_division=0)),
    }


def audit() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    required = (
        CONFIG,
        MAPPING,
        BASE_PREDICTIONS,
        TRAINING_CHECKPOINT,
        RELEASED_CHECKPOINT,
        TEST_METRICS,
        HISTORY,
        DETAILED,
        DETAILED_PREDICTIONS,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing secondary-root adapter artifacts: {', '.join(missing)}")
    if sha256(TRAINING_CHECKPOINT) != sha256(RELEASED_CHECKPOINT):
        raise ValueError("The released GSE270140 adapter checkpoint does not match the audited training checkpoint.")
    mapping = pd.read_csv(MAPPING, sep="\t", dtype=str).fillna("")
    base = pd.read_csv(BASE_PREDICTIONS, dtype={"cell_id": str})
    adapter = pd.read_csv(DETAILED_PREDICTIONS, sep="\t", dtype=str)
    test_metrics = json.loads(TEST_METRICS.read_text(encoding="utf-8"))
    history = json.loads(HISTORY.read_text(encoding="utf-8"))["epochs"]
    detailed = json.loads(DETAILED.read_text(encoding="utf-8"))
    adapter = adapter.merge(
        mapping,
        left_on="true_fine",
        right_on="source_label",
        how="left",
        validate="many_to_one",
    ).rename(columns={"mapped_model_label": "expected_semantic_label", "evaluation_tier": "true_evaluation_tier"})
    adapter = adapter.merge(
        mapping[["source_label", "mapped_model_label"]],
        left_on="pred_fine",
        right_on="source_label",
        how="left",
        validate="many_to_one",
        suffixes=("", "_pred"),
    ).rename(columns={"mapped_model_label": "adapter_semantic_prediction"})
    adapter = adapter.merge(
        base[["cell_id", "fine_label", "fine_confidence"]],
        on="cell_id",
        how="left",
        validate="one_to_one",
    ).rename(columns={"fine_label": "base_prediction", "fine_confidence": "base_confidence"})
    if adapter["expected_semantic_label"].isna().any() or adapter["base_prediction"].isna().any():
        raise ValueError("Missing mapping or base prediction while constructing the matched adapter audit.")
    shared = adapter[adapter["true_evaluation_tier"] == "shared_state"].copy()
    base_semantic = semantic_score(shared["expected_semantic_label"], shared["base_prediction"])
    adapter_semantic = semantic_score(shared["expected_semantic_label"], shared["adapter_semantic_prediction"])
    base_exact = {
        "cells": int(len(adapter)),
        "raw_output_ontology": "frozen base head has no GSE270140 raw-label classes",
        "matched_semantic_cells": int(len(shared)),
    }
    report = detailed["summary"]["fine"]["classification_report"]
    class_rows = []
    for label, values in report.items():
        if not isinstance(values, dict) or "f1-score" not in values or label in {"macro avg", "weighted avg", "micro avg", "samples avg"}:
            continue
        class_rows.append(
            {
                "author_annotation": label,
                "support": int(values["support"]),
                "precision": float(values["precision"]),
                "recall": float(values["recall"]),
                "f1": float(values["f1-score"]),
            }
        )
    per_class = pd.DataFrame(class_rows).sort_values("support", ascending=False, kind="mergesort").reset_index(drop=True)
    recovery_rows = pd.DataFrame(
        [
            {"method": "Frozen base checkpoint", **base_semantic},
            {"method": "Secondary-root LoRA-mode adapter", **adapter_semantic},
        ]
    )
    OUTPUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    per_class.to_csv(OUTPUT_TABLE, sep="\t", index=False)
    recovery_rows.to_csv(OUTPUT_SEMANTIC_TABLE, sep="\t", index=False)
    best_history = max(history, key=lambda row: float(row.get("fine_macro_f1", float("-inf"))))
    payload: dict[str, Any] = {
        "schema_version": "plant_cellfm_gse270140_secondary_root_adapter_audit_v1",
        "case_role": "Labelled, within-dataset secondary-root adaptation of the frozen root checkpoint using LoRA-mode tuning.",
        "claim_boundary": (
            "This is an author-label-supervised, cell-level held-out adaptation result from one GSE270140 sample. "
            "It is not a zero-shot result, not a leave-species result, not an independent external validation and not a matched third-party ranking."
        ),
        "source": {
            "series_accession": "GSE270140",
            "sample_accession": "GSM8335426",
            "publication_doi": "10.1038/s41477-025-01938-6",
            "cells": 11760,
            "raw_author_labels": 14,
        },
        "protocol": {
            "config": CONFIG.relative_to(ROOT).as_posix(),
            "config_sha256": sha256(CONFIG),
            "base_checkpoint": "models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt",
            "base_checkpoint_sha256": "e16564fa0a1aa74dd19ca007d9aedbe89a12fc7d1051b761c15d39705a3386fc",
            "adapter_checkpoint": RELEASED_CHECKPOINT.relative_to(ROOT).as_posix(),
            "adapter_checkpoint_sha256": sha256(RELEASED_CHECKPOINT),
            "audited_training_checkpoint": TRAINING_CHECKPOINT.relative_to(ROOT).as_posix(),
            "tuning_mode": "lora",
            "lora_rank": 8,
            "parameter_report": {"total": 9347102, "trainable": 5865501, "trainable_fraction": 0.627520808053662},
            "split": {"strategy": "group_random_by_unique_cell_id", "seed": 20260801, "train_cells": 8232, "validation_cells": 1176, "test_cells": 2352},
            "hardware": "NVIDIA GeForce RTX 4070 Laptop GPU (CUDA)",
        },
        "selection": {
            "best_epoch": 7,
            "validation_fine_macro_f1": float(best_history["fine_macro_f1"]),
            "selection_metric": "validation fine macro-F1",
        },
        "held_out_test": {
            "training_evaluator": as_builtin(test_metrics),
            "full_precision_detailed_recheck": {
                "fine_accuracy": float(detailed["summary"]["fine"]["accuracy"]),
                "fine_macro_f1": float(detailed["summary"]["fine"]["macro_f1"]),
                "weighted_f1": float(detailed["summary"]["fine"]["weighted_f1"]),
                "cells": int(detailed["summary"]["evaluated_cells"]),
                "note": "The detailed recheck runs model evaluation without mixed-precision autocast; the training evaluator value remains the primary protocol result.",
            },
        },
        "matched_three_state_semantic_recovery": {
            "evaluation_definition": "On the same held-out adapter test cells, score only source labels pre-registered as Phloem, Xylem or Root stele. Adapter raw predictions are mapped through the same frozen mapping; predictions to ontology-external labels count as errors.",
            "frozen_base_checkpoint": base_semantic,
            "secondary_root_adapter": adapter_semantic,
            "absolute_accuracy_gain": float(adapter_semantic["accuracy"] - base_semantic["accuracy"]),
            "absolute_macro_f1_gain": float(adapter_semantic["macro_f1"] - base_semantic["macro_f1"]),
        },
        "artifacts": {
            "detailed_test_metrics": DETAILED.relative_to(ROOT).as_posix(),
            "per_class_table": OUTPUT_TABLE.relative_to(ROOT).as_posix(),
            "semantic_recovery_table": OUTPUT_SEMANTIC_TABLE.relative_to(ROOT).as_posix(),
        },
    }
    return as_builtin(payload), per_class, recovery_rows


def render_markdown(payload: dict[str, Any], per_class: pd.DataFrame, recovery: pd.DataFrame) -> str:
    protocol = payload["protocol"]
    test = payload["held_out_test"]
    semantic = payload["matched_three_state_semantic_recovery"]
    lines = [
        "# GSE270140 Secondary-Root Adapter Audit",
        "",
        "## Claim Boundary",
        "",
        "- This is a labelled within-dataset adaptation, not a zero-shot or leave-species result.",
        "- The GSE270140 sample is split by unique cell barcode (80% train, 10% validation, 20% held-out test). Because it is one sample, it does not establish sample-level replication.",
        "- The frozen base head has no secondary-root labels. The same pre-registered three-state semantic map is therefore used for the matched before/after recovery audit.",
        "",
        "## Frozen Protocol",
        "",
        f"- Base checkpoint SHA256: `{protocol['base_checkpoint_sha256']}`",
        f"- Released adapter checkpoint SHA256: `{protocol['adapter_checkpoint_sha256']}` (byte-identical to `{protocol['audited_training_checkpoint']}`).",
        f"- Tuning: `LoRA-mode`, rank `{protocol['lora_rank']}`; validation selection at epoch `{payload['selection']['best_epoch']}` by macro-F1 `{payload['selection']['validation_fine_macro_f1']:.4f}`.",
        f"- Actual execution hardware: `{protocol['hardware']}`.",
        "",
        "## Held-out Adaptation Result",
        "",
        f"- Primary training-evaluator fine accuracy / macro-F1: **{test['training_evaluator']['fine_accuracy']:.4f} / {test['training_evaluator']['fine_macro_f1']:.4f}** on `{protocol['split']['test_cells']}` held-out cells.",
        f"- Detailed full-precision recheck: `{test['full_precision_detailed_recheck']['fine_accuracy']:.4f}` accuracy and `{test['full_precision_detailed_recheck']['fine_macro_f1']:.4f}` macro-F1.",
        "",
        "## Matched Three-state Semantic Recovery",
        "",
        "| Method | Held-out shared cells | Accuracy | Macro-F1 | Weighted F1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in recovery.itertuples(index=False):
        lines.append(f"| {row.method} | {row.cells} | {row.accuracy:.4f} | {row.macro_f1:.4f} | {row.weighted_f1:.4f} |")
    lines.extend(
        [
            "",
            f"- Absolute semantic accuracy gain: **{semantic['absolute_accuracy_gain']:.4f}**; macro-F1 gain: **{semantic['absolute_macro_f1_gain']:.4f}**.",
            "",
            "## Per-class Held-out Detail",
            "",
            "| Author annotation | Test cells | Precision | Recall | F1 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in per_class.itertuples(index=False):
        lines.append(f"| {row.author_annotation} | {row.support} | {row.precision:.4f} | {row.recall:.4f} | {row.f1:.4f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    payload, per_class, recovery = audit()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MARKDOWN.write_text(render_markdown(payload, per_class, recovery), encoding="utf-8")
    print(json.dumps(payload["matched_three_state_semantic_recovery"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
