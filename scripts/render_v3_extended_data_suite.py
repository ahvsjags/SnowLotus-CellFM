from __future__ import annotations

"""Render traceable Extended Data figures for the Plant-CellFM submission set."""

import json
import sys
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_v3_data_first_main_figures as main  # noqa: E402


OUT = ROOT / "figures" / "plant_cellfm_submission_v3" / "extended_data"
SOURCE = OUT / "source_data"


def setup() -> None:
    main.setup()
    OUT.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)


def save(fig: plt.Figure, stem: str, tables: dict[str, pd.DataFrame]) -> None:
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for ext, kwargs in (("svg", {}), ("pdf", {}), ("png", {"dpi": 300}), ("tiff", {"dpi": 600})):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight", pad_inches=.035, **kwargs)
    plt.close(fig)


def panel(ax: plt.Axes, letter: str, title: str) -> None:
    main.panel(ax, letter, title)


def clean(ax: plt.Axes, grid: str | None = None) -> None:
    main.clean(ax, grid)


def ed1_corpus_provenance() -> None:
    profile, composition, species_tissue, species_cell = main.profile_tables()
    species_dataset = main.read_tsv("species_by_dataset.tsv")
    datasets = species_dataset.sort_values("cells", ascending=True).dataset_id.tolist()
    species = species_dataset.groupby("species").cells.sum().sort_values(ascending=False).index.tolist()
    fig = plt.figure(figsize=(7.2, 5.85))
    grid = fig.add_gridspec(2, 3, width_ratios=(1.38, 1.0, .88), height_ratios=(1.12, .88), left=.085, right=.985, bottom=.09, top=.955, wspace=.58, hspace=.72)
    ax_a = fig.add_subplot(grid[:, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, 1])
    ax_d = fig.add_subplot(grid[1, 2])

    for row in species_dataset.itertuples(index=False):
        x = datasets.index(row.dataset_id)
        y = species.index(row.species)
        ax_a.scatter(x, y, s=26 + 640 * np.sqrt(row.cells / species_dataset.cells.max()), color=main.SPECIES.get(row.species, main.GREY), edgecolor="white", linewidth=.6, zorder=3)
    ax_a.set_xticks(range(len(datasets)), [value.replace("scplantdb_", "") for value in datasets], rotation=90, fontsize=5.0)
    ax_a.set_yticks(range(len(species)), [main.short_species(value) for value in species], fontsize=5.8)
    ax_a.set(xlabel="dataset accession", ylabel="species")
    clean(ax_a)
    panel(ax_a, "a", "Traceable corpus provenance")

    ds = species_dataset.sort_values("cells", ascending=True).copy()
    ax_b.barh(np.arange(len(ds)), ds.cells / 1000, color=[main.SPECIES.get(value, main.GREY) for value in ds.species], edgecolor="white", linewidth=.45)
    for ypos, row in enumerate(ds.itertuples(index=False)):
        ax_b.text(row.cells / 1000 + 1.0, ypos, main.short_species(row.species), va="center", fontsize=5.1, color=main.MUTED)
    ax_b.set_yticks(np.arange(len(ds)), [value.replace("scplantdb_", "") for value in ds.dataset_id], fontsize=5.2)
    ax_b.set(xlabel="cells (thousands)")
    clean(ax_b, "x")
    panel(ax_b, "b", "Dataset-scale imbalance is retained, not hidden")

    labels = species_cell.groupby("cell_type", as_index=False).cells.sum().sort_values("cells", ascending=False)
    rank = np.arange(1, len(labels) + 1)
    ax_c.plot(rank, labels.cells / 1000, color=main.TEAL, marker="o", markersize=3.2, lw=1.1)
    ax_c.set(xlabel="cell-label rank", ylabel="cells (thousands)")
    clean(ax_c, "both")
    panel(ax_c, "c", "Long-tailed cell-state abundance")

    ax_d.set_axis_off()
    stats = [
        ("272,732", "measured cells"),
        ("209,405", "genes"),
        ("9", "datasets"),
        ("31", "samples"),
        ("34", "cell labels"),
    ]
    for index, (value, label) in enumerate(stats):
        y = .86 - .17 * index
        ax_d.text(.02, y, value, fontsize=8.0, fontweight="bold", color=main.INK, transform=ax_d.transAxes)
        ax_d.text(.40, y, label, fontsize=5.7, color=main.MUTED, va="center", transform=ax_d.transAxes)
    panel(ax_d, "d", "Frozen H5AD profile")
    save(fig, "plant_cellfm_v3_ed_fig1_corpus_provenance", {"corpus_composition": composition, "species_by_dataset": species_dataset, "species_by_tissue": species_tissue, "species_by_cell_type": species_cell, "label_rank": labels})


