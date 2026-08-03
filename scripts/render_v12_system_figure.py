from __future__ import annotations

"""Render the v12 Plant-CellFM system overview with vector mechanism layers."""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.path import Path as MplPath
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

SPECIES_COLORS = {
    "Arabidopsis thaliana": BLUE,
    "Fragaria vesca": TEAL,
    "Catharanthus roseus": ORANGE,
    "Brassica rapa": PURPLE,
    "Gossypium bickii": RED,
    "Gossypium hirsutum": CYAN,
    "Eutrema salsugineum": "#63469A",
    "Triticum aestivum": NAVY,
}
ORGAN_COLORS = {"root": TEAL, "leaf": "#E6A400", "shoot_apex": BLUE, "callus": PURPLE}


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
    return pd.read_csv(V11_SOURCE / f"plant_cellfm_v11_fig1_system_{name}.tsv", sep="\t")


def short_species(value: str) -> str:
    parts = str(value).split()
    return f"{parts[0][0]}. {parts[-1]}" if len(parts) > 1 else str(value)


def panel_label(ax: plt.Axes, key: str, title: str, y: float = 1.025) -> None:
    ax.text(-0.045, y, key, transform=ax.transAxes, fontsize=8.0, fontweight="bold", color=INK, va="bottom")
    ax.text(0.0, y, title, transform=ax.transAxes, fontsize=5.6, fontweight="bold", color=INK, va="bottom")


def direct_label(ax: plt.Axes, x: float, y: float, text: str, color: str = INK, size: float = 3.2) -> None:
    artist = ax.text(x, y, text, ha="center", va="center", fontsize=size, color=color, fontweight="bold", zorder=9)
    artist.set_path_effects([path_effects.withStroke(linewidth=1.5, foreground="white")])


def curved_line(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str, width: float, alpha: float = 0.65) -> None:
    x0, y0 = start
    x1, y1 = end
    path = MplPath(
        [(x0, y0), (x0 + 0.42 * (x1 - x0), y0), (x0 + 0.58 * (x1 - x0), y1), (x1, y1)],
        [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4],
    )
    ax.add_patch(patches.PathPatch(path, facecolor="none", edgecolor=color, linewidth=width, alpha=alpha, capstyle="round"))


