from __future__ import annotations

"""Render the Plant-CellFM v5 evidence-first submission figure suite.

The v5 suite is a compositional rebuild, not a numerical refresh.  It keeps
the frozen v17/v18/few-shot records unchanged and gives each main figure one
claim: data contract, strict transfer, target adaptation, or external blind
root inference.  The final external-root panel deliberately does not use a
label-free input to imply an accuracy result.
"""

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import umap
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, Rectangle

import render_v4_top_journal_figures as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "plant_cellfm_submission_v5"
MAIN = OUT / "main"
EXTENDED = OUT / "extended_data"
SOURCE = OUT / "source_data"
PROFILE = ROOT / "figure_data" / "corpus_profile_v1"
INK = "#17232D"
MUTED = "#61778A"
GRID = "#D9E4E9"
TEAL = "#007C83"
TEAL_PALE = "#B9DFDC"
BLUE = "#2E6FAD"
ORANGE = "#D97524"
PURPLE = "#8064A7"
RED = "#B34D5B"
GREY = "#9CAAB2"
LIGHT_GREY = "#E8EFF2"


def setup() -> None:
    mpl.rcParams.update(
        {
            "font.family": "Arial",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 6.4,
            "axes.labelcolor": INK,
            "axes.edgecolor": INK,
            "axes.linewidth": 0.62,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.major.width": 0.5,
            "ytick.major.width": 0.5,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )
    for directory in (MAIN, EXTENDED, SOURCE):
        directory.mkdir(parents=True, exist_ok=True)


def clean(ax: plt.Axes, grid: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.55, zorder=0)
    ax.tick_params(length=2.1, pad=2)


def panel(ax: plt.Axes, letter: str, title: str, subtitle: str | None = None) -> None:
    if letter:
        ax.text(-0.065, 1.065, letter, transform=ax.transAxes, fontsize=7.6, fontweight="bold", va="bottom")
    ax.text(0, 1.065, title, transform=ax.transAxes, fontsize=6.55, fontweight="bold", va="bottom", color=INK)
    if subtitle:
        ax.text(0, 1.012, subtitle, transform=ax.transAxes, fontsize=5.15, color=MUTED, va="bottom")


def short_species(value: str) -> str:
    parts = str(value).split()
    return f"{parts[0][0]}. {parts[1]}" if len(parts) == 2 else str(value)


def export(fig: plt.Figure, directory: Path, stem: str, tables: dict[str, pd.DataFrame]) -> None:
    for name, frame in tables.items():
        frame.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    base.enforce_minimum_text_size(fig)
    for suffix, kwargs in (("svg", {}), ("pdf", {}), ("png", {"dpi": 350}), ("tiff", {"dpi": 600})):
        fig.savefig(directory / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **kwargs)
    plt.close(fig)


def scatter_categories(
    ax: plt.Axes,
    frame: pd.DataFrame,
    column: str,
    palette: dict[str, str],
    *,
    size: float = 3.0,
    alpha: float = 0.76,
    legend_columns: int = 2,
    legend_size: float = 4.15,
) -> list[str]:
    categories = frame[column].value_counts().index.tolist()
    for category in categories:
        subset = frame.loc[frame[column].eq(category)]
        ax.scatter(
            subset.UMAP1,
            subset.UMAP2,
            s=size,
            color=palette.get(str(category), GREY),
            linewidth=0,
            alpha=alpha,
            label=str(category).replace("_", " "),
            rasterized=True,
        )
    ax.set(xticks=[], yticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(-0.02, -0.19),
        ncol=legend_columns,
        fontsize=legend_size,
        frameon=False,
        columnspacing=0.62,
        handletextpad=0.22,
        labelspacing=0.15,
        markerscale=1.1,
    )
    return categories


def render_fig1(frame: pd.DataFrame) -> None:
    profile = json.loads((PROFILE / "corpus_profile.json").read_text(encoding="utf-8"))
    corpus_species = pd.read_csv(PROFILE / "species_by_tissue.tsv", sep="\t")
    species_total = corpus_species.groupby("species", as_index=False).cells.sum().sort_values("cells", ascending=True)
    organ_total = frame.organ.value_counts().rename_axis("organ").reset_index(name="cells")
    matrix = (
        corpus_species.pivot_table(index="species", columns="tissue", values="cells", aggfunc="sum", fill_value=0)
        .sort_index()
    )

    fig = plt.figure(figsize=(7.25, 5.45))
    grid = fig.add_gridspec(
        2,
        6,
        width_ratios=(1.25, 1.25, 1.25, 1.25, 1.04, 1.04),
        height_ratios=(1.05, 0.95),
        left=0.055,
        right=0.988,
        bottom=0.075,
        top=0.95,
        wspace=0.48,
        hspace=0.68,
    )
    ax_a = fig.add_subplot(grid[0, :2])
    ax_b = fig.add_subplot(grid[0, 2:4])
    right_grid = grid[0, 4:].subgridspec(2, 1, hspace=0.64)
    ax_c1 = fig.add_subplot(right_grid[0, 0])
    ax_c2 = fig.add_subplot(right_grid[1, 0])
    ax_d = fig.add_subplot(grid[1, :3])
    ax_e = fig.add_subplot(grid[1, 3:])

    scatter_categories(ax_a, frame, "species", base.SPECIES, size=3.4, legend_columns=2, legend_size=5.0)
    panel(ax_a, "a", "Shared evaluation embedding", "3,964 cells across eight held-out species")

    ontology_order = list(base.ONTOLOGY)
    ontology_view = frame.copy()
    ontology_view["ontology_display"] = ontology_view.ontology.where(
        ontology_view.ontology.isin(ontology_order[:-1]), "other"
    )
    scatter_categories(
        ax_b,
        ontology_view,
        "ontology_display",
        {**base.ONTOLOGY, "other": "#CBD5D8"},
        size=3.4,
        legend_columns=2,
        legend_size=5.0,
    )
    panel(ax_b, "b", "Ontology states in the same coordinates", "State structure is separated from species identity")

    y = np.arange(len(species_total))
    ax_c1.barh(y, species_total.cells / 1000, color=[base.SPECIES.get(s, GREY) for s in species_total.species], height=0.58)
    ax_c1.set(yticks=y, yticklabels=[short_species(s) for s in species_total.species], xlabel="corpus cells (thousands)")
    ax_c1.tick_params(axis="y", labelsize=5.0, length=0)
    clean(ax_c1, "x")
    panel(ax_c1, "c", "Frozen corpus profile")

    organ_order = ["leaf", "root", "shoot_apex", "callus"]
    organ_total = organ_total.set_index("organ").reindex(organ_order).fillna(0).reset_index()
    colors = {"leaf": TEAL, "root": BLUE, "shoot_apex": ORANGE, "callus": PURPLE}
    ax_c2.barh(np.arange(len(organ_total)), organ_total.cells, color=[colors[o] for o in organ_total.organ], height=0.58)
    ax_c2.set(yticks=np.arange(len(organ_total)), yticklabels=[o.replace("_", " ") for o in organ_total.organ], xlabel="strict-panel cells")
    ax_c2.tick_params(axis="y", labelsize=5.0, length=0)
    clean(ax_c2, "x")

    values = matrix.to_numpy(dtype=float)
    image = ax_d.imshow(np.log10(values + 1), aspect="auto", cmap=LinearSegmentedColormap.from_list("corpus", ["#F4F7F8", "#B8DBDC", TEAL]))
    for yi, species in enumerate(matrix.index):
        for xi, tissue in enumerate(matrix.columns):
            value = int(matrix.loc[species, tissue])
            if value:
                ax_d.text(xi, yi, f"{value // 1000}k" if value >= 1000 else str(value), ha="center", va="center", fontsize=5.0, color="white" if value > values.max() * 0.45 else INK)
    ax_d.set(xticks=range(len(matrix.columns)), xticklabels=[str(v).replace("_", " ") for v in matrix.columns], yticks=range(len(matrix.index)), yticklabels=[short_species(s) for s in matrix.index])
    ax_d.tick_params(length=0, labelsize=5.0)
    for spine in ax_d.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_d, fraction=0.026, pad=0.02)
    colorbar.set_label("log10(cells + 1)", size=4.65)
    colorbar.ax.tick_params(labelsize=5.0, length=1.3)
    panel(ax_d, "d", "Training data are distributed across species and organs", "Each cell reports the traceable frozen corpus, not a historical catalogue entry")

    ax_e.set_axis_off()
    panel(ax_e, "e", "A protocol-aware annotation contract", "The model records assumptions that change the meaning of an annotation result")
    stages = [
        (0.02, "gene IDs", "exact IDs or\northolog map", BLUE),
        (0.265, "encoder", "256-dimensional\ncell embedding", TEAL),
        (0.51, "evidence gate", "coverage and\nopen-set state", ORANGE),
        (0.755, "output", "hierarchy, markers\nand adapter record", PURPLE),
    ]
    for x, head, sub, color in stages:
        ax_e.add_patch(Rectangle((x, 0.24), 0.19, 0.45, transform=ax_e.transAxes, facecolor="#F4F7F8", edgecolor=color, linewidth=0.85, clip_on=False))
        ax_e.add_patch(Rectangle((x, 0.62), 0.19, 0.07, transform=ax_e.transAxes, facecolor=color, edgecolor=color, linewidth=0, clip_on=False))
        ax_e.text(x + 0.095, 0.52, head, transform=ax_e.transAxes, ha="center", va="center", fontsize=5.35, fontweight="bold", color=INK)
        ax_e.text(x + 0.095, 0.34, sub, transform=ax_e.transAxes, ha="center", va="center", fontsize=5.0, color=MUTED)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_e.add_patch(FancyArrowPatch((left[0] + 0.195, 0.465), (right[0] - 0.012, 0.465), transform=ax_e.transAxes, arrowstyle="-|>", mutation_scale=7, lw=0.7, color=MUTED))
    ax_e.text(0.5, 0.06, "The frozen profile, inner-fold choice, target support and deployment head are never presented as one metric.", transform=ax_e.transAxes, ha="center", fontsize=5.0, color=RED)

    export(
        fig,
        MAIN,
        "plant_cellfm_v5_fig1_foundation_contract",
        {
            "cell_embedding": frame[["cell_id", "species", "organ", "truth_label", "ontology", "UMAP1", "UMAP2"]],
            "corpus_species_by_tissue": corpus_species,
            "corpus_species_totals": species_total,
            "strict_panel_organ_totals": organ_total,
            "annotation_contract": pd.DataFrame({"stage": [row[1] for row in stages], "recorded_property": [row[2].replace("\n", " ") for row in stages]}),
        },
    )


