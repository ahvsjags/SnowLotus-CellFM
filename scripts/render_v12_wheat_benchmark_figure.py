from __future__ import annotations

"""Render the v12 wheat benchmark as an asymmetric evidence-led composite."""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.text import Text
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
V11 = ROOT / "figures" / "plant_cellfm_submission_v11"
OUT = ROOT / "figures" / "plant_cellfm_submission_v12"
MAIN = OUT / "main"
SOURCE = OUT / "source_data"
OLD_STEM = "plant_cellfm_v11_fig6_wheat_benchmark"
STEM = "plant_cellfm_v12_fig6_wheat_benchmark"

INK = "#102633"
MUTED = "#627887"
GRID = "#D9E4E9"
PALE = "#EEF4F6"
TEAL = "#008F87"
DEEP_TEAL = "#006B66"
BLUE = "#2377B9"
CYAN = "#35A7B8"
PURPLE = "#7B62A8"
ORANGE = "#EB7A2A"
GREY = "#AFC0C9"
LIGHT_GREY = "#D8E2E7"


TABLES = [
    "error_route_delta",
    "locked_test_bootstrap",
    "locked_test_metrics",
    "locked_test_per_state_f1",
    "locked_test_per_state_f1_all_methods",
    "orthology_and_split_contract",
    "plantcellfm_confusion",
    "scplantllm_full_confusion",
]


def setup() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 6.0,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "axes.linewidth": 0.55,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
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
    ax.text(-0.060, 1.035, key, transform=ax.transAxes, fontsize=7.4, color=INK, fontweight="bold", va="bottom")
    ax.text(0.0, 1.035, title, transform=ax.transAxes, fontsize=5.25, color=INK, fontweight="bold", va="bottom")


def short_label(value: str) -> str:
    replacements = {
        "Dividing Cells": "Dividing",
        "Endodermis/Phloem": "Endo./phloem",
        "Provascular cells": "Provascular",
        "Root Cap": "Root cap",
        "Root Hair": "Root hair",
    }
    return replacements.get(value, value)


