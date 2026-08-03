from __future__ import annotations

"""Render the v12 strict cross-species generalization figure."""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.text import Text
import numpy as np
import pandas as pd

try:
    from scipy.ndimage import gaussian_filter
except ImportError:  # pragma: no cover
    gaussian_filter = None


ROOT = Path(__file__).resolve().parents[1]
V11_SOURCE = ROOT / "figures" / "plant_cellfm_submission_v11" / "source_data"
OUT = ROOT / "figures" / "plant_cellfm_submission_v12"
MAIN = OUT / "main"
SOURCE = OUT / "source_data"

INK = "#10212D"
MUTED = "#5D7180"
GRID = "#DCE5EA"
PALE = "#EEF4F5"
TEAL = "#00877E"
DEEP_TEAL = "#005B56"
BLUE = "#176FB5"
NAVY = "#173A63"
CYAN = "#3BA6B9"
ORANGE = "#EE7B27"
PURPLE = "#8064A7"
RED = "#C5555C"
GREY = "#B9C6CD"

OUTCOME_COLORS = {"correct": TEAL, "covered error": ORANGE, "open / unavailable": GREY}
SPECIES_COLORS = {
    "Arabidopsis thaliana": BLUE,
    "Brassica rapa": "#68BDB2",
    "Catharanthus roseus": ORANGE,
    "Eutrema salsugineum": PURPLE,
    "Fragaria vesca": RED,
    "Gossypium bickii": CYAN,
    "Gossypium hirsutum": "#7797A7",
    "Triticum aestivum": NAVY,
}


def setup() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 6.0,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "axes.linewidth": 0.55,
            "savefig.facecolor": "white",
        }
    )
    MAIN.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)


def read_table(name: str) -> pd.DataFrame:
    return pd.read_csv(V11_SOURCE / f"plant_cellfm_v11_fig2_strict_transfer_{name}.tsv", sep="\t")


def short_species(value: str) -> str:
    parts = str(value).split()
    return f"{parts[0][0]}. {parts[-1]}" if len(parts) > 1 else str(value)


def panel_label(ax: plt.Axes, key: str, title: str, y: float = 1.025) -> None:
    ax.text(-0.045, y, key, transform=ax.transAxes, fontsize=8.0, fontweight="bold", color=INK, va="bottom")
    ax.text(0.0, y, title, transform=ax.transAxes, fontsize=5.6, fontweight="bold", color=INK, va="bottom")


def density_contours(ax: plt.Axes, frame: pd.DataFrame, color: str) -> None:
    hist, x_edges, y_edges = np.histogram2d(frame.UMAP1, frame.UMAP2, bins=(78, 62))
    if gaussian_filter is not None:
        hist = gaussian_filter(hist, sigma=1.9)
    positive = hist[hist > 0]
    if positive.size < 5:
        return
    levels = np.unique(np.quantile(positive, [0.60, 0.79, 0.92]))
    if len(levels) < 2:
        return
    x_mid = (x_edges[:-1] + x_edges[1:]) / 2
    y_mid = (y_edges[:-1] + y_edges[1:]) / 2
    ax.contour(x_mid, y_mid, hist.T, levels=levels, colors=color, linewidths=[0.32, 0.52, 0.76][: len(levels)], alpha=0.48)