def nested_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    payload = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))
    selected = pd.DataFrame(payload["selected_configs"])
    outer = pd.DataFrame(payload["outer_species_records"])
    rows = []
    for record in payload["selected_configs"]:
        for rank, candidate in enumerate(record["inner_candidate_ranking"], start=1):
            rows.append(
                {
                    "held_out_species": record["held_out_species"],
                    "candidate": candidate["candidate"]["name"],
                    "candidate_kind": candidate["candidate"]["kind"],
                    "inner_rank": rank,
                    "inner_all_cell_accuracy": candidate["summary"]["accuracy_all"],
                    "inner_known_label_accuracy": candidate["summary"]["accuracy"],
                    "inner_macro_f1": candidate["summary"]["macro_f1"],
                    "selected": candidate["candidate"]["name"] == record["selected_candidate"]["name"],
                }
            )
    return selected, outer, pd.DataFrame(rows)


def ed2_nested_selection_audit() -> None:
    selected, outer, candidates = nested_tables()
    species = outer.sort_values("held_out_species").held_out_species.tolist()
    candidate_order = candidates.groupby("candidate").inner_all_cell_accuracy.mean().sort_values(ascending=True).index.tolist()
    pivot = candidates.pivot(index="candidate", columns="held_out_species", values="inner_all_cell_accuracy").reindex(index=candidate_order, columns=species)
    fig = plt.figure(figsize=(7.2, 5.9))
    grid = fig.add_gridspec(2, 3, width_ratios=(1.5, .9, .92), height_ratios=(1.2, .8), left=.085, right=.985, bottom=.09, top=.955, wspace=.62, hspace=.76)
    ax_a = fig.add_subplot(grid[:, :2])
    ax_b = fig.add_subplot(grid[0, 2])
    ax_c = fig.add_subplot(grid[1, 2])

    cmap = LinearSegmentedColormap.from_list("nested_inner", ["#F5F7F8", "#B9DCD9", main.TEAL])
    image = ax_a.imshow(pivot.to_numpy(), aspect="auto", cmap=cmap, vmin=.20, vmax=max(.56, float(np.nanmax(pivot.to_numpy()))))
    selected_map = selected.set_index("held_out_species").selected_candidate.apply(lambda value: value["name"]).to_dict()
    for row_index, candidate in enumerate(candidate_order):
        for col_index, species_name in enumerate(species):
            if selected_map.get(species_name) == candidate:
                ax_a.add_patch(plt.Rectangle((col_index-.49, row_index-.49), .98, .98, fill=False, edgecolor=main.RED, linewidth=1.05))
    ax_a.set_xticks(range(len(species)), [main.short_species(value) for value in species], rotation=50, ha="right", fontsize=5.0)
    ax_a.set_yticks(range(len(candidate_order)), [value.replace("_", " ") for value in candidate_order], fontsize=5.0)
    ax_a.tick_params(length=0)
    for spine in ax_a.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_a, fraction=.025, pad=.018)
    colorbar.outline.set_visible(False)
    colorbar.set_label("inner all-cell accuracy", fontsize=5.2, labelpad=3)
    colorbar.ax.tick_params(labelsize=4.8, length=1.5)
    panel(ax_a, "a", "Outer-species choices use inner-source-species scores")

    choices = pd.Series(selected_map).value_counts().sort_values()
    ax_b.barh(np.arange(len(choices)), choices.to_numpy(), color=[main.TEAL if value == "gate_leaf_support_64" else main.BLUE for value in choices.index], edgecolor="white", linewidth=.4)
    ax_b.set_yticks(np.arange(len(choices)), [value.replace("_", " ") for value in choices.index], fontsize=5.2)
    ax_b.set(xlabel="outer species selected")
    clean(ax_b, "x")
    panel(ax_b, "b", "Selected configuration")

    outer = outer.sort_values("accuracy_all")
    y = np.arange(len(outer))
    ax_c.hlines(y, 0, outer.accuracy_all, color="#D9E2E5", lw=2)
    ax_c.scatter(outer.accuracy_all, y, s=28, color=main.TEAL, edgecolor="white", linewidth=.5, zorder=3)
    ax_c.set_yticks(y, [main.short_species(value) for value in outer.held_out_species], fontsize=4.9)
    ax_c.set(xlim=(-.02, 1.06), xlabel="outer all-cell accuracy")
    clean(ax_c, "x")
    panel(ax_c, "c", "Held-out outcomes")
    fig.text(.985, .015, "Red outlines indicate the candidate chosen for each outer species; all target-species labels remain outside selection.", ha="right", va="bottom", fontsize=5.1, color=main.MUTED)
    save(fig, "plant_cellfm_v3_ed_fig2_nested_selection_audit", {"outer_species_records": outer, "nested_candidate_ranking": candidates, "selected_configurations": selected})


