"""Evidence analyses for PlantCell-Agent selective annotation."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd

from .agent_tools import OPEN_SET_LABELS


def align_reference(
    predictions: pd.DataFrame,
    reference: pd.DataFrame,
    reference_label: str,
    reference_cell_id: str = "cell_id",
) -> pd.DataFrame:
    """Align predictions and reference labels with a one-to-one cell contract."""

    required = {"cell_id", "fine_label", "fine_confidence"}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"prediction table missing columns: {sorted(missing)}")
    if reference_cell_id not in reference.columns or reference_label not in reference.columns:
        raise ValueError(f"reference table requires {reference_cell_id} and {reference_label}")
    pred = predictions.copy()
    pred["cell_id"] = pred["cell_id"].astype(str)
    ref = reference[[reference_cell_id, reference_label]].copy()
    ref = ref.rename(columns={reference_cell_id: "cell_id", reference_label: "reference_label"})
    ref["cell_id"] = ref["cell_id"].astype(str)
    if pred["cell_id"].duplicated().any() or ref["cell_id"].duplicated().any():
        raise ValueError("cell_id must be unique in both prediction and reference tables")
    merged = ref.merge(pred, on="cell_id", how="inner", validate="one_to_one")
    if merged.empty:
        raise ValueError("prediction and reference tables have no overlapping cell IDs")
    merged["reference_label"] = merged["reference_label"].fillna("unknown").astype(str)
    merged["fine_label"] = merged["fine_label"].fillna("unknown").astype(str)
    merged["fine_confidence"] = (
        pd.to_numeric(merged["fine_confidence"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
    )
    merged["correct"] = merged["fine_label"].eq(merged["reference_label"])
    merged["open_set"] = merged["fine_label"].str.lower().isin(OPEN_SET_LABELS)
    return merged


def selective_curve(
    aligned: pd.DataFrame,
    thresholds: Iterable[float] = (0.5, 0.6, 0.7, 0.8, 0.9),
    case_id: str = "case",
) -> pd.DataFrame:
    """Return accept-all and Agent threshold profiles for one aligned case."""

    if aligned.empty:
        raise ValueError("aligned table is empty")
    correct = aligned["correct"].astype(bool).to_numpy()
    confidence = aligned["fine_confidence"].to_numpy(dtype=float)
    open_set = aligned["open_set"].astype(bool).to_numpy()
    rows: list[dict[str, Any]] = []

    def add_row(policy: str, threshold: float | None, accepted: np.ndarray) -> None:
        review = ~accepted
        accepted_n = int(accepted.sum())
        review_n = int(review.sum())
        total_errors = int((~correct).sum())
        rows.append(
            {
                "case_id": case_id,
                "policy": policy,
                "threshold": threshold,
                "n_cells": int(len(aligned)),
                "accepted_cells": accepted_n,
                "review_cells": review_n,
                "coverage": float(accepted.mean()),
                "all_cell_accuracy": float(correct.mean()),
                "accepted_accuracy": float(correct[accepted].mean()) if accepted_n else 0.0,
                "accepted_risk": float((~correct[accepted]).mean()) if accepted_n else 1.0,
                "review_accuracy": float(correct[review].mean()) if review_n else 0.0,
                "review_risk": float((~correct[review]).mean()) if review_n else 0.0,
                "error_capture": float((~correct[review]).sum() / total_errors) if total_errors else 0.0,
                "open_set_capture": float(open_set[review].sum() / open_set.sum()) if open_set.any() else 0.0,
                "accepted_mean_confidence": float(confidence[accepted].mean()) if accepted_n else 0.0,
            }
        )

    add_row("accept_all_baseline", None, np.ones(len(aligned), dtype=bool))
    for threshold in thresholds:
        threshold_value = float(threshold)
        accepted = (confidence >= threshold_value) & ~open_set
        add_row("agent_threshold", threshold_value, accepted)
    return pd.DataFrame(rows)


def calibration_curve(
    aligned: pd.DataFrame,
    bins: int = 10,
    case_id: str = "case",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compute confidence reliability bins and expected calibration error."""

    if aligned.empty:
        raise ValueError("aligned table is empty")
    confidence = aligned["fine_confidence"].to_numpy(dtype=float)
    correct = aligned["correct"].astype(bool).to_numpy()
    edges = np.linspace(0.0, 1.0, bins + 1)
    bin_index = np.minimum(np.digitize(confidence, edges[1:-1], right=False), bins - 1)
    rows: list[dict[str, Any]] = []
    ece = 0.0
    for index in range(bins):
        mask = bin_index == index
        n = int(mask.sum())
        mean_confidence = float(confidence[mask].mean()) if n else 0.0
        observed_accuracy = float(correct[mask].mean()) if n else 0.0
        gap = abs(mean_confidence - observed_accuracy) if n else 0.0
        ece += (n / len(aligned)) * gap
        rows.append(
            {
                "case_id": case_id,
                "bin": index,
                "bin_lower": float(edges[index]),
                "bin_upper": float(edges[index + 1]),
                "n_cells": n,
                "mean_confidence": mean_confidence,
                "observed_accuracy": observed_accuracy,
                "absolute_gap": gap,
            }
        )
    return pd.DataFrame(rows), {
        "case_id": case_id,
        "n_cells": int(len(aligned)),
        "expected_calibration_error": float(ece),
        "mean_confidence": float(confidence.mean()),
        "observed_accuracy": float(correct.mean()),
    }


