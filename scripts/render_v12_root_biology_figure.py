from __future__ import annotations

"""Render the v12 Arabidopsis root biology and locked-adaptation figure."""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.path import Path as MplPath
from matplotlib.text import Text
import numpy as np
import pandas as pd


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
YELLOW = "#E6A400"

STATE_COLORS = {
    "Lateral root cap": ORANGE,
    "Root cortex": TEAL,
    "Root stele": BLUE,
    "Unknow": GREY,
    "Root cap": PURPLE,
    "Non-hair": RED,
    "Root endodermis": DEEP_TEAL,
    "Xylem": NAVY,
    "S phase": YELLOW,
    "Root hair": CYAN,
    "Columella root cap": "#9A7057",
    "G1/G0 phase": "#7A8D98",
    "Phloem": "#B25D8D",
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
    return pd.read_csv(V11_SOURCE / f"plant_cellfm_v11_fig5_root_biology_{name}.tsv", sep="\t")


def panel_label(ax: plt.Axes, key: str, title: str, y: float = 1.025) -> None:
    ax.text(-0.045, y, key, transform=ax.transAxes, fontsize=8.0, fontweight="bold", color=INK, va="bottom")
    ax.text(0.0, y, title, transform=ax.transAxes, fontsize=5.6, fontweight="bold", color=INK, va="bottom")


def short_state(value: str) -> str:
    return (
        str(value)
        .replace("Lateral root primordium/meristem", "LR primordium")
        .replace("Vessel identity cell/expanding vessel", "expanding vessel")
        .replace("Conductive phloem parenchyma", "conductive phloem")
        .replace("Mature phloem parenchyma", "mature phloem")
        .replace("Mature xylem parenchyma", "mature xylem")
        .replace("Maturing xylem parenchyma", "maturing xylem")
        .replace("Young xylem parenchyma", "young xylem")
        .replace("Late differentiating vessel", "late vessel")
        .replace("Myrosin idioblasts", "myrosin")
    )


def curved_line(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str, width: float, alpha: float, dashed: bool = False) -> None:
    x0, y0 = start
    x1, y1 = end
    path = MplPath(
        [(x0, y0), (x0 + 0.42 * (x1 - x0), y0), (x0 + 0.58 * (x1 - x0), y1), (x1, y1)],
        [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4],
    )
    ax.add_patch(
        patches.PathPatch(
            path,
            facecolor="none",
            edgecolor=color,
            linewidth=width,
            alpha=alpha,
            linestyle="--" if dashed else "-",
            capstyle="round",
        )
    )


def draw_root_anatomy(ax: plt.Axes) -> None:
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.add_patch(patches.FancyBboxPatch((0.12, 0.045), 0.76, 0.910, boxstyle="round,pad=0.004,rounding_size=0.060", facecolor="#F7FAFB", edgecolor=GRID, linewidth=0.70))
    layer_specs = [
        (0.30, 0.060, BLUE, "stele"),
        (0.40, 0.055, DEEP_TEAL, "xylem"),
        (0.50, 0.052, TEAL, "endodermis"),
        (0.60, 0.055, ORANGE, "cortex"),
        (0.70, 0.060, PURPLE, "epidermis"),
    ]
    for x, width, color, _ in layer_specs:
        ax.add_patch(patches.FancyBboxPatch((x - width / 2, 0.145), width, 0.710, boxstyle="round,pad=0.002,rounding_size=0.030", facecolor=mpl.colors.to_rgba(color, 0.26), edgecolor=mpl.colors.to_rgba(color, 0.72), linewidth=0.60))
    for y in np.linspace(0.19, 0.81, 9):
        ax.plot([0.245, 0.755], [y, y], color="white", lw=0.55, alpha=0.90)
    ax.add_patch(patches.Wedge((0.50, 0.145), 0.250, 200, 340, facecolor=mpl.colors.to_rgba(YELLOW, 0.34), edgecolor=YELLOW, linewidth=0.75))
    for side, flip in [(0.20, -1), (0.80, 1)]:
        for y in [0.37, 0.52, 0.67]:
            path = MplPath([(side, y), (side + 0.10 * flip, y + 0.035), (side + 0.18 * flip, y + 0.010)], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])
            ax.add_patch(patches.PathPatch(path, facecolor="none", edgecolor=CYAN, linewidth=0.75, alpha=0.70))
    ax.text(0.50, 0.940, "root anatomy", ha="center", fontsize=3.2, color=INK, fontweight="bold")
    ax.text(0.50, 0.055, "schematic", ha="center", fontsize=2.8, color=MUTED)


