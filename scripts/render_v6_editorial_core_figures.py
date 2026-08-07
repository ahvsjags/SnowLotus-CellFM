from __future__ import annotations

"""Render the v6 editorial rebuild of the two evidence-critical main figures.

The renderer intentionally uses only frozen v17/v14/v9 records.  It redesigns
hierarchy and density without replacing the primary strict score, masking
open-set cells, or creating an unsupported external-model comparison.
"""

import json
import sys
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import umap
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, Rectangle
from sklearn.metrics import f1_score

import render_v4_top_journal_figures as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "plant_cellfm_submission_v6"
MAIN = OUT / "main"
SOURCE = OUT / "source_data"
PROFILE = ROOT / "figure_data" / "corpus_profile_v1"

INK = "#17232D"
MUTED = "#61778A"
GRID = "#D9E4E9"
TEAL = "#007C83"
BLUE = "#2E6FAD"
ORANGE = "#D97524"
PURPLE = "#8064A7"
RED = "#B34D5B"
GREY = "#9CAAB2"
LIGHT_GREY = "#E8EFF2"
DIRECT_ROOT_LABELS = ["Non-hair", "Phloem", "Root cap", "Root cortex", "Root endodermis", "Root hair", "Unknow", "Xylem"]


def setup() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 6.4,
            "axes.labelcolor": INK,
            "axes.edgecolor": INK,
            "axes.linewidth": 0.65,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.major.width": 0.55,
            "ytick.major.width": 0.55,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )
    MAIN.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)


def panel(
    ax: plt.Axes,
    letter: str,
    title: str,
    subtitle: str | None = None,
    *,
    title_x: float = 0.0,
) -> None:
    ax.text(-0.065, 1.06, letter, transform=ax.transAxes, fontsize=8.2, fontweight="bold", va="bottom", color=INK)
    ax.text(title_x, 1.06, title, transform=ax.transAxes, fontsize=6.75, fontweight="bold", va="bottom", color=INK)
    if subtitle:
        ax.text(title_x, 1.008, subtitle, transform=ax.transAxes, fontsize=5.12, va="bottom", color=MUTED)


