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
    frozen = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_matched_embedding_probe_v1.json").read_text(encoding="utf-8"))
    partial = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_partial_finetune_v1.json").read_text(encoding="utf-8"))
    replay = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_partial_finetune_audit_v1.json").read_text(encoding="utf-8"))
    wheat = json.loads((ROOT / "release_metadata" / "gse270342_wheat_lora_adapter_audit_v1.json").read_text(encoding="utf-8"))
    frozen_table = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S22_scPlantLLM_GSE270342_matched_embedding_probe.tsv"
    partial_table = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S23_scPlantLLM_GSE270342_partial_finetune.tsv"
    frozen_per_class = pd.read_csv(frozen_table, sep="\t").rename(columns={"f1": "f1_frozen", "support": "support_frozen"})
    partial_per_class = pd.read_csv(partial_table, sep="\t").rename(columns={"f1": "f1_partial", "support": "support_partial"})
    per_class = frozen_per_class[["author_label", "f1_frozen", "support_frozen"]].merge(
        partial_per_class[["author_label", "f1_partial", "support_partial"]], on="author_label", how="outer", validate="one_to_one"
    )
    if len(per_class) != 13 or int(per_class.support_frozen.sum()) != 1433 or int(per_class.support_partial.sum()) != 1433:
        raise ValueError("The matched frozen or partial scPlantLLM tables do not match their locked test contract.")
    if replay["state"] != "REPLAY_CONFIRMED":
        raise ValueError("The partial scPlantLLM reference does not have a confirmed replay audit.")
    per_class = per_class.sort_values("f1_partial", ascending=True, kind="mergesort").reset_index(drop=True)
    split = partial["split_contract"]
    tokens = partial["input_contract"]["scplantllm_tokenization"]
    comparison = pd.DataFrame(
        [
            {"method": "scPlantLLM frozen centroid", "accuracy": frozen["metrics"]["accuracy"], "macro_f1": frozen["metrics"]["macro_f1"], "scope": "frozen encoder + train centroid", "colour": v6.GREY},
            {"method": "scPlantLLM partial adaptation", "accuracy": partial["locked_test"]["accuracy"], "macro_f1": partial["locked_test"]["macro_f1"], "scope": "final block + new head", "colour": v6.PURPLE},
            {"method": "Plant-CellFM wheat LoRA", "accuracy": wheat["locked_full_13_class_test"]["accuracy"], "macro_f1": wheat["locked_full_13_class_test"]["macro_f1"], "scope": "wheat-specific LoRA", "colour": v6.TEAL},
        ]
    )

    fig = plt.figure(figsize=(7.25, 5.25))
    grid = fig.add_gridspec(2, 12, height_ratios=(0.80, 1.20), left=0.055, right=0.988, bottom=0.075, top=0.95, hspace=0.80, wspace=0.64)
    ax_a = fig.add_subplot(grid[0, :7])
    ax_b = fig.add_subplot(grid[0, 7:])
    ax_c = fig.add_subplot(grid[1, :7])
    ax_d = fig.add_subplot(grid[1, 7:])

    ax_a.set_axis_off()
    v6.panel(ax_a, "a", "Matched scPlantLLM references now include partial adaptation", "Same GSE270342 object, first-target mapping and exact Plant-CellFM locked test barcodes")
    stages = [
        (0.02, "GSE270342", "7,164 prepared", v6.BLUE),
        (0.27, "orthogroup + vocab", "43,335 mapped", v6.ORANGE),
        (0.52, "official backbone", "6 transformer blocks", v6.PURPLE),
        (0.77, "adapter", "last block + 13-class head", v6.TEAL),
    ]
    for x, title, detail, color in stages:
        ax_a.add_patch(Rectangle((x, 0.35), 0.20, 0.35, transform=ax_a.transAxes, facecolor="#F5F8F8", edgecolor=color, linewidth=0.9))
        ax_a.add_patch(Rectangle((x, 0.65), 0.20, 0.05, transform=ax_a.transAxes, facecolor=color, edgecolor="none"))
        ax_a.text(x + 0.10, 0.53, title, transform=ax_a.transAxes, ha="center", va="center", fontsize=4.95, color=v6.INK, fontweight="bold")
        ax_a.text(x + 0.10, 0.42, detail, transform=ax_a.transAxes, ha="center", va="center", fontsize=4.65, color=v6.MUTED)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((left[0] + 0.207, 0.52), (right[0] - 0.009, 0.52), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=0.75, color=v6.MUTED))
    ax_a.text(0.50, 0.095, "Partial adaptation leaves the first five transformer blocks frozen; best epoch is selected only by validation macro-F1.", transform=ax_a.transAxes, ha="center", fontsize=4.75, color=v6.RED, fontweight="bold")

    y = np.arange(len(comparison))
    ax_b.hlines(y, comparison.macro_f1, comparison.accuracy, color="#D7E2E6", lw=2.5, zorder=1)
    ax_b.scatter(comparison.macro_f1, y, marker="s", s=44, color=comparison.colour.tolist(), edgecolor="white", linewidth=0.55, zorder=3)
    ax_b.scatter(comparison.accuracy, y, s=48, color=comparison.colour.tolist(), edgecolor="white", linewidth=0.55, zorder=4)
    for index, row in comparison.iterrows():
        ax_b.text(max(float(row.accuracy), float(row.macro_f1)) + 0.018, index, f"{row.macro_f1:.3f} / {row.accuracy:.3f}", va="center", fontsize=4.75, color=v6.INK)
    # Keep the method names compact here: panel a carries the full adaptation
    # contract, while short labels preserve a clean boundary between panels.
    ax_b.set(yticks=y, yticklabels=["frozen", "partial", "Plant-CellFM"], xlim=(0.14, 0.74), xlabel="square: macro-F1 | circle: accuracy")
    ax_b.tick_params(axis="y", labelsize=4.75, length=0)
    v6.clean(ax_b, "x")
    v6.panel(ax_b, "b", "One locked test, distinct adaptation scopes", "1,433 cells; values are macro-F1 / accuracy, not a compute-budget-matched ranking")

    y = np.arange(len(per_class))
    ax_c.hlines(y, per_class.f1_frozen, per_class.f1_partial, color="#D7E2E6", lw=2.4, zorder=1)
    ax_c.scatter(per_class.f1_frozen, y, marker="s", s=30, color=v6.GREY, edgecolor="white", linewidth=0.45, zorder=3)
    ax_c.scatter(per_class.f1_partial, y, s=22 + per_class.support_partial.to_numpy() / 10, color=v6.PURPLE, edgecolor="white", linewidth=0.5, zorder=4)
    for index, row in per_class.iterrows():
        ax_c.text(min(max(float(row.f1_frozen), float(row.f1_partial)) + 0.014, 0.87), index, f"{row.f1_frozen:.2f} / {row.f1_partial:.2f}", va="center", fontsize=4.55, color=v6.INK)
    ax_c.set(yticks=y, yticklabels=[v6.compact_author_label(value) for value in per_class.author_label], xlim=(-0.02, 0.90), xlabel="square: frozen centroid F1 | circle: partial-adapter F1")
    ax_c.tick_params(axis="y", labelsize=4.75, length=0, pad=1.0)
    v6.clean(ax_c, "x")
    v6.panel(ax_c, "c", "The partial adapter changes per-class behaviour visibly", "Grey / violet labels show frozen / partial F1; point area is locked-test support")

    ax_d.set_axis_off()
    v6.panel(ax_d, "d", "Comparator boundary", "A matched adaptation reference, not a universal ranking")
    boundaries = [
        ("shared", "object, mapping and locked test", v6.BLUE),
        ("official", "431 MB official checkpoint", v6.PURPLE),
        ("partial", "final block + new head only", v6.TEAL),
        ("not claimed", "full-backbone or compute-matched rank", v6.RED),
    ]
    for index, (label, detail, color) in enumerate(boundaries):
        y0 = 0.78 - index * 0.20
        ax_d.plot([0.03, 0.105], [y0, y0], transform=ax_d.transAxes, color=color, lw=2.8, solid_capstyle="round")
        ax_d.text(0.15, y0 + 0.012, label, transform=ax_d.transAxes, fontsize=4.85, color=v6.MUTED)
        ax_d.text(0.15, y0 - 0.06, detail, transform=ax_d.transAxes, fontsize=4.85, color=v6.INK, fontweight="bold" if label == "not claimed" else "normal")

    contracts = pd.DataFrame(
        [
            {"field": "prepared_cells", "value": partial["input_contract"]["prepared_cells"]},
            {"field": "mapped_source_genes", "value": partial["input_contract"]["orthology"]["first_target_source_genes"]},
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
            "per_class_frozen_and_partial_metrics": per_class,
            "reference_contract": contracts,
            "matched_locked_test_comparison": comparison.drop(columns="colour"),
            "partial_replay_audit": pd.DataFrame([replay["replay"]]),
            "claim_boundary": pd.DataFrame(boundaries, columns=["scope_field", "value", "colour_role"]),
        },
    )


