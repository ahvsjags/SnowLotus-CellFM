from __future__ import annotations

"""Render the vector, evidence-led v12 context-STC main figure."""

import importlib.util
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.path import Path as MplPath
from matplotlib.text import Text
import numpy as np
import pandas as pd

try:
    from scipy.ndimage import gaussian_filter
except ImportError:  # pragma: no cover - only used on minimal plotting installs
    gaussian_filter = None


ROOT = Path(__file__).resolve().parents[1]
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
LIGHT_GREY = "#E5EBEE"

CHANGE_PALETTE = {
    "rescued": TEAL,
    "retained correct": BLUE,
    "lost": RED,
    "persistent error": ORANGE,
    "open / unavailable": GREY,
}
FAMILY_PALETTE = {
    "Brassicaceae": TEAL,
    "Apocynaceae": ORANGE,
    "Rosaceae": RED,
    "Malvaceae": CYAN,
    "Poaceae": PURPLE,
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def short_species(value: str) -> str:
    parts = str(value).split()
    return f"{parts[0][0]}. {parts[-1]}" if len(parts) > 1 else str(value)


def panel_label(ax: plt.Axes, key: str, title: str, *, y: float = 1.025) -> None:
    ax.text(-0.045, y, key, transform=ax.transAxes, fontsize=8.0, fontweight="bold", color=INK, va="bottom")
    ax.text(0.0, y, title, transform=ax.transAxes, fontsize=5.6, fontweight="bold", color=INK, va="bottom")


def direct_label(ax: plt.Axes, x: float, y: float, text: str, color: str = INK, size: float = 3.25) -> None:
    artist = ax.text(x, y, text, ha="center", va="center", fontsize=size, color=color, fontweight="bold", zorder=8)
    artist.set_path_effects([path_effects.withStroke(linewidth=1.4, foreground="white")])


def curved_line(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    width: float,
    alpha: float = 0.75,
    *,
    zorder: int = 2,
) -> None:
    x0, y0 = start
    x1, y1 = end
    vertices = [(x0, y0), (x0 + 0.42 * (x1 - x0), y0), (x0 + 0.58 * (x1 - x0), y1), (x1, y1)]
    path = MplPath(vertices, [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])
    ax.add_patch(
        patches.PathPatch(
            path,
            facecolor="none",
            edgecolor=color,
            linewidth=width,
            alpha=alpha,
            capstyle="round",
            zorder=zorder,
        )
    )


def panel_mechanism(ax: plt.Axes) -> pd.DataFrame:
    panel_label(ax, "a", "Source-derived context routing on frozen embeddings", y=1.01)
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.add_patch(
        patches.FancyBboxPatch(
            (0.010, 0.050),
            0.980,
            0.860,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            facecolor="#F7FAFB",
            edgecolor="#DCE7EB",
            linewidth=0.80,
            zorder=0,
        )
    )

    rng = np.random.default_rng(31415)
    cluster_specs = [(0.090, 0.720, BLUE), (0.110, 0.520, TEAL), (0.090, 0.320, PURPLE)]
    for cx, cy, color in cluster_specs:
        ax.scatter(cx + rng.normal(0, 0.030, 35), cy + rng.normal(0, 0.040, 35), s=7.0, color=mpl.colors.to_rgba(color, 0.58), linewidths=0, zorder=2)
    ax.text(0.095, 0.875, "held-out cells", ha="center", fontsize=3.35, color=INK, fontweight="bold")
    ax.text(0.095, 0.095, "target labels not used\nfor routing selection", ha="center", fontsize=3.0, color=ORANGE, fontweight="bold", linespacing=0.95)

    boxes = [
        (0.190, 0.590, 0.135, 0.155, "frozen\nembedding", "d=256", BLUE),
        (0.390, 0.690, 0.145, 0.125, "expression\nneighbours", "source folds", BLUE),
        (0.390, 0.500, 0.145, 0.125, "organ\nprior", "root | leaf | callus", TEAL),
        (0.390, 0.310, 0.145, 0.125, "family\nsupport", "same-family evidence", PURPLE),
        (0.620, 0.500, 0.135, 0.155, "context\ngate", "covered-label router", DEEP_TEAL),
        (0.825, 0.625, 0.135, 0.135, "covered\nlabel", "calibrated call", TEAL),
        (0.825, 0.350, 0.135, 0.135, "unsupported\nlabel", "denominator retained", GREY),
    ]
    for x, y, width, height, title, subtitle, color in boxes:
        ax.add_patch(
            patches.FancyBboxPatch(
                (x, y), width, height,
                boxstyle="round,pad=0.008,rounding_size=0.014",
                facecolor=mpl.colors.to_rgba(color, 0.105),
                edgecolor=color,
                linewidth=0.95,
                zorder=3,
            )
        )
        ax.text(x + width / 2, y + height * 0.62, title, ha="center", va="center", fontsize=3.95, color=INK, fontweight="bold", linespacing=0.95)
        ax.text(x + width / 2, y + height * 0.24, subtitle, ha="center", va="center", fontsize=2.9, color=MUTED, linespacing=0.95)

    for y, color in [(0.715, BLUE), (0.565, TEAL), (0.375, PURPLE)]:
        curved_line(ax, (0.325, 0.668), (0.390, y), color, 0.90, 0.50, zorder=2)
        curved_line(ax, (0.535, y), (0.620, 0.578), color, 1.10, 0.55, zorder=2)
    curved_line(ax, (0.755, 0.585), (0.825, 0.692), TEAL, 1.30, 0.70, zorder=2)
    curved_line(ax, (0.755, 0.520), (0.825, 0.418), GREY, 1.10, 0.55, zorder=2)
    ax.add_patch(patches.Circle((0.688, 0.578), 0.070, fill=False, edgecolor=DEEP_TEAL, linewidth=1.25, zorder=5))
    ax.add_patch(patches.Circle((0.688, 0.578), 0.045, fill=False, edgecolor=PURPLE, linewidth=1.05, zorder=5))
    ax.text(0.688, 0.578, "55.90%\ncoverage", ha="center", va="center", fontsize=3.0, color=DEEP_TEAL, fontweight="bold", linespacing=0.92, zorder=6)

    stage_meta = [
        (0.245, "frozen embeddings"),
        (0.465, "source metadata"),
        (0.682, "gate selection"),
        (0.890, "covered or retained"),
    ]
    for x, text in stage_meta:
        ax.scatter([x - 0.048], [0.080], s=8, color=TEAL, edgecolor="white", linewidth=0.35, zorder=9)
        direct_label(ax, x, 0.080, text, MUTED, 3.0)

    return pd.DataFrame(
        [
            {"stage": "rank_tokenization", "dimension": 256, "target_label_access": 0},
            {"stage": "frozen_embedding", "layers": 4, "target_label_access": 0},
            {"stage": "organ_context", "target_label_access": 0},
            {"stage": "phylogeny_context", "target_label_access": 0},
            {"stage": "source_context_router", "target_label_access": 0},
            {"stage": "coverage_retained_output", "target_label_access": 0},
        ]
    )

def density_contours(ax: plt.Axes, x: np.ndarray, y: np.ndarray, color: str) -> None:
    if len(x) < 20:
        return
    hist, x_edges, y_edges = np.histogram2d(x, y, bins=(80, 62))
    if gaussian_filter is not None:
        hist = gaussian_filter(hist, sigma=2.0)
    positive = hist[hist > 0]
    if positive.size == 0:
        return
    levels = np.quantile(positive, [0.58, 0.76, 0.90])
    levels = np.unique(levels)
    if levels.size < 2:
        return
    x_mid = (x_edges[:-1] + x_edges[1:]) / 2
    y_mid = (y_edges[:-1] + y_edges[1:]) / 2
    ax.contour(x_mid, y_mid, hist.T, levels=levels, colors=color, linewidths=[0.35, 0.55, 0.80][: len(levels)], alpha=0.55)


def zoom_species(parent: plt.Axes, bounds: list[float], cells: pd.DataFrame, species: str, delta: float) -> None:
    ax = parent.inset_axes(bounds)
    part = cells.loc[cells.species.eq(species)]
    for outcome in ["open / unavailable", "persistent error", "lost", "retained correct", "rescued"]:
        view = part.loc[part.change_vs_centroid.eq(outcome)]
        ax.scatter(
            view.UMAP1,
            view.UMAP2,
            s=4.2 if outcome == "rescued" else 2.1,
            color=CHANGE_PALETTE[outcome],
            alpha=0.84 if outcome == "rescued" else 0.58,
            linewidths=0,
            zorder=3,
        )
    ax.set(xticks=[], yticks=[])
    ax.set_facecolor("#F4F8F9")
    x_low, x_high = part.UMAP1.quantile([0.01, 0.99])
    y_low, y_high = part.UMAP2.quantile([0.01, 0.99])
    x_pad = max(0.05, 0.07 * (x_high - x_low))
    y_pad = max(0.05, 0.09 * (y_high - y_low))
    ax.set(xlim=(x_low - x_pad, x_high + x_pad), ylim=(y_low - y_pad, y_high + y_pad))
    for spine in ax.spines.values():
        spine.set_color("white")
        spine.set_linewidth(1.0)
    ax.text(0.05, 0.93, short_species(species), transform=ax.transAxes, fontsize=3.0, color=INK, fontweight="bold", va="top")
    ax.text(0.95, 0.93, f"+{delta:.1%}", transform=ax.transAxes, fontsize=3.2, color=TEAL, fontweight="bold", ha="right", va="top")


def panel_rescue_atlas(ax: plt.Axes, cells: pd.DataFrame, gains: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax, "b", "Cell-level rescue atlas")
    ax.set_facecolor("#F3F7F8")
    base = cells.loc[cells.change_vs_centroid.eq("open / unavailable")]
    ax.scatter(base.UMAP1, base.UMAP2, s=1.5, color=GREY, alpha=0.32, linewidths=0, zorder=1)
    for outcome in ["persistent error", "lost", "retained correct", "rescued"]:
        part = cells.loc[cells.change_vs_centroid.eq(outcome)]
        ax.scatter(
            part.UMAP1,
            part.UMAP2,
            s=4.0 if outcome == "rescued" else 2.0,
            color=CHANGE_PALETTE[outcome],
            alpha=0.80 if outcome == "rescued" else 0.56,
            linewidths=0,
            zorder=4 if outcome == "rescued" else 2,
        )
    density_contours(ax, cells.UMAP1.to_numpy(), cells.UMAP2.to_numpy(), "#8299A6")
    rescued = cells.loc[cells.change_vs_centroid.eq("rescued")]
    density_contours(ax, rescued.UMAP1.to_numpy(), rescued.UMAP2.to_numpy(), DEEP_TEAL)

    x_min, x_max = cells.UMAP1.min(), cells.UMAP1.max()
    y_min, y_max = cells.UMAP2.min(), cells.UMAP2.max()
    ax.set(xlim=(x_min - 0.04 * (x_max - x_min), x_max + 0.42 * (x_max - x_min)))
    ax.set(ylim=(y_min - 0.05 * (y_max - y_min), y_max + 0.04 * (y_max - y_min)))
    ax.set(xticks=[], yticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.text(0.015, 0.985, "23.6%", transform=ax.transAxes, fontsize=5.0, color=BLUE, fontweight="bold", va="top")
    ax.text(0.115, 0.974, "→", transform=ax.transAxes, fontsize=6.0, color=GRID, fontweight="bold", va="top")
    ax.text(0.170, 0.985, "42.4%", transform=ax.transAxes, fontsize=7.4, color=TEAL, fontweight="bold", va="top")
    ax.text(0.170, 0.895, "all-cell accuracy", transform=ax.transAxes, fontsize=3.0, color=MUTED, va="top")
    ax.text(0.325, 0.965, "+18.7 pp", transform=ax.transAxes, fontsize=4.0, color=ORANGE, fontweight="bold", va="top")

    delta_map = gains.set_index("held_out_species").delta.to_dict()
    zoom_species(ax, [0.735, 0.54, 0.245, 0.41], cells, "Catharanthus roseus", delta_map["Catharanthus roseus"])
    zoom_species(ax, [0.735, 0.07, 0.245, 0.41], cells, "Fragaria vesca", delta_map["Fragaria vesca"])

    legend_order = ["rescued", "retained correct", "lost", "persistent error", "open / unavailable"]
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor=CHANGE_PALETTE[name],
            markeredgewidth=0,
            markersize=3.0,
            label=f"{name} {cells.change_vs_centroid.eq(name).mean():.0%}",
        )
        for name in legend_order
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.0, -0.145),
        frameon=False,
        fontsize=3.0,
        ncol=3,
        handletextpad=0.2,
        columnspacing=0.55,
    )
    return cells[
        [
            "cell_id",
            "species",
            "organ",
            "truth_label",
            "gate_prediction",
            "centroid_prediction",
            "covered",
            "change_vs_centroid",
            "UMAP1",
            "UMAP2",
        ]
    ].copy()


