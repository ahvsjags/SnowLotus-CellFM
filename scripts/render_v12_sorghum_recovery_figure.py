from __future__ import annotations

"""Render the v12 Sorghum sealed-library validation figure."""

import importlib.util
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.path import Path as MplPath
from matplotlib.text import Text
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
V11 = ROOT / "figures" / "plant_cellfm_submission_v11"
OUT = ROOT / "figures" / "plant_cellfm_submission_v12"
MAIN = OUT / "main"
SOURCE = OUT / "source_data"
OLD_STEM = "plant_cellfm_v11_fig7_sorghum_recovery"
STEM = "plant_cellfm_v12_fig7_sorghum_recovery"

INK = "#102633"
MUTED = "#627887"
GRID = "#D9E4E9"
TEAL = "#008F87"
DEEP_TEAL = "#006B66"
BLUE = "#2377B9"
CYAN = "#35A7B8"
ORANGE = "#EB7A2A"
PURPLE = "#7B62A8"
GREY = "#AFC0C9"

TABLES = [
    "feature_transfer",
    "layer_recovery",
    "library_split",
    "matched_recovery",
    "per_state_f1",
    "root_layer_agreement",
    "sealed_test_cells",
    "state_support_geometry",
]


def load_plot_module():
    path = ROOT / "scripts" / "render_v9_sorghum_atlas_figure.py"
    spec = importlib.util.spec_from_file_location("plant_cellfm_v9_sorghum", path)
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


def read_table(name: str) -> pd.DataFrame:
    path = V11 / "source_data" / f"{OLD_STEM}_{name}.tsv"
    frame = pd.read_csv(path, sep="\t")
    frame.to_csv(SOURCE / f"{STEM}_{name}.tsv", sep="\t", index=False)
    return frame


def panel_label(ax: plt.Axes, key: str, title: str) -> None:
    ax.text(-0.065, 1.035, key, transform=ax.transAxes, fontsize=7.4, fontweight="bold", color=INK, va="bottom")
    ax.text(0.0, 1.035, title, transform=ax.transAxes, fontsize=5.25, fontweight="bold", color=INK, va="bottom")


def layer_umap_vector(ax: plt.Axes, cells: pd.DataFrame, column: str, title: str, palette: dict[str, str]) -> None:
    for name in reversed(palette):
        part = cells.loc[cells[column].eq(name)]
        ax.scatter(part.UMAP1, part.UMAP2, s=1.65, c=palette[name], alpha=0.79, linewidths=0)
    ax.set(xticks=[], yticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title, fontsize=4.25, color=INK, pad=1.2, fontweight="bold")


def correct_umap_vector(ax: plt.Axes, cells: pd.DataFrame) -> None:
    colors = np.where(cells.fine_correct, TEAL, "#C5555C")
    ax.scatter(cells.UMAP1, cells.UMAP2, s=1.65, c=colors, alpha=0.76, linewidths=0)
    ax.set(xticks=[], yticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("adapter: 27-state calls", fontsize=4.25, color=INK, pad=1.2, fontweight="bold")
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=TEAL, markeredgewidth=0, markersize=3.4, label="correct"),
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor="#C5555C", markeredgewidth=0, markersize=3.4, label="error"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.14), ncol=2, frameon=False, fontsize=3.8, handletextpad=0.22, columnspacing=0.6)


def panel_state_resolution_vector(ax: plt.Axes, per_state: pd.DataFrame, short_state) -> None:
    panel_label(ax, "d", "Sealed-library state resolution")
    frame = per_state.sort_values("f1", ascending=False).copy().reset_index(drop=True)
    values = frame[["precision", "recall", "f1"]].to_numpy(dtype=float)
    cmap = LinearSegmentedColormap.from_list("state_quality", ["#F5F8FA", "#BCE0DA", TEAL, DEEP_TEAL])
    ax.pcolormesh(
        np.arange(values.shape[1] + 1) - 0.5,
        np.arange(values.shape[0] + 1) - 0.5,
        values,
        cmap=cmap,
        vmin=0,
        vmax=1,
        shading="flat",
    )
    ax.set(xlim=(-0.5, values.shape[1] - 0.5), ylim=(values.shape[0] - 0.5, -0.5))
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            ax.text(col, row, f"{value:.0%}", ha="center", va="center", fontsize=3.0, color="white" if value >= 0.62 else INK, fontweight="bold")
    ax.set(xticks=np.arange(3), xticklabels=["precision", "recall", "F1"], yticks=np.arange(len(frame)), yticklabels=[short_state(value) for value in frame.author_annotation])
    ax.tick_params(axis="x", labelsize=3.45, length=0, pad=1.2)
    ax.tick_params(axis="y", labelsize=3.0, length=0, pad=0.9)
    for spine in ax.spines.values():
        spine.set_visible(False)