def panel_mechanism(ax: plt.Axes, contract: pd.DataFrame) -> None:
    panel_label(ax, "a", "A/B/D orthology bridge and locked-cell contract")
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.add_patch(
        patches.FancyBboxPatch((0.010, 0.235), 0.980, 0.700, boxstyle="round,pad=0.010,rounding_size=0.018", facecolor="#F7FAFB", edgecolor=GRID, linewidth=0.80)
    )
    values = dict(zip(contract.stage, contract["items"], strict=True))

    genome_x = [0.085, 0.145, 0.205]
    genome_labels = ["A", "B", "D"]
    genome_colors = [BLUE, CYAN, PURPLE]
    for x, label, color in zip(genome_x, genome_labels, genome_colors, strict=True):
        ax.add_patch(patches.FancyBboxPatch((x - 0.022, 0.535), 0.044, 0.265, boxstyle="round,pad=0.003,rounding_size=0.020", facecolor=mpl.colors.to_rgba(color, 0.18), edgecolor=color, linewidth=0.75))
        for y in np.linspace(0.560, 0.770, 7):
            ax.plot([x - 0.014, x + 0.014], [y, y], color=color, lw=0.85, alpha=0.70)
        ax.text(x, 0.825, label, ha="center", fontsize=4.0, color=color, fontweight="bold")
    ax.text(0.145, 0.895, "hexaploid wheat\nroot transcriptome", ha="center", fontsize=3.25, color=INK, fontweight="bold", linespacing=0.95)

    loom_x = np.linspace(0.330, 0.485, 6)
    loom_y = np.linspace(0.555, 0.790, 6)
    for x0, color in zip(genome_x, genome_colors, strict=True):
        for y1 in loom_y[::2]:
            ax.annotate("", xy=(0.330, y1), xytext=(x0 + 0.025, 0.670), arrowprops=dict(arrowstyle="-", color=mpl.colors.to_rgba(color, 0.35), lw=0.55), zorder=1)
    for x in loom_x:
        for y in loom_y:
            ax.scatter([x], [y], s=10, color=mpl.colors.to_rgba(TEAL if (int(x * 1000) + int(y * 1000)) % 2 else BLUE, 0.72), edgecolor="white", linewidth=0.25, zorder=3)
    ax.text(0.408, 0.895, "orthogroup\nprojection", ha="center", fontsize=3.25, color=TEAL, fontweight="bold", linespacing=0.95)

    route_boxes = [
        (0.615, 0.730, "scPlantLLM\nfull route", BLUE),
        (0.615, 0.515, "Plant-CellFM\nLoRA route", TEAL),
        (0.830, 0.625, "1,433 locked\ntest cells", ORANGE),
    ]
    for x, y, label, color in route_boxes:
        ax.add_patch(patches.FancyBboxPatch((x - 0.075, y - 0.060), 0.150, 0.120, boxstyle="round,pad=0.007,rounding_size=0.014", facecolor=mpl.colors.to_rgba(color, 0.12), edgecolor=color, linewidth=0.85, zorder=3))
        ax.text(x, y, label, ha="center", va="center", fontsize=3.15, color=INK, fontweight="bold", linespacing=0.95)
    for start_xy, end_xy, color in [((0.500, 0.690), (0.540, 0.730), BLUE), ((0.500, 0.640), (0.540, 0.515), TEAL), ((0.690, 0.730), (0.755, 0.645), BLUE), ((0.690, 0.515), (0.755, 0.605), TEAL)]:
        ax.annotate("", xy=end_xy, xytext=start_xy, arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0, shrinkA=0, shrinkB=0), zorder=2)

    rail = [
        (0.03, 0.16, f"{int(values['author_source_features']):,}\nsource features", BLUE),
        (0.28, 0.16, f"{int(values['author_orthogroups']):,}\northogroups", PURPLE),
        (0.53, 0.16, f"{int(values['checkpoint_vocabulary_resolved']):,}\nvocabulary-resolved", TEAL),
        (0.78, 0.16, f"{int(values['nonoverlap_cells']):,}\nnon-overlap cells", CYAN),
        (0.96, 0.16, f"{int(values['locked_test']):,}\nlocked test", DEEP_TEAL),
    ]
    for index, (x, y, label, color) in enumerate(rail):
        ax.scatter(x, y, s=28 if index < 4 else 42, color=color, edgecolor="white", linewidth=0.5, zorder=4)
        ha = "left" if index == 0 else "right" if index == len(rail) - 1 else "center"
        dx = 0.025 if index == 0 else -0.025 if index == len(rail) - 1 else 0
        ax.text(x + dx, 0.055, label, ha=ha, va="bottom", fontsize=3.0, color=color, fontweight="bold")
        if index < len(rail) - 1:
            next_x = rail[index + 1][0]
            ax.plot([x + 0.012, next_x - 0.012], [y, y], color=GRID, lw=1.1, solid_capstyle="round", zorder=2)
    ax.text(0.50, 0.005, f"{int(values['orthology_relations']):,} gene relations | {int(values['overlap_excluded']):,} overlapping cells excluded before the fixed split", ha="center", fontsize=2.85, color=MUTED)