def bootstrap_deltas(cells: pd.DataFrame, draws: int = 1200) -> pd.DataFrame:
    rng = np.random.default_rng(20260802)
    groups = [group.index.to_numpy() for _, group in cells.groupby("species", sort=True)]
    gate_correct = cells.gate_correct.to_numpy(dtype=bool)
    centroid_correct = cells.centroid_correct.to_numpy(dtype=bool)
    covered = cells.covered.to_numpy(dtype=bool)
    rows: list[dict[str, float | int]] = []
    for draw in range(draws):
        selected = np.concatenate([rng.choice(indices, len(indices), replace=True) for indices in groups])
        covered_selected = selected[covered[selected]]
        rows.append(
            {
                "draw": draw,
                "delta_all_cell": float(gate_correct[selected].mean() - centroid_correct[selected].mean()),
                "delta_covered": float(gate_correct[covered_selected].mean() - centroid_correct[covered_selected].mean()),
            }
        )
    return pd.DataFrame(rows)


def panel_trajectory(fig: plt.Figure, bounds: list[float], progression: pd.DataFrame, bootstrap: pd.DataFrame) -> None:
    container = fig.add_axes(bounds)
    panel_label(container, "c", "Matched-denominator performance and paired uncertainty")
    container.set_axis_off()

    top = container.inset_axes([0.0, 0.36, 1.0, 0.64])
    x = np.arange(len(progression))
    series = [
        ("all-cell", "all_cell_accuracy", BLUE),
        ("covered", "covered_label_accuracy", TEAL),
        ("macro-F1", "macro_f1", PURPLE),
    ]
    for index, (label, column, color) in enumerate(series):
        values = progression[column].to_numpy(float)
        top.plot(x, values, color=color, lw=1.55, marker="o", ms=4.1, markeredgecolor="white", markeredgewidth=0.55, zorder=4)
        top.fill_between(x, np.maximum(0, values - 0.012), np.minimum(1, values + 0.012), color=color, alpha=0.10, zorder=2)
        top.text(x[-1] + 0.08, values[-1], f"{label} {values[-1]:.1%}", color=color, fontsize=3.2, va="center", fontweight="bold")
    top.axhline(progression.coverage.iloc[0], color=ORANGE, lw=0.75, ls=(0, (3, 2)), zorder=1)
    top.text(-0.18, progression.coverage.iloc[0] + 0.018, "coverage 55.9%", color=ORANGE, fontsize=3.0)
    top.set(
        xlim=(-0.22, 3.80),
        ylim=(0.12, 0.83),
        xticks=x,
        xticklabels=["centroid", "expression\nSTC", "neural\nSTC", "context\ngate"],
        yticks=[0.2, 0.4, 0.6, 0.8],
        yticklabels=["20", "40", "60", "80"],
    )
    top.tick_params(axis="both", labelsize=3.0, length=0, pad=1.2)
    top.grid(axis="y", color=GRID, linewidth=0.55)
    for side in ("top", "right", "left", "bottom"):
        top.spines[side].set_visible(False)
    top.text(-0.24, 0.80, "%", fontsize=3.1, color=MUTED, va="center")

    bottom = container.inset_axes([0.0, 0.0, 1.0, 0.27])
    values = [bootstrap.delta_all_cell.to_numpy(), bootstrap.delta_covered.to_numpy()]
    violins = bottom.violinplot(values, positions=[0, 1], vert=False, widths=0.66, showmeans=False, showmedians=False, showextrema=False)
    for body, color in zip(violins["bodies"], [BLUE, TEAL], strict=True):
        body.set_facecolor(color)
        body.set_edgecolor("white")
        body.set_alpha(0.72)
    for y, array, color in zip([0, 1], values, [BLUE, TEAL], strict=True):
        low, median, high = np.quantile(array, [0.025, 0.5, 0.975])
        bottom.hlines(y, low, high, color=INK, lw=0.85, zorder=4)
        bottom.scatter([median], [y], s=12, color=color, edgecolor="white", linewidth=0.45, zorder=5)
        bottom.text(high + 0.006, y, f"{median:+.1%}", fontsize=3.0, color=color, fontweight="bold", va="center")
    bottom.axvline(0, color=GREY, lw=0.7, ls="--")
    bottom.set(
        yticks=[0, 1],
        yticklabels=["all-cell Δ", "covered Δ"],
        xlabel="paired stratified bootstrap gain",
        xlim=(min(0, bootstrap.delta_all_cell.min()) - 0.01, bootstrap.delta_covered.max() + 0.055),
    )
    bottom.tick_params(axis="both", labelsize=3.0, length=0, pad=1.0)
    bottom.grid(axis="x", color=GRID, lw=0.45)
    for side in ("top", "right", "left"):
        bottom.spines[side].set_visible(False)
    bottom.spines["bottom"].set_color(GRID)


