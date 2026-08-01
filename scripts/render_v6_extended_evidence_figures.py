from __future__ import annotations

"""Render the v6 Extended Data evidence pages that carry hard boundaries.

These figures deliberately keep a negative zero-target result and a partial
third-party comparator visible.  Neither page is allowed to strengthen the
strict leave-species claim or simulate a full fine-tuning comparison.
"""

import json
import sys
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import render_v4_top_journal_figures as base
import render_v6_editorial_core_figures as v6


OUT = ROOT / "figures" / "plant_cellfm_submission_v6"
EXTENDED = OUT / "extended_data"
SOURCE = OUT / "source_data"


def export(fig: plt.Figure, stem: str, tables: dict[str, pd.DataFrame]) -> None:
    EXTENDED.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    base.enforce_minimum_text_size(fig)
    for suffix, options in (("svg", {}), ("pdf", {}), ("png", {"dpi": 350}), ("tiff", {"dpi": 600})):
        fig.savefig(EXTENDED / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)


def normalise_svg_whitespace() -> None:
    """Keep generated vector paths quiet in version control without changing geometry."""
    for path in OUT.rglob("*.svg"):
        content = path.read_text(encoding="utf-8")
        path.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")


def draw_confusion(ax: plt.Axes, matrix: np.ndarray, labels: list[str], title: str, *, color: str) -> None:
    normalised = np.divide(matrix, matrix.sum(axis=1, keepdims=True), out=np.zeros_like(matrix), where=matrix.sum(axis=1, keepdims=True) > 0)
    image = ax.imshow(normalised, cmap=LinearSegmentedColormap.from_list(f"{title}_cmap", ["#F5F8F8", "#C8DEDF", color]), vmin=0, vmax=1, aspect="equal")
    for y in range(normalised.shape[0]):
        for x in range(normalised.shape[1]):
            value = normalised[y, x]
            ax.text(x, y, f"{value:.2f}", ha="center", va="center", fontsize=4.65, color="white" if value >= 0.62 else v6.INK)
    ax.set(xticks=range(len(labels)), xticklabels=labels, yticks=range(len(labels)), yticklabels=labels, xlabel="predicted state", ylabel="true state")
    ax.tick_params(axis="both", labelsize=4.55, length=0, pad=1.4)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title, fontsize=5.45, fontweight="bold", loc="left", pad=5, color=v6.INK)
    return image