def panel_system(ax: plt.Axes) -> pd.DataFrame:
    panel_label(ax, "a", "Coverage-aware plant single-cell annotation framework", y=1.01)
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(0, 1))

    ax.add_patch(
        patches.FancyBboxPatch(
            (0.005, 0.030),
            0.990,
            0.900,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            facecolor="#F7FAFB",
            edgecolor="#DCE7EB",
            linewidth=0.80,
            zorder=0,
        )
    )
    stages = [
        (0.055, 0.590, 0.150, 0.245, "public plant\nmatrices", "5 train species\n8 evaluation species", BLUE),
        (0.250, 0.590, 0.155, 0.245, "gene identity\nprojection", "exact IDs +\northogroups", TEAL),
        (0.455, 0.565, 0.150, 0.295, "frozen\nencoder", "4 layers | d=256\nCLS cell state", NAVY),
        (0.660, 0.645, 0.130, 0.155, "coverage\naudit", "complete\ncell denominator", ORANGE),
        (0.825, 0.730, 0.130, 0.125, "source-context\nrouting", "organ + family\nmetadata", PURPLE),
        (0.825, 0.540, 0.130, 0.125, "rank-8\nadapter", "target support\nheld-out query", TEAL),
    ]
    for x, y, width, height, title, subtitle, color in stages:
        ax.add_patch(
            patches.FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.008,rounding_size=0.014",
                facecolor=mpl.colors.to_rgba(color, 0.105),
                edgecolor=color,
                linewidth=0.95,
                zorder=2,
            )
        )
        ax.text(x + width / 2, y + height * 0.61, title, ha="center", va="center", fontsize=4.15, color=INK, fontweight="bold", linespacing=0.95)
        ax.text(x + width / 2, y + height * 0.25, subtitle, ha="center", va="center", fontsize=3.0, color=MUTED, linespacing=0.95)

    connectors = [
        ((0.205, 0.710), (0.250, 0.710), BLUE),
        ((0.405, 0.710), (0.455, 0.710), TEAL),
        ((0.605, 0.710), (0.660, 0.725), NAVY),
        ((0.790, 0.725), (0.825, 0.790), PURPLE),
        ((0.790, 0.690), (0.825, 0.600), TEAL),
    ]
    for start, end, color in connectors:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="-|>", color=color, lw=1.20, shrinkA=0, shrinkB=0), zorder=3)

    rng = np.random.default_rng(260803)
    species_x = np.linspace(0.075, 0.185, 5)
    for index, color in enumerate([BLUE, TEAL, ORANGE, PURPLE, RED]):
        y = 0.830 + 0.040 * np.sin(index)
        ax.scatter([species_x[index]], [y], s=36, color=color, edgecolor="white", linewidth=0.45, zorder=5)
        ax.scatter(
            species_x[index] + rng.normal(0, 0.010, 18),
            0.470 + rng.normal(0, 0.040, 18),
            s=4.5,
            color=mpl.colors.to_rgba(color, 0.40),
            linewidths=0,
            zorder=1,
        )
    for idx, y in enumerate([0.822, 0.775, 0.728, 0.681, 0.634]):
        ax.add_patch(
            patches.Rectangle(
                (0.278 + idx * 0.019, y - 0.014),
                0.050,
                0.024,
                facecolor=mpl.colors.to_rgba(TEAL if idx % 2 else BLUE, 0.26),
                edgecolor="white",
                linewidth=0.35,
                zorder=4,
            )
        )
    for radius, color in [(0.105, BLUE), (0.080, TEAL), (0.055, PURPLE)]:
        ax.add_patch(patches.Circle((0.530, 0.710), radius, fill=False, edgecolor=color, linewidth=1.05, alpha=0.70, zorder=5))
    ax.scatter([0.530], [0.710], s=52, color=NAVY, edgecolor="white", linewidth=0.6, zorder=6)

    outputs = [
        (0.695, 0.330, "39.96%\nall-cell transfer", BLUE),
        (0.825, 0.330, "75.89%\n64-cell support", TEAL),
        (0.940, 0.330, "84.98%\nSorghum broad", ORANGE),
    ]
    for x, y, text, color in outputs:
        ax.add_patch(
            patches.FancyBboxPatch(
                (x - 0.052, y - 0.052),
                0.104,
                0.104,
                boxstyle="round,pad=0.006,rounding_size=0.012",
                facecolor=mpl.colors.to_rgba(color, 0.12),
                edgecolor=color,
                linewidth=0.85,
                zorder=4,
            )
        )
        ax.text(x, y + 0.010, text, ha="center", va="center", fontsize=3.25, color=color, fontweight="bold", linespacing=0.95, zorder=5)
        curved_line(ax, (0.530, 0.565), (x, y + 0.070), color, 0.90, 0.35)

    specs = [
        (0.285, "rank-token alignment"),
        (0.460, "K=512/1024 by checkpoint"),
        (0.610, "L=4 | H=8 | d=256"),
        (0.780, "LoRA r=8"),
        (0.905, "annotation + marker output"),
    ]
    for x, text in specs:
        ax.scatter([x - 0.047], [0.085], s=9, color=TEAL, edgecolor="white", linewidth=0.35, zorder=9)
        direct_label(ax, x, 0.085, text, MUTED, 3.0)
    return pd.DataFrame(
        [
            {"stage": "frozen_corpus", "cells": 272732, "species": 5},
            {"stage": "orthology_rank_tokens", "embedding_dimension": 256},
            {"stage": "shared_backbone", "layers": 4, "attention_heads": 8, "ffn_width": 768},
            {"stage": "adapter_bank", "live_adapters": 24, "lora_rank": 8},
            {"stage": "output_tasks", "tasks": "coverage_audit|context_routing|annotation|markers|adaptation"},
        ]
    )