def panel_recovery(ax: plt.Axes, recovery: pd.DataFrame) -> None:
    panel_label(ax, "b", "A sealed library recovers both annotation levels")
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.text(0.17, 0.93, "frozen", ha="center", fontsize=3.25, color=MUTED, fontweight="bold")
    ax.text(0.84, 0.93, "Sorghum adapter", ha="center", fontsize=3.25, color=DEEP_TEAL, fontweight="bold")

    rows = [("accuracy", 0.67, BLUE), ("macro-F1", 0.27, TEAL)]
    for metric, y, color in rows:
        frozen = recovery.loc[(recovery.method == "Frozen root head") & (recovery.metric == metric)].iloc[0]
        adapter = recovery.loc[(recovery.method == "Sorghum LoRA adapter") & (recovery.metric == metric)].iloc[0]
        gain = float(adapter.point - frozen.point)
        ax.plot([0.20, 0.80], [y, y], color=GRID, lw=5.0, solid_capstyle="round", zorder=1)
        ax.annotate("", xy=(0.80, y), xytext=(0.25, y), arrowprops={"arrowstyle": "-|>", "lw": 2.25, "color": color, "shrinkA": 0, "shrinkB": 0})
        ax.scatter([0.17], [y], s=165, color="#DCE8EE", edgecolor="white", linewidth=0.7, zorder=3)
        ax.scatter([0.84], [y], s=250, color=color, edgecolor="white", linewidth=0.8, zorder=3)
        ax.text(0.17, y, f"{float(frozen.point):.1%}", ha="center", va="center", fontsize=5.0, color=INK, fontweight="bold")
        ax.text(0.84, y, f"{float(adapter.point):.1%}", ha="center", va="center", fontsize=5.0, color="white", fontweight="bold")
        ax.text(0.50, y + 0.085, f"+{gain:.1%}", ha="center", fontsize=4.2, color=color, fontweight="bold")
        ax.text(0.02, y + 0.105, metric, va="center", fontsize=3.4, color=INK, fontweight="bold")
        ax.text(0.17, y - 0.105, f"[{float(frozen.ci_low):.1%}, {float(frozen.ci_high):.1%}]", ha="center", fontsize=2.8, color=MUTED)
        ax.text(0.84, y - 0.105, f"[{float(adapter.ci_low):.1%}, {float(adapter.ci_high):.1%}]", ha="center", fontsize=2.8, color=MUTED)
    ax.text(0.02, 0.01, "n = 3,549 matched cells | 95% bootstrap CI", fontsize=3.0, color=MUTED)


def panel_transfer(ax: plt.Axes, transfer: pd.DataFrame) -> None:
    panel_label(ax, "c", "Orthogroup feature transfer")
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    frame = transfer.reset_index(drop=True)
    maximum = float(frame.gene_count.max())
    centers = [0.78, 0.50, 0.22]
    colors = [GREY, BLUE, TEAL]
    labels = ["author genes", "orthogroup mapped", "checkpoint represented"]
    widths = [0.84 * float(value) / maximum for value in frame.gene_count]
    for index, (y, width, color, label) in enumerate(zip(centers, widths, colors, labels, strict=True)):
        x0 = 0.5 - width / 2
        x1 = 0.5 + width / 2
        ax.add_patch(patches.FancyBboxPatch((x0, y - 0.08), width, 0.16, boxstyle="round,pad=0.003,rounding_size=0.012", facecolor=color, edgecolor="white", linewidth=0.6))
        text_color = INK if index == 0 else "white"
        ax.text(0.50, y + 0.015, f"{int(frame.gene_count.iloc[index]):,}", ha="center", va="center", fontsize=5.6, color=text_color, fontweight="bold")
        display_label = "checkpoint\nrepresented" if label == "checkpoint represented" else label
        ax.text(0.50, y - 0.045, display_label, ha="center", va="center", fontsize=2.8 if index == 2 else 3.0, color=text_color, linespacing=0.85)
        if index < 2:
            next_width = widths[index + 1]
            y_top = centers[index] - 0.085
            y_bottom = centers[index + 1] + 0.085
            path = MplPath(
                [
                    (0.5 - width / 2, y_top),
                    (0.5 - next_width / 2, y_bottom),
                    (0.5 + next_width / 2, y_bottom),
                    (0.5 + width / 2, y_top),
                    (0.5 - width / 2, y_top),
                ],
                [MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO, MplPath.LINETO, MplPath.CLOSEPOLY],
            )
            ax.add_patch(patches.PathPatch(path, facecolor=mpl.colors.to_rgba(colors[index + 1], 0.12), edgecolor="none", zorder=0))
            retention = float(frame.gene_count.iloc[index + 1] / frame.gene_count.iloc[index])
            ax.text(0.88, (y_top + y_bottom) / 2, f"{retention:.0%}", ha="center", va="center", fontsize=3.3, color=colors[index + 1], fontweight="bold")


