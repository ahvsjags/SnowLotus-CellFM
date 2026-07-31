from __future__ import annotations

"""Render the evidence-led v4 Plant-CellFM figure suite.

This renderer deliberately gives most of each canvas to cell-level data.  It
does not synthesize image panels or fill missing comparator results.  All
statistical marks are exported as tidy source-data tables beside the figures.
"""

import json
import sys
from collections import Counter
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


ROOT = Path(__file__).resolve().parents[1]
EMBEDDING = ROOT / "figure_data" / "v2_embeddings"
PROFILE = ROOT / "figure_data" / "corpus_profile_v1"
V3_SOURCE = ROOT / "figures" / "plant_cellfm_submission_v3" / "source_data"
OUT = ROOT / "figures" / "plant_cellfm_submission_v4"
MAIN = OUT / "main"
EXTENDED = OUT / "extended_data"
SOURCE = OUT / "source_data"

sys.path.insert(0, str(ROOT / "scripts"))
import run_revision_v14_context_stc_benchmark as v14  # noqa: E402
from run_species_ontology_label_benchmark_v9 import (  # noqa: E402
    UNKNOWN_ONTOLOGY,
    canonical_ontology,
)


INK = "#18242E"
MUTED = "#657987"
GRID = "#D8E2E7"
TEAL = "#007C83"
TEAL_PALE = "#B7E0DD"
BLUE = "#2E6FAD"
BLUE_PALE = "#BBD5EB"
ORANGE = "#D97524"
ORANGE_PALE = "#F2C29D"
PURPLE = "#8064A7"
RED = "#B34D5B"
GREY = "#9CAAB2"
LIGHT_GREY = "#E9EFF1"
SPECIES = {
    "Arabidopsis thaliana": "#0072B2",
    "Brassica rapa": "#56B4E9",
    "Catharanthus roseus": "#E69F00",
    "Eutrema salsugineum": "#009E73",
    "Fragaria vesca": "#CC79A7",
    "Gossypium bickii": "#D55E00",
    "Gossypium hirsutum": "#8C6D31",
    "Triticum aestivum": "#7A9E2F",
}
ONTOLOGY = {
    "mesophyll": "#0B7D8A",
    "epidermis": "#D67929",
    "vascular_stele": "#2D70AE",
    "xylem": "#5A95C8",
    "phloem": "#6A5BA5",
    "root_cap": "#CD8B31",
    "cortex": "#51A7A4",
    "endodermis": "#2C8F95",
    "meristem_or_stem_cell_niche": "#9E6DB3",
    "cell_cycle_state": "#7D8790",
    UNKNOWN_ONTOLOGY: "#D5DDE0",
}


def setup() -> None:
    mpl.rcParams.update(
        {
            "font.family": "Arial",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 6.5,
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
    for directory in (MAIN, EXTENDED, SOURCE):
        directory.mkdir(parents=True, exist_ok=True)


def clean(ax: plt.Axes, grid: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.55, zorder=0)
    ax.tick_params(length=2.4, pad=2)


def panel(ax: plt.Axes, letter: str, title: str, subtitle: str | None = None) -> None:
    ax.text(-0.13, 1.055, letter, transform=ax.transAxes, fontsize=9.1, fontweight="bold", va="top")
    ax.set_title(title, loc="left", fontsize=7.05, fontweight="bold", pad=8)
    if subtitle:
        ax.text(0, 1.014, subtitle, transform=ax.transAxes, fontsize=5.15, color=MUTED, va="bottom")


def short_species(value: str) -> str:
    parts = str(value).split()
    return f"{parts[0][0]}. {parts[1]}" if len(parts) == 2 else str(value)


def export(fig: plt.Figure, directory: Path, stem: str, tables: dict[str, pd.DataFrame]) -> None:
    for name, frame in tables.items():
        frame.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for suffix, kwargs in (("svg", {}), ("pdf", {}), ("png", {"dpi": 350}), ("tiff", {"dpi": 600})):
        fig.savefig(directory / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.028, **kwargs)
    plt.close(fig)


def load_cells() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    obs = v14.read_csv(ROOT / "release_metadata" / "species_ontology_obs_labels_with_ids_v9.tsv", delimiter="\t")
    prediction_rows = v14.read_csv(EMBEDDING / "predictions.csv")
    aligned, indices = v14.align_obs(obs, prediction_rows)
    embeddings = np.load(EMBEDDING / "embeddings.npy").astype(np.float32)[indices]
    strict = pd.read_csv(EMBEDDING / "v17_nested_strict_predictions.csv").set_index("cell_id")
    frame = pd.DataFrame(
        {
            "cell_id": [row.get("cell_id", "") for row in aligned],
            "species": [v14.canonical_species(row.get("species", "")) for row in aligned],
            "tissue": [row.get("tissue", "") for row in aligned],
            "organ": [v14.organ_group(row.get("tissue", "")) for row in aligned],
            "truth_label": [v14.canonical_text(row.get("cell_type", "")) for row in aligned],
        }
    )
    frame["strict_prediction"] = [strict.loc[cell_id, "strict_prediction"] for cell_id in frame.cell_id]
    frame["covered_by_train_labels"] = [strict.loc[cell_id, "covered_by_train_labels"] for cell_id in frame.cell_id]
    frame["ontology"] = [canonical_ontology(label) for label in frame.truth_label]
    reducer = umap.UMAP(n_neighbors=30, min_dist=0.30, metric="cosine", random_state=17)
    coords = reducer.fit_transform(embeddings)
    frame["UMAP1"] = coords[:, 0]
    frame["UMAP2"] = coords[:, 1]
    v17_payload = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))
    v18_payload = json.loads((ROOT / "release_metadata" / "revision_v18_identity_curated_strict.json").read_text(encoding="utf-8"))
    return frame, pd.DataFrame(v17_payload["outer_species_records"]), pd.DataFrame(v18_payload["outer_species_records"])


