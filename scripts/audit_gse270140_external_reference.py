from __future__ import annotations

"""Audit the GSE270140 secondary-root reference stress case without score inflation."""

import hashlib
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "outputs" / "external_validation" / "gse270140"
INPUT = CASE_ROOT / "GSM8335426_JWE03_author_annotated_secondary_root.h5ad"
BUNDLE = CASE_ROOT / "annotation_bundle_srp169576_1024"
PREDICTIONS = BUNDLE / "predictions.csv"
BUNDLE_METADATA = BUNDLE / "annotation_metadata.json"
PREPARATION = ROOT / "release_metadata" / "gse270140_external_input_preparation_v1.json"
MAPPING = ROOT / "release_metadata" / "gse270140_external_label_mapping_v1.tsv"
OUTPUT_JSON = ROOT / "release_metadata" / "gse270140_external_reference_stress_audit_v1.json"
OUTPUT_MARKDOWN = ROOT / "release_metadata" / "gse270140_external_reference_stress_audit_v1.md"
OUTPUT_TABLE = ROOT / "supplementary_tables" / "gse270140_external_reference_per_label_v1.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def native_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): native_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [native_json(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value):
        return None
    return value


def load_case() -> tuple[ad.AnnData, pd.DataFrame, dict[str, Any], dict[str, Any], pd.DataFrame]:
    required = (INPUT, PREDICTIONS, BUNDLE_METADATA, PREPARATION, MAPPING)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing GSE270140 stress-case assets: {', '.join(missing)}")
    adata = ad.read_h5ad(INPUT, backed=None)
    predictions = pd.read_csv(PREDICTIONS, dtype={"cell_id": str})
    bundle_metadata = json.loads(BUNDLE_METADATA.read_text(encoding="utf-8"))
    preparation = json.loads(PREPARATION.read_text(encoding="utf-8"))
    mapping = pd.read_csv(MAPPING, sep="\t", dtype=str).fillna("")
    if predictions["cell_id"].tolist() != adata.obs_names.astype(str).tolist():
        raise ValueError("Prediction ordering does not match the prepared AnnData cell order.")
    if len(predictions) != adata.n_obs or int(bundle_metadata["n_cells"]) != adata.n_obs:
        raise ValueError("Prepared input, prediction table and annotation metadata disagree on cell count.")
    if mapping["source_label"].duplicated().any():
        raise ValueError("Frozen label mapping contains duplicate source labels.")
    if set(adata.obs["expert_annotation_raw"].astype(str)) != set(mapping["source_label"]):
        raise ValueError("Frozen mapping does not cover exactly the author annotation labels.")
    return adata, predictions, bundle_metadata, preparation, mapping