def species_centres(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby("species", as_index=False).agg(UMAP1=("UMAP1", "median"), UMAP2=("UMAP2", "median"), cells=("cell_id", "size"))


def panel_strict_atlas(fig: plt.Figure, bounds: list[float], embedding: pd.DataFrame, outcomes: pd.DataFrame) -> None:
    container = fig.add_axes(bounds)
    panel_label(container, "a", "Strict leave-species-out outcome atlas")
    container.set_axis_off()
    atlas = container.inset_axes([0.0, 0.0, 0.655, 1.0])
    for outcome in ["open / unavailable", "covered error", "correct"]:
        part = embedding.loc[embedding.outcome.eq(outcome)]
        atlas.scatter(
            part.UMAP1,
            part.UMAP2,
            s=2.6 if outcome == "correct" else 1.8,
            color=OUTCOME_COLORS[outcome],
            alpha=0.78 if outcome == "correct" else 0.52,
            linewidths=0,
            zorder=3 if outcome == "correct" else 2,
        )
    density_contours(atlas, embedding, "#8299A6")
    centres = species_centres(embedding)
    for _, row in centres.iterrows():
        color = SPECIES_COLORS.get(row.species, INK)
        atlas.scatter([row.UMAP1], [row.UMAP2], s=18, color="white", edgecolor=color, linewidth=0.9, zorder=7)
        atlas.text(row.UMAP1, row.UMAP2, short_species(row.species).split()[0], fontsize=2.55, color=color, ha="center", va="center", fontweight="bold", zorder=8)
    atlas.set(xticks=[], yticks=[])
    atlas.set_facecolor(PALE)
    for spine in atlas.spines.values():
        spine.set_visible(False)
    aggregate_accuracy = float(np.average(outcomes.accuracy_all, weights=outcomes.cells))
    aggregate_coverage = float(np.average(outcomes.coverage, weights=outcomes.cells))
    atlas.text(0.02, 0.97, f"{len(embedding):,}", transform=atlas.transAxes, fontsize=7.4, color=INK, fontweight="bold", va="top")
    atlas.text(0.02, 0.885, "held-out cells", transform=atlas.transAxes, fontsize=3.0, color=MUTED, va="top")
    atlas.text(0.24, 0.97, f"{aggregate_accuracy:.1%}", transform=atlas.transAxes, fontsize=6.2, color=TEAL, fontweight="bold", va="top")
    atlas.text(0.24, 0.895, "all-cell accuracy", transform=atlas.transAxes, fontsize=3.0, color=MUTED, va="top")
    atlas.text(0.47, 0.97, f"{aggregate_coverage:.1%}", transform=atlas.transAxes, fontsize=6.2, color=ORANGE, fontweight="bold", va="top")
    atlas.text(0.47, 0.895, "source-label coverage", transform=atlas.transAxes, fontsize=3.0, color=MUTED, va="top")

    radial = container.inset_axes([0.68, 0.015, 0.32, 0.97], projection="polar")
    radial.set_theta_direction(-1)
    radial.set_theta_offset(np.pi / 2)
    plot = outcomes.sort_values("accuracy_all", ascending=False).reset_index(drop=True)
    width = 2 * np.pi / len(plot)
    for index, (_, row) in enumerate(plot.iterrows()):
        angle = index * width + width / 2
        bottom = 0.28
        values = [float(row.correct), float(row.covered_error), float(row.open_set)]
        for value, color in zip(values, [TEAL, ORANGE, GREY], strict=True):
            height = 0.53 * value
            radial.bar(angle, height, width=width * 0.84, bottom=bottom, color=color, edgecolor="white", linewidth=0.42)
            bottom += height
        radial.bar(angle, 0.025, width=width * 0.86, bottom=0.84, color=SPECIES_COLORS.get(row.held_out_species, INK), edgecolor="white", linewidth=0.2)
        radial.text(angle, 0.94, short_species(row.held_out_species), fontsize=2.7, color=INK, ha="center", va="center")
        radial.text(angle, 0.73, f"{row.accuracy_all:.0%}", fontsize=2.7, color="white" if row.accuracy_all > 0.42 else INK, ha="center", va="center", fontweight="bold")
    radial.text(0, 0.08, "8", fontsize=8.0, color=INK, ha="center", va="center", fontweight="bold")
    radial.text(0, 0.18, "strict rotations", fontsize=3.0, color=MUTED, ha="center", va="center")
    radial.set_ylim(0, 1.02)
    radial.set_axis_off()
    container.text(0.695, 0.015, "radial stack: correct / covered error / open", fontsize=2.9, color=MUTED)

    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgewidth=0, markersize=3.0, label=name)
        for name, color in OUTCOME_COLORS.items()
    ]
    container.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.325, -0.12), frameon=False, ncol=3, fontsize=2.9, handletextpad=0.2, columnspacing=0.55)