def panel_blind_atlas(fig: plt.Figure, bounds: list[float], embedding: pd.DataFrame, summary: pd.DataFrame) -> None:
    container = fig.add_axes(bounds)
    panel_label(container, "a", "Blind root-state atlas and confidence geometry")
    container.set_axis_off()
    anatomy = container.inset_axes([0.0, 0.02, 0.175, 0.96])
    draw_root_anatomy(anatomy)

    atlas = container.inset_axes([0.185, 0.02, 0.525, 0.96])
    for state, part in embedding.groupby("fine_label", sort=False):
        atlas.scatter(part.UMAP1, part.UMAP2, s=2.2, color=STATE_COLORS.get(state, GREY), alpha=0.74, linewidths=0)
    atlas.set(xticks=[], yticks=[])
    atlas.set_facecolor(PALE)
    for spine in atlas.spines.values():
        spine.set_visible(False)
    atlas.text(0.02, 0.97, f"GSE152766 · {len(embedding):,} cells", transform=atlas.transAxes, fontsize=3.2, color=INK, fontweight="bold", va="top")
    atlas.text(0.98, 0.035, "13 blind states", transform=atlas.transAxes, fontsize=3.0, color=MUTED, ha="right")

    field = container.inset_axes([0.745, 0.08, 0.255, 0.84])
    plot = summary.copy()
    sizes = 18 + 210 * np.sqrt(plot.cells / plot.cells.max())
    for (_, row), size in zip(plot.iterrows(), sizes, strict=True):
        color = STATE_COLORS.get(row.fine_label, GREY)
        field.scatter(row.fraction, row.mean_confidence, s=size, color=color, alpha=0.82, edgecolor="white", linewidth=0.65, zorder=3)
        if row.fraction >= 0.045 or row.mean_confidence < 0.62:
            field.text(row.fraction + 0.006, row.mean_confidence, row.fine_label.replace("Root ", ""), fontsize=2.75, color=color, va="center")
        field.vlines(row.fraction, row.mean_confidence, row.median_confidence, color=mpl.colors.to_rgba(color, 0.38), lw=0.8, zorder=1)
    field.axhline(0.75, color=GRID, lw=0.65, ls=(0, (3, 2)))
    field.set(xlim=(-0.005, 0.39), ylim=(0.45, 1.00), xlabel="blind-state fraction", ylabel="mean confidence")
    field.tick_params(axis="both", labelsize=3.0, length=0, pad=1.0)
    field.grid(color=GRID, lw=0.45, zorder=0)
    for side in ("top", "right"):
        field.spines[side].set_visible(False)
    field.spines["left"].set_color(GRID)
    field.spines["bottom"].set_color(GRID)
    field.text(0.02, 0.98, "area scales with cell count", transform=field.transAxes, fontsize=2.9, color=MUTED, va="top")

    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgewidth=0, markersize=2.8, label=name.replace("Root ", ""))
        for name, color in list(STATE_COLORS.items())[:8]
    ]
    container.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.45, -0.10), ncol=4, frameon=False, fontsize=2.75, handletextpad=0.15, columnspacing=0.45)