def panel_corpus_wheel(fig: plt.Figure, bounds: list[float], species: pd.DataFrame, states: pd.DataFrame) -> None:
    container = fig.add_axes(bounds)
    panel_label(container, "b", "Frozen corpus composition")
    container.set_axis_off()
    ax = container.inset_axes([0.03, -0.02, 0.94, 1.02], projection="polar")
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2)
    species = species.sort_values("cells", ascending=False).reset_index(drop=True)
    starts = np.r_[0, np.cumsum(species.fraction.to_numpy())[:-1]] * 2 * np.pi
    widths = species.fraction.to_numpy() * 2 * np.pi
    for start, width, (_, row) in zip(starts, widths, species.iterrows(), strict=True):
        color = row.color
        ax.bar(start + width / 2, 0.24, width=width * 0.97, bottom=0.30, color=color, edgecolor="white", linewidth=0.7)
        angle = start + width / 2
        if width > 0.24:
            ax.text(angle, 0.425, f"{short_species(row.species)}\n{row.cells / 1000:.0f}k", fontsize=2.8, ha="center", va="center", color="white", fontweight="bold")

    state_colors = mpl.colormaps["YlGnBu"](np.linspace(0.28, 0.92, len(states)))
    state_width = 2 * np.pi / len(states)
    states = states.sort_values("cells", ascending=False).reset_index(drop=True)
    for index, (_, row) in enumerate(states.iterrows()):
        angle = index * state_width + state_width / 2
        height = 0.10 + 0.18 * np.sqrt(float(row.fraction) / states.fraction.max())
        ax.bar(angle, height, width=state_width * 0.88, bottom=0.62, color=state_colors[index], edgecolor="white", linewidth=0.35)
        if index < 5:
            ax.text(angle, 0.89, row.cell_state.replace(" system", "\nsystem"), fontsize=2.65, ha="center", va="center", color=INK)

    ax.text(0, 0.10, "272,732", fontsize=7.2, color=INK, fontweight="bold", ha="center", va="center")
    ax.text(0, 0.20, "cells", fontsize=3.0, color=MUTED, ha="center", va="center")
    ax.set_ylim(0, 0.97)
    ax.set_axis_off()
    container.text(0.06, 0.02, "inner ring: five frozen-corpus species", fontsize=3.0, color=MUTED)
    container.text(0.94, 0.02, "outer ring: 12 reported cell states", fontsize=3.0, color=MUTED, ha="right")


def density_contours(ax: plt.Axes, frame: pd.DataFrame, color: str) -> None:
    hist, x_edges, y_edges = np.histogram2d(frame.UMAP1, frame.UMAP2, bins=(74, 60))
    if gaussian_filter is not None:
        hist = gaussian_filter(hist, sigma=1.8)
    positive = hist[hist > 0]
    if positive.size < 5:
        return
    levels = np.unique(np.quantile(positive, [0.60, 0.79, 0.92]))
    if len(levels) < 2:
        return
    x_mid = (x_edges[:-1] + x_edges[1:]) / 2
    y_mid = (y_edges[:-1] + y_edges[1:]) / 2
    ax.contour(x_mid, y_mid, hist.T, levels=levels, colors=color, linewidths=[0.32, 0.52, 0.75][: len(levels)], alpha=0.45)


def scatter_map(ax: plt.Axes, embedding: pd.DataFrame, column: str, palette: dict[str, str], title: str, size: float) -> None:
    for value, part in embedding.groupby(column, sort=False):
        color = palette.get(value, GREY)
        ax.scatter(part.UMAP1, part.UMAP2, s=size, color=color, alpha=0.75, linewidths=0)
    density_contours(ax, embedding, "#8299A6")
    ax.set(xticks=[], yticks=[])
    ax.set_facecolor(PALE)
    ax.set_title(title, loc="left", fontsize=3.4, color=INK, fontweight="bold", pad=1.4)
    for spine in ax.spines.values():
        spine.set_visible(False)


def panel_embedding(fig: plt.Figure, bounds: list[float], embedding: pd.DataFrame) -> None:
    container = fig.add_axes(bounds)
    panel_label(container, "c", "Held-out representation atlas")
    container.set_axis_off()
    main = container.inset_axes([0.0, 0.0, 0.72, 1.0])
    scatter_map(main, embedding, "species", SPECIES_COLORS, "species geometry", 2.0)
    main.text(0.02, 0.96, f"{len(embedding):,} cells", transform=main.transAxes, fontsize=3.4, color=INK, fontweight="bold", va="top")
    inset = container.inset_axes([0.74, 0.05, 0.26, 0.90])
    scatter_map(inset, embedding, "organ", ORGAN_COLORS, "organ context", 1.25)
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgewidth=0, markersize=2.8, label=short_species(name))
        for name, color in SPECIES_COLORS.items()
        if name in set(embedding.species)
    ]
    container.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.37, -0.16), frameon=False, fontsize=2.75, ncol=4, handletextpad=0.15, columnspacing=0.45)


