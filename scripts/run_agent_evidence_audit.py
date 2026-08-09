"""Build selective-risk, calibration and expert-audit evidence for PlantCell-Agent."""

from __future__ import annotations

import json
import hashlib
import argparse
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from snowcell.agent_evidence import (
    align_reference,
    calibration_curve,
    sample_expert_audit,
    score_reference_backed_audit,
    score_completed_expert_audit,
    selective_curve,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release_metadata"
FIG = ROOT / "figures" / "plantcell_agent"
PRIVATE_AUDIT_DIR = ROOT / "outputs" / "internal"


CASES: list[dict[str, Any]] = [
    {
        "case_id": "strict_heldout_3964",
        "label": "Strict held-out 3,964-cell locked bundle",
        "mode": "raw_h5ad_end_to_end_or_locked_bundle",
        "prediction_direct": "outputs/editor_submission_v9/runtime_smoke_predictions_v9.csv",
        "prediction_agent": "outputs/editor_submission_v9/runtime_smoke_predictions_v9.csv",
        "reference": "release_metadata/species_ontology_obs_labels_with_ids_v9.tsv",
        "reference_label": "cell_type",
        "reference_cell_id": "cell_id",
        "reference_sep": "\t",
        "raw_input": "data/external_validation/v9_benchmark_subset_256_shared_genes.h5ad",
    },
    {
        "case_id": "arabidopsis_secondary_root",
        "label": "Arabidopsis secondary root",
        "mode": "agent_replay",
        "prediction_direct": "outputs/agent_replay_v2/arabidopsis/predictions_direct.csv",
        "prediction_agent": "outputs/agent_replay_v2/arabidopsis/predictions.csv",
        "reference": "outputs/external_validation/gse270140/GSM8335426_JWE03_author_annotated_secondary_root.h5ad",
        "reference_label": "expert_annotation_raw",
        "reference_cell_id": "cell_id",
        "raw_input": "outputs/external_validation/gse270140/GSM8335426_JWE03_author_annotated_secondary_root.h5ad",
    },
    {
        "case_id": "wheat_nonoverlap",
        "label": "Wheat root",
        "mode": "agent_replay",
        "prediction_direct": "outputs/agent_replay_v2/wheat/predictions_direct.csv",
        "prediction_agent": "outputs/agent_replay_v2/wheat/predictions.csv",
        "reference": "outputs/external_validation/gse270342/GSE270342_wheat_root_author_annotated_nonoverlap_diagnostic.h5ad",
        "reference_label": "expert_annotation_raw",
        "reference_cell_id": "cell_id",
        "raw_input": "outputs/external_validation/gse270342/GSE270342_wheat_root_author_annotated_nonoverlap_diagnostic.h5ad",
    },
    {
        "case_id": "sorghum_sealed_library",
        "label": "Sorghum root",
        "mode": "agent_replay",
        "prediction_direct": "outputs/agent_replay_v2/sorghum/predictions_direct.csv",
        "prediction_agent": "outputs/agent_replay_v2/sorghum/predictions.csv",
        "reference": "outputs/external_validation/gse297576_bicolor_root/GSE297576_bicolor_root_author_atlas.h5ad",
        "reference_label": "celltype",
        "reference_cell_id": "cell_id",
        "raw_input": "outputs/external_validation/gse297576_bicolor_root/GSE297576_bicolor_root_author_atlas.h5ad",
    },
]


def _path(value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _load_reference(case: dict[str, Any]) -> tuple[pd.DataFrame, bool]:
    path = _path(case["reference"])
    if case.get("reference_sep"):
        return pd.read_csv(path, sep=case["reference_sep"]), _path(case["raw_input"]).exists()
    try:
        import anndata as ad
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("anndata is required for H5AD evidence audit") from exc
    adata = ad.read_h5ad(path, backed="r")
    obs = adata.obs.copy()
    obs.index.name = None
    obs[case["reference_cell_id"]] = (
        obs[case["reference_cell_id"]].astype(str)
        if case["reference_cell_id"] in obs
        else obs.index.astype(str)
    )
    obs[case["reference_label"]] = obs[case["reference_label"]].astype(str)
    return obs, True


def _safe_case(case: dict[str, Any], threshold: float, per_group: int) -> dict[str, Any]:
    direct_path = _path(case["prediction_direct"])
    agent_path = _path(case["prediction_agent"])
    reference_path = _path(case["reference"])
    if not direct_path.exists() or not agent_path.exists() or not reference_path.exists():
        return {
            "case_id": case["case_id"],
            "label": case["label"],
            "status": "NOT_REPLAYED_EVIDENCE_INPUT_MISSING",
            "missing_inputs": [
                str(path)
                for path in (direct_path, agent_path, reference_path)
                if not path.exists()
            ],
            "raw_input_available": _path(case["raw_input"]).exists(),
        }
    reference, raw_input_available = _load_reference(case)
    direct = pd.read_csv(direct_path)
    agent = pd.read_csv(agent_path)
    direct_aligned = align_reference(
        direct, reference, case["reference_label"], case["reference_cell_id"]
    )
    agent_aligned = align_reference(
        agent, reference, case["reference_label"], case["reference_cell_id"]
    )
    direct_curve = selective_curve(direct_aligned, case_id=case["case_id"])
    direct_curve["model_output"] = "direct_baseline"
    agent_curve = selective_curve(agent_aligned, case_id=case["case_id"])
    agent_curve["model_output"] = "agent_output"
    direct_cal, direct_cal_summary = calibration_curve(direct_aligned, case_id=case["case_id"])
    direct_cal["model_output"] = "direct_baseline"
    agent_cal, agent_cal_summary = calibration_curve(agent_aligned, case_id=case["case_id"])
    agent_cal["model_output"] = "agent_output"
    public, key = sample_expert_audit(
        agent_aligned, case["case_id"], threshold=threshold, per_group=per_group
    )
    evidence_mode = "raw_h5ad_end_to_end" if raw_input_available else "locked_bundle_replay"
    return {
        "case_id": case["case_id"],
        "label": case["label"],
        "mode": evidence_mode,
        "status": evidence_mode,
        "raw_input_available": raw_input_available,
        "raw_input_end_to_end": bool(raw_input_available),
        "raw_input_sha256": hashlib.sha256(_path(case["raw_input"]).read_bytes()).hexdigest() if raw_input_available else None,
        "n_matched": int(len(agent_aligned)),
        "direct_agent_label_agreement": float(
            direct_aligned["fine_label"].eq(agent_aligned["fine_label"]).mean()
        ),
        "direct_calibration": direct_cal_summary,
        "agent_calibration": agent_cal_summary,
        "reference_backed_audit": score_reference_backed_audit(
            agent_aligned, case["case_id"], threshold=threshold
        ),
        "direct_curve": direct_curve,
        "agent_curve": agent_curve,
        "direct_calibration_curve": direct_cal,
        "agent_calibration_curve": agent_cal,
        "expert_public": public,
        "expert_key": key,
    }


def _plot(curves: pd.DataFrame, calibration: pd.DataFrame, output: Path) -> None:
    mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})
    cases = list(curves["case_id"].drop_duplicates())
    colors = ["#087f78", "#2878b5", "#d97925", "#7655a6"]
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.5), constrained_layout=True)
    ax = axes[0, 0]
    for case_id, color in zip(cases, colors, strict=False):
        data = curves[(curves.case_id == case_id) & (curves.model_output == "agent_output")]
        ax.plot(data.coverage, data.accepted_accuracy, "o-", color=color, label=case_id)
        base = data[data.policy == "accept_all_baseline"]
        if not base.empty:
            ax.scatter(base.coverage, base.accepted_accuracy, marker="s", color=color, s=34)
    ax.set(xlabel="accepted coverage", ylabel="accepted accuracy", title="Coverage-accuracy")
    ax.set_xlim(0, 1.03)
    ax.set_ylim(0, 1.03)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=6, frameon=False)

    ax = axes[0, 1]
    for case_id, color in zip(cases, colors, strict=False):
        data = curves[(curves.case_id == case_id) & (curves.model_output == "agent_output")]
        ax.plot(data.coverage, data.accepted_risk, "o-", color=color, label=case_id)
    ax.set(xlabel="accepted coverage", ylabel="accepted risk (1 - accuracy)", title="Selective risk")
    ax.set_xlim(0, 1.03)
    ax.set_ylim(0, 1.03)
    ax.grid(alpha=0.25)

    ax = axes[1, 0]
    for case_id, color in zip(cases, colors, strict=False):
        data = calibration[(calibration.case_id == case_id) & (calibration.model_output == "agent_output")]
        data = data[data.n_cells > 0]
        ax.plot(data.mean_confidence, data.observed_accuracy, "o-", color=color, label=case_id)
    ax.plot([0, 1], [0, 1], "--", color="#7c8b94", linewidth=1)
    ax.set(xlabel="mean confidence", ylabel="observed accuracy", title="Confidence calibration")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.25)

    ax = axes[1, 1]
    summary = curves[(curves.policy == "agent_threshold") & (curves.model_output == "agent_output")]
    for case_id, color in zip(cases, colors, strict=False):
        data = summary[summary.case_id == case_id]
        ax.plot(data.threshold, data.error_capture, "o-", color=color, label=case_id)
    ax.set(xlabel="review threshold", ylabel="error captured by review", title="Review triage")
    ax.set_xlim(0.45, 0.95)
    ax.set_ylim(0, 1.03)
    ax.grid(alpha=0.25)
    fig.suptitle("PlantCell-Agent: selective reliability evidence", fontsize=14, fontweight="bold")
    fig.savefig(output, format="svg")
    fig.savefig(output.with_suffix(".pdf"), format="pdf")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expert-completed", type=Path, default=None, help="Completed public blind worksheet TSV")
    parser.add_argument("--reviewer-id", default="", help="External reviewer identifier recorded in the audit payload")
    parser.add_argument("--reviewer-role", default="", help="External reviewer role recorded in the audit payload")
    args = parser.parse_args()
    threshold = 0.70
    per_group = 25
    results: list[dict[str, Any]] = []
    curves: list[pd.DataFrame] = []
    calibration: list[pd.DataFrame] = []
    audit_rows: list[dict[str, Any]] = []
    public_tables: list[pd.DataFrame] = []
    key_tables: list[pd.DataFrame] = []
    for case in CASES:
        result = _safe_case(case, threshold, per_group)
        results.append({key: value for key, value in result.items() if not isinstance(value, pd.DataFrame)})
        if result["status"] == "NOT_REPLAYED_EVIDENCE_INPUT_MISSING":
            continue
        curves.extend([result["direct_curve"], result["agent_curve"]])
        calibration.extend([result["direct_calibration_curve"], result["agent_calibration_curve"]])
        audit_rows.append(result["reference_backed_audit"])
        public_tables.append(result["expert_public"])
        key_tables.append(result["expert_key"])

    # Release gate: the review branch must be empirically risk-enriched at the
    # prespecified threshold in every case included in the evidence package.
    failed_cases = [
        row["case_id"]
        for row in audit_rows
        if row["review_error_rate"] <= row["accepted_error_rate"]
    ]
    if failed_cases:
        raise RuntimeError(
            "review-risk separation failed at threshold 0.70 for: " + ", ".join(failed_cases)
        )

    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    curve_table = pd.concat(curves, ignore_index=True)
    calibration_table = pd.concat(calibration, ignore_index=True)
    curve_table.to_csv(OUT / "plantcell_agent_selective_metrics_v1.tsv", sep="\t", index=False)
    calibration_table.to_csv(OUT / "plantcell_agent_calibration_curve_v1.tsv", sep="\t", index=False)
    pd.DataFrame(audit_rows).to_csv(OUT / "plantcell_agent_reference_audit_v1.tsv", sep="\t", index=False)
    public_template = OUT / "plantcell_agent_expert_audit_template_v2.tsv"
    private_key = PRIVATE_AUDIT_DIR / "plantcell_agent_expert_audit_key_v2.tsv"
    pd.concat(public_tables, ignore_index=True).to_csv(public_template, sep="\t", index=False)
    PRIVATE_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    pd.concat(key_tables, ignore_index=True).to_csv(private_key, sep="\t", index=False)
    independent_audit: dict[str, Any] = {
        "status": "pending_external_expert",
        "completed_worksheet": None,
        "public_template": str(public_template),
        "scoring_key": "outputs/internal/plantcell_agent_expert_audit_key_v2.tsv (not shipped)",
        "reviewer_id": args.reviewer_id or None,
        "reviewer_role": args.reviewer_role or None,
    }
    if args.expert_completed:
        completed_path = args.expert_completed if args.expert_completed.is_absolute() else ROOT / args.expert_completed
        if not completed_path.exists():
            raise FileNotFoundError(completed_path)
        completed = pd.read_csv(completed_path, sep="\t")
        if "reference_label" in completed.columns or "hidden_group" in completed.columns:
            raise ValueError("completed worksheet must remain blinded and cannot include reference_label or hidden_group")
        key = pd.concat(key_tables, ignore_index=True)
        scored = score_completed_expert_audit(completed, key)
        scored.to_csv(OUT / "plantcell_agent_independent_expert_audit_v1.tsv", sep="\t", index=False)
        independent_audit = {
            "status": "completed_external_expert",
            "completed_worksheet": str(completed_path),
            "completed_sha256": hashlib.sha256(completed_path.read_bytes()).hexdigest(),
            "reviewer_id": args.reviewer_id or None,
            "reviewer_role": args.reviewer_role or None,
            "n_rows": int(len(completed)),
            "n_completed_labels": int((completed["expert_label"].fillna("").astype(str).str.strip() != "").sum()),
            "scoring_key": "outputs/internal/plantcell_agent_expert_audit_key_v2.tsv (not shipped)",
        }
    _plot(curve_table, calibration_table, FIG / "plantcell_agent_extended_data_fig2.svg")
    payload = {
        "schema_version": "plantcell_agent_evidence_audit_v1",
        "review_threshold": threshold,
        "expert_sample_per_group": per_group,
        "cases": results,
        "independent_blind_audit": independent_audit,
        "interpretation": {
            "strict_case": "raw_h5ad_end_to_end when raw input exists; otherwise locked_bundle_replay",
            "reference_audit": "author-label reference-backed audit; independent blind expert worksheet is exported separately and scored only when supplied",
            "baseline": "accept_all_baseline retains the complete denominator",
            "agent": "agent_threshold rejects low-confidence or open-set predictions",
        },
    }
    (OUT / "plantcell_agent_evidence_audit_v1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    lines = [
        "# PlantCell-Agent evidence audit v1",
        "",
        "This release separates accept-all direct inference from the Agent threshold policy.",
        "The strict case is marked raw_h5ad_end_to_end only when the manifest H5AD is available; otherwise the report remains a locked 3,964-row prediction/embedding replay.",
        "",
        "## Reference-backed audit",
        "",
        "| Case | n | Accepted n | Coverage | Accepted accuracy | Review accuracy | Accepted error | Review error | Difference |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in audit_rows:
        n_cells = row["accepted_cells"] + row["review_cells"]
        lines.append(
            f"| {row['case_id']} | {n_cells} | {row['accepted_cells']} | "
            f"{row['accepted_cells'] / n_cells:.4f} | {row['accepted_accuracy']:.4f} | {row['review_accuracy']:.4f} | "
            f"{row['accepted_error_rate']:.4f} | {row['review_error_rate']:.4f} | "
            f"{row['review_error_rate_minus_accepted_error_rate']:.4f} |"
        )
    lines.extend(
        [
            "",
            "A positive Difference means the Agent review group has higher reference error than the automatically accepted group.",
            "The public expert worksheet hides the acceptance group and reference label. Independent expert validation is claimed only when a completed blinded worksheet is passed to this script.",
            "",
        ]
    )
    (OUT / "plantcell_agent_evidence_audit_v1.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "cases": results}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