def species_response(cells: pd.DataFrame, gains: pd.DataFrame, routing: pd.DataFrame) -> pd.DataFrame:
    order = ["rescued", "retained correct", "lost", "persistent error", "open / unavailable"]
    fate = pd.crosstab(cells.species, cells.change_vs_centroid).reindex(columns=order, fill_value=0)
    fate = fate.div(fate.sum(axis=1), axis=0)
    family_by_species = {
        "Arabidopsis thaliana": "Brassicaceae",
        "Brassica rapa": "Brassicaceae",
        "Catharanthus roseus": "Apocynaceae",
        "Eutrema salsugineum": "Brassicaceae",
        "Fragaria vesca": "Rosaceae",
        "Gossypium bickii": "Malvaceae",
        "Gossypium hirsutum": "Malvaceae",
        "Triticum aestivum": "Poaceae",
    }
    routing = routing.copy()
    routing["family"] = routing.held_out_species.map(family_by_species)
    frame = gains.merge(
        routing[["held_out_species", "selected_expert", "training_support", "family"]],
        on="held_out_species",
        validate="one_to_one",
    ).merge(fate.reset_index(names="held_out_species"), on="held_out_species", validate="one_to_one")
    return frame


def panel_species_tree(ax: plt.Axes, frame: pd.DataFrame) -> None:
    panel_label(ax, "d", "Phylogeny-linked species response")
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(-0.75, len(frame) - 0.15))
    family_order = ["Brassicaceae", "Apocynaceae", "Rosaceae", "Malvaceae", "Poaceae"]
    species_order: list[str] = []
    for family in family_order:
        species_order.extend(frame.loc[frame.family.eq(family), "held_out_species"].tolist())
    plot = frame.set_index("held_out_species").loc[species_order].reset_index()
    y_positions = np.arange(len(plot) - 1, -1, -1)

    root_x, family_x, leaf_x = 0.025, 0.115, 0.235
    root_y = float(np.mean(y_positions))
    ax.scatter([root_x], [root_y], s=14, color=INK, edgecolor="white", linewidth=0.35, zorder=5)
    for family in family_order:
        rows = plot.index[plot.family.eq(family)].tolist()
        if not rows:
            continue
        ys = [y_positions[index] for index in rows]
        fy = float(np.mean(ys))
        color = FAMILY_PALETTE[family]
        curved_line(ax, (root_x, root_y), (family_x, fy), color, 1.05, 0.56)
        ax.scatter([family_x], [fy], s=18, color=color, edgecolor="white", linewidth=0.45, zorder=5)
        ax.text(family_x, fy + 0.32, family.replace("aceae", "."), fontsize=2.8, color=color, ha="center", fontweight="bold")
        for row_index in rows:
            y = y_positions[row_index]
            curved_line(ax, (family_x, fy), (leaf_x, y), color, 0.78, 0.62)
            ax.scatter([leaf_x], [y], s=18, color=color, edgecolor="white", linewidth=0.45, zorder=5)

    x0, x1 = 0.48, 0.94
    outcome_order = ["rescued", "retained correct", "lost", "persistent error", "open / unavailable"]
    for row_index, row in plot.iterrows():
        y = y_positions[row_index]
        ax.text(0.265, y, short_species(row.held_out_species), fontsize=3.05, color=INK, va="center", fontweight="bold")
        expert_color = TEAL if row.selected_expert == "organ prior" else BLUE
        ax.scatter([0.425], [y], s=13, color=expert_color, marker="D" if row.selected_expert == "organ prior" else "o", edgecolor="white", linewidth=0.4)
        left = x0
        for outcome in outcome_order:
            width = (x1 - x0) * float(row[outcome])
            if width > 0:
                ax.add_patch(
                    patches.Rectangle(
                        (left, y - 0.25),
                        width,
                        0.50,
                        facecolor=CHANGE_PALETTE[outcome],
                        edgecolor="white",
                        linewidth=0.25,
                    )
                )
            left += width
        ax.text(0.965, y, f"{row.accuracy_all_gate:.0%}", fontsize=3.05, color=TEAL if row.accuracy_all_gate > 0 else MUTED, va="center", ha="right", fontweight="bold")

    ax.text(0.315, len(plot) - 0.25, "held-out species", fontsize=3.0, color=MUTED, ha="center")
    ax.text(0.425, len(plot) - 0.25, "expert", fontsize=3.0, color=MUTED, ha="center")
    ax.text((x0 + x1) / 2, len(plot) - 0.25, "cell fate relative to centroid", fontsize=3.0, color=MUTED, ha="center")
    ax.text(0.965, len(plot) - 0.25, "acc.", fontsize=3.0, color=MUTED, ha="right")

    handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", markerfacecolor=CHANGE_PALETTE[name], markeredgewidth=0, markersize=3.0, label=name)
        for name in outcome_order
    ]
    handles.extend(
        [
            plt.Line2D([0], [0], marker="D", linestyle="", markerfacecolor=TEAL, markeredgewidth=0, markersize=3.0, label="organ prior"),
            plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=BLUE, markeredgewidth=0, markersize=3.0, label="expression"),
        ]
    )
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.58, -0.20), ncol=4, frameon=False, fontsize=2.75, handletextpad=0.16, columnspacing=0.45)