def panel_interval_forest(ax: plt.Axes, intervals: pd.DataFrame) -> None:
    panel_label(ax, "b", "Coverage-to-accuracy interval field")
    accuracy = intervals.loc[intervals.metric.eq("all_cell_accuracy")].set_index("held_out_species")
    coverage = intervals.loc[intervals.metric.eq("coverage")].set_index("held_out_species")
    order = accuracy.sort_values("point", ascending=True).index.tolist()
    y = np.arange(len(order))
    for yi, species in zip(y, order, strict=True):
        acc = accuracy.loc[species]
        cov = coverage.loc[species]
        ax.hlines(yi, acc.point, cov.point, color=GRID, lw=2.5, zorder=1)
        ax.errorbar(acc.point, yi - 0.11, xerr=[[acc.point - acc.ci_low], [acc.ci_high - acc.point]], fmt="o", ms=4.0, color=BLUE, ecolor=BLUE, elinewidth=0.8, capsize=1.6, markeredgecolor="white", markeredgewidth=0.45, zorder=4)
        ax.errorbar(cov.point, yi + 0.11, xerr=[[cov.point - cov.ci_low], [cov.ci_high - cov.point]], fmt="o", ms=4.0, color=TEAL, ecolor=TEAL, elinewidth=0.8, capsize=1.6, markeredgecolor="white", markeredgewidth=0.45, zorder=4)
        ax.text(max(acc.point, cov.point) + 0.018, yi, f"{acc.point:.0%} / {cov.point:.0%}", fontsize=2.85, color=INK, va="center")
    ax.set(yticks=y, yticklabels=[short_species(value) for value in order], xlim=(-0.02, 1.12), xticks=[0, 0.25, 0.5, 0.75, 1], xticklabels=["0", "25", "50", "75", "100"], xlabel="percent of held-out cells")
    ax.tick_params(axis="both", labelsize=3.0, length=0, pad=1.2)
    ax.grid(axis="x", color=GRID, linewidth=0.55, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=BLUE, markeredgewidth=0, markersize=3.2, label="all-cell accuracy"),
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=TEAL, markeredgewidth=0, markersize=3.2, label="coverage"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=2.9, ncol=2, handletextpad=0.2, columnspacing=0.55)


def panel_metric_field(ax: plt.Axes, metrics: pd.DataFrame) -> None:
    panel_label(ax, "c", "Species-by-metric field")
    columns = ["accuracy_all", "coverage", "covered_accuracy", "macro_f1"]
    labels = ["all-cell", "coverage", "covered", "macro-F1"]
    plot = metrics.sort_values("accuracy_all", ascending=False).reset_index(drop=True)
    cmap = mpl.colors.LinearSegmentedColormap.from_list("metric", ["#E7EEF2", "#A9CDDE", BLUE, TEAL, DEEP_TEAL])
    for row_index, row in plot.iterrows():
        for col_index, column in enumerate(columns):
            value = row[column]
            if pd.isna(value):
                ax.scatter(col_index, row_index, s=16, facecolor="white", edgecolor=GREY, linewidth=0.65)
                continue
            ax.scatter(col_index, row_index, s=24 + 125 * float(value) ** 1.3, color=cmap(float(value)), edgecolor="white", linewidth=0.55)
            ax.text(col_index, row_index, f"{value:.0%}", fontsize=2.7, color="white" if value > 0.52 else INK, ha="center", va="center", fontweight="bold")
    ax.set(xticks=np.arange(len(columns)), xticklabels=labels, yticks=np.arange(len(plot)), yticklabels=[short_species(value) for value in plot.held_out_species], xlim=(-0.6, 3.6), ylim=(len(plot) - 0.45, -0.55))
    ax.tick_params(axis="both", labelsize=2.85, length=0, pad=1.1)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for row in range(len(plot) - 1):
        ax.axhline(row + 0.5, color=GRID, lw=0.4, zorder=0)


def panel_checkpoint_gain(ax: plt.Axes, checkpoint: pd.DataFrame) -> None:
    panel_label(ax, "d", "Matched-checkpoint gain")
    plot = checkpoint.sort_values("delta", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    for yi, row in plot.iterrows():
        ax.hlines(yi, row.v3, row.v9, color=GRID, lw=4.0, zorder=1)
        ax.scatter([row.v3], [yi], s=28, color=GREY, edgecolor="white", linewidth=0.5, zorder=3)
        ax.scatter([row.v9], [yi], s=34, color=TEAL, edgecolor="white", linewidth=0.55, zorder=4)
        ax.text(row.v9 + 0.02, yi, f"+{row.delta:.1%}", fontsize=3.1, color=TEAL, fontweight="bold", va="center")
    labels = checkpoint.protocol.replace({"leave dataset": "leave dataset", "leave sample": "leave sample", "leave species": "leave species"})
    ax.set(yticks=y, yticklabels=plot.protocol, xlim=(0, 0.72), xlabel="all-cell accuracy")
    ax.tick_params(axis="both", labelsize=3.0, length=0, pad=1.2)
    ax.grid(axis="x", color=GRID, lw=0.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=GREY, markeredgewidth=0, markersize=3.2, label="v3"),
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=TEAL, markeredgewidth=0, markersize=3.2, label="Plant-CellFM"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=2.9, ncol=2, handletextpad=0.2, columnspacing=0.5)


