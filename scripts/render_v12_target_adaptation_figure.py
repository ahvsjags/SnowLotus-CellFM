from __future__ import annotations

"""Render the v12 target-species adaptation figure."""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.patheffects as path_effects
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
    return pd.read_csv(V11_SOURCE / f"plant_cellfm_v11_fig4_target_adaptation_{name}.tsv", sep="\t")


def short_species(value: str) -> str:
    parts = str(value).split()
    return f"{parts[0][0]}. {parts[-1]}" if len(parts) > 1 else str(value)


def panel_label(ax: plt.Axes, key: str, title: str, y: float = 1.025) -> None:
    ax.text(-0.045, y, key, transform=ax.transAxes, fontsize=8.0, fontweight="bold", color=INK, va="bottom")
    ax.text(0.0, y, title, transform=ax.transAxes, fontsize=5.6, fontweight="bold", color=INK, va="bottom")


def direct_label(ax: plt.Axes, x: float, y: float, text: str, color: str = INK, size: float = 3.1) -> None:
    artist = ax.text(x, y, text, ha="center", va="center", fontsize=size, color=color, fontweight="bold", zorder=9)
    artist.set_path_effects([path_effects.withStroke(linewidth=1.5, foreground="white")])


def density_contours(ax: plt.Axes, frame: pd.DataFrame, color: str) -> None:
    hist, x_edges, y_edges = np.histogram2d(frame.UMAP1, frame.UMAP2, bins=(72, 58))
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
    ax.contour(x_mid, y_mid, hist.T, levels=levels, colors=color, linewidths=[0.30, 0.50, 0.72][: len(levels)], alpha=0.45)


def scatter_embedding(ax: plt.Axes, cohort: pd.DataFrame, column: str, palette: dict[object, str], title: str) -> None:
    for value, part in cohort.groupby(column, sort=False):
        ax.scatter(part.UMAP1, part.UMAP2, s=1.65, color=palette.get(value, GREY), alpha=0.72, linewidths=0)
    density_contours(ax, cohort, "#8299A6")
    ax.set(xticks=[], yticks=[])
    ax.set_facecolor(PALE)
    ax.set_title(title, loc="left", fontsize=3.25, color=INK, fontweight="bold", pad=1.2)
    for spine in ax.spines.values():
        spine.set_visible(False)


def panel_landscape(fig: plt.Figure, bounds: list[float], cohort: pd.DataFrame) -> pd.DataFrame:
    container = fig.add_axes(bounds)
    panel_label(container, "a", "Sparse target adaptation landscape")
    container.set_axis_off()

    art = container.inset_axes([0.0, 0.0, 0.565, 1.0])
    art.set_axis_off()
    art.set(xlim=(0, 1), ylim=(0, 1))
    art.add_patch(
        patches.FancyBboxPatch(
            (0.025, 0.070), 0.950, 0.840,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            facecolor="#F7FAFB",
            edgecolor="#DCE7EB",
            linewidth=0.80,
        )
    )
    rng = np.random.default_rng(20260803)
    centers = [(0.180, 0.650), (0.285, 0.440), (0.385, 0.690), (0.500, 0.420)]
    colors = [BLUE, TEAL, ORANGE, PURPLE]
    for (cx, cy), color in zip(centers, colors, strict=True):
        art.scatter(cx + rng.normal(0, 0.040, 44), cy + rng.normal(0, 0.045, 44), s=5.0, color=mpl.colors.to_rgba(color, 0.42), linewidths=0, zorder=1)
        art.scatter([cx], [cy], s=28, color=color, edgecolor="white", linewidth=0.45, zorder=3)
    art.text(0.285, 0.875, "shared frozen embedding", ha="center", fontsize=3.45, color=NAVY, fontweight="bold")

    module_boxes = [
        (0.595, 0.650, "LoRA A", BLUE),
        (0.705, 0.650, "rank 8", TEAL),
        (0.815, 0.650, "LoRA B", BLUE),
        (0.650, 0.405, "target head", PURPLE),
        (0.795, 0.405, "query calls", ORANGE),
    ]
    for x, y, label, color in module_boxes:
        art.add_patch(
            patches.FancyBboxPatch((x - 0.052, y - 0.050), 0.104, 0.100, boxstyle="round,pad=0.006,rounding_size=0.012", facecolor=mpl.colors.to_rgba(color, 0.12), edgecolor=color, linewidth=0.82, zorder=4)
        )
        art.text(x, y, label, ha="center", va="center", fontsize=3.2, color=INK, fontweight="bold", zorder=5)
    for start_xy, end_xy, color in [((0.425, 0.565), (0.545, 0.650), TEAL), ((0.650, 0.650), (0.705, 0.650), BLUE), ((0.760, 0.650), (0.815, 0.650), BLUE), ((0.705, 0.600), (0.650, 0.455), PURPLE), ((0.702, 0.405), (0.743, 0.405), ORANGE)]:
        art.annotate("", xy=end_xy, xytext=start_xy, arrowprops=dict(arrowstyle="-|>", color=color, lw=1.05, shrinkA=0, shrinkB=0), zorder=3)

    for x, text, color in [(0.095, "support", BLUE), (0.185, "query", GREY), (0.835, "adapter output", TEAL)]:
        art.scatter([x], [0.130], s=16, color=color, edgecolor="white", linewidth=0.35)
        art.text(x + 0.025, 0.130, text, va="center", fontsize=3.0, color=INK if color != GREY else MUTED, fontweight="bold")
    art.text(0.500, 0.040, "support labels tune low-rank updates; query cells remain disjoint", ha="center", fontsize=3.0, color=MUTED)

    species_ax = container.inset_axes([0.590, 0.05, 0.255, 0.90])
    scatter_embedding(species_ax, cohort, "species", SPECIES_COLORS, "target-cohort geometry")
    species_ax.text(0.03, 0.965, f"{len(cohort):,} cells", transform=species_ax.transAxes, fontsize=3.2, color=INK, fontweight="bold", va="top")
    available_ax = container.inset_axes([0.855, 0.05, 0.145, 0.90])
    scatter_embedding(available_ax, cohort, "available", {True: TEAL, False: GREY}, "source-label scope")
    available_ax.text(0.97, 0.035, f"{cohort.available.mean():.1%} represented", transform=available_ax.transAxes, fontsize=2.9, color=TEAL, fontweight="bold", ha="right")
    return cohort.copy()