def panel_adapters(ax: plt.Axes, architecture: pd.DataFrame) -> None:
    panel_label(ax, "d", "Adapter ecology around a frozen core")
    adapters = architecture.loc[architecture.component.eq("adapter")].copy().head(24).reset_index(drop=True)
    evidence = pd.to_numeric(adapters.evidence_datasets, errors="coerce").fillna(0).to_numpy()
    angles = np.linspace(0, 2 * np.pi, len(adapters), endpoint=False)
    radii = 0.39 + 0.07 * np.sin(angles * 3 + 0.5)
    x = 0.5 + radii * np.cos(angles)
    y = 0.51 + radii * np.sin(angles)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.set_axis_off()

    ax.add_patch(patches.Circle((0.5, 0.51), 0.155, facecolor="#F5F9FA", edgecolor=NAVY, linewidth=1.1))
    for radius, color in [(0.125, BLUE), (0.095, TEAL), (0.065, PURPLE), (0.035, ORANGE)]:
        ax.add_patch(patches.Circle((0.5, 0.51), radius, fill=False, edgecolor=color, linewidth=0.85, alpha=0.72))
    ax.text(0.5, 0.525, "24", ha="center", va="center", fontsize=8.0, color=INK, fontweight="bold")
    ax.text(0.5, 0.455, "live adapters", ha="center", fontsize=3.0, color=MUTED)

    for index, row in adapters.iterrows():
        active = evidence[index] > 0
        color = TEAL if active else "#8EBECD"
        width = 0.5 + 0.20 * np.sqrt(evidence[index])
        curved_line(ax, (0.5, 0.51), (x[index], y[index]), color, width, 0.32 if active else 0.18)
        size = 20 + 18 * np.sqrt(evidence[index] + 0.2)
        ax.scatter([x[index]], [y[index]], s=size, color=color, edgecolor="white", linewidth=0.50, zorder=5)
        species = str(row.species)
        if evidence[index] > 0 or "Saussurea" in species:
            label = short_species(species).replace("Group", "")
            dx = 0.024 * np.cos(angles[index])
            dy = 0.024 * np.sin(angles[index])
            ax.text(x[index] + dx, y[index] + dy, label, fontsize=2.65, color=INK, ha="center", va="center")
    ax.text(0.02, 0.02, "node area scales with supporting datasets", fontsize=3.0, color=MUTED)
    ax.scatter([0.74, 0.86], [0.045, 0.045], s=[18, 18], color=[TEAL, "#8EBECD"], edgecolor="white", linewidth=0.3)
    ax.text(0.76, 0.045, "evidence-linked", va="center", fontsize=2.8, color=MUTED)
    ax.text(0.88, 0.045, "fallback", va="center", fontsize=2.8, color=MUTED)