def panel_benchmark(ax: plt.Axes, metrics: pd.DataFrame) -> None:
    panel_label(ax, "b", "Matched routes converge on 66.6% macro-F1")
    method_order = ["scPlantLLM frozen", "scPlantLLM partial", "scPlantLLM full", "Plant-CellFM LoRA"]
    method_names = ["frozen", "partial", "full", "Plant-CellFM"]
    metric_order = ["accuracy", "macro-F1", "weighted-F1"]
    colors = {"accuracy": BLUE, "macro-F1": TEAL, "weighted-F1": PURPLE}
    markers = {"accuracy": "o", "macro-F1": "s", "weighted-F1": "^"}
    pivot = metrics.pivot(index="method", columns="metric", values="score")
    ypos = np.arange(len(method_order))[::-1]
    ax.axhspan(-0.45, 0.45, color=mpl.colors.to_rgba(TEAL, 0.075), zorder=0)
    for y, method in zip(ypos, method_order, strict=True):
        values = [float(pivot.loc[method, metric]) for metric in metric_order]
        line_color = DEEP_TEAL if method == "Plant-CellFM LoRA" else GREY
        ax.plot([min(values), max(values)], [y, y], color=line_color, lw=2.2 if method == "Plant-CellFM LoRA" else 1.2, alpha=0.9, solid_capstyle="round")
        for metric, value in zip(metric_order, values, strict=True):
            ax.scatter(value, y, marker=markers[metric], s=30 if method == "Plant-CellFM LoRA" else 22, color=colors[metric], edgecolor="white", linewidth=0.55, zorder=3)
            if method == "Plant-CellFM LoRA":
                x_shift = {"accuracy": -0.010, "macro-F1": 0.010, "weighted-F1": 0.0}[metric]
                y_shift = {"accuracy": -0.30, "macro-F1": -0.30, "weighted-F1": 0.31}[metric]
                ax.text(value + x_shift, y + y_shift, f"{value:.0%}", ha="center", fontsize=3.2, color=colors[metric], fontweight="bold")
    ax.set(yticks=ypos, yticklabels=method_names, xlim=(0.12, 0.72), ylim=(-0.55, 3.55), xlabel="score on the same 1,433 locked cells")
    ax.set_xticks(np.arange(0.2, 0.71, 0.1))
    ax.tick_params(axis="both", labelsize=3.15, length=0, pad=1.2)
    ax.grid(axis="x", color=GRID, lw=0.55)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    handles = [plt.Line2D([0], [0], marker=markers[m], color="none", markerfacecolor=colors[m], markeredgecolor="white", markersize=4.0, label=m) for m in metric_order]
    ax.legend(handles=handles, loc="upper left", frameon=False, ncol=3, fontsize=2.85, handletextpad=0.25, columnspacing=0.75, borderaxespad=0)
    full_acc = float(pivot.loc["scPlantLLM full", "accuracy"])
    full_macro = float(pivot.loc["scPlantLLM full", "macro-F1"])
    plant_acc = float(pivot.loc["Plant-CellFM LoRA", "accuracy"])
    plant_macro = float(pivot.loc["Plant-CellFM LoRA", "macro-F1"])
    ax.text(0.715, 0.75, f"+{plant_acc - full_acc:.1%}\naccuracy", ha="right", va="center", fontsize=3.7, color=BLUE, fontweight="bold")
    ax.text(0.715, 1.55, f"+{plant_macro - full_macro:.1%}\nmacro-F1", ha="right", va="center", fontsize=3.7, color=TEAL, fontweight="bold")


def panel_state_routes(ax: plt.Axes, state: pd.DataFrame, all_methods: pd.DataFrame) -> None:
    panel_label(ax, "c", "State-wise recovery across four model routes")
    method_colors = {"frozen": LIGHT_GREY, "partial": "#8EB7CF", "full": BLUE, "Plant-CellFM": TEAL}
    state_order = state.sort_values("plant_cellfm_f1", ascending=True).author_label.tolist()
    lookup = all_methods.pivot(index="author_label", columns="method", values="f1")
    supports = state.set_index("author_label").support.to_dict()
    y = np.arange(len(state_order))
    for row, label in enumerate(state_order):
        full = float(lookup.loc[label, "full"])
        plant = float(lookup.loc[label, "Plant-CellFM"])
        gain_color = TEAL if plant >= full else ORANGE
        ax.plot([full, plant], [row, row], color=gain_color, lw=2.1, alpha=0.68, solid_capstyle="round", zorder=1)
        for method in ["frozen", "partial", "full", "Plant-CellFM"]:
            value = float(lookup.loc[label, method])
            ax.scatter(value, row, s=11 if method != "Plant-CellFM" else 26, color=method_colors[method], edgecolor="white", linewidth=0.45, zorder=3)
        ax.text(min(1.015, plant + 0.018), row, f"{plant:.0%}", fontsize=2.65, color=gain_color, va="center", fontweight="bold")
    labels = [f"{short_label(label)}  n={int(supports[label])}" for label in state_order]
    ax.set(yticks=y, yticklabels=labels, xlim=(0.0, 1.08), ylim=(-0.65, len(y) - 0.35), xlabel="per-state F1")
    ax.set_xticks(np.arange(0, 1.01, 0.2))
    ax.tick_params(axis="both", labelsize=2.75, length=0, pad=1.0)
    ax.grid(axis="x", color=GRID, lw=0.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    handles = [plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=method_colors[m], markeredgecolor="white", markersize=4.0, label=m) for m in ["frozen", "partial", "full", "Plant-CellFM"]]
    ax.legend(handles=handles, loc="lower right", frameon=False, ncol=4, fontsize=2.65, handletextpad=0.2, columnspacing=0.65, borderaxespad=0.25)