def panel_marker_program(ax: plt.Axes, markers: pd.DataFrame) -> None:
    panel_label(ax, "b", "Predeclared marker-to-identity coherence")
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(-0.6, len(markers) - 0.3))
    plot = markers.sort_values(["expected_label", "marker_symbol"]).reset_index(drop=True)
    identities = list(dict.fromkeys(plot.expected_label.tolist()))
    identity_y = {identity: np.mean(plot.index[plot.expected_label.eq(identity)]) for identity in identities}
    for identity, y in identity_y.items():
        color = STATE_COLORS.get(identity, TEAL)
        ax.scatter([0.10], [y], s=58, color=color, edgecolor="white", linewidth=0.6, zorder=4)
        ax.text(0.055, y, identity.replace("Root ", ""), ha="right", va="center", fontsize=3.0, color=INK, fontweight="bold")
    max_expr = plot.target_mean_log1p_normalised_expression.max()
    for index, row in plot.iterrows():
        y = float(index)
        color = STATE_COLORS.get(row.expected_label, TEAL)
        concordant = bool(row.is_top_mean_expression_label and row.is_top_detection_label)
        width = 0.7 + 3.0 * max(0.02, float(row.detection_fraction_delta))
        curved_line(ax, (0.12, identity_y[row.expected_label]), (0.47, y), color if concordant else RED, width, 0.72, dashed=not concordant)
        ax.scatter([0.49], [y], s=34, color=color if concordant else RED, edgecolor="white", linewidth=0.5, zorder=4)
        ax.text(0.515, y, row.marker_symbol, fontsize=3.0, color=INK if concordant else RED, va="center", fontweight="bold")
        target = float(row.target_mean_log1p_normalised_expression) / max_expr
        outside = float(row.outside_mean_log1p_normalised_expression) / max_expr
        ax.add_patch(patches.Rectangle((0.63, y - 0.16), 0.28, 0.13, facecolor="#EDF2F4", edgecolor="none"))
        ax.add_patch(patches.Rectangle((0.63, y - 0.16), 0.28 * target, 0.13, facecolor=color, edgecolor="none"))
        ax.add_patch(patches.Rectangle((0.63, y + 0.03), 0.28, 0.08, facecolor="#EDF2F4", edgecolor="none"))
        ax.add_patch(patches.Rectangle((0.63, y + 0.03), 0.28 * outside, 0.08, facecolor=GREY, edgecolor="none"))
        ax.text(0.94, y - 0.08, f"Δ {row.mean_expression_delta:.2f}", fontsize=2.75, color=color if concordant else RED, va="center", fontweight="bold")
    ax.text(0.10, len(plot) - 0.35, "predicted identity", ha="center", fontsize=3.0, color=MUTED)
    ax.text(0.50, len(plot) - 0.35, "fixed marker", ha="center", fontsize=3.0, color=MUTED)
    ax.text(0.77, len(plot) - 0.35, "target / outside expression", ha="center", fontsize=3.0, color=MUTED)
    ax.text(0.02, -0.48, "solid: concordant top marker | dashed red: failed anchor", fontsize=2.9, color=MUTED)