def audit() -> tuple[dict[str, Any], pd.DataFrame]:
    adata, predictions, bundle_metadata, preparation, mapping = load_case()
    input_obs = adata.obs[["cell_id", "expert_annotation_raw"]].copy()
    input_obs["cell_id"] = input_obs["cell_id"].astype(str)
    scored = (
        input_obs.merge(predictions, on="cell_id", how="inner", validate="one_to_one")
        .merge(mapping, left_on="expert_annotation_raw", right_on="source_label", how="left", validate="many_to_one")
        .copy()
    )
    if len(scored) != adata.n_obs or scored["evaluation_tier"].isna().any():
        raise ValueError("Every author annotation must have exactly one frozen mapping row.")
    fine_labels = sorted(set(predictions["fine_label"].astype(str)))
    mapped_labels = sorted(set(mapping.loc[mapping["evaluation_tier"] == "shared_state", "mapped_model_label"]))
    if not set(mapped_labels).issubset(set(fine_labels) | {"Phloem", "Root stele", "Xylem"}):
        raise ValueError("The mapping includes a label absent from the frozen model output ontology.")

    shared = scored[scored["evaluation_tier"] == "shared_state"].copy()
    ood = scored[scored["evaluation_tier"] == "no_direct_model_state"].copy()
    shared_true = shared["mapped_model_label"].astype(str)
    shared_pred = shared["fine_label"].astype(str)
    accuracy = float(accuracy_score(shared_true, shared_pred))
    macro_f1 = float(f1_score(shared_true, shared_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(shared_true, shared_pred, average="weighted", zero_division=0))
    unknown_rejection = float((ood["fine_label"] == "Unknow").mean())
    shared_unknown_rate = float((shared["fine_label"] == "Unknow").mean())
    unknown_precision = float((scored.loc[scored["fine_label"] == "Unknow", "evaluation_tier"] == "no_direct_model_state").mean())
    per_class = precision_recall_fscore_support(
        shared_true,
        shared_pred,
        labels=mapped_labels,
        zero_division=0,
    )
    class_scores = pd.DataFrame(
        {
            "mapped_model_label": mapped_labels,
            "precision": per_class[0],
            "recall": per_class[1],
            "f1": per_class[2],
            "support": per_class[3],
        }
    )
    per_author = (
        scored.groupby(
            ["expert_annotation_raw", "mapped_model_label", "evaluation_tier", "mapping_rationale"],
            as_index=False,
            dropna=False,
        )
        .agg(
            cells=("cell_id", "size"),
            predicted_unknown_fraction=("fine_label", lambda values: float((values == "Unknow").mean())),
            mean_confidence=("fine_confidence", lambda values: float(pd.to_numeric(values).mean())),
        )
        .sort_values("cells", ascending=False, kind="mergesort")
        .reset_index(drop=True)
    )
    per_author["mapped_model_label"] = per_author["mapped_model_label"].replace("", "not_in_frozen_ontology")
    prediction_distribution = (
        scored.groupby("fine_label", as_index=False)
        .agg(cells=("cell_id", "size"), mean_confidence=("fine_confidence", lambda values: float(pd.to_numeric(values).mean())))
        .assign(fraction=lambda frame: frame["cells"] / len(scored))
        .sort_values("cells", ascending=False, kind="mergesort")
        .reset_index(drop=True)
    )
    table = per_author.merge(class_scores, on="mapped_model_label", how="left")
    output_table = OUTPUT_TABLE
    output_table.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_table, sep="\t", index=False)
    checkpoint_path = ROOT / str(bundle_metadata["checkpoint_path"])
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"Recorded checkpoint does not exist for hashing: {checkpoint_path}")
    payload: dict[str, Any] = {
        "schema_version": "plant_cellfm_gse270140_external_reference_stress_audit_v1",
        "case_role": "Author-labelled secondary-root stress test of a frozen root annotation checkpoint.",
        "claim_boundary": (
            "This is not the primary strict leave-species result, not an all-plant accuracy claim and not a matched "
            "third-party benchmark. GSE270140 appears in historical corpus manifests; it is retained as a provenance-aware "
            "post-hoc stress case. Shared-state scoring uses a frozen coarse semantic map, while ontology-external states "
            "remain in a separate rejection audit rather than being deleted from the record."
        ),
        "source": preparation["source"],
        "provenance": {
            "prepared_h5ad": INPUT.relative_to(ROOT).as_posix(),
            "prepared_h5ad_sha256": sha256(INPUT),
            "frozen_mapping": MAPPING.relative_to(ROOT).as_posix(),
            "frozen_mapping_sha256": sha256(MAPPING),
            "prediction_csv": PREDICTIONS.relative_to(ROOT).as_posix(),
            "prediction_csv_sha256": sha256(PREDICTIONS),
            "checkpoint": str(bundle_metadata["checkpoint_path"]),
            "checkpoint_sha256": sha256(checkpoint_path),
        },
        "data": {
            "cells": int(adata.n_obs),
            "genes": int(adata.n_vars),
            "author_annotation_labels": int(adata.obs["expert_annotation_raw"].nunique()),
            "shared_state_cells": int(len(shared)),
            "ontology_external_cells": int(len(ood)),
            "shared_state_fraction": float(len(shared) / len(scored)),
        },
        "shared_state_score": {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "scored_cells": int(len(shared)),
            "evaluation_labels": mapped_labels,
            "interpretation": "Low recovery identifies an out-of-domain secondary-growth failure mode; this score is retained as a diagnostic, not promoted as a generalization headline.",
        },
        "ontology_external_rejection": {
            "cells": int(len(ood)),
            "predicted_unknow_fraction": unknown_rejection,
            "shared_state_predicted_unknow_fraction": shared_unknown_rate,
            "unknow_precision_for_ontology_external_state": unknown_precision,
            "interpretation": "The frozen Unknow head rejects many ontology-external states but also rejects many mapped shared vascular states, showing incomplete calibration for secondary root growth.",
        },
        "per_author_annotation": native_json(per_author.to_dict(orient="records")),
        "per_shared_model_state": native_json(class_scores.to_dict(orient="records")),
        "prediction_distribution": native_json(prediction_distribution.to_dict(orient="records")),
        "supplementary_table": output_table.relative_to(ROOT).as_posix(),
    }
    return native_json(payload), table


