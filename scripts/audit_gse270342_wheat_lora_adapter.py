from __future__ import annotations

"""Audit the barcode-non-overlap GSE270342 wheat LoRA adaptation case."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from snowcell.artifacts import load_checkpoint
from snowcell.config import ExperimentConfig
from snowcell.data import prepare_data


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "gse270342_wheat_root_lora_adapter_4070.yaml"
DEFAULT_TRAIN_DIR = ROOT / "outputs" / "gse270342_wheat_root_lora_adapter_4070"
DEFAULT_RELEASED_CHECKPOINT = ROOT / "models" / "Plant_CellFM_GSE270342_wheat_root_lora_adapter_best.pt"
DEFAULT_FROZEN_BUNDLE = ROOT / "outputs" / "external_validation" / "gse270342" / "annotation_bundle_nonoverlap_author_orthogroups"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "gse270342_wheat_root_lora_adapter_4070" / "audit"
DEFAULT_RECORD = ROOT / "release_metadata" / "gse270342_wheat_lora_adapter_audit_v1.json"
DEFAULT_MARKDOWN = ROOT / "release_metadata" / "gse270342_wheat_lora_adapter_audit_v1.md"

DIRECT_AUTHOR_TO_ROOT = {
    "Unknown": "Unknow",
    "Epidermis": "Non-hair",
    "Cortex": "Root cortex",
    "Root Hair": "Root hair",
    "Endodermis": "Root endodermis",
    "Xylem": "Xylem",
    "Phloem": "Phloem",
    "Root Cap": "Root cap",
}
OUTSIDE_DIRECT_MAP = "__outside_direct_map__"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def score_matched_direct(frame: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    selected = frame.loc[frame["true_fine"].isin(DIRECT_AUTHOR_TO_ROOT)].copy()
    selected["expected_root_label"] = selected["true_fine"].map(DIRECT_AUTHOR_TO_ROOT)
    selected["adapted_root_label"] = selected["pred_fine"].map(DIRECT_AUTHOR_TO_ROOT).fillna(OUTSIDE_DIRECT_MAP)
    y_true = selected["expected_root_label"].tolist()
    frozen = selected["frozen_fine_label"].tolist()
    adapted = selected["adapted_root_label"].tolist()
    targets = sorted(DIRECT_AUTHOR_TO_ROOT.values())
    summary = {
        "evaluated_cells": int(len(selected)),
        "author_labels": sorted(DIRECT_AUTHOR_TO_ROOT),
        "root_labels": targets,
        "frozen_first_projection_accuracy": float(accuracy_score(y_true, frozen)),
        "frozen_first_projection_macro_f1": float(f1_score(y_true, frozen, labels=targets, average="macro", zero_division=0)),
        "adapted_lora_accuracy": float(accuracy_score(y_true, adapted)),
        "adapted_lora_macro_f1": float(f1_score(y_true, adapted, labels=targets, average="macro", zero_division=0)),
    }
    summary["accuracy_gain_percentage_points"] = (
        100.0 * (summary["adapted_lora_accuracy"] - summary["frozen_first_projection_accuracy"])
    )
    return summary, selected


def markdown(record: dict[str, Any]) -> str:
    full = record["locked_full_13_class_test"]
    matched = record["matched_direct_root_subset"]
    return "\n".join(
        [
            "# GSE270342 Wheat Root LoRA Adaptation Audit",
            "",
            f"- Prepared barcode-non-overlap input: `{record['input']['cells']}` cells.",
            f"- Fixed split: `{record['split']['train_cells']}` train / `{record['split']['validation_cells']}` validation / `{record['split']['test_cells']}` locked test cells.",
            f"- Selected checkpoint epoch: `{record['checkpoint']['best_epoch']}` using validation fine macro-F1.",
            f"- Released checkpoint: `{record['checkpoint']['path']}` (SHA256 `{record['checkpoint']['sha256']}`).",
            f"- Locked 13-class fine test: accuracy `{full['accuracy']:.2%}`, macro-F1 `{full['macro_f1']:.4f}`.",
            f"- Matched direct-root locked subset: frozen `{matched['frozen_first_projection_accuracy']:.2%}` to adapted `{matched['adapted_lora_accuracy']:.2%}` ({matched['accuracy_gain_percentage_points']:.2f} percentage points).",
            "",
            "## Evidence Boundary",
            "",
            "- This is a single-study, author-label-supervised species-adaptation experiment on a barcode-non-overlap input, not zero-shot transfer or independent external validation.",
            "- The frozen baseline and LoRA adapter are compared only on the same locked cells and a predeclared direct anatomical map.",
            "- The 13-class primary test metric uses author labels and is not directly comparable to the frozen 13-state root checkpoint vocabulary.",
            "- No test labels selected the checkpoint, mapping policy, epoch, or hyperparameters.",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--train-dir", type=Path, default=DEFAULT_TRAIN_DIR)
    parser.add_argument("--released-checkpoint", type=Path, default=DEFAULT_RELEASED_CHECKPOINT)
    parser.add_argument("--frozen-bundle", type=Path, default=DEFAULT_FROZEN_BUNDLE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    config_path = args.config.resolve()
    train_dir = args.train_dir.resolve()
    released_checkpoint = args.released_checkpoint.resolve()
    frozen_bundle = args.frozen_bundle.resolve()
    output_dir = args.output_dir.resolve()
    config = ExperimentConfig.load(config_path)
    prepared = prepare_data(config.data, config.train.seed, require_labels=True)
    best_path = train_dir / "best.pt"
    detailed_path = train_dir / "detailed_test" / "predictions.tsv"
    detailed_metrics_path = train_dir / "detailed_test" / "detailed_metrics.json"
    frozen_predictions_path = frozen_bundle / "predictions.csv"
    required = [best_path, released_checkpoint, detailed_path, detailed_metrics_path, frozen_predictions_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing adaptation audit inputs: {', '.join(missing)}")
    training_sha256 = sha256(best_path)
    released_sha256 = sha256(released_checkpoint)
    if training_sha256 != released_sha256:
        raise ValueError("Released wheat adapter checkpoint does not match the audited training checkpoint.")

    detailed = pd.read_csv(detailed_path, sep="\t", dtype={"cell_id": str}).reset_index(drop=True)
    test_ids = prepared.matrix.obs[config.data.cell_id_key][prepared.split.test].astype(str).tolist()
    if detailed["cell_id"].tolist() != test_ids:
        raise ValueError("Detailed prediction rows do not exactly match the fixed test split.")
    frozen = pd.read_csv(frozen_predictions_path, dtype={"cell_id": str}).set_index("cell_id")
    if frozen.index.duplicated().any() or not set(test_ids).issubset(frozen.index):
        raise ValueError("Frozen bundle does not contain every locked test cell exactly once.")
    detailed["frozen_fine_label"] = frozen.loc[test_ids, "fine_label"].astype(str).to_numpy()
    matched, matched_cells = score_matched_direct(detailed)
    output_dir.mkdir(parents=True, exist_ok=True)
    matched_cells.to_csv(output_dir / "matched_direct_root_locked_test.tsv", sep="\t", index=False)
    detailed_metrics = json.loads(detailed_metrics_path.read_text(encoding="utf-8"))
    per_class = detailed_metrics["summary"]["fine"]["classification_report"]
    per_class_rows = pd.DataFrame(
        [
            {"author_label": label, **values}
            for label, values in per_class.items()
            if isinstance(values, dict)
            and "f1-score" in values
            and label not in {"macro avg", "weighted avg", "micro avg", "samples avg"}
        ]
    )
    per_class_rows.to_csv(output_dir / "locked_test_per_class.tsv", sep="\t", index=False)
    metrics = detailed_metrics["summary"]["fine"]
    checkpoint = load_checkpoint(best_path, map_location="cpu")
    input_record_path = ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_input_preparation_v1.json"
    input_record = json.loads(input_record_path.read_text(encoding="utf-8")) if input_record_path.is_file() else {}
    record = {
        "schema_version": "plant_cellfm_gse270342_wheat_lora_adapter_audit_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "case_role": "Barcode-non-overlap, same-study author-label-supervised wheat root species adaptation using LoRA.",
        "input": {
            "path": config.data.path,
            "cells": int(prepared.matrix.n_cells),
            "nonzero_counts": int(prepared.matrix.X.nnz),
            "prior_strict_overlap_excluded": input_record.get("overlap_audit", {}).get("exact_cs1_barcode_overlap_excluded"),
        },
        "configuration": {
            "path": config_path.relative_to(ROOT).as_posix(),
            "sha256": sha256(config_path),
            "ortholog_map": config.data.ortholog_map,
            "ortholog_aggregation": config.data.ortholog_aggregation,
            "tuning_mode": config.train.tuning_mode,
            "seed": config.train.seed,
            "base_checkpoint": config.train.init_checkpoint,
        },
        "split": {
            "strategy": config.data.split_strategy,
            "train_cells": int(len(prepared.split.train)),
            "validation_cells": int(len(prepared.split.validation)),
            "test_cells": int(len(prepared.split.test)),
            "test_cell_id_sha256": hashlib.sha256("\n".join(test_ids).encode("utf-8")).hexdigest(),
        },
        "checkpoint": {
            "path": released_checkpoint.relative_to(ROOT).as_posix(),
            "sha256": released_sha256,
            "training_path": best_path.relative_to(ROOT).as_posix(),
            "training_sha256": training_sha256,
            "best_epoch": int(checkpoint.get("epoch", -1)),
            "validation_metrics_at_selection": checkpoint.get("metrics", {}),
        },
        "locked_full_13_class_test": {
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "weighted_f1": metrics["weighted_f1"],
            "class_count": metrics["class_count"],
            "detailed_metrics_path": detailed_metrics_path.relative_to(ROOT).as_posix(),
            "detailed_metrics_sha256": sha256(detailed_metrics_path),
            "prediction_path": detailed_path.relative_to(ROOT).as_posix(),
            "prediction_sha256": sha256(detailed_path),
        },
        "matched_direct_root_subset": matched,
        "claim_boundary": (
            "The adapter is evaluated on a fixed, author-label-supervised cell-level test split from a public wheat "
            "root study after excluding exact barcode overlap with a prior strict-transfer subset. It is not a zero-shot "
            "or independent external validation result. The matched direct-root comparison is restricted to the predeclared "
            "eight-label map and does not replace the full 13-class author-label test metric."
        ),
    }
    record_path = args.record.resolve()
    markdown_path = args.markdown.resolve()
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown(record), encoding="utf-8")
    print(json.dumps({"locked_full_13_class_test": record["locked_full_13_class_test"], "matched_direct_root_subset": matched}, ensure_ascii=False))


if __name__ == "__main__":
    main()