def ed3_open_set_audit() -> None:
    cells, records, _ = main.load_strict_cells()
    cells["exact_correct"] = cells.truth_label.eq(cells.strict_prediction)
    rows = []
    for species, frame in cells.groupby("species", sort=False):
        n = len(frame)
        covered = frame.covered_by_train_labels.astype(bool)
        rows.append(
            {
                "species": species,
                "cells": n,
                "correct_known_label": int((frame.exact_correct & covered).sum()),
                "wrong_known_label": int(((~frame.exact_correct) & covered).sum()),
                "open_label_space": int((~covered).sum()),
            }
        )
    summary = pd.DataFrame(rows).sort_values("cells", ascending=True)
    summary["correct_share"] = summary.correct_known_label / summary.cells
    summary["wrong_share"] = summary.wrong_known_label / summary.cells
    summary["open_share"] = summary.open_label_space / summary.cells
    organ_species = cells.groupby(["species", "organ"], as_index=False).size().rename(columns={"size": "cells"})
    label_counts = cells.groupby("truth_label", as_index=False).size().rename(columns={"size": "cells"}).sort_values("cells", ascending=False)
    fig = plt.figure(figsize=(7.2, 5.95))
    grid = fig.add_gridspec(2, 3, width_ratios=(1.36, 1.0, .82), height_ratios=(1.05, .95), left=.085, right=.985, bottom=.09, top=.955, wspace=.60, hspace=.72)
    ax_a = fig.add_subplot(grid[:, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, 1])
    ax_d = fig.add_subplot(grid[1, 2])

    y = np.arange(len(summary))
    ax_a.barh(y, summary.correct_share, color=main.TEAL, edgecolor="white", linewidth=.35, label="exactly correct")
    ax_a.barh(y, summary.wrong_share, left=summary.correct_share, color=main.GREY, edgecolor="white", linewidth=.35, label="wrong, seen label")
    ax_a.barh(y, summary.open_share, left=summary.correct_share + summary.wrong_share, color=main.ORANGE_LIGHT, edgecolor="white", linewidth=.35, label="held-out label")
    ax_a.set_yticks(y, [main.short_species(value) for value in summary.species], fontsize=5.7)
    ax_a.set(xlim=(0, 1.02), xlabel="fraction of strict test cells")
    ax_a.legend(loc="lower right", fontsize=4.8, frameon=False, handletextpad=.25, labelspacing=.25)
    clean(ax_a, "x")
    panel(ax_a, "a", "Exact-label denominator exposes the open set")

    organs = sorted(organ_species.organ.unique())
    species_order = summary.species.tolist()
    for row in organ_species.itertuples(index=False):
        ax_b.scatter(organs.index(row.organ), species_order.index(row.species), s=14 + 400*np.sqrt(row.cells / organ_species.cells.max()), color=main.SPECIES.get(row.species, main.GREY), edgecolor="white", linewidth=.5)
    ax_b.set_xticks(range(len(organs)), [value.replace("_", "\n") for value in organs], fontsize=5.5)
    ax_b.set_yticks(range(len(species_order)), [main.short_species(value) for value in species_order], fontsize=5.3)
    ax_b.set(xlabel="evaluation organ")
    clean(ax_b)
    panel(ax_b, "b", "Open-set challenge is species and organ structured")

    records = records.sort_values("coverage")
    ax_c.scatter(records.coverage, records.accuracy_all, s=np.maximum(24, records.n_test / 6), color=main.TEAL_LIGHT, edgecolor=main.TEAL, linewidth=.6)
    for row in records.itertuples(index=False):
        ax_c.text(row.coverage+.018, row.accuracy_all, main.short_species(row.held_out_species), fontsize=4.4, va="center")
    ax_c.set(xlim=(-.04, 1.08), ylim=(-.04, 1.06), xlabel="source-label coverage", ylabel="all-cell accuracy")
    clean(ax_c, "both")
    panel(ax_c, "c", "Coverage is a measurable determinant")

    top = label_counts.head(10).iloc[::-1]
    ax_d.barh(np.arange(len(top)), top.cells, color=main.PURPLE, edgecolor="white", linewidth=.35)
    ax_d.set_yticks(np.arange(len(top)), [str(value)[:18] for value in top.truth_label], fontsize=4.7)
    ax_d.set(xlabel="test cells")
    clean(ax_d, "x")
    panel(ax_d, "d", "Label abundance")
    save(fig, "plant_cellfm_v3_ed_fig3_open_set_audit", {"strict_cell_space_summary": summary, "species_by_organ": organ_species, "outer_species_metrics": records, "strict_truth_label_counts": label_counts})