def panel_error_delta(ax: plt.Axes, delta: pd.DataFrame) -> None:
    panel_label(ax, "d", "Error-route rewiring after Plant-CellFM adaptation")
    matrix = delta.set_index("author_label")
    values = matrix.to_numpy(dtype=float)
    cmap = LinearSegmentedColormap.from_list("error_delta", ["#E98B55", "#F6F8F8", TEAL])
    image = ax.pcolormesh(
        np.arange(values.shape[1] + 1) - 0.5,
        np.arange(values.shape[0] + 1) - 0.5,
        values,
        cmap=cmap,
        vmin=-0.42,
        vmax=0.42,
        shading="flat",
    )
    ax.set(xlim=(-0.5, values.shape[1] - 0.5), ylim=(values.shape[0] - 0.5, -0.5))
    labels = [short_label(value) for value in matrix.index]
    ax.set(xticks=np.arange(len(labels)), xticklabels=labels, yticks=np.arange(len(labels)), yticklabels=labels)
    ax.tick_params(axis="x", labelrotation=90, labelsize=2.45, length=0, pad=0.7)
    ax.tick_params(axis="y", labelsize=2.45, length=0, pad=0.7)
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            if abs(value) >= 0.065 or (row == col and abs(value) >= 0.03):
                color = "white" if abs(value) >= 0.20 else INK
                ax.text(col, row, f"{value:+.0%}", ha="center", va="center", fontsize=2.2, color=color, fontweight="bold")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("predicted label", fontsize=3.0)
    ax.set_ylabel("author label", fontsize=3.0)
    cax = ax.inset_axes([0.72, 1.005, 0.26, 0.030])
    cb = plt.colorbar(image, cax=cax, orientation="horizontal", ticks=[-0.4, 0, 0.4])
    cb.ax.tick_params(labelsize=2.3, length=0, pad=0.3)
    cb.outline.set_visible(False)
    cax.set_title("probability moved out / into route", fontsize=2.45, color=MUTED, pad=0.5)