def draw_root_anatomy(ax: plt.Axes, *, alpha: float = 1.0) -> None:
    ax.add_patch(patches.FancyBboxPatch((0.018, 0.060), 0.140, 0.860, boxstyle="round,pad=0.003,rounding_size=0.035", facecolor=mpl.colors.to_rgba("#F7FAFB", alpha), edgecolor=mpl.colors.to_rgba(GRID, alpha), linewidth=0.65))
    layer_colors = [BLUE, TEAL, ORANGE, PURPLE]
    xs = [0.055, 0.080, 0.105, 0.130]
    widths = [0.020, 0.018, 0.018, 0.020]
    for x, width, color in zip(xs, widths, layer_colors, strict=True):
        ax.add_patch(patches.FancyBboxPatch((x - width / 2, 0.165), width, 0.660, boxstyle="round,pad=0.001,rounding_size=0.015", facecolor=mpl.colors.to_rgba(color, 0.24 * alpha), edgecolor=mpl.colors.to_rgba(color, 0.60 * alpha), linewidth=0.48))
    for y in np.linspace(0.205, 0.785, 7):
        ax.plot([0.043, 0.142], [y, y], color="white", lw=0.45, alpha=0.85 * alpha)
    ax.add_patch(patches.Wedge((0.092, 0.160), 0.060, 205, 335, facecolor=mpl.colors.to_rgba(CYAN, 0.25 * alpha), edgecolor=mpl.colors.to_rgba(CYAN, 0.75 * alpha), linewidth=0.60))
    for y in [0.365, 0.515, 0.665]:
        path = MplPath([(0.035, y), (0.000, y + 0.030), (-0.025, y + 0.010)], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])
        ax.add_patch(patches.PathPatch(path, facecolor="none", edgecolor=mpl.colors.to_rgba(CYAN, 0.70 * alpha), linewidth=0.55))
    ax.text(0.088, 0.965, "root layers", ha="center", fontsize=2.8, color=MUTED)


def panel_library_contract(ax: plt.Axes, split: pd.DataFrame) -> None:
    panel_label(ax, "e", "Independent-library contract")
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    draw_root_anatomy(ax, alpha=0.95)
    ax.annotate("", xy=(0.235, 0.50), xytext=(0.175, 0.50), arrowprops={"arrowstyle": "-|>", "lw": 0.85, "color": TEAL})
    role_colors = {"train": BLUE, "validation": ORANGE, "sealed test": TEAL}
    x_positions = [0.30, 0.50, 0.70, 0.90]
    for index, (_, row) in enumerate(split.iterrows()):
        x = x_positions[index]
        color = role_colors[str(row.role)]
        ax.plot([x, x], [0.28, 0.75], color=color, lw=10.0, alpha=0.13, solid_capstyle="butt")
        for barcode in range(8):
            y = 0.32 + barcode * 0.052
            width = 0.040 + 0.010 * ((barcode + index) % 3)
            ax.plot([x - width, x + width], [y, y], color=color, lw=2.1 if barcode % 2 else 1.2, solid_capstyle="butt")
        ax.text(x, 0.83, str(row.library), ha="center", fontsize=4.0, color=INK, fontweight="bold")
        ax.text(x, 0.20, str(row.role), ha="center", fontsize=3.0, color=color, fontweight="bold")
        if str(row.role) == "sealed test":
            ax.add_patch(patches.Arc((x, 0.13), 0.055, 0.052, theta1=0, theta2=180, color=TEAL, lw=0.9))
            ax.add_patch(patches.Rectangle((x - 0.026, 0.085), 0.052, 0.047, facecolor=mpl.colors.to_rgba(TEAL, 0.13), edgecolor=TEAL, linewidth=0.8))
            ax.text(x, 0.015, f"{int(row.cells):,} cells | {int(row.states)} states", ha="center", fontsize=2.8, color=MUTED)
        if index < 3:
            ax.annotate("", xy=(x_positions[index + 1] - 0.075, 0.50), xytext=(x + 0.075, 0.50), arrowprops={"arrowstyle": "-|>", "lw": 0.55, "color": GRID})
    ax.text(0.60, 0.96, "fit only", ha="center", fontsize=2.8, color=BLUE)
    ax.text(0.70, 0.96, "select", ha="center", fontsize=2.8, color=ORANGE)
    ax.text(0.90, 0.96, "locked", ha="center", fontsize=2.8, color=TEAL)