def scatter_by_category(
    ax: plt.Axes,
    frame: pd.DataFrame,
    column: str,
    palette: dict[str, str],
    *,
    title: str,
    subtitle: str | None = None,
    max_categories: int | None = None,
    point_size: float = 3.5,
    alpha: float = 0.76,
) -> pd.DataFrame:
    counts = frame[column].value_counts()
    categories = counts.index.tolist() if max_categories is None else counts.head(max_categories).index.tolist()
    if max_categories is not None and len(counts) > max_categories:
        plotted = frame[column].where(frame[column].isin(categories), "other")
        local_palette = {**palette, "other": "#CCD6DA"}
    else:
        plotted = frame[column]
        local_palette = palette
    for category in sorted(set(plotted.tolist()), key=lambda item: str(item)):
        subset = frame.loc[plotted.eq(category)]
        ax.scatter(
            subset.UMAP1,
            subset.UMAP2,
            s=point_size,
            color=local_palette.get(str(category), GREY),
            alpha=alpha,
            linewidth=0,
            label=str(category).replace("_", " "),
            rasterized=True,
        )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    panel(ax, "", title, subtitle)
    ax.text(-0.10, 1.055, "", transform=ax.transAxes)
    return pd.DataFrame({column: plotted, "cells": 1}).groupby(column, as_index=False).cells.sum()


def label_panel(ax: plt.Axes, letter: str, title: str, subtitle: str | None = None) -> None:
    panel(ax, letter, title, subtitle)


def render_fig1(frame: pd.DataFrame) -> None:
    profile = json.loads((PROFILE / "corpus_profile.json").read_text(encoding="utf-8"))
    species_tissue = pd.read_csv(PROFILE / "species_by_tissue.tsv", sep="\t")
    fig = plt.figure(figsize=(7.25, 5.55))
    grid = fig.add_gridspec(
        2, 4, width_ratios=(1.22, 1.22, 0.92, 0.92), height_ratios=(1.16, 0.84),
        left=0.06, right=0.987, bottom=0.08, top=0.95, wspace=0.34, hspace=0.42,
    )
    ax_a = fig.add_subplot(grid[:, :2])
    ax_b = fig.add_subplot(grid[0, 2:])
    ax_c = fig.add_subplot(grid[1, 2])
    ax_d = fig.add_subplot(grid[1, 3])

    for species in sorted(frame.species.unique()):
        subset = frame[frame.species.eq(species)]
        ax_a.scatter(subset.UMAP1, subset.UMAP2, s=3.9, color=SPECIES.get(species, GREY), alpha=.73, linewidth=0, label=short_species(species), rasterized=True)
    ax_a.set_xticks([]); ax_a.set_yticks([])
    for spine in ax_a.spines.values():
        spine.set_visible(False)
    label_panel(ax_a, "a", "A shared plant-cell representation\nspans eight evaluation species")
    ax_a.legend(loc="lower left", bbox_to_anchor=(-.02, -.12), ncol=4, fontsize=4.8, frameon=False, columnspacing=.55, handletextpad=.22, markerscale=1.45)

    top_ontology = frame.ontology.value_counts().head(9).index.tolist()
    ontology_view = frame.copy()
    ontology_view["display_ontology"] = ontology_view.ontology.where(ontology_view.ontology.isin(top_ontology), "other")
    ontology_palette = {**ONTOLOGY, "other": "#CBD5D8"}
    for category in top_ontology + (["other"] if (ontology_view.display_ontology == "other").any() else []):
        subset = ontology_view[ontology_view.display_ontology.eq(category)]
        ax_b.scatter(subset.UMAP1, subset.UMAP2, s=3.6, color=ontology_palette.get(category, GREY), alpha=.76, linewidth=0, label=category.replace("_", " "), rasterized=True)
    ax_b.set_xticks([]); ax_b.set_yticks([])
    for spine in ax_b.spines.values():
        spine.set_visible(False)
    label_panel(ax_b, "b", "Cell-state topology is visible\nacross the same coordinates")
    ax_b.legend(loc="lower left", bbox_to_anchor=(-.03, -.22), ncol=3, fontsize=4.4, frameon=False, columnspacing=.52, handletextpad=.20, labelspacing=.18, markerscale=1.35)

    organ_order = ["leaf", "root", "shoot_apex", "callus"]
    organ_counts = frame.organ.value_counts().reindex(organ_order).fillna(0).astype(int)
    left = 0
    organ_colors = {"leaf": TEAL, "root": BLUE, "shoot_apex": ORANGE, "callus": PURPLE}
    for organ, value in organ_counts.items():
        ax_c.barh([0], [value], left=left, height=.42, color=organ_colors[organ], edgecolor="white", linewidth=.5)
        if value >= 150:
            ax_c.text(left + value / 2, 0, f"{organ.replace('_', ' ')}\n{value:,}", ha="center", va="center", fontsize=4.65, color="white" if organ != "shoot_apex" else INK)
        left += value
    ax_c.set(xlim=(0, int(organ_counts.sum())), ylim=(-.55, .68), yticks=[], xlabel="evaluation cells")
    clean(ax_c, None)
    label_panel(ax_c, "c", "Input organs are explicitly\nrepresented")

    ordered = species_tissue.groupby("species").cells.sum().sort_values(ascending=False)
    y = np.arange(len(ordered))
    ax_d.barh(y, ordered.values / 1000, color=[SPECIES.get(s, GREY) for s in ordered.index], edgecolor="white", linewidth=.45)
    ax_d.set_yticks(y, [short_species(s) for s in ordered.index], fontsize=4.85)
    ax_d.invert_yaxis()
    ax_d.set_xlabel("training-corpus cells (thousands)")
    clean(ax_d, "x")
    label_panel(
        ax_d,
        "d",
        "The traceable corpus exceeds\nthe strict panel",
        f"{profile['shape']['cells']:,} cells; {profile['shape']['genes']:,} genes",
    )

    export(
        fig,
        MAIN,
        "plant_cellfm_v4_fig1_cross_species_atlas",
        {
            "cell_embedding": frame[["cell_id", "species", "organ", "truth_label", "ontology", "UMAP1", "UMAP2"]],
            "organ_counts": organ_counts.rename_axis("organ").reset_index(name="cells"),
            "training_species_counts": ordered.rename_axis("species").reset_index(name="cells"),
        },
    )