def panel_sensitivity(ax: plt.Axes, sensitivity: pd.DataFrame) -> None:
    panel_label(ax, "e", "Context sensitivity lane")
    x = np.arange(len(sensitivity))
    series = [
        ("all-cell", "all_cell_accuracy", BLUE),
        ("known-label", "known_label_accuracy", TEAL),
        ("macro-F1", "macro_f1", PURPLE),
    ]
    for label, column, color in series:
        values = sensitivity[column].to_numpy(float)
        ax.plot(x, values, color=color, lw=1.5, marker="o", ms=4.0, markeredgecolor="white", markeredgewidth=0.5)
        ax.text(x[-1] + 0.08, values[-1], f"{label} {values[-1]:.1%}", fontsize=3.0, color=color, va="center", fontweight="bold")
    ax.axhline(0.559, color=ORANGE, lw=0.75, ls=(0, (3, 2)))
    ax.text(-0.05, 0.575, "coverage 55.9%", fontsize=2.9, color=ORANGE)
    ax.set(xticks=x, xticklabels=[str(value).replace("\n", " ") for value in sensitivity.stage], xlim=(-0.2, 3.75), ylim=(0.12, 0.83), yticks=[0.2, 0.4, 0.6, 0.8], yticklabels=["20", "40", "60", "80"])
    ax.tick_params(axis="both", labelsize=2.9, length=0, pad=1.0)
    ax.grid(axis="y", color=GRID, lw=0.5)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)


def render() -> None:
    setup()
    outcomes = read_table("per_species_outcome_composition")
    intervals = read_table("bootstrap_interval_field")
    coverage = read_table("coverage_accuracy")
    protocol = read_table("holdout_protocol")
    checkpoint = read_table("matched_checkpoint_comparison")
    metrics = read_table("per_species_metric_matrix")
    sensitivity = read_table("context_sensitivity")
    embedding = read_table("strict_embedding_outcomes")

    fig = plt.figure(figsize=(7.25, 7.90))
    atlas_bounds = [0.045, 0.565, 0.940, 0.355]
    ax_b = fig.add_axes([0.050, 0.300, 0.505, 0.200])
    ax_c = fig.add_axes([0.615, 0.300, 0.355, 0.200])
    ax_d = fig.add_axes([0.050, 0.070, 0.260, 0.150])
    ax_e = fig.add_axes([0.390, 0.070, 0.580, 0.150])

    panel_strict_atlas(fig, atlas_bounds, embedding, outcomes)
    panel_interval_forest(ax_b, intervals)
    panel_metric_field(ax_c, metrics)
    panel_checkpoint_gain(ax_d, checkpoint)
    panel_sensitivity(ax_e, sensitivity)

    fig.text(0.042, 0.980, "Strict cross-species generalization under target exclusion", fontsize=9.15, fontweight="bold", color=INK, va="top")
    fig.text(0.988, 0.980, "8 leave-species-out rotations · 3,964 held-out cells · target labels absent", fontsize=3.8, color=MUTED, ha="right", va="top")
    fig.add_artist(plt.Line2D([0.042, 0.988], [0.540, 0.540], transform=fig.transFigure, color=GRID, lw=0.65))

    for artist in fig.findobj(match=Text):
        if artist.get_fontsize() < 3.0:
            artist.set_fontsize(3.0)

    stem = "plant_cellfm_v12_fig2_strict_transfer"
    tables = {
        "per_species_outcome_composition": outcomes,
        "bootstrap_interval_field": intervals,
        "coverage_accuracy": coverage,
        "holdout_protocol": protocol,
        "matched_checkpoint_comparison": checkpoint,
        "per_species_metric_matrix": metrics,
        "context_sensitivity": sensitivity,
        "strict_embedding_outcomes": embedding,
    }
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for suffix, options in (("svg", {"dpi": 600}), ("pdf", {"dpi": 600}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)
    print({"figure": str(MAIN / f"{stem}.png"), "cells": len(embedding), "source_tables": len(tables)})


if __name__ == "__main__":
    render()