def ablation_matrix(ablations: pd.DataFrame) -> tuple[np.ndarray, list[str], list[float]]:
    row_order = [
        ("knn", "organ", "all"),
        ("knn", "organ", "clean"),
        ("knn", "tissue", "all"),
        ("knn", "tissue", "clean"),
        ("topk", "organ", "all"),
        ("topk", "organ", "clean"),
        ("topk", "tissue", "all"),
        ("topk", "tissue", "clean"),
    ]
    weights = sorted(ablations.prior_weight.unique())
    matrix = np.full((len(row_order), len(weights)), np.nan)
    for row, (decoder, context, variant) in enumerate(row_order):
        part = ablations.loc[
            ablations.decoder.eq(decoder) & ablations.context.eq(context) & ablations.variant.eq(variant)
        ].set_index("prior_weight")
        for column, weight in enumerate(weights):
            matrix[row, column] = float(part.loc[weight, "all_cell_accuracy"])
    labels = [f"{decoder.upper()}·{context[:3]}" + ("*" if variant == "clean" else "") for decoder, context, variant in row_order]
    return matrix, labels, weights


def panel_ablation_hex(ax: plt.Axes, ablations: pd.DataFrame, gate_score: float) -> None:
    panel_label(ax, "e", "Forty-eight context-prior perturbations")
    matrix, labels, weights = ablation_matrix(ablations)
    cmap = LinearSegmentedColormap.from_list("hexfield", ["#E8EFF2", "#9CCADD", BLUE, TEAL, DEEP_TEAL])
    norm = Normalize(vmin=0.22, vmax=gate_score)
    radius = 0.44
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            x = column + 0.52 * (row % 2)
            y = matrix.shape[0] - 1 - row
            value = matrix[row, column]
            hexagon = patches.RegularPolygon(
                (x, y),
                numVertices=6,
                radius=radius,
                orientation=np.pi / 6,
                facecolor=cmap(norm(value)),
                edgecolor="white",
                linewidth=0.58,
            )
            ax.add_patch(hexagon)
            ax.text(x, y, f"{value:.0%}", ha="center", va="center", fontsize=2.8, color="white" if value >= 0.34 else INK, fontweight="bold")
    best_index = np.unravel_index(np.nanargmax(matrix), matrix.shape)
    bx = best_index[1] + 0.52 * (best_index[0] % 2)
    by = matrix.shape[0] - 1 - best_index[0]
    ax.add_patch(patches.Circle((bx, by), 0.53, fill=False, edgecolor=ORANGE, linewidth=1.0))
    ax.annotate(
        f"best prior {matrix[best_index]:.1%}",
        xy=(bx, by),
        xytext=(6.55, 6.85),
        fontsize=3.0,
        color=ORANGE,
        fontweight="bold",
        arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.65),
    )
    ax.scatter([6.8], [3.65], s=165, color=TEAL, edgecolor="white", linewidth=0.8, zorder=5)
    ax.text(6.8, 3.65, f"{gate_score:.0%}", ha="center", va="center", fontsize=3.8, color="white", fontweight="bold", zorder=6)
    ax.text(6.8, 2.95, "context gate", ha="center", fontsize=3.0, color=TEAL, fontweight="bold")
    ax.plot([5.7, 6.5], [3.65, 3.65], color=GRID, lw=1.0, zorder=1)
    ax.set(xlim=(-1.22, 7.45), ylim=(-0.75, 8.05), xticks=[], yticks=[])
    for row, label in enumerate(labels):
        ax.text(-0.72, matrix.shape[0] - 1 - row, label, ha="right", va="center", fontsize=2.85, color=INK)
    for column, weight in enumerate(weights):
        ax.text(column + 0.24, -0.58, f"{weight:g}", ha="center", fontsize=2.8, color=MUTED)
    ax.text(2.75, -0.72, "context-prior weight", ha="center", fontsize=3.0, color=MUTED)
    for spine in ax.spines.values():
        spine.set_visible(False)