def bootstrap(frame: pd.DataFrame, *, iterations: int = 3000) -> pd.DataFrame:
    rng = np.random.default_rng(2207)
    truth = frame.truth_label.to_numpy()
    pred = frame.strict_prediction.to_numpy()
    rows = []
    for index in range(iterations):
        sampled = rng.integers(0, len(frame), len(frame))
        rows.append({"bootstrap": index, "all_cell_accuracy": float((truth[sampled] == pred[sampled]).mean())})
    return pd.DataFrame(rows)


def render_fig2(frame: pd.DataFrame, v17: pd.DataFrame, v18: pd.DataFrame) -> None:
    focus = frame[frame.species.eq("Catharanthus roseus")].copy()
    label_order = focus.truth_label.value_counts().index.tolist()
    focus_palette = {label: color for label, color in zip(label_order, [TEAL, ORANGE, PURPLE, BLUE, RED, "#7A9E2F", GREY], strict=False)}
    fig = plt.figure(figsize=(7.25, 6.15))
    grid = fig.add_gridspec(
        3, 4, width_ratios=(1.05, 1.05, 1.15, .95), height_ratios=(.96, .22, 1.13),
        left=.06, right=.987, bottom=.075, top=.955, wspace=.38, hspace=.44,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    ax_c = fig.add_subplot(grid[:2, 2:])
    ax_d = fig.add_subplot(grid[2, :3])
    ax_e = fig.add_subplot(grid[2, 3])

    for label in label_order:
        subset = focus[focus.truth_label.eq(label)]
        ax_a.scatter(subset.UMAP1, subset.UMAP2, s=8.0, color=focus_palette[label], alpha=.80, linewidth=0, label=label, rasterized=True)
    ax_a.set_xticks([]); ax_a.set_yticks([])
    for spine in ax_a.spines.values(): spine.set_visible(False)
    label_panel(ax_a, "a", "Held-out C. roseus", "Reference labels; 256 leaf cells")
    ax_a.legend(loc="lower left", bbox_to_anchor=(-.08, -.28), fontsize=3.85, frameon=False, handletextpad=.18, labelspacing=.16, markerscale=1.05)

    for label in label_order:
        subset = focus[focus.strict_prediction.eq(label)]
        if len(subset):
            ax_b.scatter(subset.UMAP1, subset.UMAP2, s=8.0, color=focus_palette[label], alpha=.80, linewidth=0, rasterized=True)
    unknown_prediction = focus[~focus.strict_prediction.isin(label_order)]
    if len(unknown_prediction):
        ax_b.scatter(unknown_prediction.UMAP1, unknown_prediction.UMAP2, s=8.0, color=GREY, alpha=.8, linewidth=0, rasterized=True)
    ax_b.set_xticks([]); ax_b.set_yticks([])
    for spine in ax_b.spines.values(): spine.set_visible(False)
    label_panel(ax_b, "b", "Nested zero-shot decoding", "Target labels are never used in fitting or selection")
    ax_b.text(.98, .02, f"all-cell accuracy\n{(focus.truth_label == focus.strict_prediction).mean():.1%}", transform=ax_b.transAxes, ha="right", va="bottom", fontsize=5.1, color=INK, fontweight="bold")

    ax_c.set_axis_off()
    label_panel(ax_c, "c", "A strict protocol separates model\ntransfer from label availability")
    steps = [
        (.06, "source species", "labels + embeddings", BLUE),
        (.34, "nested selection", "source-species folds", TEAL),
        (.64, "held-out species", "labels locked", RED),
        (.90, "score once", "all cells retained", ORANGE),
    ]
    for x, head, sub, color in steps:
        ax_c.scatter([x] * 6, [.73, .68, .63, .58, .53, .48], s=20, color=color, alpha=.9, transform=ax_c.transAxes, clip_on=False)
        ax_c.text(x, .34, head, transform=ax_c.transAxes, ha="center", va="center", fontsize=5.9, fontweight="bold", color=INK)
        ax_c.text(x, .20, sub, transform=ax_c.transAxes, ha="center", va="center", fontsize=4.8, color=MUTED)
    for (x0, *_), (x1, *_) in zip(steps[:-1], steps[1:], strict=True):
        ax_c.add_patch(FancyArrowPatch((x0+.075,.61), (x1-.075,.61), transform=ax_c.transAxes, arrowstyle="-|>", mutation_scale=7, lw=.75, color=MUTED))
    ax_c.text(.50, .89, "No target cell label enters the decoder, gate choice or calibration.", transform=ax_c.transAxes, ha="center", fontsize=5.25, color=RED, fontweight="bold")

    boot = bootstrap(frame)
    boot_low, boot_high = boot.all_cell_accuracy.quantile([.025, .975]).tolist()
    records = v17.sort_values("accuracy_all").reset_index(drop=True)
    y = np.arange(len(records))
    ax_d.hlines(y, records.accuracy_all, records.accuracy, color="#D9E3E6", lw=2.1, zorder=1)
    ax_d.scatter(records.accuracy_all, y, color=TEAL, s=30, zorder=3, label="all cells")
    ax_d.scatter(records.accuracy, y, color=BLUE, s=30, zorder=3, label="known labels")
    ax_d.scatter(records.coverage, y, color=ORANGE, marker="s", s=29, zorder=3, label="label coverage")
    ax_d.set_yticks(y, [short_species(s) for s in records.held_out_species], fontsize=5.25)
    ax_d.set(xlim=(-.02, 1.05), xlabel="accuracy or available-label coverage")
    ax_d.legend(loc="lower right", ncol=3, fontsize=4.7, frameon=False, handletextpad=.25, columnspacing=.65)
    clean(ax_d, "x")
    label_panel(ax_d, "d", "All eight held-out species remain visible in the primary stress test", f"Teal: all-cell accuracy; blue: conditional accuracy; orange: coverage | fixed-cell bootstrap 95% central interval {boot_low:.3f}-{boot_high:.3f}")

    v18_payload = json.loads((ROOT / "release_metadata" / "revision_v18_identity_curated_strict.json").read_text(encoding="utf-8"))
    audit = v18_payload["label_integrity_audit"]
    cascade = [audit["input_cells"], audit["identity_curated_cells"], v18_payload["summary"]["n_evaluable"]]
    cascade_labels = ["public\nlabels", "explicit\nidentities", "shared\nidentities"]
    cascade_colors = [GREY, TEAL, BLUE]
    for x, (value, label, color) in enumerate(zip(cascade, cascade_labels, cascade_colors, strict=True)):
        ax_e.bar(x, value, width=.58, color=color, edgecolor="white", linewidth=.5)
        ax_e.text(x, value + 75, f"{value:,}", ha="center", fontsize=5.4, fontweight="bold")
        ax_e.text(x, -250, label, ha="center", va="top", fontsize=4.7)
    ax_e.set(xticks=[], yticks=[], ylim=(0, 4300))
    for spine in ax_e.spines.values(): spine.set_visible(False)
    label_panel(ax_e, "e", "Label-integrity audit", "v18 is a companion cohort, not a substituted headline")

    export(
        fig,
        MAIN,
        "plant_cellfm_v4_fig2_nested_strict_transfer",
        {
            "cell_predictions": frame[["cell_id", "species", "organ", "truth_label", "strict_prediction", "covered_by_train_labels", "UMAP1", "UMAP2"]],
            "v17_species_metrics": v17,
            "v18_identity_curated_metrics": v18,
            "all_cell_bootstrap": boot,
            "identity_integrity_cascade": pd.DataFrame({"stage": cascade_labels, "cells": cascade}),
        },
    )


def fewshot_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    payload = json.loads((ROOT / "release_metadata" / "revision_v11_fewshot_adapter_benchmark.json").read_text(encoding="utf-8"))
    all_draws: list[dict[str, Any]] = []
    species_draws: list[dict[str, Any]] = []
    for summary in payload["summaries"]:
        if summary["mode"] != "budgeted_random":
            continue
        for run in summary.get("raw_runs", []):
            all_draws.append(
                {
                    "support_per_species": int(run["support_value"]),
                    "seed": int(run["seed"]),
                    "query_cells": int(run["query_cells"]),
                    "support_cells": int(run["support_cells"]),
                    "accuracy_all_query": float(run["accuracy_all_query"]),
                    "macro_f1_query": float(run["macro_f1_query"]),
                }
            )
            for row in run["per_species"]:
                species_draws.append(
                    {
                        "support_per_species": int(run["support_value"]),
                        "seed": int(run["seed"]),
                        **row,
                    }
                )
    return pd.DataFrame(all_draws), pd.DataFrame(species_draws)


def render_fig3() -> None:
    draws, species_draws = fewshot_tables()
    budget_order = sorted(draws.support_per_species.unique().tolist())
    fig = plt.figure(figsize=(7.25, 5.70))
    grid = fig.add_gridspec(
        2, 4, width_ratios=(.78, 1.15, 1.15, .96), height_ratios=(1.12, .88),
        left=.06, right=.987, bottom=.09, top=.955, wspace=.42, hspace=.62,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, :2])
    ax_d = fig.add_subplot(grid[1, 2:])

    ax_a.set_axis_off()
    positions = [.14, .50, .86]
    nodes = [("new\nspecies", GREY), ("labeled\nsupport", ORANGE), ("held-out\nquery", TEAL)]
    for x, (label, color) in zip(positions, nodes, strict=True):
        ax_a.scatter([x] * 6, [.75, .69, .63, .57, .51, .45], s=20, color=color, transform=ax_a.transAxes, clip_on=False)
        ax_a.text(x, .23, label, ha="center", va="center", transform=ax_a.transAxes, fontsize=5.6, fontweight="bold")
    for x0, x1 in zip(positions[:-1], positions[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((x0+.10,.60), (x1-.10,.60), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=7, lw=.75, color=MUTED))
    ax_a.text(.50, .91, "Support and query cells never overlap", transform=ax_a.transAxes, ha="center", fontsize=5.0, color=RED, fontweight="bold")
    label_panel(ax_a, "a", "Target-species adaptation")

    rng = np.random.default_rng(24)
    for index, budget in enumerate(budget_order):
        values = draws.loc[draws.support_per_species.eq(budget), "accuracy_all_query"].to_numpy()
        jitter = rng.normal(index, .045, len(values))
        ax_b.scatter(jitter, values, s=18, color=TEAL_PALE, edgecolor="white", linewidth=.35, zorder=2)
        ax_b.errorbar(index, values.mean(), yerr=values.std(ddof=0), color=TEAL, marker="o", markersize=5.6, markeredgecolor="white", markeredgewidth=.7, capsize=2.3, lw=1.35, zorder=3)
        ax_b.text(index, values.mean()+.032, f"{values.mean():.3f}", ha="center", fontsize=5.35, fontweight="bold")
    ax_b.plot(range(len(budget_order)), [draws.loc[draws.support_per_species.eq(b), "accuracy_all_query"].mean() for b in budget_order], color=TEAL, lw=1.15, zorder=1)
    ax_b.set(xticks=range(len(budget_order)), xticklabels=budget_order, ylim=(.49, .80), xlabel="labeled support cells per target species", ylabel="query all-cell accuracy")
    ax_b.text(.99, .05, "10 random support draws at each budget\nerror bars: s.d.; dots: individual draws", transform=ax_b.transAxes, ha="right", va="bottom", fontsize=5.0, color=MUTED)
    clean(ax_b, "y")
    label_panel(ax_b, "b", "A small labeled set produces a stable,\ndose-responsive adaptation gain")

    macro = draws.groupby("support_per_species", as_index=False).agg(mean_macro_f1=("macro_f1_query", "mean"), sd_macro_f1=("macro_f1_query", "std"))
    ax_c.errorbar(macro.support_per_species, macro.mean_macro_f1, yerr=macro.sd_macro_f1.fillna(0), color=PURPLE, marker="o", markersize=5.2, markeredgecolor="white", markeredgewidth=.7, capsize=2.2, lw=1.25)
    ax_c.set(xticks=budget_order, ylim=(.16, .52), xlabel="support cells per target species", ylabel="query macro-F1")
    clean(ax_c, "y")
    label_panel(ax_c, "c", "Fine-label recovery follows the\nsame support-response pattern")

    mean_species = species_draws.groupby(["species", "support_per_species"], as_index=False).agg(accuracy_all_query=("accuracy_all_query", "mean"))
    species_order = sorted(mean_species.species.unique().tolist(), key=lambda value: short_species(value))
    matrix = mean_species.pivot(index="species", columns="support_per_species", values="accuracy_all_query").reindex(index=species_order, columns=budget_order)
    v18_audit = json.loads((ROOT / "release_metadata" / "revision_v18_identity_curated_strict.json").read_text(encoding="utf-8"))["label_integrity_audit"]
    audit_only_species = set(v18_audit["dropped_all_uninformative_species"])
    image = ax_d.imshow(matrix.to_numpy(), aspect="auto", cmap=LinearSegmentedColormap.from_list("adaptation", ["#F4F7F8", "#B7DEDA", TEAL]), vmin=.0, vmax=1.0)
    for yi, species in enumerate(matrix.index):
        for xi, budget in enumerate(matrix.columns):
            value = matrix.loc[species, budget]
            ax_d.text(xi, yi, f"{value:.2f}", ha="center", va="center", fontsize=4.5, color="white" if value >= .65 else INK)
    ax_d.set_xticks(range(len(budget_order)), budget_order)
    ax_d.set_yticks(
        range(len(matrix.index)),
        [f"{short_species(value)}*" if value in audit_only_species else short_species(value) for value in matrix.index],
        fontsize=4.9,
    )
    ax_d.tick_params(length=0)
    for spine in ax_d.spines.values(): spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_d, fraction=.045, pad=.025)
    colorbar.outline.set_visible(False); colorbar.ax.tick_params(labelsize=4.6, length=1.5)
    label_panel(ax_d, "d", "The adaptation response is heterogeneous\nbut measurable by species")
    fig.text(.987, .018, "* single-label public records; excluded from v18 explicit-identity evidence but retained here as the v11 protocol record.", ha="right", va="bottom", fontsize=4.55, color=MUTED)

    export(
        fig,
        MAIN,
        "plant_cellfm_v4_fig3_fewshot_target_adaptation",
        {"fewshot_draws": draws, "fewshot_species_draws": species_draws, "fewshot_species_budget_means": mean_species},
    )