def render_fig2(frame: pd.DataFrame, v17: pd.DataFrame) -> None:
    focus = frame.loc[frame.species.eq("Catharanthus roseus")].copy()
    labels = sorted(set(focus.truth_label.astype(str)).union(set(focus.strict_prediction.astype(str))))
    colors = [TEAL, ORANGE, PURPLE, BLUE, RED, "#7A9E2F", "#7F8C8D", "#D8A000", "#5D88B4", "#A76D99"]
    focus_palette = {label: colors[index % len(colors)] for index, label in enumerate(labels)}
    bootstrap = base.bootstrap(frame, iterations=3000)
    low, high = bootstrap.all_cell_accuracy.quantile([0.025, 0.975]).tolist()
    records = v17.sort_values("accuracy_all", ascending=True).reset_index(drop=True)
    strict = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))["summary"]

    fig = plt.figure(figsize=(7.25, 5.58))
    grid = fig.add_gridspec(2, 6, width_ratios=(1, 1, 1, 1, 1.08, 1.08), height_ratios=(0.94, 1.06), left=0.055, right=0.988, bottom=0.085, top=0.95, wspace=0.48, hspace=0.78)
    ax_a = fig.add_subplot(grid[0, :2])
    ax_b = fig.add_subplot(grid[0, 2:4])
    ax_c = fig.add_subplot(grid[0, 4:])
    ax_d = fig.add_subplot(grid[1, :4])
    ax_e = fig.add_subplot(grid[1, 4:])

    for label in labels:
        subset = focus.loc[focus.truth_label.eq(label)]
        if len(subset):
            ax_a.scatter(subset.UMAP1, subset.UMAP2, s=6.2, color=focus_palette[label], linewidth=0, alpha=0.82, label=label, rasterized=True)
    ax_a.set(xticks=[], yticks=[])
    for spine in ax_a.spines.values():
        spine.set_visible(False)
    ax_a.legend(loc="lower left", bbox_to_anchor=(-0.04, -0.36), ncol=2, fontsize=5.0, frameon=False, columnspacing=0.58, handletextpad=0.20, labelspacing=0.20, markerscale=1.0)
    panel(ax_a, "a", "Held-out reference identities", "C. roseus: 256 leaf cells")

    for label in labels:
        subset = focus.loc[focus.strict_prediction.eq(label)]
        if len(subset):
            ax_b.scatter(subset.UMAP1, subset.UMAP2, s=6.2, color=focus_palette[label], linewidth=0, alpha=0.82, rasterized=True)
    ax_b.set(xticks=[], yticks=[])
    for spine in ax_b.spines.values():
        spine.set_visible(False)
    panel(ax_b, "b", "Strict zero-shot outputs", "Target labels never enter fitting or inner-fold selection")
    ax_b.text(0.98, 0.025, f"all-cell\n{(focus.truth_label == focus.strict_prediction).mean():.1%}", transform=ax_b.transAxes, ha="right", va="bottom", fontsize=5.2, fontweight="bold")

    ax_c.set_axis_off()
    panel(ax_c, "c", "Primary denominator remains intact", "A coverage-aware report keeps open-set cells visible")
    stages = [
        ("all test cells", int(strict["n_test"]), GREY),
        ("source-label\ncovered", int(strict["n_evaluable"]), TEAL),
        ("open-set or\nunavailable", int(strict["open_set_cells"]), ORANGE),
    ]
    max_cells = max(value for _, value, _ in stages)
    for yi, (label, value, color) in enumerate(stages):
        ax_c.add_patch(Rectangle((0.04, 0.71 - yi * 0.23), 0.70 * value / max_cells, 0.11, transform=ax_c.transAxes, facecolor=color, edgecolor="none"))
        ax_c.text(0.04, 0.84 - yi * 0.23, label, transform=ax_c.transAxes, fontsize=5.0, color=MUTED, va="bottom")
        ax_c.text(0.78, 0.765 - yi * 0.23, f"{value:,}", transform=ax_c.transAxes, fontsize=5.6, fontweight="bold", va="center")
    ax_c.text(0.04, 0.08, f"v17 all-cell accuracy 39.96%\nbootstrap central 95% interval {low:.3f}-{high:.3f}", transform=ax_c.transAxes, fontsize=5.0, color=INK)

    y = np.arange(len(records))
    ax_d.hlines(y, records.accuracy_all, records.accuracy, color="#DDE6E9", lw=2.1, zorder=1)
    ax_d.scatter(records.accuracy_all, y, color=TEAL, s=34, zorder=3, label="all cells")
    ax_d.scatter(records.accuracy, y, color=BLUE, s=34, zorder=3, label="covered labels")
    ax_d.scatter(records.coverage, y, color=ORANGE, marker="s", s=31, zorder=3, label="coverage")
    ax_d.set(yticks=y, yticklabels=[short_species(value) for value in records.held_out_species], xlim=(-0.03, 1.05), xlabel="fraction of held-out cells")
    ax_d.tick_params(axis="y", labelsize=5.0)
    clean(ax_d, "x")
    panel(ax_d, "d", "Strict transfer is heterogeneous across all eight held-out species", "Teal: all-cell accuracy; blue: conditional accuracy; orange: source-label coverage")

    innovation = json.loads((ROOT / "release_metadata" / "algorithm_innovation_v14.json").read_text(encoding="utf-8"))["metrics"]
    method_rows = [
        ("centroid baseline", innovation["centroid_baseline"], GREY),
        ("expression STC", innovation["v10_expression_stc"], BLUE),
        ("neural STC", innovation["v13_neural_stc"], PURPLE),
        ("context-aware gate", innovation["v14_context_aware_stc"], TEAL),
    ]
    method_table = pd.DataFrame(
        [
            {
                "method": name,
                "all_cell_accuracy": values["all_cell_accuracy"],
                "known_label_accuracy": values["known_label_accuracy"],
                "known_label_macro_f1": values["known_label_macro_f1"],
                "coverage": values["coverage"],
            }
            for name, values, _ in method_rows
        ]
    )
    y = np.arange(len(method_rows))
    for index, (name, values, color) in enumerate(method_rows):
        ax_e.hlines(index, 0, values["all_cell_accuracy"], color=LIGHT_GREY, lw=2.0, zorder=1)
        ax_e.scatter(values["all_cell_accuracy"], index, s=34, color=color, edgecolor="white", linewidth=.55, zorder=3)
        ax_e.text(values["all_cell_accuracy"] + .012, index, f"{values['all_cell_accuracy']:.1%}", va="center", fontsize=5.0, fontweight="bold" if index == len(method_rows) - 1 else "normal")
    method_display = ["centroid", "expression", "neural", "context gate"]
    ax_e.set(yticks=y, yticklabels=method_display, xlim=(-.015, .50), xlabel="all-cell accuracy")
    ax_e.tick_params(axis="y", labelsize=5.0, pad=1.3, length=0)
    clean(ax_e, "x")
    panel(ax_e, "e", "Context-aware calibration improves the frozen transfer panel", "Same cells and 55.90% coverage; global sensitivity analysis, not the nested primary result")
    best = method_rows[-1][1]
    gain = best["all_cell_accuracy"] - method_rows[0][1]["all_cell_accuracy"]
    ax_e.text(.99, .06, f"+{gain:.1%} vs centroid\nknown-label accuracy {best['known_label_accuracy']:.1%}", transform=ax_e.transAxes, ha="right", va="bottom", fontsize=5.0, color=TEAL)

    export(
        fig,
        MAIN,
        "plant_cellfm_v5_fig2_strict_transfer",
        {
            "focus_reference_and_predictions": focus[["cell_id", "truth_label", "strict_prediction", "covered_by_train_labels", "UMAP1", "UMAP2"]],
            "v17_species_metrics": v17,
            "all_cell_bootstrap": bootstrap,
            "strict_denominator": pd.DataFrame({"stage": [row[0].replace("\n", " ") for row in stages], "cells": [row[1] for row in stages]}),
            "context_stc_methods": method_table,
        },
    )