def render_markdown(payload: dict[str, Any], table: pd.DataFrame) -> str:
    data = payload["data"]
    shared = payload["shared_state_score"]
    rejection = payload["ontology_external_rejection"]
    lines = [
        "# GSE270140 Secondary-Root Reference Stress Audit",
        "",
        "## Scope and Boundary",
        "",
        f"- Author-labelled input: `{data['cells']}` cells, `{data['genes']}` genes and `{data['author_annotation_labels']}` raw annotations from GSE270140/GSM8335426.",
        "- The frozen mapping is applied before inspecting predictions. It maps compatible vascular states to `Phloem`, `Xylem` or `Root stele`; periderm, myrosin idioblast and lateral-root-primordium states stay explicitly out of the frozen output ontology.",
        "- GSE270140 is present in historical project manifest registration. This is therefore recorded as a provenance-aware stress case, not promoted as an unqualified unseen-data benchmark.",
        "",
        "## Diagnostic Result",
        "",
        f"- Shared-state denominator: `{shared['scored_cells']}` cells ({data['shared_state_fraction']:.1%} of the complete input).",
        f"- Shared-state accuracy / macro-F1: **{shared['accuracy']:.4f} / {shared['macro_f1']:.4f}**.",
        f"- Ontology-external states: `{rejection['cells']}` cells; `Unknow` rejection rate **{rejection['predicted_unknow_fraction']:.1%}**.",
        f"- Mapped shared states also predicted as `Unknow`: **{rejection['shared_state_predicted_unknow_fraction']:.1%}**.",
        "",
        "## Interpretation",
        "",
        "- The frozen root checkpoint does not recover secondary-growth vascular labels sufficiently for a positive external-accuracy claim.",
        "- Its partial `Unknow` response demonstrates a detectable open-set signal, but the high unknown rate on compatible vascular states shows that a secondary-root adapter and a broader developmental ontology are required before this dataset can be used as a validation win.",
        "- This audit is retained to prevent accidental promotion of label-free marker coherence into a substitute for expert-labelled accuracy.",
        "",
        "## Frozen Mapping and Per-label Audit",
        "",
        "| Author annotation | Frozen model state | Tier | Cells | Unknown fraction | Mean confidence | Recall | F1 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in table.itertuples(index=False):
        recall = "" if pd.isna(row.recall) else f"{row.recall:.4f}"
        f1 = "" if pd.isna(row.f1) else f"{row.f1:.4f}"
        lines.append(
            f"| {row.expert_annotation_raw} | {row.mapped_model_label} | {row.evaluation_tier} | {row.cells} | {row.predicted_unknown_fraction:.4f} | {row.mean_confidence:.4f} | {recall} | {f1} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload, table = audit()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MARKDOWN.write_text(render_markdown(payload, table), encoding="utf-8")
    print(
        json.dumps(
            {
                "shared_state_accuracy": payload["shared_state_score"]["accuracy"],
                "shared_state_macro_f1": payload["shared_state_score"]["macro_f1"],
                "ontology_external_unknown_rejection": payload["ontology_external_rejection"]["predicted_unknow_fraction"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