def panel_dose_response(fig: plt.Figure, bounds: list[float], summary: pd.DataFrame, draws: pd.DataFrame) -> None:
    container = fig.add_axes(bounds)
    panel_label(container, "b", "Support-dose response across independent draws")
    container.set_axis_off()
    random_summary = summary.loc[summary["mode"].eq("budgeted_random")].sort_values("support_value")
    random_draws = draws.loc[draws["mode"].eq("budgeted_random")]
    budgets = random_summary.support_value.astype(int).tolist()

    accuracy_ax = container.inset_axes([0.0, 0.37, 1.0, 0.63])
    positions = np.arange(len(budgets))
    arrays = [random_draws.loc[random_draws.support_value.eq(budget), "accuracy_all_query"].to_numpy() for budget in budgets]
    violins = accuracy_ax.violinplot(arrays, positions=positions, widths=0.74, showextrema=False, showmedians=False)
    for body in violins["bodies"]:
        body.set_facecolor(BLUE)
        body.set_edgecolor("white")
        body.set_alpha(0.62)
    for x, budget, values in zip(positions, budgets, arrays, strict=True):
        rng = np.random.default_rng(100 + budget)
        accuracy_ax.scatter(np.full(len(values), x) + rng.normal(0, 0.055, len(values)), values, s=10, color=mpl.colors.to_rgba(BLUE, 0.36), edgecolor="white", linewidth=0.25, zorder=3)
        mean = values.mean()
        accuracy_ax.scatter([x], [mean], s=30, color=BLUE, edgecolor="white", linewidth=0.55, zorder=5)
        accuracy_ax.text(x, mean + 0.035, f"{mean:.1%}", fontsize=3.25, color=BLUE, fontweight="bold", ha="center")
    accuracy_ax.plot(positions, random_summary.mean_accuracy_all_query, color=BLUE, lw=1.35, zorder=4)
    accuracy_ax.set(xticks=positions, xticklabels=[], ylim=(0.47, 0.82), ylabel="query accuracy")
    accuracy_ax.tick_params(axis="y", labelsize=3.0, length=0, pad=1.0)
    accuracy_ax.grid(axis="y", color=GRID, lw=0.5)
    for side in ("top", "right", "left", "bottom"):
        accuracy_ax.spines[side].set_visible(False)

    f1_ax = container.inset_axes([0.0, 0.0, 1.0, 0.28])
    f1_arrays = [random_draws.loc[random_draws.support_value.eq(budget), "macro_f1_query"].to_numpy() for budget in budgets]
    for x, budget, values in zip(positions, budgets, f1_arrays, strict=True):
        f1_ax.vlines(x, 0, values.mean(), color=mpl.colors.to_rgba(TEAL, 0.35), lw=7.5, zorder=1)
        rng = np.random.default_rng(200 + budget)
        f1_ax.scatter(np.full(len(values), x) + rng.normal(0, 0.055, len(values)), values, s=9, color=mpl.colors.to_rgba(TEAL, 0.34), linewidths=0, zorder=2)
        f1_ax.scatter([x], [values.mean()], s=25, color=TEAL, edgecolor="white", linewidth=0.5, zorder=4)
        f1_ax.text(x, values.mean() + 0.05, f"{values.mean():.2f}", fontsize=2.9, color=TEAL, fontweight="bold", ha="center")
    f1_ax.plot(positions, random_summary.mean_macro_f1_query, color=TEAL, lw=1.2, zorder=3)
    f1_ax.set(xticks=positions, xticklabels=budgets, ylim=(0.08, 0.58), ylabel="macro-F1", xlabel="labelled support cells / species")
    f1_ax.tick_params(axis="both", labelsize=3.0, length=0, pad=1.0)
    f1_ax.grid(axis="y", color=GRID, lw=0.45)
    for side in ("top", "right", "left"):
        f1_ax.spines[side].set_visible(False)
    f1_ax.spines["bottom"].set_color(GRID)