def render_fig3() -> None:
    draws, species_draws = base.fewshot_tables()
    budgets = sorted(draws.support_per_species.unique().tolist())
    macro = draws.groupby("support_per_species", as_index=False).agg(mean=("macro_f1_query", "mean"), sd=("macro_f1_query", "std"))
    mean_species = species_draws.groupby(["species", "support_per_species"], as_index=False).agg(accuracy=("accuracy_all_query", "mean"))
    species_order = sorted(mean_species.species.unique().tolist(), key=short_species)
    heat = mean_species.pivot(index="species", columns="support_per_species", values="accuracy").reindex(index=species_order, columns=budgets)

    draw_summary = draws.groupby("support_per_species", as_index=False).agg(
        draws=("seed", "nunique"),
        support_cells=("support_cells", "median"),
        query_cells=("query_cells", "median"),
    )

    fig = plt.figure(figsize=(7.25, 5.28))
    grid = fig.add_gridspec(2, 6, width_ratios=(1.28, 1.28, 1.0, 1.0, 1.0, 1.0), height_ratios=(1.05, .95), left=.055, right=.988, bottom=.09, top=.95, wspace=.46, hspace=.76)
    ax_a = fig.add_subplot(grid[0, :2])
    ax_b = fig.add_subplot(grid[0, 2:])
    ax_c = fig.add_subplot(grid[1, :3])
    ax_d = fig.add_subplot(grid[1, 3:])

    ax_a.set_axis_off()
    panel(ax_a, "a", "Support and query cells are physically disjoint", "Eight held-out species; ten fixed-seed support draws at each budget")
    ax_a.add_patch(Rectangle((.04, .15), .20, .62, transform=ax_a.transAxes, facecolor="#F4F7F8", edgecolor=GREY, linewidth=.7))
    ax_a.text(.14, .61, "target\nspecies", transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, fontweight="bold")
    ax_a.text(.14, .29, "labels locked\nuntil support draw", transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, color=MUTED)
    ax_a.add_patch(FancyArrowPatch((.25, .48), (.35, .48), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=.75, color=MUTED))
    ax_a.add_patch(Rectangle((.37, .53), .23, .24, transform=ax_a.transAxes, facecolor="#FFF4E9", edgecolor=ORANGE, linewidth=.85))
    ax_a.add_patch(Rectangle((.37, .15), .23, .24, transform=ax_a.transAxes, facecolor="#EAF5F4", edgecolor=TEAL, linewidth=.85))
    ax_a.text(.485, .65, "labelled\nsupport", transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, fontweight="bold")
    ax_a.text(.485, .27, "unlabelled\nquery", transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, fontweight="bold")
    ax_a.add_patch(FancyArrowPatch((.61, .48), (.70, .48), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=.75, color=MUTED))
    ax_a.add_patch(Rectangle((.72, .15), .24, .62, transform=ax_a.transAxes, facecolor="#F4F7F8", edgecolor=PURPLE, linewidth=.7))
    ax_a.text(.84, .61, "target\nadapter", transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, fontweight="bold")
    ax_a.text(.84, .32, "fit only on\nsupport labels", transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, color=MUTED)
    ax_a.text(.5, .06, "No support cell is included in query scoring.", transform=ax_a.transAxes, ha="center", fontsize=5.0, color=RED, fontweight="bold")

    rng = np.random.default_rng(24)
    means = []
    for index, budget in enumerate(budgets):
        values = draws.loc[draws.support_per_species.eq(budget), "accuracy_all_query"].to_numpy()
        means.append(values.mean())
        ax_b.scatter(rng.normal(index, .043, len(values)), values, s=18, color=TEAL_PALE, edgecolor="white", linewidth=.35, zorder=2)
        ax_b.errorbar(index, values.mean(), yerr=values.std(ddof=0), color=TEAL, marker="o", markersize=5.9, markeredgecolor="white", markeredgewidth=.7, capsize=2.2, lw=1.3, zorder=3)
        ax_b.text(index, values.mean() + .028, f"{values.mean():.3f}", ha="center", fontsize=5.15, fontweight="bold")
    ax_b.plot(range(len(budgets)), means, color=TEAL, lw=1.1, zorder=1)
    ax_b.set(xticks=range(len(budgets)), xticklabels=budgets, ylim=(.49, .80), xlabel="labelled support cells per target species", ylabel="query all-cell accuracy")
    ax_b.text(.99, .05, "10 independent support draws per budget\npoints: raw draws; bars: s.d.", transform=ax_b.transAxes, ha="right", va="bottom", fontsize=5.0, color=MUTED)
    clean(ax_b, "y")
    panel(ax_b, "b", "Adaptation improves monotonically with a small labelled support set", "The 64-cell setting reaches 75.89% mean query all-cell accuracy")

    ax_c.errorbar(macro.support_per_species, macro["mean"], yerr=macro["sd"].fillna(0), color=PURPLE, marker="o", markersize=5.6, markeredgecolor="white", markeredgewidth=.7, capsize=2.2, lw=1.25)
    ax_c.set(xticks=budgets, ylim=(.16, .52), xlabel="support cells per target species", ylabel="query macro-F1")
    clean(ax_c, "y")
    panel(ax_c, "c", "Fine-label recovery follows the same dose response", "Macro-F1 is reported separately from the all-cell headline")

    image = ax_d.imshow(heat.to_numpy(), aspect="auto", cmap=LinearSegmentedColormap.from_list("fewshot", ["#F4F7F8", "#B9DFDC", TEAL]), vmin=0, vmax=1)
    for yi, species in enumerate(heat.index):
        for xi, budget in enumerate(heat.columns):
            value = heat.loc[species, budget]
            ax_d.text(xi, yi, f"{value:.2f}", ha="center", va="center", fontsize=5.0, color="white" if value >= .65 else INK)
    ax_d.set(xticks=range(len(budgets)), xticklabels=budgets, yticks=range(len(heat.index)), yticklabels=[short_species(s) for s in heat.index])
    ax_d.tick_params(length=0, labelsize=5.0)
    for spine in ax_d.spines.values():
        spine.set_visible(False)
    bar = fig.colorbar(image, ax=ax_d, fraction=.035, pad=.02)
    bar.ax.tick_params(labelsize=5.0, length=1.2)
    panel(ax_d, "d", "Species-specific gains remain visible", "Rows marked with * in the paper are single-label public records")

    export(
        fig,
        MAIN,
        "plant_cellfm_v5_fig3_target_adaptation",
        {
            "fewshot_draws": draws,
            "fewshot_species_draws": species_draws,
            "fewshot_species_budget_means": mean_species,
            "fewshot_protocol_summary": draw_summary,
        },
    )