def render() -> None:
    setup()
    helper = load_module("v10_context_helpers", ROOT / "scripts" / "render_v10_context_stc_figure.py")
    v10_plot = load_module("v10_context_plot", ROOT / "scripts" / "render_v10_context_stc_figure_v2.py")
    runner = load_module("context_v14_runner", ROOT / "scripts" / "run_revision_v14_context_stc_benchmark.py")

    v14 = helper.read_json(helper.V14)
    innovation = helper.read_json(helper.INNOVATION)
    v10 = helper.read_json(helper.V10)
    progression = helper.progression_frame(innovation)
    ablations = helper.ablation_frame(v14)
    gate = helper.gate_records(v14)
    centroid = helper.centroid_records(v10)
    cells = v10_plot.cellwise_predictions(runner)
    gains = gate[["held_out_species", "accuracy_all", "coverage", "n_test"]].merge(
        centroid[["held_out_species", "accuracy_all"]],
        on="held_out_species",
        suffixes=("_gate", "_centroid"),
        validate="one_to_one",
    )
    gains["delta"] = gains.accuracy_all_gate - gains.accuracy_all_centroid
    bootstrap = bootstrap_deltas(cells)
    response = species_response(cells, gains, gate)

    fig = plt.figure(figsize=(7.25, 7.90))
    ax_a = fig.add_axes([0.042, 0.570, 0.946, 0.355])
    ax_b = fig.add_axes([0.050, 0.300, 0.505, 0.215])
    trajectory_bounds = [0.600, 0.300, 0.370, 0.215]
    ax_d = fig.add_axes([0.050, 0.060, 0.545, 0.180])
    ax_e = fig.add_axes([0.640, 0.060, 0.330, 0.180])

    architecture = panel_mechanism(ax_a)
    geometry = panel_rescue_atlas(ax_b, cells, gains)
    panel_trajectory(fig, trajectory_bounds, progression, bootstrap)
    panel_species_tree(ax_d, response)
    panel_ablation_hex(ax_e, ablations, float(v14["best_method"]["summary"]["accuracy_all"]))

    fig.text(0.042, 0.980, "Source context improves coverage-aware species transfer", fontsize=9.2, fontweight="bold", color=INK, va="top")
    fig.text(
        0.988,
        0.980,
        "8 held-out species · 3,964 cells · 0 target labels · fixed denominator",
        fontsize=3.8,
        color=MUTED,
        ha="right",
        va="top",
    )
    fig.add_artist(plt.Line2D([0.042, 0.988], [0.545, 0.545], transform=fig.transFigure, color=GRID, lw=0.65))

    for artist in fig.findobj(match=Text):
        if artist.get_fontsize() < 3.0:
            artist.set_fontsize(3.0)

    stem = "plant_cellfm_v12_fig3_context_stc"
    tables = {
        "mechanism_contract": architecture,
        "cellwise_rescue_atlas": geometry,
        "method_progression": progression,
        "paired_stratified_bootstrap": bootstrap,
        "species_response": response,
        "context_ablation_landscape": ablations,
    }
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for suffix, options in (("svg", {"dpi": 600}), ("pdf", {"dpi": 600}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)
    print(
        {
            "figure": str(MAIN / f"{stem}.png"),
            "mechanism_layer": "scripted_vector",
            "cells": len(cells),
            "bootstrap_draws": len(bootstrap),
            "source_tables": len(tables),
        }
    )


if __name__ == "__main__":
    render()