def panel_locked_recovery(fig: plt.Figure, bounds: list[float], recovery: pd.DataFrame, confusion: pd.DataFrame) -> None:
    container = fig.add_axes(bounds)
    panel_label(container, "c", "Locked secondary-root recovery")
    container.set_axis_off()
    frozen = recovery.iloc[0]
    adapter = recovery.iloc[1]
    score = container.inset_axes([0.0, 0.04, 0.30, 0.90])
    score.set_axis_off()
    score.text(0.05, 0.83, f"{frozen.accuracy:.1%}", fontsize=7.2, color=GREY, fontweight="bold")
    score.text(0.05, 0.73, "frozen", fontsize=3.0, color=MUTED)
    score.annotate("", xy=(0.80, 0.30), xytext=(0.25, 0.66), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.6))
    score.text(0.43, 0.50, f"+{adapter.accuracy - frozen.accuracy:.1%}", fontsize=3.4, color=ORANGE, fontweight="bold", rotation=-27)
    score.text(0.50, 0.15, f"{adapter.accuracy:.1%}", fontsize=9.0, color=TEAL, fontweight="bold", ha="center")
    score.text(0.50, 0.05, "adapter accuracy", fontsize=3.0, color=MUTED, ha="center")
    score.text(0.50, -0.05, f"macro-F1 {adapter.macro_f1:.1%}", fontsize=3.2, color=TEAL, fontweight="bold", ha="center")

    matrix_ax = container.inset_axes([0.34, 0.0, 0.66, 0.98])
    labels = confusion.true_label.tolist()
    values = confusion.drop(columns="true_label").to_numpy(float)
    cmap = mpl.colors.LinearSegmentedColormap.from_list("confusion", ["#F4F7F8", "#B8D8E2", TEAL, DEEP_TEAL])
    matrix_ax.pcolormesh(
        np.arange(values.shape[1] + 1) - 0.5,
        np.arange(values.shape[0] + 1) - 0.5,
        values,
        cmap=cmap,
        vmin=0,
        vmax=1,
        shading="flat",
    )
    matrix_ax.set(xlim=(-0.5, values.shape[1] - 0.5), ylim=(values.shape[0] - 0.5, -0.5))
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            if value >= 0.075:
                matrix_ax.text(col, row, f"{value:.0%}", ha="center", va="center", fontsize=2.45, color="white" if value >= 0.55 else INK, fontweight="bold")
    short = [short_state(label) for label in labels]
    matrix_ax.set(xticks=np.arange(len(short)), xticklabels=short, yticks=np.arange(len(short)), yticklabels=short)
    matrix_ax.tick_params(axis="x", labelrotation=90, labelsize=2.35, length=0, pad=0.7)
    matrix_ax.tick_params(axis="y", labelsize=2.35, length=0, pad=0.7)
    for spine in matrix_ax.spines.values():
        spine.set_visible(False)
    matrix_ax.set_title("14-state locked-test confusion", loc="left", fontsize=3.2, color=INK, fontweight="bold", pad=1.5)