def render_fig4_root_resource() -> None:
    markers = pd.read_csv(V3_SOURCE / "plant_cellfm_v3_fig5_arabidopsis_root_candidate_resource_root_marker_candidates.tsv", sep="\t")
    taxonomy = pd.read_csv(V3_SOURCE / "plant_cellfm_v3_fig5_arabidopsis_root_candidate_resource_root_identity_taxonomy.tsv", sep="\t")
    root_order = ["Columella root cap", "Lateral root cap", "Root cap", "Root hair", "Non-hair", "Root cortex", "Root endodermis", "Root stele", "Phloem", "Xylem"]
    markers = markers[markers.label.isin(root_order)].copy()
    markers["compartment"] = pd.Categorical(markers.compartment, ["root cap", "epidermis", "ground tissue", "vascular"], ordered=True)
    colors = {"root cap": ORANGE, "epidermis": PURPLE, "ground tissue": TEAL, "vascular": BLUE}
    fig = plt.figure(figsize=(7.25, 5.85))
    grid = fig.add_gridspec(2, 4, width_ratios=(.88, 1.17, 1.17, 1.04), height_ratios=(1.10, .90), left=.06, right=.987, bottom=.09, top=.955, wspace=.42, hspace=.67)
    ax_a = fig.add_subplot(grid[:, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, 1:3])
    ax_d = fig.add_subplot(grid[1, 3])

    ax_a.set_axis_off()
    y_positions = {label: index for index, label in enumerate(root_order[::-1])}
    display_taxonomy = {
        "Columella root cap": "Columella",
        "Lateral root cap": "Lateral cap",
        "Root cap": "Root cap",
        "Root hair": "Root hair",
        "Non-hair": "Non-hair",
        "Root cortex": "Cortex",
        "Root endodermis": "Endodermis",
        "Root stele": "Stele",
        "Phloem": "Phloem",
        "Xylem": "Xylem",
    }
    for label in root_order:
        y = y_positions[label]
        group = markers.loc[markers.label.eq(label), "compartment"].iloc[0]
        color = colors[str(group)]
        ax_a.plot([.03, .23], [y, y], color=color, lw=1.25, solid_capstyle="round")
        ax_a.scatter(.28, y, s=39, color=color, edgecolor="white", linewidth=.55, zorder=3)
        ax_a.text(.39, y, display_taxonomy[label], va="center", fontsize=4.65)
    for text, y, color in [("cap", 8.0, ORANGE), ("epi", 5.5, PURPLE), ("ground", 3.3, TEAL), ("vascular", 1.0, BLUE)]:
        ax_a.text(-.34, y, text, ha="left", va="center", fontsize=4.25, color=color, fontweight="bold")
    ax_a.set(xlim=(-.37, 1.28), ylim=(-.65, 9.65))
    label_panel(ax_a, "a", "Root identity\ntaxonomy")

    top = markers[markers["rank"].le(5)]
    score = top.pivot(index="label", columns="rank", values="log2fc").reindex(index=root_order, columns=range(1, 6))
    genes = top.pivot(index="label", columns="rank", values="gene").reindex(index=root_order, columns=range(1, 6))
    cmap = LinearSegmentedColormap.from_list("marker", ["#F5F8F8", "#B8DEDA", TEAL, "#075764"])
    image = ax_b.imshow(score.to_numpy(), aspect="auto", cmap=cmap, vmin=1.0, vmax=max(6.5, float(np.nanmax(score.to_numpy()))))
    for yi, label in enumerate(root_order):
        for xi, rank in enumerate(range(1, 6)):
            value = score.loc[label, rank]
            gene = genes.loc[label, rank]
            if pd.notna(gene):
                ax_b.text(xi, yi, str(gene), ha="center", va="center", fontsize=4.65, color="white" if value >= 4.4 else INK)
    ax_b.set_xticks(range(5), [f"rank {x}" for x in range(1, 6)])
    ax_b.set_yticks(range(len(root_order)), root_order, fontsize=5.0)
    ax_b.tick_params(length=0)
    for spine in ax_b.spines.values(): spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_b, fraction=.03, pad=.018)
    colorbar.outline.set_visible(False); colorbar.ax.tick_params(labelsize=4.4, length=1.4)
    colorbar.set_label("candidate log2 fold-change", fontsize=4.9, labelpad=3)
    label_panel(ax_b, "b", "State-resolved marker-candidate\nprograms", "Top five candidates per root identity")

    markers["detection_delta"] = markers.detection_in - markers.detection_out
    for group, subset in markers.groupby("compartment", observed=True):
        ax_c.scatter(subset.log2fc, subset.detection_delta, s=12 + 23 * subset.score / subset.score.max(), color=colors[str(group)], alpha=.78, edgecolor="white", linewidth=.28, label=str(group))
    chosen = markers.sort_values(["score", "detection_delta"], ascending=False).head(8)
    for row in chosen.itertuples(index=False):
        ax_c.text(row.log2fc+.07, row.detection_delta+.008, row.gene, fontsize=4.2, color=INK)
    ax_c.set(xlabel="candidate log2 fold-change", ylabel="detection-rate separation")
    ax_c.legend(loc="upper right", fontsize=4.45, frameon=False, handletextpad=.2, labelspacing=.16)
    clean(ax_c, "both")
    label_panel(ax_c, "c", "Candidate effect size and detection separation\nidentify testable markers")

    summary = (
        markers.groupby(["label", "compartment"], as_index=False, observed=True)
        .agg(median_score=("score", "median"))
        .set_index("label")
        .reindex(root_order)
        .reset_index()
    )
    y = np.arange(len(summary))
    ax_d.barh(y, summary.median_score, color=[colors[str(value)] for value in summary.compartment], edgecolor="white", linewidth=.35)
    ax_d.set_yticks(y, [label.replace(" root", "") for label in summary.label], fontsize=4.65)
    ax_d.invert_yaxis(); ax_d.set_xlabel("median candidate score")
    clean(ax_d, "x")
    label_panel(ax_d, "d", "Program strength differs\nacross root identities")
    fig.text(.987, .012, "Public-data computational resource. Candidate markers are not presented as wet-lab validation.", ha="right", va="bottom", fontsize=5.0, color=MUTED)
    export(fig, MAIN, "plant_cellfm_v4_fig4_arabidopsis_root_candidate_resource", {"root_marker_candidates": markers, "root_identity_taxonomy": taxonomy, "root_marker_summary": summary})