def sample_expert_audit(
    aligned: pd.DataFrame,
    case_id: str,
    threshold: float = 0.70,
    per_group: int = 20,
    seed: int = 20260809,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create a blinded audit sheet and a keyed reference sheet.

    The public sheet hides the Agent acceptance group and reference label. The
    keyed sheet is retained for scoring after an expert completes the public
    sheet. Existing author labels can be used for a reference-backed audit, but
    they are never written into the blinded worksheet.
    """

    rng = np.random.default_rng(seed)
    work = aligned.copy()
    work["hidden_group"] = np.where(
        (work["fine_confidence"] >= threshold) & ~work["open_set"], "accepted", "review"
    )
    samples: list[pd.DataFrame] = []
    for group in ("accepted", "review"):
        subset = work[work["hidden_group"] == group]
        if subset.empty:
            continue
        count = min(per_group, len(subset))
        indices = rng.choice(len(subset), size=count, replace=False)
        samples.append(subset.iloc[np.sort(indices)].copy())
    if not samples:
        raise ValueError("no cells available for expert audit sampling")
    sampled = pd.concat(samples, ignore_index=True)
    sampled.insert(0, "audit_id", [f"{case_id}_audit_{i:04d}" for i in range(len(sampled))])
    public = sampled[["audit_id", "cell_id", "fine_label"]].rename(
        columns={"fine_label": "agent_label"}
    )
    public["expert_label"] = ""
    public["expert_confidence"] = ""
    public["expert_decision"] = ""
    public["expert_notes"] = ""
    key = sampled[
        ["audit_id", "cell_id", "hidden_group", "reference_label", "fine_label", "fine_confidence", "correct"]
    ].rename(columns={"fine_label": "agent_label", "correct": "agent_correct"})
    return public, key


def score_reference_backed_audit(
    aligned: pd.DataFrame,
    case_id: str,
    threshold: float = 0.70,
) -> dict[str, Any]:
    """Score accepted versus review cells against author/reference labels."""

    group = np.where(
        (aligned["fine_confidence"] >= threshold) & ~aligned["open_set"], "accepted", "review"
    )
    rows: dict[str, Any] = {"case_id": case_id, "threshold": float(threshold)}
    for name in ("accepted", "review"):
        mask = group == name
        rows[f"{name}_cells"] = int(mask.sum())
        rows[f"{name}_accuracy"] = float(aligned.loc[mask, "correct"].mean()) if mask.any() else None
        rows[f"{name}_error_rate"] = float((~aligned.loc[mask, "correct"]).mean()) if mask.any() else None
    rows["review_error_rate_minus_accepted_error_rate"] = float(
        rows["review_error_rate"] - rows["accepted_error_rate"]
    )
    rows["reference_type"] = "author_label_reference_not_independent_blind_review"
    return rows


def score_completed_expert_audit(
    completed: pd.DataFrame,
    key: pd.DataFrame,
    expert_label_column: str = "expert_label",
) -> pd.DataFrame:
    """Score a completed worksheet against the hidden group and reference key."""

    if expert_label_column not in completed.columns:
        raise ValueError(f"completed worksheet requires {expert_label_column}")
    merged = key.merge(
        completed[["audit_id", expert_label_column]], on="audit_id", how="inner", validate="one_to_one"
    )
    merged[expert_label_column] = merged[expert_label_column].fillna("").astype(str)
    merged["expert_label_matches_reference"] = (
        merged[expert_label_column] != ""
    ) & merged[expert_label_column].eq(merged["reference_label"])
    merged["expert_label_matches_agent"] = (
        merged[expert_label_column] != ""
    ) & merged[expert_label_column].eq(merged["agent_label"])
    summary = (
        merged.groupby("hidden_group", sort=True)
        .agg(
            n_completed=(expert_label_column, lambda values: int((values != "").sum())),
            expert_reference_accuracy=("expert_label_matches_reference", "mean"),
            expert_agent_agreement=("expert_label_matches_agent", "mean"),
            agent_reference_accuracy=("agent_correct", "mean"),
        )
        .reset_index()
    )
    return summary