def panel_bootstrap(ax: plt.Axes, draws: pd.DataFrame) -> None:
    panel_label(ax, "e", "Paired bootstrap uncertainty")
    order = ["scPlantLLM frozen", "scPlantLLM partial", "scPlantLLM full", "Plant-CellFM LoRA"]
    names = ["frozen", "partial", "full", "Plant-CellFM"]
    y = np.arange(len(order))[::-1]
    ax.axhspan(-0.42, 0.42, color=mpl.colors.to_rgba(TEAL, 0.075), zorder=0)
    for pos, method in zip(y, order, strict=True):
        subset = draws.loc[draws.method == method]
        for offset, column, color in [(-0.12, "accuracy", BLUE), (0.12, "macro_f1", TEAL)]:
            values = subset[column].to_numpy(dtype=float)
            violin = ax.violinplot(values, positions=[pos + offset], vert=False, widths=0.20, showextrema=False)
            for body in violin["bodies"]:
                body.set_facecolor(color)
                body.set_edgecolor("none")
                body.set_alpha(0.55 if method != "Plant-CellFM LoRA" else 0.82)
            median = float(np.median(values))
            low, high = np.quantile(values, [0.025, 0.975])
            ax.plot([low, high], [pos + offset, pos + offset], color=color, lw=1.1, zorder=3)
            ax.scatter(median, pos + offset, color=color, edgecolor="white", linewidth=0.4, s=15, zorder=4)
    ax.set(yticks=y, yticklabels=names, xlim=(0.14, 0.72), ylim=(-0.55, 3.55), xlabel="score (95% paired bootstrap interval)")
    ax.tick_params(axis="both", labelsize=2.9, length=0, pad=1.0)
    ax.grid(axis="x", color=GRID, lw=0.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    handles = [
        patches.Patch(facecolor=BLUE, alpha=0.65, label="accuracy"),
        patches.Patch(facecolor=TEAL, alpha=0.65, label="macro-F1"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=2.75, ncol=2, handlelength=0.8, columnspacing=0.8)


def panel_gain_support(ax: plt.Axes, state: pd.DataFrame) -> None:
    panel_label(ax, "f", "Gain is broad across state support")
    positive = state.delta_f1 >= 0
    sizes = 22 + 95 * np.sqrt(state.support / state.support.max())
    colors = np.where(positive, TEAL, ORANGE)
    ax.scatter(state.support, state.delta_f1, s=sizes, color=colors, edgecolor="white", linewidth=0.65, alpha=0.90, zorder=3)
    ax.axhline(0, color=ORANGE, lw=0.8)
    ax.axvline(float(state.support.median()), color=GRID, lw=0.8, ls=(0, (3, 2)))
    label_offsets = {
        "Root Cap": (7, 0.010),
        "Meristems": (8, 0.012),
        "Endodermis/Phloem": (8, 0.010),
        "Xylem": (8, -0.018),
        "Phloem": (8, -0.010),
        "Unknown": (-12, 0.018),
    }
    for _, row in state.iterrows():
        if row.delta_f1 >= 0.28 or row.delta_f1 < 0 or row.support >= 300:
            dx, dy = label_offsets.get(row.author_label, (6, 0.005))
            ha = "right" if dx < 0 else "left"
            ax.text(row.support + dx, row.delta_f1 + dy, short_label(row.author_label), fontsize=2.7, color=TEAL if row.delta_f1 >= 0 else ORANGE, ha=ha, va="center")
    improved = int(positive.sum())
    ax.text(0.98, 0.96, f"{improved}/{len(state)} states improve\nmedian gain {state.delta_f1.median():+.1%}", transform=ax.transAxes, ha="right", va="top", fontsize=3.5, color=DEEP_TEAL, fontweight="bold")
    ax.set(xlabel="locked-test state support", ylabel="Plant-CellFM minus scPlantLLM full F1", xlim=(0, state.support.max() * 1.08), ylim=(-0.10, 0.72))
    ax.tick_params(axis="both", labelsize=2.9, length=0, pad=1.0)
    ax.grid(color=GRID, lw=0.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)


def render() -> None:
    setup()
    tables = {name: read_table(name) for name in TABLES}

    fig = plt.figure(figsize=(7.25, 7.75))
    ax_a = fig.add_axes([0.050, 0.610, 0.570, 0.305])
    ax_b = fig.add_axes([0.665, 0.625, 0.305, 0.275])
    ax_c = fig.add_axes([0.075, 0.335, 0.405, 0.205])
    ax_d = fig.add_axes([0.555, 0.325, 0.415, 0.225])
    ax_e = fig.add_axes([0.075, 0.075, 0.385, 0.175])
    ax_f = fig.add_axes([0.555, 0.075, 0.415, 0.175])

    panel_mechanism(ax_a, tables["orthology_and_split_contract"])
    panel_benchmark(ax_b, tables["locked_test_metrics"])
    panel_state_routes(ax_c, tables["locked_test_per_state_f1"], tables["locked_test_per_state_f1_all_methods"])
    panel_error_delta(ax_d, tables["error_route_delta"])
    panel_bootstrap(ax_e, tables["locked_test_bootstrap"])
    panel_gain_support(ax_f, tables["locked_test_per_state_f1"])

    fig.text(0.050, 0.982, "Wheat root: allopolyploid transfer resolves the locked benchmark", fontsize=8.9, fontweight="bold", color=INK, va="top")
    fig.text(0.970, 0.982, "GSE270342 | 1,433 physically locked cells | identical evaluation barcodes", fontsize=3.7, color=MUTED, ha="right", va="top")
    fig.text(0.050, 0.018, "All benchmark routes use the same author labels, split and locked-test denominator; intervals are paired bootstrap estimates.", fontsize=2.85, color=MUTED)

    for artist in fig.findobj(match=Text):
        if artist.get_fontsize() < 3.0:
            artist.set_fontsize(3.0)

    for suffix, options in (("svg", {"dpi": 600}), ("pdf", {"dpi": 600}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{STEM}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)

    print({"figure": str(MAIN / f"{STEM}.png"), "source_tables": len(TABLES)})


if __name__ == "__main__":
    render()