def render() -> None:
    setup()
    module = load_plot_module()
    tables = {name: read_table(name) for name in TABLES}
    cells = tables["sealed_test_cells"]
    per_state = tables["per_state_f1"]

    fig = plt.figure(figsize=(7.25, 7.75))
    atlas_left = 0.050
    atlas_bottom = 0.605
    atlas_width = 0.590
    atlas_height = 0.305
    gap = 0.009
    single = (atlas_width - 2 * gap) / 3
    ax_a1 = fig.add_axes([atlas_left, atlas_bottom, single, atlas_height])
    ax_a2 = fig.add_axes([atlas_left + single + gap, atlas_bottom, single, atlas_height])
    ax_a3 = fig.add_axes([atlas_left + 2 * (single + gap), atlas_bottom, single, atlas_height])
    ax_b = fig.add_axes([0.700, 0.625, 0.270, 0.265])
    ax_c = fig.add_axes([0.060, 0.330, 0.175, 0.210])
    ax_d = fig.add_axes([0.285, 0.315, 0.405, 0.235])
    ax_e = fig.add_axes([0.750, 0.330, 0.220, 0.210])
    ax_f = fig.add_axes([0.060, 0.065, 0.455, 0.190])
    ax_g = fig.add_axes([0.590, 0.075, 0.185, 0.170])
    ax_h = fig.add_axes([0.825, 0.075, 0.145, 0.170])

    for axis in (ax_a1, ax_a2, ax_a3):
        axis.set_facecolor("#EAF1F3")
    layer_umap_vector(ax_a1, cells, "layer", "author root layers", module.LAYER_COLORS)
    layer_umap_vector(ax_a2, cells, "predicted_layer", "adapter root layers", module.LAYER_COLORS)
    correct_umap_vector(ax_a3, cells)
    ax_a1.text(-0.075, 1.035, "a", transform=ax_a1.transAxes, fontsize=7.4, fontweight="bold", color=INK, va="bottom")
    ax_a1.text(0.0, 1.035, "Sealed OUGHW root atlas", transform=ax_a1.transAxes, fontsize=5.25, fontweight="bold", color=INK, va="bottom")
    layer_legend = ["atrichoblast", "cortex", "endodermis", "phloem", "stele", "xylem"]
    handles = [plt.Line2D([0], [0], marker="o", linestyle="", markersize=3.2, markerfacecolor=module.LAYER_COLORS[name], markeredgewidth=0, label=name) for name in layer_legend]
    ax_a1.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.10, -0.12), ncol=3, frameon=False, fontsize=3.4, handletextpad=0.2, columnspacing=0.55, borderaxespad=0)
    ax_a3.text(0.99, -0.16, "OUGHW | 4,150 cells | 27 author states", transform=ax_a3.transAxes, ha="right", fontsize=3.5, color=MUTED)

    panel_recovery(ax_b, tables["matched_recovery"])
    panel_transfer(ax_c, tables["feature_transfer"])
    panel_state_resolution_vector(ax_d, per_state, module.short_state)
    panel_library_contract(ax_e, tables["library_split"])
    module.plot_layer_agreement(ax_f, cells)
    module.plot_state_support_geometry(ax_g, tables["state_support_geometry"])
    module.plot_layer_recovery(ax_h, cells)

    fig.text(0.050, 0.982, "Sorghum root: a physically sealed library recovers 27 cell states", fontsize=8.9, fontweight="bold", color=INK, va="top")
    fig.text(0.970, 0.982, "4 independent libraries | OUGHW withheld from fitting | target-supervised LoRA", fontsize=3.7, color=MUTED, ha="right", va="top")
    fig.text(0.050, 0.017, "All state, layer and uncertainty summaries use only the author-labelled OUGHW sealed-test library.", fontsize=2.85, color=MUTED)

    for artist in fig.findobj(match=Text):
        if artist.get_fontsize() < 3.0:
            artist.set_fontsize(3.0)

    for suffix, options in (("svg", {"dpi": 600}), ("pdf", {"dpi": 600}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{STEM}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)
    print({"figure": str(MAIN / f"{STEM}.png"), "source_tables": len(TABLES)})


if __name__ == "__main__":
    render()