def panel_state_f1(ax: plt.Axes, states: pd.DataFrame) -> None:
    panel_label(ax, "d", "State support and F1")
    threshold = float(states.f1.median())
    colors = np.where(states.f1 >= threshold, TEAL, ORANGE)
    sizes = 20 + 85 * np.sqrt(states.support / states.support.max())
    ax.scatter(states.support, states.f1, s=sizes, color=colors, edgecolor="white", linewidth=0.6, alpha=0.90, zorder=3)
    label_offsets = {
        "Lateral root primordium/meristem": (8, -0.010),
        "Late differentiating vessel": (8, 0.009),
        "Sieve element": (9, 0.004),
        "Myrosin idioblasts": (9, 0.011),
        "Vessel identity cell/expanding vessel": (9, -0.009),
        "Companion cell": (9, -0.006),
    }
    for _, row in states.iterrows():
        if row.support < 35 or row.f1 < 0.76 or row.f1 > 0.91:
            dx, dy = label_offsets.get(row.label, (6, 0.0))
            ax.text(
                row.support + dx,
                row.f1 + dy,
                short_state(row.label),
                fontsize=2.7,
                color=TEAL if row.f1 >= threshold else ORANGE,
                va="center",
            )
    ax.axhline(threshold, color=TEAL, lw=0.75, ls=(0, (3, 2)))
    ax.set(xlabel="locked-test state support", ylabel="per-state F1", xlim=(-10, states.support.max() * 1.12), ylim=(0.69, 0.95))
    ax.tick_params(axis="both", labelsize=3.0, length=0, pad=1.0)
    ax.grid(color=GRID, lw=0.5, zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.text(0.02, 0.03, "area scales with support", transform=ax.transAxes, fontsize=2.9, color=MUTED)


def panel_validation(ax: plt.Axes, history: pd.DataFrame) -> None:
    panel_label(ax, "e", "Validation-only model selection")
    ax.plot(history.epoch, history.fine_accuracy, color=TEAL, marker="o", ms=3.6, lw=1.35, label="fine accuracy")
    ax.plot(history.epoch, history.fine_macro_f1, color=PURPLE, marker="o", ms=3.6, lw=1.35, label="fine macro-F1")
    ax.plot(history.epoch, 1 - history.eval_loss / history.eval_loss.max(), color=ORANGE, lw=0.9, ls=(0, (3, 2)), label="1 - scaled loss")
    selected_epoch = int(history.loc[history.fine_macro_f1.idxmax(), "epoch"])
    ax.axvline(selected_epoch, color=ORANGE, lw=0.9, ls=(0, (4, 2)))
    ax.text(selected_epoch - 0.15, 0.28, f"selected epoch {selected_epoch}", rotation=90, fontsize=2.9, color=ORANGE, ha="right", va="bottom", fontweight="bold")
    ax.set(xticks=history.epoch, xlabel="training epoch", ylabel="validation score", ylim=(0.18, 0.88))
    ax.tick_params(axis="both", labelsize=3.0, length=0, pad=1.0)
    ax.grid(color=GRID, lw=0.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.legend(loc="lower right", frameon=False, fontsize=2.8, handlelength=1.2)


def render() -> None:
    setup()
    embedding = read_table("blind_embedding")
    summary = read_table("blind_state_summary")
    markers = read_table("fixed_marker_contrast")
    marker_links = read_table("marker_identity_links")
    confusion = read_table("secondary_root_confusion")
    per_class = read_table("secondary_root_per_class_f1")
    recovery = read_table("secondary_root_semantic_recovery")
    split = read_table("secondary_root_split")
    history = read_table("secondary_root_validation_history")

    fig = plt.figure(figsize=(7.25, 7.90))
    atlas_bounds = [0.042, 0.575, 0.946, 0.345]
    ax_b = fig.add_axes([0.050, 0.305, 0.420, 0.205])
    recovery_bounds = [0.520, 0.305, 0.450, 0.205]
    ax_d = fig.add_axes([0.050, 0.070, 0.420, 0.160])
    ax_e = fig.add_axes([0.550, 0.070, 0.420, 0.160])

    panel_blind_atlas(fig, atlas_bounds, embedding, summary)
    panel_marker_program(ax_b, marker_links)
    panel_locked_recovery(fig, recovery_bounds, recovery, confusion)
    panel_state_f1(ax_d, per_class)
    panel_validation(ax_e, history)

    fig.text(0.042, 0.980, "Arabidopsis root: blind coherence to locked adaptation", fontsize=9.15, fontweight="bold", color=INK, va="top")
    fig.text(0.988, 0.980, "GSE152766 blind execution · GSE270140 author-labelled locked test", fontsize=3.8, color=MUTED, ha="right", va="top")
    fig.add_artist(plt.Line2D([0.042, 0.988], [0.545, 0.545], transform=fig.transFigure, color=GRID, lw=0.65))

    for artist in fig.findobj(match=Text):
        if artist.get_fontsize() < 3.0:
            artist.set_fontsize(3.0)

    stem = "plant_cellfm_v12_fig5_root_biology"
    tables = {
        "blind_embedding": embedding,
        "blind_state_summary": summary,
        "fixed_marker_contrast": markers,
        "marker_identity_links": marker_links,
        "secondary_root_confusion": confusion,
        "secondary_root_per_class_f1": per_class,
        "secondary_root_semantic_recovery": recovery,
        "secondary_root_split": split,
        "secondary_root_validation_history": history,
    }
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for suffix, options in (("svg", {"dpi": 600}), ("pdf", {"dpi": 600}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)
    print({"figure": str(MAIN / f"{stem}.png"), "source_tables": len(tables)})


if __name__ == "__main__":
    render()