def ed4_fewshot_stability() -> None:
    payload = json.loads((ROOT / "release_metadata" / "revision_v11_fewshot_adapter_benchmark.json").read_text(encoding="utf-8"))
    summaries = pd.DataFrame(payload["summaries"])
    budgeted = summaries[summaries["mode"].eq("budgeted_random")].copy().sort_values("support_value")
    species_rows = []
    for row in budgeted.itertuples(index=False):
        for record in row.representative_per_species:
            species_rows.append({**record, "support_cells_per_species": int(row.support_value), "seed": int(row.representative_seed)})
    species_data = pd.DataFrame(species_rows)
    pivot = species_data.pivot(index="species", columns="support_cells_per_species", values="accuracy_all_query")
    species_order = pivot.mean(axis=1).sort_values().index.tolist()
    fig = plt.figure(figsize=(7.2, 5.8))
    grid = fig.add_gridspec(2, 3, width_ratios=(1.25, 1.1, .92), height_ratios=(1.1, .9), left=.085, right=.985, bottom=.09, top=.955, wspace=.60, hspace=.72)
    ax_a = fig.add_subplot(grid[:, :2])
    ax_b = fig.add_subplot(grid[0, 2])
    ax_c = fig.add_subplot(grid[1, 2])

    for species in species_order:
        frame = species_data[species_data.species.eq(species)].sort_values("support_cells_per_species")
        ax_a.plot(frame.support_cells_per_species, frame.accuracy_all_query, marker="o", markersize=4.3, lw=1.1, color=main.SPECIES.get(species, main.GREY), label=main.short_species(species))
    ax_a.set(xticks=budgeted.support_value.astype(int).tolist(), xlim=(4, 68), ylim=(-.04, 1.06), xlabel="random labeled support cells per target species", ylabel="representative query all-cell accuracy")
    ax_a.legend(loc="center left", bbox_to_anchor=(1.0, .50), fontsize=4.8, frameon=False, handletextpad=.25, labelspacing=.24)
    clean(ax_a, "y")
    panel(ax_a, "a", "Adaptation trajectories across target species")

    ax_b.errorbar(budgeted.support_value, budgeted.mean_accuracy_all_query, yerr=budgeted.std_accuracy_all_query, color=main.TEAL, marker="o", markersize=5.2, markeredgecolor="white", markeredgewidth=.65, capsize=2.4, lw=1.2)
    ax_b.set(xticks=budgeted.support_value.astype(int).tolist(), xlabel="support", ylabel="query accuracy", ylim=(.49, .80))
    ax_b.text(.97, .08, "mean +/- s.d.\n10 support draws", transform=ax_b.transAxes, ha="right", va="bottom", fontsize=5.0, color=main.MUTED)
    clean(ax_b, "y")
    panel(ax_b, "b", "Random-support stability")

    support = species_data[species_data.support_cells_per_species.eq(64)].sort_values("accuracy_all_query")
    y = np.arange(len(support))
    ax_c.barh(y, support.support_labels, color=[main.SPECIES.get(value, main.GREY) for value in support.species], edgecolor="white", linewidth=.35)
    ax_c.set_yticks(y, [main.short_species(value) for value in support.species], fontsize=4.7)
    ax_c.set(xlabel="represented target labels")
    clean(ax_c, "x")
    panel(ax_c, "c", "Support-label diversity at 64 cells")
    fig.text(.985, .015, "Representative per-species rows use the preregistered seed 0; aggregate curves summarize ten independently sampled support draws.", ha="right", va="bottom", fontsize=5.1, color=main.MUTED)
    save(fig, "plant_cellfm_v3_ed_fig4_fewshot_stability", {"fewshot_aggregate_summary": budgeted.drop(columns=["representative_per_species"]), "fewshot_representative_species": species_data, "fewshot_species_accuracy_matrix": pivot.reset_index()})


def main_render() -> None:
    setup()
    ed1_corpus_provenance()
    ed2_nested_selection_audit()
    ed3_open_set_audit()
    ed4_fewshot_stability()
    print(json.dumps({"out": str(OUT), "figures": 4}, ensure_ascii=False))


if __name__ == "__main__":
    main_render()