def render_ed7_zero_target_transfer() -> None:
    record = json.loads((ROOT / "release_metadata" / "gse270140_to_gse270342_zero_target_transfer_audit_v1.json").read_text(encoding="utf-8"))
    primary = record["results"]["primary_three_state"]
    frozen = primary["source_only_decoders"]["frozen_root_checkpoint"]
    adapter = primary["source_only_decoders"]["gse270140_source_adapter"]
    labels = ["phloem", "stele", "xylem"]
    rows: list[dict[str, object]] = []
    for k in (9, 31, 101):
        for name, bundle in (("Frozen root checkpoint", frozen), ("GSE270140 source adapter", adapter)):
            result = bundle[f"knn_{k}"]
            rows.append(
                {
                    "decoder": f"k={k}",
                    "representation": name,
                    "accuracy": result["accuracy"],
                    "balanced_accuracy": result["balanced_accuracy"],
                    "macro_f1": result["macro_f1"],
                }
            )
    metrics = pd.DataFrame(rows)
    frozen_matrix = np.asarray(frozen["knn_9"]["confusion_matrix_rows_true_columns_predicted"], dtype=float)
    adapter_matrix = np.asarray(adapter["knn_9"]["confusion_matrix_rows_true_columns_predicted"], dtype=float)
    target_counts = pd.DataFrame(
        [{"state": state, "target_cells": primary["target_class_counts"][state], "source_cells": primary["source_class_counts"][state]} for state in labels]
    )

    fig = plt.figure(figsize=(7.25, 5.28))
    grid = fig.add_gridspec(2, 12, height_ratios=(0.82, 1.18), left=0.055, right=0.988, bottom=0.075, top=0.95, hspace=0.78, wspace=0.62)
    ax_a = fig.add_subplot(grid[0, :5])
    ax_b = fig.add_subplot(grid[0, 5:])
    confusion_grid = grid[1, :7].subgridspec(1, 2, wspace=0.55)
    ax_c1 = fig.add_subplot(confusion_grid[0, 0])
    ax_c2 = fig.add_subplot(confusion_grid[0, 1])
    ax_d = fig.add_subplot(grid[1, 7:])

    ax_a.set_axis_off()
    v6.panel(ax_a, "a", "Zero-target labels remain physically separated", "The source-only decoder is written before wheat labels are read for scoring")
    stages = [
        (0.02, "Arabidopsis source", "9,334 cells", v6.BLUE),
        (0.35, "source-only decoder", "kNN only", v6.PURPLE),
        (0.68, "wheat target", "1,020 scored", v6.ORANGE),
    ]
    for x, title, detail, color in stages:
        ax_a.add_patch(Rectangle((x, 0.34), 0.25, 0.35, transform=ax_a.transAxes, facecolor="#F5F8F8", edgecolor=color, linewidth=0.9))
        ax_a.add_patch(Rectangle((x, 0.64), 0.25, 0.05, transform=ax_a.transAxes, facecolor=color, edgecolor="none"))
        ax_a.text(x + 0.125, 0.53, title, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.25, color=v6.INK, fontweight="bold")
        ax_a.text(x + 0.125, 0.42, detail, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, color=v6.MUTED)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((left[0] + 0.257, 0.515), (right[0] - 0.012, 0.515), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=0.75, color=v6.MUTED))
    ax_a.text(0.50, 0.095, "No wheat labels are used for fitting, calibration or decoder selection.", transform=ax_a.transAxes, ha="center", fontsize=4.85, color=v6.RED, fontweight="bold")

    order = ["k=9", "k=31", "k=101"]
    y = np.arange(len(order))
    frozen_values = metrics.loc[metrics.representation.eq("Frozen root checkpoint")].set_index("decoder").loc[order]
    adapter_values = metrics.loc[metrics.representation.eq("GSE270140 source adapter")].set_index("decoder").loc[order]
    ax_b.hlines(y, frozen_values.macro_f1, adapter_values.macro_f1, color="#D7E2E6", lw=2.5, zorder=1)
    ax_b.scatter(frozen_values.macro_f1, y, s=53, color=v6.TEAL, edgecolor="white", linewidth=0.65, zorder=3, label="frozen root checkpoint")
    ax_b.scatter(adapter_values.macro_f1, y, s=53, color=v6.PURPLE, edgecolor="white", linewidth=0.65, zorder=3, label="source adapter")
    for index, (left, right) in enumerate(zip(frozen_values.macro_f1, adapter_values.macro_f1, strict=True)):
        ax_b.text(max(left, right) + 0.006, index, f"{left:.3f} / {right:.3f}", va="center", fontsize=4.9, color=v6.INK)
    ax_b.set(yticks=y, yticklabels=order, xlim=(0.34, 0.46), xlabel="three-state target macro-F1")
    ax_b.tick_params(axis="y", labelsize=5.0, length=0)
    v6.clean(ax_b, "x")
    v6.panel(ax_b, "b", "Source adaptation does not improve zero-target macro-F1", "All kNN decoders retained; teal=frozen and violet=source adapter")

    draw_confusion(ax_c1, frozen_matrix, labels, "Frozen root checkpoint (k=9)", color=v6.TEAL)
    draw_confusion(ax_c2, adapter_matrix, labels, "GSE270140 source adapter (k=9)", color=v6.PURPLE)
    ax_c1.text(-0.32, 1.32, "c", transform=ax_c1.transAxes, fontsize=8.2, fontweight="bold", color=v6.INK)
    ax_c1.text(0.0, 1.32, "Cross-species vascular-state errors remain inspectable", transform=ax_c1.transAxes, fontsize=6.25, fontweight="bold", color=v6.INK)
    ax_c1.text(0.0, 1.235, "Row-normalized three-state confusion; all target classes are retained", transform=ax_c1.transAxes, fontsize=4.8, color=v6.MUTED)

    ax_d.set_axis_off()
    v6.panel(ax_d, "d", "Why the negative result remains", "Retaining the failure prevents a selective cross-species narrative")
    highlights = [
        ("primary k=9", "frozen macro-F1 0.423", v6.TEAL),
        ("source adapter", "macro-F1 0.404", v6.PURPLE),
        ("target balance", "129 phloem / 637 stele / 254 xylem", v6.ORANGE),
        ("scope", "not strict leave-species or independent", v6.RED),
    ]
    for index, (label, detail, color) in enumerate(highlights):
        y0 = 0.78 - index * 0.20
        ax_d.plot([0.03, 0.105], [y0, y0], transform=ax_d.transAxes, color=color, lw=2.8, solid_capstyle="round")
        ax_d.text(0.15, y0 + 0.012, label, transform=ax_d.transAxes, fontsize=4.9, color=v6.MUTED)
        ax_d.text(0.15, y0 - 0.06, detail, transform=ax_d.transAxes, fontsize=4.85, color=v6.INK, fontweight="bold" if label == "scope" else "normal")

    export(
        fig,
        "plant_cellfm_v6_ed_fig7_zero_target_transfer",
        {
            "all_source_only_decoder_metrics": metrics,
            "primary_target_class_counts": target_counts,
            "frozen_k9_confusion": pd.DataFrame(frozen_matrix, index=labels, columns=labels).rename_axis("true_state").reset_index(),
            "source_adapter_k9_confusion": pd.DataFrame(adapter_matrix, index=labels, columns=labels).rename_axis("true_state").reset_index(),
            "claim_boundary": pd.DataFrame(highlights, columns=["scope_field", "value", "colour_role"]),
        },
    )