def panel_capabilities(ax: plt.Axes, routes: pd.DataFrame, model_card: pd.DataFrame) -> None:
    panel_label(ax, "e", "Capability routes and deployable footprint")
    colors = {"strict": BLUE, "support": TEAL, "label-free": ORANGE, "adapter": PURPLE}
    routes = routes.copy()
    routes["route_label"] = routes.route.replace({"adapter": "adapter library"})
    y = np.arange(len(routes))[::-1]
    for yi, (_, row) in zip(y, routes.iterrows(), strict=True):
        color = colors[row.route]
        accuracy = float(row.all_cell_accuracy)
        ax.hlines(yi, 0, accuracy, color=color, lw=8.0, alpha=0.88, zorder=2)
        ax.scatter([accuracy], [yi], s=42, color=color, edgecolor="white", linewidth=0.65, zorder=4)
        ax.text(accuracy + 0.018, yi, f"{accuracy:.0%}", va="center", fontsize=3.15, color=color, fontweight="bold")
        access = str(row.label_access)
        ax.text(-0.02, yi, f"{row.route_label}\naccess: {access}", ha="right", va="center", fontsize=2.9, color=INK, fontweight="bold")
        if pd.notna(row.coverage):
            ax.scatter([float(row.coverage)], [yi + 0.13], marker="|", s=42, color=ORANGE, linewidth=1.0, zorder=5)
        if pd.notna(row.macro_f1):
            ax.scatter([float(row.macro_f1)], [yi - 0.13], marker="D", s=14, color=DEEP_TEAL, edgecolor="white", linewidth=0.35, zorder=5)
    ax.set(xlim=(0, 1.02), ylim=(-0.75, len(routes) - 0.20), xticks=[0, 0.25, 0.5, 0.75, 1.0], xticklabels=["0", "25", "50", "75", "100"], yticks=[])
    ax.tick_params(axis="x", labelsize=3.0, length=0, pad=1.0)
    ax.grid(axis="x", color=GRID, linewidth=0.55, zorder=0)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.text(0.98, -0.62, "all-cell accuracy (%)", ha="right", fontsize=3.0, color=MUTED)

    labels = {
        "embedding": "d=256",
        "encoder layers": "L=4",
        "attention heads": "H=8",
        "FFN width": "FFN=768",
        "live adapters": "A=24",
        "LoRA rank": "r=8",
    }
    for index, (_, row) in enumerate(model_card.iterrows()):
        x = (index + 0.5) / len(model_card)
        ax.plot([x - 0.050, x + 0.050], [-0.48, -0.48], color=row.color, lw=3.0, solid_capstyle="round", clip_on=False)
        ax.text(x, -0.66, labels.get(row.component, row.component), ha="center", fontsize=2.8, color=INK, fontweight="bold")


def render() -> None:
    setup()
    species = read_table("corpus_species")
    states = read_table("corpus_cell_state_coverage")
    routes = read_table("evaluation_map")
    model_card = read_table("model_card_architecture")
    architecture = read_table("architecture")
    embedding = read_table("strict_embedding")

    fig = plt.figure(figsize=(7.25, 7.90))
    ax_a = fig.add_axes([0.042, 0.570, 0.946, 0.355])
    corpus_bounds = [0.050, 0.300, 0.275, 0.205]
    embedding_bounds = [0.365, 0.300, 0.605, 0.205]
    ax_d = fig.add_axes([0.050, 0.060, 0.420, 0.170])
    ax_e = fig.add_axes([0.545, 0.090, 0.425, 0.140])

    mechanism = panel_system(ax_a)
    panel_corpus_wheel(fig, corpus_bounds, species, states)
    panel_embedding(fig, embedding_bounds, embedding)
    panel_adapters(ax_d, architecture)
    panel_capabilities(ax_e, routes, model_card)

    fig.text(0.042, 0.980, "Plant-CellFM: a coverage-aware framework for plant single-cell annotation", fontsize=9.15, fontweight="bold", color=INK, va="top")
    fig.text(0.988, 0.980, "272,732 frozen-corpus cells · 24 live adapters · shared transformer backbone", fontsize=3.8, color=MUTED, ha="right", va="top")
    fig.add_artist(plt.Line2D([0.042, 0.988], [0.545, 0.545], transform=fig.transFigure, color=GRID, lw=0.65))

    for artist in fig.findobj(match=Text):
        if artist.get_fontsize() < 3.0:
            artist.set_fontsize(3.0)

    stem = "plant_cellfm_v12_fig1_system"
    tables = {
        "mechanism_contract": mechanism,
        "corpus_species": species,
        "corpus_cell_state_coverage": states,
        "evaluation_routes": routes,
        "model_card_architecture": model_card,
        "adapter_registry": architecture,
        "heldout_embedding": embedding,
    }
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for suffix, options in (("svg", {"dpi": 600}), ("pdf", {"dpi": 600}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)
    print({"figure": str(MAIN / f"{stem}.png"), "source_tables": len(tables), "mechanism_layer": "scripted_vector"})


if __name__ == "__main__":
    render()