def render_ed1_label_integrity(v17: pd.DataFrame, v18: pd.DataFrame) -> None:
    payload = json.loads((ROOT / "release_metadata" / "revision_v18_identity_curated_strict.json").read_text(encoding="utf-8"))
    audit = payload["label_integrity_audit"]
    species = list(audit["total_cells_by_species"])
    values = pd.DataFrame(
        {
            "species": species,
            "public_labels": [audit["total_cells_by_species"][s] for s in species],
            "explicit_identities": [audit["kept_cells_by_species"][s] for s in species],
            "audit_only_unknown": [audit["excluded_cells_by_species"][s] for s in species],
        }
    )
    fig = plt.figure(figsize=(7.25, 4.65))
    grid = fig.add_gridspec(1, 3, width_ratios=(1.30, 1.10, 1.15), left=.07, right=.987, bottom=.12, top=.93, wspace=.48)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    ax_c = fig.add_subplot(grid[0, 2])
    y = np.arange(len(values))
    ax_a.barh(y, values.explicit_identities, color=TEAL, label="explicit identities")
    ax_a.barh(y, values.audit_only_unknown, left=values.explicit_identities, color=LIGHT_GREY, label="unknown/unannotated audit-only")
    ax_a.set_yticks(y, [short_species(s) for s in values.species], fontsize=5.15); ax_a.invert_yaxis(); ax_a.set_xlabel("aligned public labels")
    ax_a.legend(loc="lower right", fontsize=4.5, frameon=False, handletextpad=.2)
    clean(ax_a, "x")
    label_panel(ax_a, "a", "Excluded labels remain counted\nin the integrity audit")
    v17_summary = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))["summary"]
    v18_summary = payload["summary"]
    methods = pd.DataFrame(
        [
            {"cohort": "v17 public-label stress test", **v17_summary},
            {"cohort": "v18 explicit-identity companion", **v18_summary},
        ]
    )
    labels = ["public-label\nstress test", "explicit-identity\ncompanion"]
    for index, row in methods.iterrows():
        ax_b.scatter(row.coverage, row.accuracy_all, s=70, color=[GREY, TEAL][index], edgecolor="white", linewidth=.7, zorder=3)
        dx, dy = [(-.055, -.018), (.014, .012)][index]
        ax_b.text(row.coverage + dx, row.accuracy_all + dy, ["v17", "v18"][index], va="center", fontsize=5.2, fontweight="bold")
    ax_b.set(xlim=(.30, 1.02), ylim=(-.02, .55), xlabel="source-label coverage", ylabel="all-cell accuracy")
    clean(ax_b, "both")
    label_panel(ax_b, "b", "The companion cohort makes\nits denominator explicit")
    rows = v18.sort_values("accuracy_all")
    y2 = np.arange(len(rows))
    ax_c.hlines(y2, 0, rows.accuracy_all, color=LIGHT_GREY, lw=2)
    ax_c.scatter(rows.accuracy_all, y2, s=34, color=TEAL, edgecolor="white", linewidth=.5)
    ax_c.set_yticks(y2, [short_species(s) for s in rows.held_out_species], fontsize=5.0); ax_c.set(xlim=(0, .85), xlabel="v18 all-cell accuracy")
    clean(ax_c, "x")
    label_panel(ax_c, "c", "Curated identity transfer\nremains species-dependent")
    export(fig, EXTENDED, "plant_cellfm_v4_ed_fig1_label_integrity", {"label_integrity_by_species": values, "v17_metrics": v17, "v18_metrics": v18, "cohort_comparison": methods})