def render_ed8_scplantllm_reference() -> None:
    record = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_matched_embedding_probe_v1.json").read_text(encoding="utf-8"))
    table_path = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S22_scPlantLLM_GSE270342_matched_embedding_probe.tsv"
    per_class = pd.read_csv(table_path, sep="\t")
    if len(per_class) != 13 or int(per_class.support.sum()) != 1433:
        raise ValueError("The matched scPlantLLM per-class table does not match its locked test contract.")
    per_class = per_class.sort_values("f1", ascending=True, kind="mergesort").reset_index(drop=True)
    metrics = record["metrics"]
    split = record["split_contract"]
    tokens = record["input_contract"]["scplantllm_tokenization"]

    fig = plt.figure(figsize=(7.25, 5.18))
    grid = fig.add_gridspec(2, 12, height_ratios=(0.80, 1.20), left=0.055, right=0.988, bottom=0.075, top=0.95, hspace=0.80, wspace=0.64)
    ax_a = fig.add_subplot(grid[0, :7])
    ax_b = fig.add_subplot(grid[0, 7:])
    ax_c = fig.add_subplot(grid[1, :7])
    ax_d = fig.add_subplot(grid[1, 7:])

    ax_a.set_axis_off()
    v6.panel(ax_a, "a", "A matched frozen scPlantLLM reference is now auditable", "Same GSE270342 object, first-target mapping and exact Plant-CellFM locked test barcodes")
    stages = [
        (0.02, "GSE270342", "7,164 prepared", v6.BLUE),
        (0.27, "orthogroup + vocab", "43,335 mapped", v6.ORANGE),
        (0.52, "frozen encoder", "512-d embeddings", v6.PURPLE),
        (0.77, "centroid readout", "train-only labels", v6.TEAL),
    ]
    for x, title, detail, color in stages:
        ax_a.add_patch(Rectangle((x, 0.35), 0.20, 0.35, transform=ax_a.transAxes, facecolor="#F5F8F8", edgecolor=color, linewidth=0.9))
        ax_a.add_patch(Rectangle((x, 0.65), 0.20, 0.05, transform=ax_a.transAxes, facecolor=color, edgecolor="none"))
        ax_a.text(x + 0.10, 0.53, title, transform=ax_a.transAxes, ha="center", va="center", fontsize=4.95, color=v6.INK, fontweight="bold")
        ax_a.text(x + 0.10, 0.42, detail, transform=ax_a.transAxes, ha="center", va="center", fontsize=4.65, color=v6.MUTED)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((left[0] + 0.207, 0.52), (right[0] - 0.009, 0.52), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=0.75, color=v6.MUTED))
    ax_a.text(0.50, 0.095, "No scPlantLLM fine-tuning occurs; this is a frozen representation readout only.", transform=ax_a.transAxes, ha="center", fontsize=4.85, color=v6.RED, fontweight="bold")

    ax_b.set_axis_off()
    v6.panel(ax_b, "b", "Locked-test reference metrics", "1,433 cells; labels used only to train the centroid on 5,014 training cells")
    metric_rows = [("accuracy", metrics["accuracy"], v6.TEAL), ("macro-F1", metrics["macro_f1"], v6.PURPLE), ("weighted F1", metrics["weighted_f1"], v6.BLUE)]
    for index, (label, value, color) in enumerate(metric_rows):
        y0 = 0.70 - index * 0.22
        ax_b.plot([0.02, 0.13], [y0, y0], transform=ax_b.transAxes, color=color, lw=3.0, solid_capstyle="round")
        ax_b.text(0.18, y0 + 0.015, label, transform=ax_b.transAxes, fontsize=5.15, color=v6.MUTED)
        ax_b.text(0.18, y0 - 0.075, f"{value:.4f}", transform=ax_b.transAxes, fontsize=6.6, color=v6.INK, fontweight="bold")
    ax_b.text(0.02, 0.035, "Checkpoint: 0 missing keys / 0 unexpected keys", transform=ax_b.transAxes, fontsize=4.65, color=v6.MUTED)

    y = np.arange(len(per_class))
    colours = [v6.TEAL if value >= 0.25 else v6.ORANGE for value in per_class.f1]
    ax_c.hlines(y, 0, per_class.f1, color=v6.LIGHT_GREY, lw=2.5, zorder=1)
    ax_c.scatter(per_class.f1, y, s=20 + per_class.support.to_numpy() / 10, color=colours, edgecolor="white", linewidth=0.5, zorder=3)
    for index, row in per_class.iterrows():
        ax_c.text(min(float(row.f1) + 0.014, 0.49), index, f"{row.f1:.2f}", va="center", fontsize=4.75, color=v6.INK)
    ax_c.set(yticks=y, yticklabels=[v6.compact_author_label(value) for value in per_class.author_label], xlim=(0, 0.52), xlabel="frozen scPlantLLM centroid-readout F1")
    ax_c.tick_params(axis="y", labelsize=4.75, length=0, pad=1.0)
    v6.clean(ax_c, "x")
    v6.panel(ax_c, "c", "Per-class behaviour remains visible rather than summarized by one score", "Point area is locked-test support; all 13 author labels are retained")

    ax_d.set_axis_off()
    v6.panel(ax_d, "d", "Comparator boundary", "This closes a matched frozen-reference gap, not the full head-to-head question")
    boundaries = [
        ("shared", "object, mapping and locked test", v6.BLUE),
        ("official", "431 MB official checkpoint", v6.PURPLE),
        ("readout", "centroids fit on train only", v6.TEAL),
        ("not claimed", "fine-tuning superiority", v6.RED),
    ]
    for index, (label, detail, color) in enumerate(boundaries):
        y0 = 0.78 - index * 0.20
        ax_d.plot([0.03, 0.105], [y0, y0], transform=ax_d.transAxes, color=color, lw=2.8, solid_capstyle="round")
        ax_d.text(0.15, y0 + 0.012, label, transform=ax_d.transAxes, fontsize=4.85, color=v6.MUTED)
        ax_d.text(0.15, y0 - 0.06, detail, transform=ax_d.transAxes, fontsize=4.85, color=v6.INK, fontweight="bold" if label == "not claimed" else "normal")

    contracts = pd.DataFrame(
        [
            {"field": "prepared_cells", "value": record["input_contract"]["prepared_cells"]},
            {"field": "mapped_source_genes", "value": record["input_contract"]["orthology"]["first_target_source_genes"]},
            {"field": "train_cells", "value": split["train_cells"]},
            {"field": "validation_cells", "value": split["validation_cells"]},
            {"field": "locked_test_cells", "value": split["locked_test_cells"]},
            {"field": "max_nonpadding_tokens", "value": tokens["selected_nonpadding_tokens_when_available"]},
        ]
    )
    export(
        fig,
        "plant_cellfm_v6_ed_fig8_scplantllm_matched_reference",
        {
            "per_class_locked_test_metrics": per_class,
            "reference_contract": contracts,
            "headline_metrics": pd.DataFrame(metric_rows, columns=["metric", "value", "colour_role"]),
            "claim_boundary": pd.DataFrame(boundaries, columns=["scope_field", "value", "colour_role"]),
        },
    )


def main() -> None:
    v6.setup()
    render_ed7_zero_target_transfer()
    render_ed8_scplantllm_reference()
    normalise_svg_whitespace()
    print(json.dumps({"figure_suite": "v6_extended_evidence", "extended_figures": 2}, ensure_ascii=False))


if __name__ == "__main__":
    main()