def render_fig4_external_root() -> None:
    record_path = ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    case_root = ROOT / "outputs" / "external_validation" / "gse152766_gsm4626007" / "annotation_bundle"
    predictions = pd.read_csv(case_root / "predictions.csv")
    embeddings = np.load(case_root / "embeddings.npy").astype(np.float32)
    states = pd.DataFrame(record["prediction_distribution"])
    markers = pd.DataFrame(record["predefined_marker_coherence"])
    if len(predictions) != embeddings.shape[0] or len(markers) != 6:
        raise ValueError("The external root audit does not match its prediction bundle.")
    coordinates = umap.UMAP(n_neighbors=30, min_dist=.34, metric="cosine", random_state=31).fit_transform(embeddings)
    plotted = predictions[["cell_id", "fine_label", "fine_confidence"]].copy()
    plotted["UMAP1"] = coordinates[:, 0]
    plotted["UMAP2"] = coordinates[:, 1]

    fig = plt.figure(figsize=(7.25, 5.5))
    grid = fig.add_gridspec(2, 6, width_ratios=(1.1, 1.1, 1.1, 1, 1, 1), height_ratios=(1.05, .95), left=.055, right=.988, bottom=.095, top=.95, wspace=.48, hspace=.65)
    ax_a = fig.add_subplot(grid[:, :3])
    ax_b = fig.add_subplot(grid[0, 3:])
    ax_c = fig.add_subplot(grid[1, 3:])

    for label in states.sort_values("cells", ascending=False).fine_label:
        subset = plotted.loc[plotted.fine_label.eq(label)]
        ax_a.scatter(subset.UMAP1, subset.UMAP2, s=2.2, color=base.ROOT_STATE.get(label, GREY), alpha=.76, linewidth=0, rasterized=True)
    ax_a.set(xticks=[], yticks=[])
    for spine in ax_a.spines.values():
        spine.set_visible(False)
    panel(ax_a, "a", "A label-free external root matrix resolves into structured predicted states", "GSE152766/GSM4626007: 6,566 cells; not listed in the frozen v4 corpus profile")
    ax_a.text(.01, -.065, "Coordinates derive from frozen 256-dimensional model embeddings. Colours are model outputs, never supplied labels.", transform=ax_a.transAxes, fontsize=5.0, color=MUTED)

    display = states.sort_values("cells", ascending=True).reset_index(drop=True)
    y = np.arange(len(display))
    ax_b.barh(y, display["fraction"], color=[base.ROOT_STATE.get(label, GREY) for label in display.fine_label], height=.58, edgecolor="white", linewidth=.4)
    ax_b.scatter(display.mean_confidence, y, s=np.clip(display.cells.to_numpy() / 14, 10, 57), color=INK, edgecolor="white", linewidth=.45, zorder=3)
    for index, row in display.iterrows():
        ax_b.text(max(float(row["fraction"]), float(row.mean_confidence)) + .015, index, f"{int(row.cells):,}", va="center", fontsize=5.0)
    ax_b.set(yticks=y, yticklabels=display.fine_label.tolist(), xlim=(0, 1.16), xlabel="bar: fraction; dot: mean confidence")
    ax_b.tick_params(axis="y", labelsize=5.0, pad=1.2, length=0)
    clean(ax_b, "x")
    panel(ax_b, "b", "All 13 output states and confidences remain inspectable", "Numbers are predicted cells, not an external ground truth")

    marker = markers.sort_values("mean_expression_delta", ascending=True).reset_index(drop=True)
    y_marker = np.arange(len(marker))
    ax_c.axvline(0, color=GRID, lw=.7)
    ax_c.hlines(y_marker, 0, marker.mean_expression_delta, color=LIGHT_GREY, lw=2.4, zorder=1)
    ax_c.scatter(marker.mean_expression_delta, y_marker, s=36 + marker.target_detection_fraction.to_numpy() * 46, color=[base.ROOT_STATE.get(label, TEAL) for label in marker.expected_label], edgecolor="white", linewidth=.6, zorder=3)
    for index, row in marker.iterrows():
        rank = int(row.rank_among_predicted_labels_by_mean_expression)
        ax_c.text(float(row.mean_expression_delta) + .018, index, f"rank {rank}/13; n={int(row.predicted_label_cells)}; detection delta {row.detection_fraction_delta:+.2f}", va="center", fontsize=5.0, color=INK if rank == 1 else MUTED)
    ax_c.set(yticks=y_marker, yticklabels=[f"{row.marker_symbol} | {row.expected_label}" for row in marker.itertuples(index=False)], xlim=(-.04, max(1.22, float(marker.mean_expression_delta.max()) + .62)), xlabel="expected-group minus all-other-groups mean log1p expression")
    ax_c.tick_params(axis="y", labelsize=5.0, pad=1.8, length=0)
    clean(ax_c, "x")
    panel(ax_c, "c", "Five of six fixed literature anchors peak in their expected predicted group", "Marker coherence is a biologic plausibility check, not external accuracy or experimental validation")

    export(
        fig,
        MAIN,
        "plant_cellfm_v5_fig4_external_root_evidence",
        {"external_embedding_umap": plotted, "external_prediction_distribution": states, "external_marker_coherence": markers},
    )