def render_ed2_nested_selection() -> None:
    payload = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for record in payload["selected_configs"]:
        for rank, candidate in enumerate(record["inner_candidate_ranking"], start=1):
            rows.append(
                {
                    "held_out_species": record["held_out_species"],
                    "candidate": candidate["candidate"]["name"],
                    "rank": rank,
                    "inner_accuracy_all": candidate["summary"]["accuracy_all"],
                    "selected": candidate["candidate"]["name"] == record["selected_candidate"]["name"],
                }
            )
    table = pd.DataFrame(rows)
    candidates = table.groupby("candidate").inner_accuracy_all.mean().sort_values(ascending=False).index.tolist()
    species = sorted(table.held_out_species.unique().tolist())
    matrix = table.pivot(index="candidate", columns="held_out_species", values="inner_accuracy_all").reindex(index=candidates, columns=species)
    selected = table[table.selected]
    fig = plt.figure(figsize=(7.25, 4.65))
    grid = fig.add_gridspec(1, 2, width_ratios=(1.35, .95), left=.07, right=.985, bottom=.15, top=.93, wspace=.52)
    ax_a = fig.add_subplot(grid[0, 0]); ax_b = fig.add_subplot(grid[0, 1])
    image = ax_a.imshow(matrix.to_numpy(), aspect="auto", cmap=LinearSegmentedColormap.from_list("nested", ["#F4F7F8", "#C5E3E0", TEAL]), vmin=0, vmax=max(.62, float(np.nanmax(matrix.to_numpy()))))
    for yi, cand in enumerate(matrix.index):
        for xi, sp in enumerate(matrix.columns):
            value = matrix.loc[cand, sp]
            ax_a.text(xi, yi, f"{value:.2f}", ha="center", va="center", fontsize=4.25, color="white" if value >= .46 else INK)
    ax_a.set_xticks(range(len(species)), [short_species(s) for s in species], rotation=30, ha="right", fontsize=4.45)
    ax_a.set_yticks(range(len(candidates)), [c.replace("gate_", "").replace("_", " ") for c in candidates], fontsize=4.5)
    ax_a.tick_params(length=0)
    for spine in ax_a.spines.values(): spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_a, fraction=.032, pad=.015); colorbar.outline.set_visible(False); colorbar.ax.tick_params(labelsize=4.3, length=1.3)
    label_panel(ax_a, "a", "Candidate decoding rules are selected\ninside source-species folds", "Cell values are inner held-out-source all-cell accuracies")
    counts = selected.candidate.value_counts().sort_values()
    y = np.arange(len(counts))
    ax_b.barh(y, counts.values, color=[TEAL if "organ_context" in value else BLUE for value in counts.index], edgecolor="white", linewidth=.5)
    ax_b.set_yticks(y, [value.replace("gate_", "").replace("_", " ") for value in counts.index], fontsize=5.2)
    ax_b.set(xlim=(0, 8.4), xlabel="outer held-out species selecting rule")
    for yi, value in zip(y, counts.values, strict=True): ax_b.text(value+.13, yi, str(value), va="center", fontsize=5.0)
    clean(ax_b, "x")
    label_panel(ax_b, "b", "No globally selected decoder is\npromoted to a primary claim")
    export(fig, EXTENDED, "plant_cellfm_v4_ed_fig2_nested_selection_audit", {"inner_candidate_scores": table, "selected_candidate_counts": counts.rename_axis("candidate").reset_index(name="outer_species_count")})