def clean(ax: plt.Axes, axis: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if axis:
        ax.grid(axis=axis, color=GRID, linewidth=0.58, zorder=0)
    ax.tick_params(length=2.1, pad=2.0)


def short_species(value: str) -> str:
    words = str(value).split()
    return f"{words[0][0]}. {words[1]}" if len(words) == 2 else str(value)


def export(fig: plt.Figure, stem: str, tables: dict[str, pd.DataFrame]) -> None:
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    base.enforce_minimum_text_size(fig)
    # Use the same 600-dpi raster contract for rasterized scatter/heatmap
    # artists embedded in the otherwise editable vector pages.
    for suffix, options in (("svg", {"dpi": 600}), ("pdf", {"dpi": 600}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)


def normalise_svg_whitespace() -> None:
    """Keep generated vector paths quiet in version control without changing geometry."""
    for path in OUT.rglob("*.svg"):
        content = path.read_text(encoding="utf-8")
        path.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")


def plot_embedding(ax: plt.Axes, frame: pd.DataFrame, column: str, palette: dict[str, str], *, size: float, alpha: float) -> None:
    for value, subset in frame.groupby(column, sort=False):
        ax.scatter(
            subset.UMAP1,
            subset.UMAP2,
            s=size,
            linewidth=0,
            alpha=alpha,
            color=palette.get(str(value), GREY),
            rasterized=True,
        )
    ax.set(xticks=[], yticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)


def compact_author_label(value: str) -> str:
    labels = {
        "Dividing Cells": "Dividing",
        "Endodermis/Phloem": "Endo./phloem",
        "Provascular cells": "Provascular",
        "Root Cap": "Root cap",
        "Root Hair": "Root hair",
    }
    return labels.get(str(value), str(value))


def direct_root_bootstrap(frame: pd.DataFrame, column: str, *, seed: int) -> pd.DataFrame:
    """Bootstrap the two fixed predictions without reopening the held-out split."""
    rng = np.random.default_rng(seed)
    truth = frame.expected_root_label.to_numpy(dtype=str)
    predicted = frame[column].to_numpy(dtype=str)
    rows: list[dict[str, float | int]] = []
    for iteration in range(3000):
        take = rng.integers(0, len(frame), len(frame))
        rows.append(
            {
                "iteration": iteration,
                "accuracy": float(np.mean(truth[take] == predicted[take])),
                "macro_f1": float(f1_score(truth[take], predicted[take], labels=DIRECT_ROOT_LABELS, average="macro", zero_division=0)),
            }
        )
    return pd.DataFrame(rows)


def render_fig1(frame: pd.DataFrame) -> None:
    profile = json.loads((PROFILE / "corpus_profile.json").read_text(encoding="utf-8"))
    corpus = pd.read_csv(PROFILE / "species_by_tissue.tsv", sep="\t")
    species = corpus.groupby("species", as_index=False).cells.sum().sort_values("cells", ascending=False)
    matrix = corpus.pivot_table(index="species", columns="tissue", values="cells", aggfunc="sum", fill_value=0).sort_index()
    strict_species = frame.groupby("species", as_index=False).size().rename(columns={"size": "strict_panel_cells"})
    ontology_display = frame.ontology.where(frame.ontology.isin(list(base.ONTOLOGY)[:-1]), "other")

    fig = plt.figure(figsize=(7.25, 5.78))
    grid = fig.add_gridspec(
        2,
        10,
        height_ratios=(0.91, 1.09),
        width_ratios=(1.15, 1.15, 1.15, 1.15, 1.15, 1.15, 1.00, 1.00, 1.00, 1.00),
        left=0.055,
        right=0.988,
        bottom=0.07,
        top=0.95,
        hspace=0.47,
        wspace=0.51,
    )
    ax_a = fig.add_subplot(grid[0, :6])
    ax_b = fig.add_subplot(grid[0, 6:])
    ax_c = fig.add_subplot(grid[1, :4])
    ax_d = fig.add_subplot(grid[1, 4:7])
    ax_e = fig.add_subplot(grid[1, 7:])

    ax_a.set_axis_off()
    panel(ax_a, "a", "A traceable gene-to-cell contract defines each annotation", "The visual hierarchy begins with the data contract, not a headline score")
    stages = [
        (0.01, 0.29, "input genes", "counts + IDs\nper cell", BLUE),
        (0.255, 0.29, "orthology", "deterministic\nprojection", ORANGE),
        (0.50, 0.29, "Plant-CellFM", "256-dim\ncell state", TEAL),
        (0.745, 0.29, "evidence record", "coverage + adapter\n+ markers", PURPLE),
    ]
    for x, width, title, subtitle, color in stages:
        ax_a.add_patch(Rectangle((x, 0.40), width - 0.035, 0.39, transform=ax_a.transAxes, facecolor="#F6F8F9", edgecolor=color, linewidth=1.0))
        ax_a.add_patch(Rectangle((x, 0.73), width - 0.035, 0.06, transform=ax_a.transAxes, facecolor=color, edgecolor=color, linewidth=0))
        ax_a.text(x + (width - 0.035) / 2, 0.60, title, transform=ax_a.transAxes, ha="center", va="center", fontsize=6.0, fontweight="bold", color=INK)
        ax_a.text(x + (width - 0.035) / 2, 0.47, subtitle, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.1, color=MUTED)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((left[0] + left[1] - 0.025, 0.595), (right[0] - 0.014, 0.595), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=0.8, color=MUTED))
    footer = [("frozen corpus", f"{profile['shape']['cells']:,} cells", GREY), ("strict transfer", f"{len(frame):,} cells", TEAL), ("adaptation registry", "24 species modules", PURPLE)]
    for index, (label, value, color) in enumerate(footer):
        x = 0.02 + index * 0.32
        ax_a.plot([x, x + 0.035], [0.17, 0.17], transform=ax_a.transAxes, color=color, lw=2.7, solid_capstyle="round")
        ax_a.text(x + 0.05, 0.19, label, transform=ax_a.transAxes, fontsize=4.95, color=MUTED, va="center")
        ax_a.text(x + 0.05, 0.10, value, transform=ax_a.transAxes, fontsize=5.65, color=INK, fontweight="bold", va="center")
    ax_a.text(0.995, 0.035, "All reported outputs retain mapping, denominator and scope metadata.", transform=ax_a.transAxes, ha="right", fontsize=4.95, color=RED)

    species_order = species.species.tolist()[::-1]
    colors = [base.SPECIES.get(value, GREY) for value in species_order]
    values = species.set_index("species").loc[species_order, "cells"].to_numpy() / 1000
    y = np.arange(len(species_order))
    ax_b.barh(y, values, color=colors, height=0.58)
    for index, value in enumerate(values):
        ax_b.text(value + 2.0, index, f"{value:.0f}k", va="center", fontsize=5.2, color=INK)
    ax_b.set(yticks=y, yticklabels=[short_species(value) for value in species_order], xlabel="frozen-profile cells (thousands)", xlim=(0, max(values) * 1.22))
    ax_b.tick_params(axis="y", labelsize=5.2, length=0)
    clean(ax_b, "x")
    panel(ax_b, "b", "Training profile is compact and declared", "Five profiled species; historical catalogues are excluded")

    plot_embedding(ax_c, frame, "species", base.SPECIES, size=3.0, alpha=0.80)
    label_positions = {
        "Arabidopsis thaliana": (0.03, 0.05),
        "Brassica rapa": (0.03, 0.12),
        "Catharanthus roseus": (0.03, 0.19),
        "Eutrema salsugineum": (0.52, 0.05),
        "Fragaria vesca": (0.52, 0.12),
        "Gossypium bickii": (0.52, 0.19),
        "Gossypium hirsutum": (0.52, 0.26),
        "Triticum aestivum": (0.52, 0.33),
    }
    for species_name, (x, y_value) in label_positions.items():
        ax_c.scatter([x - 0.02], [y_value], transform=ax_c.transAxes, s=12, color=base.SPECIES.get(species_name, GREY), clip_on=False)
        ax_c.text(x, y_value, short_species(species_name), transform=ax_c.transAxes, fontsize=4.75, va="center", color=INK)
    panel(ax_c, "c", "Held-out species occupy a shared representation", "3,964 cells; color encodes species, not predicted identity")

    ontology_frame = frame.assign(ontology_display=ontology_display)
    ontology_palette = {**base.ONTOLOGY, "other": "#CBD5D8"}
    plot_embedding(ax_d, ontology_frame, "ontology_display", ontology_palette, size=3.0, alpha=0.83)
    ontology_labels = ["mesophyll", "epidermis", "root cap", "vascular stele", "xylem", "phloem", "cortex", "endodermis", "other"]
    for index, label in enumerate(ontology_labels):
        column, row = divmod(index, 3)
        x, y_value = 0.02 + column * 0.32, 0.05 + row * 0.07
        ax_d.scatter([x], [y_value], transform=ax_d.transAxes, s=10, color=ontology_palette.get(label, GREY), clip_on=False)
        ax_d.text(x + 0.025, y_value, label, transform=ax_d.transAxes, fontsize=4.3, va="center", color=INK)
    panel(ax_d, "d", "Ontology states recur across species", "Recorded separately from species identity")

    values = matrix.to_numpy(dtype=float)
    image = ax_e.imshow(np.log10(values + 1), aspect="auto", cmap=LinearSegmentedColormap.from_list("v6_corpus", ["#F5F7F8", "#AED7D4", TEAL]))
    for yi, species_name in enumerate(matrix.index):
        for xi, tissue in enumerate(matrix.columns):
            value = int(matrix.loc[species_name, tissue])
            if value:
                ax_e.text(xi, yi, f"{value // 1000}k" if value >= 1000 else str(value), ha="center", va="center", fontsize=4.6, color="white" if value > values.max() * 0.4 else INK)
    ax_e.set(xticks=np.arange(len(matrix.columns)), xticklabels=[str(value).replace("_", " ") for value in matrix.columns], yticks=np.arange(len(matrix.index)), yticklabels=[short_species(value) for value in matrix.index])
    ax_e.tick_params(axis="x", labelsize=4.45, rotation=32, length=0, pad=1.1)
    ax_e.tick_params(axis="y", labelsize=4.7, length=0, pad=1.2)
    for spine in ax_e.spines.values():
        spine.set_visible(False)
    bar = fig.colorbar(image, ax=ax_e, fraction=0.045, pad=0.02)
    bar.ax.tick_params(labelsize=4.7, length=1.5)
    bar.set_label("log10(cells + 1)", size=4.6)
    panel(ax_e, "e", "Frozen species-by-tissue matrix", "Only profile cells enter this matrix")

    export(
        fig,
        "plant_cellfm_v6_fig1_foundation_contract",
        {
            "strict_embedding": frame[["cell_id", "species", "organ", "truth_label", "ontology", "UMAP1", "UMAP2"]],
            "frozen_profile_species": species,
            "frozen_profile_species_by_tissue": corpus,
            "strict_species_counts": strict_species,
            "workflow_contract": pd.DataFrame(
                {"stage": [entry[2] for entry in stages], "recorded_property": [entry[3].replace("\n", " ") for entry in stages]}
            ),
        },
    )


def render_fig2(frame: pd.DataFrame, v17: pd.DataFrame) -> None:
    strict = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))["summary"]
    v14 = json.loads((ROOT / "release_metadata" / "algorithm_innovation_v14.json").read_text(encoding="utf-8"))["metrics"]
    v3v9 = json.loads((ROOT / "release_metadata" / "v9_benchmarks" / "v9_lora_vs_v3_shared_comparison.json").read_text(encoding="utf-8"))
    records = v17.sort_values("accuracy_all", ascending=True).reset_index(drop=True)
    records["open_or_unavailable"] = 1.0 - records.coverage
    records["cells"] = records.n_test.astype(int)
    bootstrap = base.bootstrap(frame, iterations=3000)
    ci_low, ci_high = bootstrap.all_cell_accuracy.quantile([0.025, 0.975]).tolist()

    fig = plt.figure(figsize=(7.25, 5.78))
    grid = fig.add_gridspec(
        2,
        10,
        height_ratios=(1.06, 0.94),
        width_ratios=(1.15, 1.15, 1.15, 1.15, 1.15, 1.00, 1.00, 1.00, 1.00, 1.00),
        left=0.055,
        right=0.988,
        bottom=0.07,
        top=0.95,
        hspace=0.66,
        wspace=0.57,
    )
    ax_a = fig.add_subplot(grid[:, :5])
    ax_b = fig.add_subplot(grid[0, 5:])
    ax_c = fig.add_subplot(grid[1, 5:7])
    ax_d = fig.add_subplot(grid[1, 7:])

    y = np.arange(len(records))
    ax_a.hlines(y, records.accuracy_all, records.accuracy, color="#D7E2E6", lw=2.25, zorder=1)
    ax_a.scatter(records.coverage, y, marker="s", s=38, color=ORANGE, zorder=3, label="source-label coverage")
    ax_a.scatter(records.accuracy, y, s=44, color=BLUE, zorder=3, label="covered-label accuracy")
    ax_a.scatter(records.accuracy_all, y, s=44, color=TEAL, zorder=4, label="all-cell accuracy")
    ax_a.axvline(strict["accuracy_all"], color=TEAL, lw=0.75, ls="--", alpha=0.58)
    ax_a.set(yticks=y, yticklabels=[short_species(value) for value in records.held_out_species], xlim=(-0.03, 1.05), xlabel="fraction of held-out cells")
    ax_a.tick_params(axis="y", labelsize=5.15)
    clean(ax_a, "x")
    ax_a.legend(loc="lower right", bbox_to_anchor=(1.01, 1.02), ncol=3, frameon=False, fontsize=4.75, handletextpad=0.25, columnspacing=0.65)
    panel(ax_a, "a", "Strict transfer is measurable but highly heterogeneous across held-out species", "Teal is the primary all-cell score; denominators for every species are retained in source data")
    ax_a.text(0.01, -0.19, "The dashed line is the locked v17 primary all-cell estimate across all 3,964 cells: 39.96%.", transform=ax_a.transAxes, fontsize=4.8, color=TEAL, fontweight="bold")

    ax_b.set_axis_off()
    panel(ax_b, "b", "The primary denominator stays visible", "Open-set or unavailable labels are retained rather than filtered out")
    denominator = [
        ("all held-out cells", int(strict["n_test"]), GREY),
        ("source-label covered", int(strict["n_evaluable"]), TEAL),
        ("open-set / unavailable", int(strict["open_set_cells"]), ORANGE),
    ]
    max_count = max(value for _, value, _ in denominator)
    for index, (label, count, color) in enumerate(denominator):
        y0 = 0.69 - index * 0.22
        width = 0.66 * count / max_count
        ax_b.add_patch(Rectangle((0.02, y0), width, 0.105, transform=ax_b.transAxes, facecolor=color, edgecolor="none"))
        ax_b.text(0.02, y0 + 0.125, label, transform=ax_b.transAxes, fontsize=5.0, color=MUTED, va="bottom")
        ax_b.text(0.72, y0 + 0.052, f"{count:,}", transform=ax_b.transAxes, fontsize=6.1, color=INK, fontweight="bold", va="center")
    metrics = [("all-cell accuracy", strict["accuracy_all"], TEAL), ("known-label accuracy", strict["accuracy"], BLUE), ("known-label macro-F1", strict["macro_f1"], PURPLE), ("coverage", strict["coverage"], ORANGE)]
    for index, (label, value, color) in enumerate(metrics):
        x = 0.02 + (index % 2) * 0.48
        y0 = 0.14 - (index // 2) * 0.085
        ax_b.text(x, y0 + 0.053, label, transform=ax_b.transAxes, fontsize=4.55, color=MUTED)
        ax_b.text(x, y0, f"{value:.1%}", transform=ax_b.transAxes, fontsize=6.5, color=color, fontweight="bold")
    ax_b.text(0.98, 0.012, f"fixed bootstrap 95% interval: {ci_low:.3f}–{ci_high:.3f}", transform=ax_b.transAxes, ha="right", fontsize=4.45, color=MUTED)

    coverage_display = records.sort_values("coverage", ascending=True).reset_index(drop=True)
    y = np.arange(len(coverage_display))
    ax_c.barh(y, coverage_display.coverage, color=ORANGE, height=0.62, label="covered")
    ax_c.barh(y, coverage_display.open_or_unavailable, left=coverage_display.coverage, color=LIGHT_GREY, height=0.62, label="open / unavailable")
    ax_c.set(yticks=y, yticklabels=[short_species(value) for value in coverage_display.held_out_species], xlim=(0, 1), xlabel="label coverage")
    ax_c.tick_params(axis="y", labelsize=4.55, length=0)
    clean(ax_c, "x")
    panel(ax_c, "c", "Coverage audit", "Zero shared labels stay visible", title_x=0.10)

    historical = pd.DataFrame(
        [
            {"protocol": "leave dataset", "v3": v3v9["baseline"]["summary"]["leave_dataset_out"]["fine"]["accuracy_all"], "v9": v3v9["candidate"]["summary"]["leave_dataset_out"]["fine"]["accuracy_all"]},
            {"protocol": "leave sample", "v3": v3v9["baseline"]["summary"]["leave_sample_out"]["fine"]["accuracy_all"], "v9": v3v9["candidate"]["summary"]["leave_sample_out"]["fine"]["accuracy_all"]},
            {"protocol": "leave species", "v3": v3v9["baseline"]["summary"]["leave_species_out"]["fine"]["accuracy_all"], "v9": v3v9["candidate"]["summary"]["leave_species_out"]["fine"]["accuracy_all"]},
        ]
    )
    method_rows = [
        ("centroid", v14["centroid_baseline"], GREY),
        ("expression", v14["v10_expression_stc"], BLUE),
        ("neural", v14["v13_neural_stc"], PURPLE),
        ("context gate", v14["v14_context_aware_stc"], TEAL),
    ]
    y = np.arange(len(method_rows))
    for index, (name, values, color) in enumerate(method_rows):
        ax_d.hlines(index, 0, values["all_cell_accuracy"], color=LIGHT_GREY, lw=2.0, zorder=1)
        ax_d.scatter(values["all_cell_accuracy"], index, s=38, color=color, edgecolor="white", linewidth=0.55, zorder=3)
        ax_d.text(values["all_cell_accuracy"] + 0.008, index, f"{values['all_cell_accuracy']:.1%}", va="center", fontsize=4.65, color=INK)
    ax_d.set(yticks=y, yticklabels=[value[0] for value in method_rows], xlim=(-0.015, 0.50), xlabel="all-cell accuracy")
    ax_d.tick_params(axis="y", labelsize=4.7, length=0, pad=1.2)
    clean(ax_d, "x")
    panel(ax_d, "d", "Context sensitivity", "Sensitivity only; not nested v17", title_x=0.10)

    export(
        fig,
        "plant_cellfm_v6_fig2_strict_transfer",
        {
            "v17_species_metrics": records,
            "primary_denominator": pd.DataFrame({"stage": [value[0] for value in denominator], "cells": [value[1] for value in denominator]}),
            "all_cell_bootstrap": bootstrap,
            "v14_context_sensitivity": pd.DataFrame(
                [
                    {"method": name, "all_cell_accuracy": values["all_cell_accuracy"], "coverage": values["coverage"], "known_label_accuracy": values["known_label_accuracy"], "known_label_macro_f1": values["known_label_macro_f1"]}
                    for name, values, _ in method_rows
                ]
            ),
            "historical_matched_v3_to_v9": historical,
        },
    )


def render_fig3() -> None:
    draws, species_draws = base.fewshot_tables()
    budgets = sorted(draws.support_per_species.unique().tolist())
    accuracy = draws.groupby("support_per_species", as_index=False).agg(
        mean=("accuracy_all_query", "mean"),
        sd=("accuracy_all_query", "std"),
    )
    macro = draws.groupby("support_per_species", as_index=False).agg(
        mean=("macro_f1_query", "mean"),
        sd=("macro_f1_query", "std"),
    )
    species_summary = species_draws.groupby(["species", "support_per_species"], as_index=False).agg(
        accuracy=("accuracy_all_query", "mean"),
        query_labels=("query_labels", "median"),
        query_cells=("query_cells", "median"),
    )
    order = sorted(species_summary.species.unique().tolist(), key=short_species)
    heat = species_summary.pivot(index="species", columns="support_per_species", values="accuracy").reindex(index=order, columns=budgets)
    label_counts = species_summary.pivot(index="species", columns="support_per_species", values="query_labels").reindex(index=order, columns=budgets)
    protocol = draws.groupby("support_per_species", as_index=False).agg(
        draws=("seed", "nunique"),
        support_cells=("support_cells", "median"),
        query_cells=("query_cells", "median"),
    )

    fig = plt.figure(figsize=(7.25, 5.45))
    grid = fig.add_gridspec(
        2,
        10,
        height_ratios=(0.95, 1.05),
        width_ratios=(1.1, 1.1, 1.1, 1.15, 1.15, 1.15, 1.15, 1.15, 1.15, 1.15),
        left=0.055,
        right=0.988,
        bottom=0.09,
        top=0.95,
        hspace=0.74,
        wspace=0.54,
    )
    ax_a = fig.add_subplot(grid[0, :3])
    ax_b = fig.add_subplot(grid[0, 3:])
    ax_c = fig.add_subplot(grid[1, :5])
    ax_d = fig.add_subplot(grid[1, 5:])

    ax_a.set_axis_off()
    panel(ax_a, "a", "Support and query cells are disjoint", "Eight held-out species; ten fixed support draws per budget")
    stages = [
        (0.02, 0.29, "target species", "labels locked\nuntil draw", GREY),
        (0.37, 0.29, "support", "labelled\n8–64 cells", ORANGE),
        (0.37, 0.04, "query", "unlabelled\nscored once", TEAL),
        (0.73, 0.29, "adapter", "fit only to\nsupport", PURPLE),
    ]
    for x, y0, title, subline, color in stages:
        height = 0.53 if title in {"target species", "adapter"} else 0.22
        ax_a.add_patch(Rectangle((x, y0), 0.23, height, transform=ax_a.transAxes, facecolor="#F5F7F8", edgecolor=color, linewidth=0.85))
        ax_a.text(x + 0.115, y0 + height * 0.60, title, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.35, fontweight="bold", color=INK)
        ax_a.text(x + 0.115, y0 + height * 0.25, subline, transform=ax_a.transAxes, ha="center", va="center", fontsize=4.6, color=MUTED)
    ax_a.add_patch(FancyArrowPatch((0.27, 0.55), (0.34, 0.55), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=0.75, color=MUTED))
    ax_a.add_patch(FancyArrowPatch((0.63, 0.55), (0.70, 0.55), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=0.75, color=MUTED))
    ax_a.text(0.50, -0.055, "Support cells never re-enter query scoring.", transform=ax_a.transAxes, ha="center", fontsize=4.85, color=RED, fontweight="bold")

    rng = np.random.default_rng(20260801)
    means = []
    for index, budget in enumerate(budgets):
        values = draws.loc[draws.support_per_species.eq(budget), "accuracy_all_query"].to_numpy()
        means.append(values.mean())
        ax_b.scatter(rng.normal(index, 0.038, len(values)), values, s=20, color="#B9DFDC", edgecolor="white", linewidth=0.35, zorder=2)
        ax_b.errorbar(index, values.mean(), yerr=values.std(ddof=0), color=TEAL, marker="o", markersize=6.4, markeredgecolor="white", markeredgewidth=0.7, capsize=2.4, lw=1.45, zorder=4)
        ax_b.text(index, values.mean() + 0.026, f"{values.mean():.3f}", ha="center", fontsize=5.3, fontweight="bold", color=INK)
    ax_b.plot(range(len(budgets)), means, color=TEAL, lw=1.25, zorder=3)
    ax_b.set(xticks=range(len(budgets)), xticklabels=budgets, ylim=(0.49, 0.80), xlabel="labelled support cells per target species", ylabel="query all-cell accuracy")
    clean(ax_b, "y")
    panel(ax_b, "b", "Small labelled support produces a repeatable adaptation dose response", "64 support cells per species: 75.89% mean query all-cell accuracy")
    ax_b.text(0.99, 0.05, "10 independent support draws per budget\npoints: raw draws; intervals: s.d.", transform=ax_b.transAxes, ha="right", fontsize=4.8, color=MUTED)

    macro_means = []
    for index, budget in enumerate(budgets):
        values = draws.loc[draws.support_per_species.eq(budget), "macro_f1_query"].to_numpy()
        macro_means.append(values.mean())
        ax_c.scatter(rng.normal(index, 0.038, len(values)), values, s=18, color="#DCCEEB", edgecolor="white", linewidth=0.35, zorder=2)
        ax_c.errorbar(index, values.mean(), yerr=values.std(ddof=0), color=PURPLE, marker="o", markersize=6.0, markeredgecolor="white", markeredgewidth=0.7, capsize=2.3, lw=1.35, zorder=4)
        ax_c.text(index, values.mean() + 0.027, f"{values.mean():.3f}", ha="center", fontsize=5.05, fontweight="bold", color=INK)
    ax_c.plot(range(len(budgets)), macro_means, color=PURPLE, lw=1.2, zorder=3)
    ax_c.set(xticks=range(len(budgets)), xticklabels=budgets, ylim=(0.16, 0.52), xlabel="support cells per target species", ylabel="query macro-F1")
    clean(ax_c, "y")
    panel(ax_c, "c", "Fine-label recovery follows the same support response", "Macro-F1 remains distinct from the all-cell headline")

    image = ax_d.imshow(heat.to_numpy(), aspect="auto", cmap=LinearSegmentedColormap.from_list("fewshot_v6", ["#F4F7F8", "#B9DFDC", TEAL]), vmin=0, vmax=1)
    for yi, species_name in enumerate(heat.index):
        for xi, budget in enumerate(heat.columns):
            value = float(heat.loc[species_name, budget])
            low_information = int(label_counts.loc[species_name, budget]) <= 1
            if low_information:
                ax_d.add_patch(Rectangle((xi - 0.5, yi - 0.5), 1, 1, facecolor="#DCE2E5", edgecolor="white", linewidth=0.45, hatch="////", zorder=2))
            ax_d.text(xi, yi, f"{value:.2f}{'†' if low_information else ''}", ha="center", va="center", fontsize=5.0, color=INK if low_information or value < 0.65 else "white", zorder=3)
    ax_d.set(xticks=np.arange(len(budgets)), xticklabels=budgets, yticks=np.arange(len(heat.index)), yticklabels=[short_species(value) for value in heat.index])
    ax_d.tick_params(axis="x", labelsize=5.0, length=0)
    ax_d.tick_params(axis="y", labelsize=4.8, length=0, pad=1.6)
    for spine in ax_d.spines.values():
        spine.set_visible(False)
    bar = fig.colorbar(image, ax=ax_d, fraction=0.037, pad=0.022)
    bar.ax.tick_params(labelsize=4.8, length=1.1)
    panel(ax_d, "d", "Species gains remain inspectable", "† query label space has one class; retained as low-information")

    export(
        fig,
        "plant_cellfm_v6_fig3_target_adaptation",
        {
            "fewshot_draws": draws,
            "fewshot_species_draws": species_draws,
            "fewshot_accuracy_summary": accuracy,
            "fewshot_macro_f1_summary": macro,
            "fewshot_species_budget_means": species_summary,
            "fewshot_protocol_summary": protocol,
        },
    )


def render_fig4_external_root() -> None:
    """Render an explicitly label-free biological execution page."""
    record = json.loads((ROOT / "release_metadata" / "gse152766_external_root_blind_inference_v4.json").read_text(encoding="utf-8"))
    case_root = ROOT / "outputs" / "external_validation" / "gse152766_gsm4626007" / "annotation_bundle"
    predictions = pd.read_csv(case_root / "predictions.csv")
    embeddings = np.load(case_root / "embeddings.npy").astype(np.float32)
    states = pd.DataFrame(record["prediction_distribution"])
    markers = pd.DataFrame(record["predefined_marker_coherence"])
    if len(predictions) != embeddings.shape[0] or len(predictions) != 6566 or len(markers) != 6:
        raise ValueError("The label-free external-root bundle does not match its frozen audit contract.")
    coordinates = umap.UMAP(n_neighbors=30, min_dist=0.34, metric="cosine", random_state=31).fit_transform(embeddings)
    plotted = predictions[["cell_id", "fine_label", "fine_confidence"]].copy()
    plotted["UMAP1"] = coordinates[:, 0]
    plotted["UMAP2"] = coordinates[:, 1]

    fig = plt.figure(figsize=(7.25, 5.58))
    grid = fig.add_gridspec(
        2,
        12,
        height_ratios=(1.03, 0.97),
        left=0.055,
        right=0.988,
        bottom=0.075,
        top=0.95,
        hspace=0.70,
        wspace=0.64,
    )
    ax_a = fig.add_subplot(grid[:, :6])
    ax_b = fig.add_subplot(grid[0, 6:])
    ax_c = fig.add_subplot(grid[1, 6:10])
    ax_d = fig.add_subplot(grid[1, 10:])

    display_order = states.sort_values("cells", ascending=False).fine_label.tolist()
    for label in reversed(display_order):
        subset = plotted.loc[plotted.fine_label.eq(label)]
        ax_a.scatter(subset.UMAP1, subset.UMAP2, s=2.25, linewidth=0, alpha=0.77, color=base.ROOT_STATE.get(label, GREY), rasterized=True)
    ax_a.set(xticks=[], yticks=[])
    for spine in ax_a.spines.values():
        spine.set_visible(False)
    panel(ax_a, "a", "A frozen model partitions a label-free external root matrix into 13 predicted states", "GSE152766 / GSM4626007; 6,566 cells; colours are model outputs, never supplied labels")
    legend_positions = [(index % 3, index // 3) for index in range(len(display_order))]
    for label, (column, row) in zip(display_order, legend_positions, strict=True):
        x, y = 0.02 + column * 0.32, 0.025 + row * 0.047
        ax_a.scatter([x], [y], transform=ax_a.transAxes, s=11, color=base.ROOT_STATE.get(label, GREY), clip_on=False)
        ax_a.text(x + 0.024, y, label, transform=ax_a.transAxes, va="center", fontsize=4.45, color=INK)
    ax_a.text(0.995, -0.055, "Embedding coordinates are from the frozen 256-dimensional cell representation.", transform=ax_a.transAxes, ha="right", fontsize=4.8, color=MUTED)

    display = states.sort_values("cells", ascending=True).reset_index(drop=True)
    y = np.arange(len(display))
    ax_b.barh(y, display.fraction, color=[base.ROOT_STATE.get(label, GREY) for label in display.fine_label], height=0.57, edgecolor="white", linewidth=0.42)
    ax_b.scatter(display.mean_confidence, y, s=np.clip(display.cells.to_numpy() / 14, 12, 62), color=INK, edgecolor="white", linewidth=0.45, zorder=3)
    for index, row in display.iterrows():
        ax_b.text(max(float(row.fraction), float(row.mean_confidence)) + 0.014, index, f"{int(row.cells):,}", va="center", fontsize=4.85, color=INK)
    ax_b.set(yticks=y, yticklabels=display.fine_label.tolist(), xlim=(0, 1.16), xlabel="bar: predicted fraction | dot: mean confidence")
    ax_b.tick_params(axis="y", labelsize=4.85, pad=1.15, length=0)
    clean(ax_b, "x")
    panel(ax_b, "b", "Every output state and confidence remains inspectable", "Counts are predictions, not a hidden external ground truth")

    marker = markers.sort_values("mean_expression_delta", ascending=True).reset_index(drop=True)
    marker_y = np.arange(len(marker))
    ax_c.axvline(0, color=GRID, lw=0.7)
    ax_c.hlines(marker_y, 0, marker.mean_expression_delta, color=LIGHT_GREY, lw=2.5, zorder=1)
    ax_c.scatter(
        marker.mean_expression_delta,
        marker_y,
        s=34 + marker.target_detection_fraction.to_numpy() * 46,
        color=[base.ROOT_STATE.get(label, TEAL) for label in marker.expected_label],
        edgecolor="white",
        linewidth=0.58,
        zorder=3,
    )
    for index, row in marker.iterrows():
        rank = int(row.rank_among_predicted_labels_by_mean_expression)
        ax_c.text(float(row.mean_expression_delta) + 0.02, index, f"rank {rank}/13", va="center", fontsize=4.75, color=INK if rank == 1 else MUTED)
    ax_c.set(
        yticks=marker_y,
        yticklabels=[f"{row.marker_symbol} | {row.expected_label}" for row in marker.itertuples(index=False)],
        xlim=(-0.04, max(1.22, float(marker.mean_expression_delta.max()) + 0.48)),
        xlabel="expected group minus other groups (mean log1p expression)",
    )
    ax_c.tick_params(axis="y", labelsize=4.75, pad=1.45, length=0)
    clean(ax_c, "x")
    panel(ax_c, "c", "Fixed markers support five expected groups", "Biological coherence, not an external accuracy estimate")

    ax_d.set_axis_off()
    panel(ax_d, "d", "Scope", "Useful biology, bounded claim", title_x=0.12)
    boundary_rows = [
        ("input", "label-free root matrix", BLUE),
        ("model", "frozen checkpoint", TEAL),
        ("anchor plan", "six loci fixed before scoring", ORANGE),
        ("not claimed", "accuracy or wet-lab validation", RED),
    ]
    for index, (label, detail, color) in enumerate(boundary_rows):
        y0 = 0.78 - index * 0.20
        ax_d.plot([0.03, 0.10], [y0, y0], transform=ax_d.transAxes, color=color, lw=2.8, solid_capstyle="round")
        ax_d.text(0.15, y0 + 0.018, label, transform=ax_d.transAxes, fontsize=4.9, color=MUTED, va="center")
        ax_d.text(0.15, y0 - 0.055, detail, transform=ax_d.transAxes, fontsize=4.8, color=INK, va="center", fontweight="bold" if label == "not claimed" else "normal")

    export(
        fig,
        "plant_cellfm_v6_fig4_external_root_evidence",
        {
            "external_embedding_umap": plotted,
            "external_prediction_distribution": states,
            "external_marker_coherence": markers,
            "external_root_evidence_boundary": pd.DataFrame(boundary_rows, columns=["scope_field", "value", "colour_role"]),
        },
    )


def render_fig5_wheat_adapter() -> None:
    """Render the provenance-controlled wheat adaptation stress test."""
    audit = json.loads((ROOT / "release_metadata" / "gse270342_wheat_lora_adapter_audit_v1.json").read_text(encoding="utf-8"))
    frozen_audit = json.loads((ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_frozen_diagnostic_v1.json").read_text(encoding="utf-8"))
    input_record = json.loads((ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_input_preparation_v1.json").read_text(encoding="utf-8"))
    train_root = ROOT / "outputs" / "gse270342_wheat_root_lora_adapter_4070"
    matched = pd.read_csv(train_root / "audit" / "matched_direct_root_locked_test.tsv", sep="\t", dtype=str)
    per_class = pd.read_csv(train_root / "audit" / "locked_test_per_class.tsv", sep="\t")
    confusion = pd.read_csv(train_root / "detailed_test" / "fine_confusion_matrix.tsv", sep="\t")
    history = pd.DataFrame(json.loads((train_root / "history.json").read_text(encoding="utf-8"))["epochs"])
    if len(matched) != 964 or len(per_class) != 13 or len(confusion) != 13:
        raise ValueError("The wheat adaptation artifacts no longer match their frozen figure contract.")

    first_bootstrap = direct_root_bootstrap(matched, "frozen_fine_label", seed=20260811).assign(method="Frozen first projection")
    adapted_bootstrap = direct_root_bootstrap(matched, "adapted_root_label", seed=20260812).assign(method="Wheat LoRA adapter")
    bootstrap = pd.concat([first_bootstrap, adapted_bootstrap], ignore_index=True)
    intervals = bootstrap.groupby("method", as_index=False).agg(
        accuracy_low=("accuracy", lambda value: float(np.quantile(value, 0.025))),
        accuracy_high=("accuracy", lambda value: float(np.quantile(value, 0.975))),
        macro_f1_low=("macro_f1", lambda value: float(np.quantile(value, 0.025))),
        macro_f1_high=("macro_f1", lambda value: float(np.quantile(value, 0.975))),
    )
    comparison = pd.DataFrame(
        [
            {"method": "Frozen first projection", "accuracy": audit["matched_direct_root_subset"]["frozen_first_projection_accuracy"], "macro_f1": audit["matched_direct_root_subset"]["frozen_first_projection_macro_f1"]},
            {"method": "Wheat LoRA adapter", "accuracy": audit["matched_direct_root_subset"]["adapted_lora_accuracy"], "macro_f1": audit["matched_direct_root_subset"]["adapted_lora_macro_f1"]},
        ]
    ).merge(intervals, on="method", how="left", validate="one_to_one")
    labels = confusion.true_label.tolist()
    matrix = confusion.drop(columns="true_label").to_numpy(dtype=float)
    normalised = np.divide(matrix, matrix.sum(axis=1, keepdims=True), out=np.zeros_like(matrix), where=matrix.sum(axis=1, keepdims=True) > 0)
    per_class = per_class.sort_values("f1-score", ascending=True, kind="mergesort").reset_index(drop=True)
    modes = pd.DataFrame(
        [
            {"projection": item["mode"], "direct_accuracy": item["direct_anatomical_map"]["accuracy"], "direct_macro_f1": item["direct_anatomical_map"]["macro_f1_declared_targets"]}
            for item in frozen_audit["modes"]
        ]
    )
    best = history.loc[history.fine_macro_f1.idxmax()]
    coverage = input_record["mapping_coverage"]

    fig = plt.figure(figsize=(7.25, 6.55))
    grid = fig.add_gridspec(
        3,
        10,
        height_ratios=(0.79, 1.40, 0.93),
        left=0.055,
        right=0.988,
        bottom=0.06,
        top=0.957,
        hspace=0.70,
        wspace=0.67,
    )
    ax_a = fig.add_subplot(grid[0, :4])
    ax_b = fig.add_subplot(grid[0, 4:7])
    ax_c = fig.add_subplot(grid[0, 7:])
    ax_d = fig.add_subplot(grid[1, :5])
    ax_e = fig.add_subplot(grid[1, 5:])
    ax_f = fig.add_subplot(grid[2, :5])
    ax_g = fig.add_subplot(grid[2, 5:])

    ax_a.set_axis_off()
    panel(ax_a, "a", "Wheat stress-test provenance", "224 historical strict-set barcodes removed before splitting")
    stages = [
        (0.02, "author object", "7,388", GREY),
        (0.28, "overlap removed", "224", RED),
        (0.54, "diagnostic set", "7,164", BLUE),
        (0.80, "locked test", "1,433", TEAL),
    ]
    for x, title, value, color in stages:
        ax_a.add_patch(Rectangle((x, 0.42), 0.18, 0.30, transform=ax_a.transAxes, facecolor="#F5F7F8", edgecolor=color, linewidth=0.9))
        ax_a.add_patch(Rectangle((x, 0.67), 0.18, 0.05, transform=ax_a.transAxes, facecolor=color, edgecolor="none"))
        ax_a.text(x + 0.09, 0.56, title, transform=ax_a.transAxes, ha="center", va="center", fontsize=4.72, color=INK, fontweight="bold")
        ax_a.text(x + 0.09, 0.46, value, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.7, color=INK)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((left[0] + 0.188, 0.57), (right[0] - 0.008, 0.57), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=7, lw=0.7, color=MUTED))
    split = [("train", int(audit["split"]["train_cells"]), ORANGE), ("validation", int(audit["split"]["validation_cells"]), PURPLE), ("locked test", int(audit["split"]["test_cells"]), TEAL)]
    total = sum(value for _, value, _ in split)
    cursor = 0.02
    for label, value, color in split:
        width = 0.96 * value / total
        ax_a.add_patch(Rectangle((cursor, 0.17), width, 0.10, transform=ax_a.transAxes, facecolor=color, edgecolor="white", linewidth=0.55))
        caption = {"train": "train", "validation": "val.", "locked test": "test"}[label]
        ax_a.text(cursor + width / 2, 0.08, f"{caption} {value:,}", transform=ax_a.transAxes, ha="center", fontsize=4.55, color=INK)
        cursor += width

    ax_b.set_axis_off()
    panel(ax_b, "b", "Mapping retention", "Deterministic first-target map is disclosed")
    rows = [("compatible features", coverage["checkpoint_compatible_gene_fraction"], "53.75%", BLUE), ("compatible UMI", coverage["checkpoint_compatible_umi_fraction"], "76.33%", TEAL)]
    for index, (label, value, headline, color) in enumerate(rows):
        y0 = 0.62 - index * 0.27
        ax_b.text(0.02, y0 + 0.10, label, transform=ax_b.transAxes, fontsize=4.8, color=MUTED)
        ax_b.add_patch(Rectangle((0.02, y0), 0.62, 0.10, transform=ax_b.transAxes, facecolor=LIGHT_GREY, edgecolor="none"))
        ax_b.add_patch(Rectangle((0.02, y0), 0.62 * value, 0.10, transform=ax_b.transAxes, facecolor=color, edgecolor="none"))
        ax_b.text(0.69, y0 + 0.045, headline, transform=ax_b.transAxes, fontsize=5.75, color=INK, fontweight="bold", va="center")
    ax_b.text(0.02, 0.055, "First projection sensitivity is retained in source data.", transform=ax_b.transAxes, fontsize=4.5, color=RED)

    y = np.arange(len(comparison))
    colors = [GREY, PURPLE]
    ax_c.hlines(y, comparison.accuracy_low, comparison.accuracy_high, color=colors, lw=3.2, zorder=1)
    ax_c.scatter(comparison.accuracy, y, s=70, color=colors, edgecolor="white", linewidth=0.75, zorder=3)
    for index, row in comparison.iterrows():
        ax_c.text(float(row.accuracy) + 0.03, index + 0.06, f"{row.accuracy:.3f}", fontsize=5.55, color=INK, fontweight="bold")
        ax_c.text(0.01, index - 0.21, f"macro-F1 {row.macro_f1:.3f}", fontsize=4.45, color=MUTED)
    ax_c.set(yticks=y, yticklabels=["frozen", "wheat LoRA"], xlim=(-0.04, 0.82), xlabel="matched direct-root accuracy")
    ax_c.tick_params(axis="y", labelsize=4.75, length=0)
    clean(ax_c, "x")
    panel(ax_c, "c", "Adaptation recovery", "964 fixed cells; target labels are permitted")

    image = ax_d.imshow(normalised, cmap=LinearSegmentedColormap.from_list("wheat_v6", ["#F5F8F8", "#B9DFDC", TEAL]), vmin=0, vmax=1, aspect="auto")
    ax_d.set(xticks=range(len(labels)), xticklabels=[compact_author_label(value) for value in labels], yticks=range(len(labels)), yticklabels=[compact_author_label(value) for value in labels], xlabel="predicted author state")
    ax_d.tick_params(axis="x", labelsize=4.55, rotation=35, length=0, pad=1.2)
    ax_d.tick_params(axis="y", labelsize=4.55, length=0, pad=1.1)
    for tick in ax_d.get_xticklabels():
        tick.set_horizontalalignment("right")
    for spine in ax_d.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_d, fraction=0.032, pad=0.018)
    colorbar.ax.tick_params(labelsize=4.4, length=1.0)
    panel(ax_d, "d", "The 13-class locked test preserves each author state", "Row-normalized confusion; 1,433 cells; source data contains full numeric values")

    yy = np.arange(len(per_class))
    point_colors = [TEAL if value >= 0.65 else ORANGE for value in per_class["f1-score"]]
    ax_e.hlines(yy, 0, per_class["f1-score"], color=LIGHT_GREY, lw=2.4, zorder=1)
    ax_e.scatter(per_class["f1-score"], yy, s=20 + per_class.support.to_numpy() / 11, color=point_colors, edgecolor="white", linewidth=0.48, zorder=3)
    for index, row in per_class.iterrows():
        ax_e.text(min(float(row["f1-score"]) + 0.035, 1.01), index, f"{row['f1-score']:.2f}", va="center", fontsize=4.55, color=INK)
    ax_e.set(yticks=yy, yticklabels=[compact_author_label(value) for value in per_class.author_label], xlim=(0, 1.10), xlabel="locked-test per-class F1")
    ax_e.tick_params(axis="y", labelsize=4.65, length=0, pad=1.0)
    clean(ax_e, "x")
    panel(ax_e, "e", "Rare and mixed root states remain visible", "Point area reports class support; no author class is omitted")

    ax_f.plot(history.epoch, history.fine_macro_f1, color=PURPLE, marker="o", markersize=4.0, markeredgecolor="white", markeredgewidth=0.5, lw=1.2, label="validation macro-F1")
    ax_f.plot(history.epoch, history.fine_accuracy, color=TEAL, marker="o", markersize=3.8, markeredgecolor="white", markeredgewidth=0.5, lw=1.05, label="validation accuracy")
    ax_f.axvline(best.epoch, color=ORANGE, lw=0.85, ls="--")
    ax_f.annotate(f"selected epoch {int(best.epoch)}", xy=(best.epoch, best.fine_macro_f1), xytext=(best.epoch - 3.6, 0.45), arrowprops={"arrowstyle": "-|>", "lw": 0.6, "color": ORANGE}, fontsize=4.65, color=INK)
    ax_f.set(xticks=history.epoch.tolist(), ylim=(0.16, 0.78), xlabel="training epoch", ylabel="validation score")
    ax_f.legend(loc="lower right", fontsize=4.6, frameon=False, handlelength=1.65)
    clean(ax_f, "y")
    panel(ax_f, "f", "Selection precedes the locked test", "Selected at epoch 8; held-out accuracy 62.25%; macro-F1 0.6660")

    ax_g.set_axis_off()
    panel(ax_g, "g", "Interpretation guardrail", "This panel does not substitute an independent species-validation experiment")
    safeguards = [
        ("input", "wheat author-labelled study", BLUE),
        ("split", "same-study cell-level", ORANGE),
        ("adapter", "target-supervised LoRA", PURPLE),
        ("claim", "adaptation, not zero-shot", RED),
    ]
    for index, (label, value, color) in enumerate(safeguards):
        y0 = 0.76 - index * 0.20
        ax_g.plot([0.03, 0.105], [y0, y0], transform=ax_g.transAxes, color=color, lw=2.8, solid_capstyle="round")
        ax_g.text(0.15, y0 + 0.012, label, transform=ax_g.transAxes, fontsize=4.65, color=MUTED)
        ax_g.text(0.15, y0 - 0.065, value, transform=ax_g.transAxes, fontsize=4.75, color=INK, fontweight="bold" if label == "claim" else "normal")

    fig.text(0.988, 0.012, "One public study with supervised adaptation: report the gain as a conditional module, not a universal transfer result.", ha="right", fontsize=4.8, color=RED, fontweight="bold")
    split_table = pd.DataFrame([{"set": label, "cells": cells} for label, cells, _ in split])
    mapping_table = pd.DataFrame(
        [
            {"quantity": "checkpoint_compatible_feature_fraction", "value": coverage["checkpoint_compatible_gene_fraction"]},
            {"quantity": "checkpoint_compatible_umi_fraction", "value": coverage["checkpoint_compatible_umi_fraction"]},
            {"quantity": "excluded_historical_barcode_overlap", "value": input_record["overlap_audit"]["exact_cs1_barcode_overlap_excluded"]},
        ]
    )
    export(
        fig,
        "plant_cellfm_v6_fig5_wheat_adapter",
        {
            "provenance_split": split_table,
            "mapping_contract": mapping_table,
            "frozen_projection_sensitivity": modes,
            "matched_direct_root_test_cells": matched,
            "matched_direct_root_bootstrap": bootstrap,
            "matched_direct_root_summary": comparison,
            "locked_test_confusion": confusion,
            "locked_test_per_class": per_class,
            "validation_history": history,
            "interpretation_guardrail": pd.DataFrame(safeguards, columns=["scope_field", "value", "colour_role"]),
        },
    )


def main() -> None:
    setup()
    frame, v17, _ = base.load_cells()
    render_fig1(frame)
    render_fig2(frame, v17)
    render_fig3()
    render_fig4_external_root()
    render_fig5_wheat_adapter()
    normalise_svg_whitespace()
    print(json.dumps({"figure_suite": "v6_editorial_core", "main_figures": 5}, ensure_ascii=False))


if __name__ == "__main__":
    main()