def render_extended_data(v17: pd.DataFrame, v18: pd.DataFrame) -> None:
    # Extended Data keeps the detailed audits but receives the v5 typography and
    # output directory.  Its quantitative inputs are untouched.
    base.OUT = OUT
    base.MAIN = MAIN
    base.EXTENDED = EXTENDED
    base.SOURCE = SOURCE
    base.panel = panel
    base.label_panel = lambda ax, letter, title, subtitle=None: panel(ax, letter, title, subtitle)
    base.render_ed1_label_integrity(v17, v18)
    base.render_ed2_nested_selection()
    base.render_ed3_matched_checkpoint_comparison()
    base.render_ed4_literature_marker_concordance()
    base.render_ed5_external_root_blind_inference()


def normalise_svg_whitespace() -> None:
    """Keep generated vector assets clean in version control without altering paths."""
    for path in OUT.rglob("*.svg"):
        content = path.read_text(encoding="utf-8")
        path.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")


def main() -> None:
    setup()
    frame, v17, v18 = base.load_cells()
    render_fig1(frame)
    render_fig2(frame, v17)
    render_fig3()
    render_fig4_external_root()
    render_extended_data(v17, v18)
    normalise_svg_whitespace()
    print(json.dumps({"figure_suite": "v5", "main_figures": 4, "extended_data_figures": 5}, ensure_ascii=False))


if __name__ == "__main__":
    main()