def render_ed3_matched_checkpoint_comparison() -> None:
    """Expose the frozen v3-to-v9 comparison on its matched protocols.

    This is intentionally an Extended Data result rather than a claim of
    superiority over an external foundation model.  The two checkpoints share
    the same frozen public benchmark and denominator within each protocol.
    """
    table = pd.read_csv(
        V3_SOURCE / "plant_cellfm_v3_fig3_matched_comparisons_matched_checkpoint_metrics.tsv",
        sep="\t",
    )
    protocol_order = ["leave-dataset-out", "leave-sample-out", "leave-species-out"]
    display = {"leave-dataset-out": "leave dataset", "leave-sample-out": "leave sample", "leave-species-out": "leave species"}
    table["protocol"] = pd.Categorical(table.protocol, protocol_order, ordered=True)
    table = table.sort_values(["protocol", "method"]).reset_index(drop=True)
    pivot = table.pivot(index="protocol", columns="method", values="all_cell_accuracy").reindex(protocol_order)
    macro = table.pivot(index="protocol", columns="method", values="known_label_macro_f1").reindex(protocol_order)
    coverage = table.pivot(index="protocol", columns="method", values="coverage").reindex(protocol_order)
    baseline = "frozen v3"
    candidate = "Plant-CellFM v9"

    fig = plt.figure(figsize=(7.25, 4.65))
    grid = fig.add_gridspec(1, 3, width_ratios=(1.15, 1.12, .83), left=.075, right=.987, bottom=.16, top=.93, wspace=.54)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    ax_c = fig.add_subplot(grid[0, 2])
    y = np.arange(len(protocol_order))
    for index, protocol in enumerate(protocol_order):
        ax_a.plot([pivot.loc[protocol, baseline], pivot.loc[protocol, candidate]], [index, index], color=LIGHT_GREY, lw=2.3, zorder=1)
    ax_a.scatter(pivot[baseline], y, s=38, color=GREY, edgecolor="white", linewidth=.55, label="frozen v3", zorder=3)
    ax_a.scatter(pivot[candidate], y, s=38, color=TEAL, edgecolor="white", linewidth=.55, label="Plant-CellFM v9", zorder=3)
    for index, protocol in enumerate(protocol_order):
        delta = pivot.loc[protocol, candidate] - pivot.loc[protocol, baseline]
        ax_a.text(pivot.loc[protocol, candidate] + .012, index, f"+{delta:.3f}", va="center", fontsize=5.0, color=TEAL, fontweight="bold")
    ax_a.set(yticks=y, yticklabels=[display[p] for p in protocol_order], xlim=(.10, .70), xlabel="matched all-cell accuracy")
    ax_a.invert_yaxis(); ax_a.legend(loc="lower right", fontsize=4.7, frameon=False, handletextpad=.22)
    clean(ax_a, "x")
    label_panel(ax_a, "a", "Frozen checkpoint gains persist\nacross matched protocols")

    x = np.arange(len(protocol_order)); width = .31
    ax_b.bar(x - width / 2, macro[baseline], width, color=GREY, label="frozen v3", edgecolor="white", linewidth=.45)
    ax_b.bar(x + width / 2, macro[candidate], width, color=BLUE, label="Plant-CellFM v9", edgecolor="white", linewidth=.45)
    for index, protocol in enumerate(protocol_order):
        ax_b.text(index + width / 2, macro.loc[protocol, candidate] + .013, f"{macro.loc[protocol, candidate]:.2f}", ha="center", fontsize=4.7, color=INK)
    ax_b.set(xticks=x, xticklabels=["dataset", "sample", "species"], ylim=(0, .58), ylabel="known-label macro-F1")
    clean(ax_b, "y")
    label_panel(ax_b, "b", "Fine-label recovery improves\nunder the same denominator")

    delta = pd.DataFrame(
        {
            "protocol": protocol_order,
            "delta_all_cell_accuracy": [pivot.loc[p, candidate] - pivot.loc[p, baseline] for p in protocol_order],
            "delta_known_label_macro_f1": [macro.loc[p, candidate] - macro.loc[p, baseline] for p in protocol_order],
            "shared_coverage": [coverage.loc[p, candidate] for p in protocol_order],
        }
    )
    ax_c.barh(y, delta.delta_all_cell_accuracy, color=[TEAL, TEAL, ORANGE], edgecolor="white", linewidth=.45)
    for index, row in delta.iterrows():
        ax_c.text(row.delta_all_cell_accuracy + .008, index, f"{row.delta_all_cell_accuracy:+.3f}", va="center", fontsize=5.2, fontweight="bold")
    ax_c.set(yticks=y, yticklabels=["dataset", "sample", "species"], xlim=(0, .29), xlabel="gain in all-cell accuracy")
    ax_c.invert_yaxis(); clean(ax_c, "x")
    label_panel(ax_c, "c", "The species transfer comparison\nremains the hardest matched setting")
    fig.text(.987, .018, "Same frozen benchmark and coverage within each protocol; this is not an external-model ranking.", ha="right", va="bottom", fontsize=4.85, color=MUTED)
    export(
        fig,
        EXTENDED,
        "plant_cellfm_v4_ed_fig3_matched_checkpoint_comparison",
        {"matched_checkpoint_metrics": table, "matched_checkpoint_deltas": delta},
    )


def main() -> None:
    setup()
    cells, v17, v18 = load_cells()
    render_fig1(cells)
    render_fig2(cells, v17, v18)
    render_fig3()
    render_fig4_root_resource()
    render_ed1_label_integrity(v17, v18)
    render_ed2_nested_selection()
    render_ed3_matched_checkpoint_comparison()
    print(json.dumps({"main_figures": 4, "extended_data_figures": 3, "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