def render_ed8_scplantllm_full_reference() -> None:
    """Render the full-scope continuation of the matched scPlantLLM reference."""
    frozen = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_matched_embedding_probe_v1.json").read_text(encoding="utf-8"))
    partial = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_partial_finetune_v1.json").read_text(encoding="utf-8"))
    partial_replay = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_partial_finetune_audit_v1.json").read_text(encoding="utf-8"))
    full = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_full_finetune_v1.json").read_text(encoding="utf-8"))
    full_replay = json.loads((ROOT / "release_metadata" / "scplantllm_gse270342_full_finetune_audit_v1.json").read_text(encoding="utf-8"))
    wheat = json.loads((ROOT / "release_metadata" / "gse270342_wheat_lora_adapter_audit_v1.json").read_text(encoding="utf-8"))
    table_root = ROOT / "supplementary_tables" / "submission_v4"
    frozen_per_class = pd.read_csv(table_root / "Supplementary_Table_S22_scPlantLLM_GSE270342_matched_embedding_probe.tsv", sep="\t").rename(columns={"f1": "f1_frozen", "support": "support_frozen"})
    partial_per_class = pd.read_csv(table_root / "Supplementary_Table_S23_scPlantLLM_GSE270342_partial_finetune.tsv", sep="\t").rename(columns={"f1": "f1_partial", "support": "support_partial"})
    full_per_class = pd.read_csv(table_root / "Supplementary_Table_S24_scPlantLLM_GSE270342_full_finetune.tsv", sep="\t").rename(columns={"f1": "f1_full", "support": "support_full"})
    per_class = frozen_per_class[["author_label", "f1_frozen", "support_frozen"]].merge(
        partial_per_class[["author_label", "f1_partial", "support_partial"]], on="author_label", how="outer", validate="one_to_one"
    ).merge(full_per_class[["author_label", "f1_full", "support_full"]], on="author_label", how="outer", validate="one_to_one")
    if len(per_class) != 13 or any(int(per_class[column].sum()) != 1433 for column in ("support_frozen", "support_partial", "support_full")):
        raise ValueError("The matched scPlantLLM tables do not match the 1,433-cell locked-test contract.")
    if partial_replay["state"] != "REPLAY_CONFIRMED" or full_replay["state"] != "REPLAY_CONFIRMED":
        raise ValueError("Every adapted scPlantLLM reference requires a confirmed replay audit.")
    per_class = per_class.sort_values("f1_full", ascending=True, kind="mergesort").reset_index(drop=True)
    comparison = pd.DataFrame(
        [
            {"method": "scPlantLLM frozen", "accuracy": frozen["metrics"]["accuracy"], "macro_f1": frozen["metrics"]["macro_f1"], "colour": v6.GREY},
            {"method": "scPlantLLM partial", "accuracy": partial["locked_test"]["accuracy"], "macro_f1": partial["locked_test"]["macro_f1"], "colour": v6.PURPLE},
            {"method": "scPlantLLM full", "accuracy": full["locked_test"]["accuracy"], "macro_f1": full["locked_test"]["macro_f1"], "colour": v6.ORANGE},
            {"method": "Plant-CellFM LoRA", "accuracy": wheat["locked_full_13_class_test"]["accuracy"], "macro_f1": wheat["locked_full_13_class_test"]["macro_f1"], "colour": v6.TEAL},
        ]
    )
    fig = plt.figure(figsize=(7.25, 5.25))
    grid = fig.add_gridspec(2, 12, height_ratios=(0.80, 1.20), left=0.055, right=0.988, bottom=0.075, top=0.95, hspace=0.80, wspace=0.66)
    ax_a = fig.add_subplot(grid[0, :6])
    ax_b = fig.add_subplot(grid[0, 6:])
    ax_c = fig.add_subplot(grid[1, :8])
    ax_d = fig.add_subplot(grid[1, 8:])

    ax_a.set_axis_off()
    v6.panel(ax_a, "a", "One shared object, mapping and locked test", "GSE270342 and 1,433 Plant-CellFM locked test barcodes are held constant")
    stages = [
        (0.02, "author object", "7,164 cells", v6.BLUE),
        (0.27, "orthogroup map", "43,335 genes", v6.ORANGE),
        (0.52, "official model", "six blocks", v6.PURPLE),
        (0.77, "locked test", "1,433 cells", v6.TEAL),
    ]
    for x, title, detail, color in stages:
        ax_a.add_patch(Rectangle((x, 0.35), 0.20, 0.35, transform=ax_a.transAxes, facecolor="#F5F8F8", edgecolor=color, linewidth=0.9))
        ax_a.add_patch(Rectangle((x, 0.65), 0.20, 0.05, transform=ax_a.transAxes, facecolor=color, edgecolor="none"))
        ax_a.text(x + 0.10, 0.53, title, transform=ax_a.transAxes, ha="center", va="center", fontsize=4.95, color=v6.INK, fontweight="bold")
        ax_a.text(x + 0.10, 0.42, detail, transform=ax_a.transAxes, ha="center", va="center", fontsize=4.65, color=v6.MUTED)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((left[0] + 0.207, 0.52), (right[0] - 0.009, 0.52), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=0.75, color=v6.MUTED))
    ax_a.text(0.50, 0.095, "Partial and full runs select epoch on validation macro-F1 only, then replay their locked predictions exactly.", transform=ax_a.transAxes, ha="center", fontsize=4.55, color=v6.RED, fontweight="bold")

    y = np.arange(len(comparison))
    ax_b.hlines(y, comparison.macro_f1, comparison.accuracy, color="#D7E2E6", lw=2.5, zorder=1)
    ax_b.scatter(comparison.macro_f1, y, marker="s", s=44, color=comparison.colour.tolist(), edgecolor="white", linewidth=0.55, zorder=3)
    ax_b.scatter(comparison.accuracy, y, s=48, color=comparison.colour.tolist(), edgecolor="white", linewidth=0.55, zorder=4)
    for index, row in comparison.iterrows():
        ax_b.text(max(float(row.accuracy), float(row.macro_f1)) + 0.018, index, f"{row.macro_f1:.3f} / {row.accuracy:.3f}", va="center", fontsize=4.75, color=v6.INK)
    ax_b.set(yticks=y, yticklabels=["frozen", "partial", "full", "Plant-CellFM"], xlim=(0.14, 0.74), xlabel="square: macro-F1 | circle: accuracy")
    ax_b.tick_params(axis="y", labelsize=4.75, length=0)
    v6.clean(ax_b, "x")
    v6.panel(ax_b, "b", "Full scPlantLLM adaptation improves this same-study reference", "Macro-F1 / accuracy; this is not a compute-budget-matched model rank")

    y = np.arange(len(per_class))
    ax_c.hlines(y, per_class.f1_frozen, per_class.f1_full, color="#D7E2E6", lw=2.4, zorder=1)
    ax_c.scatter(per_class.f1_frozen, y, marker="s", s=30, color=v6.GREY, edgecolor="white", linewidth=0.45, zorder=3)
    ax_c.scatter(per_class.f1_partial, y, marker="D", s=21 + per_class.support_partial.to_numpy() / 11, color=v6.PURPLE, edgecolor="white", linewidth=0.5, zorder=4)
    ax_c.scatter(per_class.f1_full, y, s=20 + per_class.support_full.to_numpy() / 12, color=v6.ORANGE, edgecolor="white", linewidth=0.5, zorder=5)
    ax_c.set(yticks=y, yticklabels=[v6.compact_author_label(value) for value in per_class.author_label], xlim=(-0.02, 0.90), xlabel="square / diamond / circle: frozen / partial / full F1")
    ax_c.tick_params(axis="y", labelsize=4.75, length=0, pad=1.0)
    v6.clean(ax_c, "x")
    v6.panel(ax_c, "c", "Full adaptation changes the per-class profile beyond partial adaptation", "Point area is locked-test support; all 13 author labels and exact F1 values are in source data")

    ax_d.set_axis_off()
    v6.panel(ax_d, "d", "Comparator boundary", "A replayed adaptation reference, not a universal ranking")
    boundaries = [
        ("shared", "object, mapping and locked test", v6.BLUE),
        ("official", "431 MB checkpoint; clean state load", v6.PURPLE),
        ("full", "107.3 M trainable parameters + head", v6.ORANGE),
        ("replay", "partial and full predictions reproduced", v6.TEAL),
        ("not claimed", "independent, strict or compute-matched rank", v6.RED),
    ]
    for index, (label, detail, color) in enumerate(boundaries):
        y0 = 0.80 - index * 0.16
        ax_d.plot([0.03, 0.105], [y0, y0], transform=ax_d.transAxes, color=color, lw=2.8, solid_capstyle="round")
        ax_d.text(0.15, y0 + 0.012, label, transform=ax_d.transAxes, fontsize=4.85, color=v6.MUTED)
        ax_d.text(0.15, y0 - 0.06, detail, transform=ax_d.transAxes, fontsize=4.85, color=v6.INK, fontweight="bold" if label == "not claimed" else "normal")

    split = full["split_contract"]
    tokens = full["input_contract"]["scplantllm_tokenization"]
    contracts = pd.DataFrame(
        [
            {"field": "prepared_cells", "value": full["input_contract"]["prepared_cells"]},
            {"field": "mapped_source_genes", "value": full["input_contract"]["orthology"]["first_target_source_genes"]},
            {"field": "train_cells", "value": split["train_cells"]},
            {"field": "validation_cells", "value": split["validation_cells"]},
            {"field": "locked_test_cells", "value": split["locked_test_cells"]},
            {"field": "max_nonpadding_tokens", "value": tokens["selected_nonpadding_tokens_when_available"]},
            {"field": "full_trainable_parameters", "value": full["model"]["adaptation"]["trainable_parameter_count"]},
            {"field": "full_best_validation_epoch", "value": full["selection"]["best_epoch"]},
        ]
    )
    export(
        fig,
        "plant_cellfm_v6_ed_fig8_scplantllm_matched_reference",
        {
            "per_class_frozen_partial_full_metrics": per_class,
            "reference_contract": contracts,
            "matched_locked_test_comparison": comparison.drop(columns="colour"),
            "partial_replay_audit": pd.DataFrame([partial_replay["replay"]]),
            "full_replay_audit": pd.DataFrame([full_replay["replay"]]),
            "claim_boundary": pd.DataFrame(boundaries, columns=["scope_field", "value", "colour_role"]),
        },
    )
    source_root = ROOT / "figures" / "plant_cellfm_submission_v6" / "source_data"
    for obsolete in (
        "plant_cellfm_v6_ed_fig8_scplantllm_matched_reference_headline_metrics.tsv",
        "plant_cellfm_v6_ed_fig8_scplantllm_matched_reference_per_class_frozen_and_partial_metrics.tsv",
        "plant_cellfm_v6_ed_fig8_scplantllm_matched_reference_per_class_locked_test_metrics.tsv",
    ):
        (source_root / obsolete).unlink(missing_ok=True)


def main() -> None:
    v6.setup()
    render_ed7_zero_target_transfer()
    render_ed8_scplantllm_full_reference()
    normalise_svg_whitespace()
    print(json.dumps({"figure_suite": "v6_extended_evidence", "extended_figures": 2}, ensure_ascii=False))


if __name__ == "__main__":
    main()