def panel_species_lanes(ax: plt.Axes, species_means: pd.DataFrame) -> None:
    panel_label(ax, "c", "Species-resolved adaptation trajectories")
    budgets = sorted(species_means.support_value.unique())
    x = np.arange(len(budgets))
    species_order = list(SPECIES_COLORS)
    ax.set(xlim=(-0.15, len(budgets) - 0.20), ylim=(-0.55, len(species_order) - 0.15))
    for row, species in enumerate(species_order[::-1]):
        part = species_means.loc[species_means.species.eq(species)].set_index("support_value").loc[budgets]
        values = part.species_accuracy_all_query.to_numpy(float)
        y0 = row
        lane = y0 - 0.22 + 0.44 * values
        color = SPECIES_COLORS[species]
        ax.plot(x, lane, color=color, lw=1.25, marker="o", ms=3.4, markeredgecolor="white", markeredgewidth=0.42, zorder=3)
        ax.hlines(y0, x[0], x[-1], color=GRID, lw=0.45, zorder=0)
        ax.text(-0.18, y0, short_species(species), ha="right", va="center", fontsize=2.8, color=INK)
        ax.text(x[-1] + 0.05, lane[-1], f"{values[-1]:.0%}", fontsize=2.85, color=color, fontweight="bold", va="center")
    ax.set(xticks=x, xticklabels=budgets, yticks=[], xlabel="support cells / species")
    ax.tick_params(axis="x", labelsize=3.0, length=0, pad=1.0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.text(0.02, 0.98, "lane height encodes query accuracy", transform=ax.transAxes, fontsize=2.9, color=MUTED, va="top")


def panel_contract(ax: plt.Axes, contract: pd.DataFrame) -> None:
    panel_label(ax, "d", "Physically disjoint support/query contract")
    frame = contract.sort_values("support_value").reset_index(drop=True)
    ax.set_axis_off()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    for index, row in frame.iterrows():
        y = 0.80 - index * 0.20
        total = row.mean_support_cells + row.mean_query_cells
        support_fraction = row.mean_support_cells / total
        ax.text(0.02, y, f"{int(row.support_value)} / species", fontsize=3.0, color=BLUE, fontweight="bold", va="center")
        support_size = 22 + 130 * np.sqrt(row.mean_support_cells / frame.mean_support_cells.max())
        query_size = 22 + 130 * np.sqrt(row.mean_query_cells / frame.mean_query_cells.max())
        ax.scatter([0.25], [y], s=support_size, color=BLUE, edgecolor="white", linewidth=0.55, zorder=3)
        ax.scatter([0.73], [y], s=query_size, color=GREY, edgecolor="white", linewidth=0.55, zorder=3)
        ax.annotate("", xy=(0.65, y), xytext=(0.33, y), arrowprops=dict(arrowstyle="->", color=GRID, lw=1.4))
        ax.text(0.25, y, f"{int(row.mean_support_cells)}", ha="center", va="center", fontsize=2.9, color="white", fontweight="bold")
        ax.text(0.73, y, f"{int(row.mean_query_cells):,}", ha="center", va="center", fontsize=2.9, color=INK, fontweight="bold")
        ax.text(0.96, y, f"{row.mean_accuracy_all_query:.1%}", ha="right", va="center", fontsize=3.1, color=TEAL, fontweight="bold")
    ax.text(0.25, 0.98, "labelled support", ha="center", fontsize=3.0, color=BLUE, fontweight="bold")
    ax.text(0.73, 0.98, "unlabelled query", ha="center", fontsize=3.0, color=MUTED, fontweight="bold")
    ax.text(0.96, 0.98, "accuracy", ha="right", fontsize=3.0, color=MUTED)


def panel_strategy(ax: plt.Axes, strategy: pd.DataFrame, draws: pd.DataFrame) -> None:
    panel_label(ax, "e", "Allocation strategy landscape")
    frame = strategy.sort_values(["mode", "support_value", "support_weight"]).reset_index(drop=True)
    labels = frame.setting.tolist()
    y = np.arange(len(frame))[::-1]
    for yi, (_, row) in zip(y, frame.iterrows(), strict=True):
        values = draws.loc[
            draws["mode"].eq(row["mode"]) & draws.support_value.eq(row.support_value) & draws.support_weight.eq(row.support_weight),
            "accuracy_all_query",
        ].to_numpy()
        color = BLUE if row["mode"] == "budgeted_random" else PURPLE
        parts = ax.violinplot([values], positions=[yi], vert=False, widths=0.62, showextrema=False, showmeans=False, showmedians=False)
        body = parts["bodies"][0]
        body.set_facecolor(color)
        body.set_edgecolor("white")
        body.set_alpha(0.50)
        rng = np.random.default_rng(400 + yi)
        ax.scatter(values, np.full(len(values), yi) + rng.normal(0, 0.055, len(values)), s=7.5, color=mpl.colors.to_rgba(color, 0.46), linewidths=0, zorder=3)
        ax.scatter([row.mean_accuracy_all_query], [yi], s=27, color=color, edgecolor="white", linewidth=0.5, zorder=4)
        ax.text(row.mean_accuracy_all_query + 0.012, yi, f"{row.mean_accuracy_all_query:.1%}", fontsize=2.85, color=color, fontweight="bold", va="center")
    ax.set(yticks=y, yticklabels=labels, xlim=(0.38, 0.82), xlabel="query accuracy")
    ax.tick_params(axis="both", labelsize=2.9, length=0, pad=1.0)
    ax.grid(axis="x", color=GRID, lw=0.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.text(0.01, 0.02, "blue: random budget | violet: label-stratified", transform=ax.transAxes, fontsize=2.9, color=MUTED)


def render() -> None:
    setup()
    summary = read_table("fewshot_summary")
    species_means = read_table("per_species_budget_means")
    contract = read_table("support_query_contract")
    strategy = read_table("allocation_strategy_summary")
    cohort = read_table("target_cohort_embedding")
    draws = read_table("raw_draw_metrics")
    species_draws = read_table("per_species_draw_metrics")

    fig = plt.figure(figsize=(7.25, 7.90))
    landscape_bounds = [0.042, 0.570, 0.946, 0.355]
    dose_bounds = [0.050, 0.305, 0.505, 0.205]
    ax_c = fig.add_axes([0.620, 0.305, 0.350, 0.205])
    ax_d = fig.add_axes([0.050, 0.070, 0.395, 0.160])
    ax_e = fig.add_axes([0.510, 0.070, 0.460, 0.160])

    cohort_table = panel_landscape(fig, landscape_bounds, cohort)
    panel_dose_response(fig, dose_bounds, summary, draws)
    panel_species_lanes(ax_c, species_means)
    panel_contract(ax_d, contract)
    panel_strategy(ax_e, strategy, draws)

    fig.text(0.042, 0.980, "Target-species adaptation from sparse labelled support", fontsize=9.15, fontweight="bold", color=INK, va="top")
    fig.text(0.988, 0.980, "8 target species · 10 fixed draws per setting · support/query partitions disjoint", fontsize=3.8, color=MUTED, ha="right", va="top")
    fig.add_artist(plt.Line2D([0.042, 0.988], [0.545, 0.545], transform=fig.transFigure, color=GRID, lw=0.65))

    for artist in fig.findobj(match=Text):
        if artist.get_fontsize() < 3.0:
            artist.set_fontsize(3.0)

    stem = "plant_cellfm_v12_fig4_target_adaptation"
    tables = {
        "fewshot_summary": summary,
        "raw_draw_metrics": draws,
        "per_species_draw_metrics": species_draws,
        "per_species_budget_means": species_means,
        "target_cohort_embedding": cohort_table,
        "support_query_contract": contract,
        "allocation_strategy_summary": strategy,
    }
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for suffix, options in (("svg", {"dpi": 600}), ("pdf", {"dpi": 600}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)
    print({"figure": str(MAIN / f"{stem}.png"), "source_tables": len(tables)})


if __name__ == "__main__":
    render()
