from __future__ import annotations

"""Render data-first Plant-CellFM main-figure drafts and traceable source data.

Figures are intentionally built from the frozen H5AD composition profile and
cell-level strict predictions.  No synthetic values or unclosed external-model
metrics are used in this renderer.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyArrowPatch
from sklearn.utils import resample
import umap


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "figure_data" / "corpus_profile_v1"
EMBEDDING = ROOT / "figure_data" / "v2_embeddings"
OUT = ROOT / "figures" / "plant_cellfm_submission_v3"
DRAFTS = OUT / "drafts"
SOURCE = OUT / "source_data"
sys.path.insert(0, str(ROOT / "scripts"))
import run_revision_v14_context_stc_benchmark as v14  # noqa: E402


INK = "#19222B"
MUTED = "#60717D"
GRID = "#D8E0E4"
TEAL = "#087E8B"
TEAL_LIGHT = "#A8D8D6"
BLUE = "#2D6FAF"
BLUE_LIGHT = "#B8D2EC"
ORANGE = "#DA7C30"
ORANGE_LIGHT = "#F1C9A5"
PURPLE = "#8764A8"
RED = "#B84B5A"
GREY = "#9CAAB2"
PALE = "#F4F7F8"
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


def setup() -> None:
    mpl.rcParams.update(
        {
            "font.family": "Arial",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 6.6,
            "axes.labelcolor": INK,
            "axes.edgecolor": INK,
            "axes.linewidth": 0.6,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.major.width": 0.55,
            "ytick.major.width": 0.55,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )
    DRAFTS.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)


def panel(ax: plt.Axes, letter: str, title: str) -> None:
    ax.text(-0.14, 1.08, letter, transform=ax.transAxes, fontweight="bold", fontsize=9.2, va="top")
    ax.set_title(title, loc="left", fontsize=7.5, fontweight="bold", pad=10)


def clean(ax: plt.Axes, grid: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.55, zorder=0)
    ax.tick_params(length=2.5, pad=2)


def save(fig: plt.Figure, stem: str, tables: dict[str, pd.DataFrame]) -> None:
    for name, frame in tables.items():
        frame.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for ext, kwargs in (("svg", {}), ("pdf", {}), ("png", {"dpi": 300}), ("tiff", {"dpi": 600})):
        fig.savefig(DRAFTS / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.035, **kwargs)
    plt.close(fig)


def read_tsv(name: str) -> pd.DataFrame:
    return pd.read_csv(CORPUS / name, sep="\t")


def short_species(value: str) -> str:
    parts = str(value).split()
    if len(parts) == 2:
        return f"{parts[0][0]}. {parts[1]}"
    return str(value)


def profile_tables() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    profile = json.loads((CORPUS / "corpus_profile.json").read_text(encoding="utf-8"))
    composition = read_tsv("corpus_composition.tsv")
    species_tissue = read_tsv("species_by_tissue.tsv")
    species_cell = read_tsv("species_by_cell_type.tsv")
    return profile, composition, species_tissue, species_cell


def load_strict_cells() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    obs = v14.read_csv(ROOT / "release_metadata" / "species_ontology_obs_labels_with_ids_v9.tsv", delimiter="\t")
    pred_rows = v14.read_csv(EMBEDDING / "predictions.csv")
    aligned, indices = v14.align_obs(obs, pred_rows)
    embeddings = np.load(EMBEDDING / "embeddings.npy").astype(np.float32)[indices]
    v17 = pd.read_csv(EMBEDDING / "v17_nested_strict_predictions.csv")
    by_id = v17.set_index("cell_id")
    frame = pd.DataFrame(
        {
            "cell_id": [row.get("cell_id", "") for row in aligned],
            "species": [v14.canonical_species(row.get("species", "")) for row in aligned],
            "tissue": [row.get("tissue", "") for row in aligned],
            "organ": [v14.organ_group(row.get("tissue", "")) for row in aligned],
            "truth_label": [v14.canonical_text(row.get("cell_type", "")) for row in aligned],
        }
    )
    frame["strict_prediction"] = [by_id.loc[cell_id, "strict_prediction"] for cell_id in frame.cell_id]
    frame["covered_by_train_labels"] = [by_id.loc[cell_id, "covered_by_train_labels"] for cell_id in frame.cell_id]
    reducer = umap.UMAP(n_neighbors=30, min_dist=0.32, metric="cosine", random_state=17)
    coords = reducer.fit_transform(embeddings)
    frame["UMAP1"] = coords[:, 0]
    frame["UMAP2"] = coords[:, 1]
    v17_json = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))
    records = pd.DataFrame(v17_json["outer_species_records"])
    return frame, records, pd.DataFrame(v17_json["selected_configs"])


def render_fig1() -> None:
    profile, composition, species_tissue, species_cell = profile_tables()
    strict_cells, _, _ = load_strict_cells()
    species_order = species_tissue.groupby("species").cells.sum().sort_values(ascending=False).index.tolist()
    tissue_order = species_tissue.groupby("tissue").cells.sum().sort_values(ascending=False).index.tolist()
    fig = plt.figure(figsize=(7.2, 6.55))
    grid = fig.add_gridspec(
        3, 3, width_ratios=(1.06, 1.06, 0.92), height_ratios=(1.08, 1.08, 0.44),
        left=0.085, right=0.985, bottom=0.06, top=0.955, wspace=0.60, hspace=0.72,
    )
    ax_a = fig.add_subplot(grid[:2, :2])
    ax_b = fig.add_subplot(grid[0, 2])
    ax_c = fig.add_subplot(grid[1, 2])
    ax_d = fig.add_subplot(grid[2, :])

    x_positions = {value: index for index, value in enumerate(tissue_order)}
    y_positions = {value: index for index, value in enumerate(species_order)}
    max_cells = species_tissue.cells.max()
    for row in species_tissue.itertuples(index=False):
        ax_a.scatter(
            x_positions[row.tissue], y_positions[row.species],
            s=16 + 770 * np.sqrt(row.cells / max_cells), color=SPECIES.get(row.species, GREY),
            edgecolor="white", linewidth=0.55, zorder=3,
        )
    totals = species_tissue.groupby("species").cells.sum().reindex(species_order)
    for species, total in totals.items():
        y = y_positions[species]
        ax_a.text(-0.70, y, f"{total/1000:.0f}k", ha="right", va="center", color=MUTED, fontsize=6)
    ax_a.set_xticks(range(len(tissue_order)), [value.replace(" ", "\n") for value in tissue_order], rotation=0)
    ax_a.set_yticks(range(len(species_order)), [short_species(value) for value in species_order])
    ax_a.set_xlim(-.8, len(tissue_order)-.45)
    ax_a.set_ylim(len(species_order)-.45, -.45)
    ax_a.set_xlabel("input tissue", labelpad=6)
    clean(ax_a)
    panel(ax_a, "a", "Traceable training-corpus coverage")

    top_labels = (
        species_cell.groupby("cell_type").cells.sum().sort_values(ascending=False).head(12).index.tolist()
    )
    cell_matrix = (
        species_cell[species_cell.cell_type.isin(top_labels)]
        .pivot(index="species", columns="cell_type", values="cells")
        .reindex(index=species_order, columns=top_labels)
        .fillna(0)
    )
    values = np.log10(cell_matrix.to_numpy() + 1)
    cmap = LinearSegmentedColormap.from_list("plant_teal", ["#F6FAFA", "#B8DDDA", "#087E8B"])
    image = ax_b.imshow(values, aspect="auto", cmap=cmap, vmin=0, vmax=max(1, values.max()))
    ax_b.set_yticks(range(len(species_order)), [short_species(value) for value in species_order], fontsize=5.2)
    ax_b.set_xticks(range(len(top_labels)), [value.replace(" ", "\n") for value in top_labels], rotation=90, fontsize=4.7)
    ax_b.tick_params(length=0)
    for spine in ax_b.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_b, fraction=.055, pad=.02)
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(labelsize=4.6, length=1.5)
    colorbar.set_label("log10(cells + 1)", fontsize=5.2, labelpad=3)
    panel(ax_b, "b", "Cell-state breadth")

    organ_palette = {"callus": PURPLE, "leaf": TEAL, "root": BLUE, "shoot_apex": ORANGE}
    for organ in sorted(strict_cells.organ.unique()):
        subset = strict_cells[strict_cells.organ.eq(organ)]
        ax_c.scatter(subset.UMAP1, subset.UMAP2, s=2.4, color=organ_palette.get(organ, GREY), alpha=.72, linewidth=0, label=organ.replace("_", " "))
    ax_c.set_xticks([]); ax_c.set_yticks([])
    ax_c.set_xlabel("shared embedding", fontsize=5.8, labelpad=3)
    for spine in ax_c.spines.values():
        spine.set_visible(False)
    ax_c.legend(loc="upper left", bbox_to_anchor=(-.04, -.28), ncol=2, fontsize=4.8, frameon=False, handletextpad=.25, columnspacing=.5, labelspacing=.25)
    panel(ax_c, "c", "Eight-species evaluation atlas by organ")

    ax_d.set_axis_off()
    nodes = [
        (0.03, "272,732 measured cells", "source-traceable corpus"),
        (0.28, "209,405 genes", "shared-gene / ortholog contract"),
        (0.56, "256-d Plant-CellFM", "4 layers; LoRA-adapted encoder"),
        (0.84, "auditable outputs", "strict zero-shot | few-shot | deployment"),
    ]
    for x, headline, subhead in nodes:
        ax_d.text(x, .58, headline, transform=ax_d.transAxes, ha="center", va="center", fontsize=7.0, fontweight="bold", color=INK)
        ax_d.text(x, .28, subhead, transform=ax_d.transAxes, ha="center", va="center", fontsize=5.5, color=MUTED)
    for (x0, _, _), (x1, _, _) in zip(nodes[:-1], nodes[1:], strict=True):
        arrow = FancyArrowPatch((x0+.10, .45), (x1-.11, .45), transform=ax_d.transAxes, arrowstyle="-|>", mutation_scale=8, lw=.85, color="#74858E")
        ax_d.add_patch(arrow)
    ax_d.text(-.013, .98, "d", transform=ax_d.transAxes, fontweight="bold", fontsize=9.2, va="top")
    ax_d.text(.03, .98, "One common data contract, three explicitly separated usage protocols", transform=ax_d.transAxes, fontweight="bold", fontsize=7.5, va="top")
    save(
        fig,
        "plant_cellfm_v3_fig1_corpus_and_representation",
        {
            "corpus_composition": composition,
            "species_by_tissue": species_tissue,
            "species_by_cell_type": species_cell,
            "evaluation_embedding_coordinates": strict_cells[["cell_id", "species", "tissue", "organ", "truth_label", "UMAP1", "UMAP2"]],
        },
    )


def bootstrap_accuracy(frame: pd.DataFrame, iterations: int = 2000) -> pd.DataFrame:
    rng = np.random.default_rng(19)
    truth = frame.truth_label.to_numpy()
    pred = frame.strict_prediction.to_numpy()
    rows = []
    for iteration in range(iterations):
        idx = rng.integers(0, len(frame), len(frame))
        rows.append({"bootstrap": iteration, "all_cell_accuracy": float((truth[idx] == pred[idx]).mean())})
    return pd.DataFrame(rows)


def render_fig2() -> None:
    strict_cells, records, _ = load_strict_cells()
    v14_payload = json.loads((ROOT / "release_metadata" / "revision_v14_context_stc_benchmark.json").read_text(encoding="utf-8"))
    v16_payload = json.loads((ROOT / "release_metadata" / "revision_v16_nested_hierarchical_probe.json").read_text(encoding="utf-8"))
    v17_payload = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))
    bootstrap = bootstrap_accuracy(strict_cells)
    summary = v17_payload["summary"]
    records = records.sort_values("accuracy_all").reset_index(drop=True)
    fig = plt.figure(figsize=(7.2, 6.25))
    grid = fig.add_gridspec(
        3, 3, width_ratios=(.78, 1.55, .92), height_ratios=(.70, 1.12, .98),
        left=.085, right=.985, bottom=.075, top=.955, wspace=.58, hspace=.72,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1:, :2])
    ax_d = fig.add_subplot(grid[1, 2])
    ax_e = fig.add_subplot(grid[2, 2])

    ax_a.set_axis_off()
    ax_a.text(0, .82, "strict leave-species split", fontsize=7.8, fontweight="bold", transform=ax_a.transAxes)
    ax_a.text(0, .58, "target cell labels locked", fontsize=6.1, color=RED, fontweight="bold", transform=ax_a.transAxes)
    ax_a.text(0, .30, "outer test species\ninner source-species selection\nno target labels in fitting", fontsize=5.8, color=MUTED, linespacing=1.45, transform=ax_a.transAxes)
    panel(ax_a, "a", "Protocol")

    metrics = pd.DataFrame(
        [
            {"method": "centroid", "all_cell_accuracy": .2364, "status": "matched baseline"},
            {"method": "expression STC", "all_cell_accuracy": .3010, "status": "matched baseline"},
            {"method": "nested learned probe", "all_cell_accuracy": v16_payload["summary"]["accuracy_all"], "status": "nested"},
            {"method": "nested metadata gate", "all_cell_accuracy": summary["accuracy_all"], "status": "nested"},
            {"method": "global metadata gate", "all_cell_accuracy": v14_payload["best_method"]["summary"]["accuracy_all"], "status": "exploratory"},
        ]
    )
    colors = [GREY, GREY, BLUE_LIGHT, TEAL, "#D9DEE1"]
    y = np.arange(len(metrics))
    ax_b.hlines(y, 0, metrics.all_cell_accuracy, color="#D9E1E4", lw=3, zorder=1)
    ax_b.scatter(metrics.all_cell_accuracy, y, s=39, color=colors, edgecolor="white", linewidth=.55, zorder=3)
    for row, ypos in zip(metrics.itertuples(index=False), y, strict=True):
        suffix = "*" if row.status == "exploratory" else ""
        ax_b.text(row.all_cell_accuracy+.012, ypos, f"{row.all_cell_accuracy:.3f}{suffix}", va="center", fontsize=5.7, color=INK)
    ax_b.set_yticks(y, metrics.method, fontsize=5.7)
    ax_b.set(xlim=(0, .50), xlabel="strict all-cell accuracy")
    ax_b.axvline(summary["accuracy_all"], color=TEAL, lw=.7, ls=":")
    ax_b.text(.495, -.58, "* global selection uses all folds; shown only as exploratory sensitivity", fontsize=4.8, ha="right", color=MUTED)
    clean(ax_b, "x")
    panel(ax_b, "b", "Nested selection is the primary strict result")

    display_names = {key: short_species(key) for key in records.held_out_species}
    y = np.arange(len(records))
    ax_c.hlines(y, records.accuracy_all, records.accuracy, color="#D7E0E3", lw=2.0, zorder=1)
    ax_c.scatter(records.accuracy_all, y, color=TEAL, s=27, zorder=3, label="all cells")
    ax_c.scatter(records.accuracy, y, color=BLUE, s=27, zorder=3, label="known labels")
    ax_c.scatter(records.coverage, y, color=ORANGE, marker="s", s=25, zorder=3, label="train-label coverage")
    ax_c.set_yticks(y, [display_names[value] for value in records.held_out_species], fontsize=5.8)
    ax_c.set(xlim=(-.02, 1.03), xlabel="accuracy or coverage")
    ax_c.legend(loc="lower right", ncol=3, fontsize=5.1, frameon=False, handletextpad=.35, columnspacing=.9)
    clean(ax_c, "x")
    panel(ax_c, "c", "Species-level heterogeneity remains visible")

    ax_d.hist(bootstrap.all_cell_accuracy, bins=32, color=TEAL_LIGHT, edgecolor="white", linewidth=.35)
    lo, hi = np.quantile(bootstrap.all_cell_accuracy, [.025, .975])
    ax_d.axvline(summary["accuracy_all"], color=TEAL, lw=1.1)
    ax_d.text(.98, .92, f"{summary['accuracy_all']:.3f}\ncell bootstrap\n{lo:.3f}-{hi:.3f}", transform=ax_d.transAxes, ha="right", va="top", fontsize=5.4, color=MUTED)
    ax_d.set_xlabel("all-cell accuracy", fontsize=5.8)
    ax_d.set_ylabel("bootstrap count", fontsize=5.8)
    clean(ax_d, "y")
    panel(ax_d, "d", "Uncertainty on fixed cells")

    ax_e.scatter(records.coverage, records.accuracy_all, s=np.maximum(36, records.n_test / 4.2), color="#B8DCE5", edgecolor=BLUE, linewidth=.75)
    ax_e.axhline(summary["accuracy_all"], ls="--", lw=.75, color=TEAL)
    ax_e.axvline(summary["coverage"], ls="--", lw=.75, color=ORANGE)
    for row in records.itertuples(index=False):
        if row.held_out_species in {"Gossypium hirsutum", "Arabidopsis thaliana", "Brassica rapa"}:
            ax_e.text(row.coverage+.02, row.accuracy_all, short_species(row.held_out_species), fontsize=4.8, va="center")
    ax_e.set(xlim=(-.05, 1.08), ylim=(-.05, 1.07), xlabel="train-label coverage", ylabel="all-cell accuracy")
    clean(ax_e, "both")
    panel(ax_e, "e", "The open-set boundary")
    save(
        fig,
        "plant_cellfm_v3_fig2_nested_strict_transfer",
        {
            "nested_method_comparison": metrics,
            "nested_per_species_metrics": records,
            "cell_bootstrap": bootstrap,
            "strict_cell_predictions": strict_cells[["cell_id", "species", "organ", "truth_label", "strict_prediction", "covered_by_train_labels"]],
        },
    )


def render_fig3() -> None:
    comparison = json.loads((ROOT / "release_metadata" / "v9_benchmarks" / "v9_lora_vs_v3_shared_comparison.json").read_text(encoding="utf-8"))
    external = json.loads((ROOT / "release_metadata" / "external_benchmark_panel_v9.json").read_text(encoding="utf-8"))
    protocols = [
        ("leave_dataset_out", "leave-dataset-out"),
        ("leave_sample_out", "leave-sample-out"),
        ("leave_species_out", "leave-species-out"),
    ]
    rows = []
    for key, display in protocols:
        baseline = comparison["baseline"]["summary"][key]["fine"]
        candidate = comparison["candidate"]["summary"][key]["fine"]
        for method, values in (("frozen v3", baseline), ("Plant-CellFM v9", candidate)):
            rows.append(
                {
                    "protocol": display,
                    "method": method,
                    "all_cell_accuracy": values["accuracy_all"],
                    "known_label_macro_f1": values["macro_f1"],
                    "coverage": values["coverage"],
                }
            )
    metrics = pd.DataFrame(rows)
    gain = (metrics.pivot(index="protocol", columns="method", values=["all_cell_accuracy", "known_label_macro_f1"])
            .reset_index())
    fig = plt.figure(figsize=(7.2, 5.8))
    grid = fig.add_gridspec(
        2, 3, width_ratios=(1.32, 1.10, .88), height_ratios=(1.02, .98),
        left=.085, right=.985, bottom=.09, top=.955, wspace=.57, hspace=.70,
    )
    ax_a = fig.add_subplot(grid[0, :2])
    ax_b = fig.add_subplot(grid[1, 0])
    ax_c = fig.add_subplot(grid[1, 1])
    ax_d = fig.add_subplot(grid[:, 2])

    order = [display for _, display in protocols]
    x = np.arange(len(order))
    width = .34
    v3 = metrics[metrics.method.eq("frozen v3")].set_index("protocol").loc[order]
    v9 = metrics[metrics.method.eq("Plant-CellFM v9")].set_index("protocol").loc[order]
    ax_a.bar(x-width/2, v3.all_cell_accuracy, width, color="#BAC7CD", label="frozen v3", edgecolor="white", linewidth=.5)
    ax_a.bar(x+width/2, v9.all_cell_accuracy, width, color=TEAL, label="Plant-CellFM v9", edgecolor="white", linewidth=.5)
    for index, (before, after) in enumerate(zip(v3.all_cell_accuracy, v9.all_cell_accuracy, strict=True)):
        ax_a.text(index+width/2, after+.018, f"+{after-before:.3f}", ha="center", fontsize=5.5, color=TEAL)
    ax_a.set(xticks=x, xticklabels=["dataset\nholdout", "sample\nholdout", "species\nholdout"], ylim=(0, .70), ylabel="all-cell accuracy")
    ax_a.legend(loc="upper left", ncol=2, fontsize=5.4, frameon=False, handletextpad=.35, columnspacing=.85)
    clean(ax_a, "y")
    panel(ax_a, "a", "Frozen checkpoint gains under matched grouped splits")

    y = np.arange(len(order))
    ax_b.hlines(y, v3["known_label_macro_f1"], v9["known_label_macro_f1"], color="#D9E2E5", lw=2.1)
    ax_b.scatter(v3["known_label_macro_f1"], y, s=30, color="#BAC7CD", label="v3", zorder=3)
    ax_b.scatter(v9["known_label_macro_f1"], y, s=30, color=TEAL, label="v9", zorder=3)
    ax_b.set_yticks(y, ["dataset", "sample", "species"], fontsize=5.8)
    ax_b.set(xlabel="known-label macro-F1", xlim=(0, .56))
    clean(ax_b, "x")
    panel(ax_b, "b", "Fine-label recovery")

    coverage_values = pd.DataFrame({"protocol": order, "coverage": v9.coverage.to_numpy(), "v9_all": v9.all_cell_accuracy.to_numpy()})
    ax_c.scatter(coverage_values.coverage, coverage_values.v9_all, s=56, color=TEAL_LIGHT, edgecolor=TEAL, linewidth=.8)
    for row in coverage_values.itertuples(index=False):
        ax_c.text(row.coverage+.015, row.v9_all, row.protocol.replace("leave-", "").replace("-out", ""), fontsize=5.0, va="center")
    ax_c.set(xlim=(0, 1.05), ylim=(0, .70), xlabel="train-label coverage", ylabel="v9 all-cell accuracy")
    clean(ax_c, "both")
    panel(ax_c, "c", "Protocol difficulty is explicit")

    audit_rows = pd.DataFrame(external["comparisons"])
    def audit_status(comparison: str) -> str:
        return audit_rows.loc[audit_rows.comparison.eq(comparison), "status"].iloc[0]

    status = pd.DataFrame(
        [
            {"method": "matched v3-v9", "protocol": "three grouped holdouts", "status": audit_status("Plant-CellFM v9 vs frozen v3 extended")},
            {"method": "cosine centroid", "protocol": "SRP169576 sample holdout", "status": audit_status("Classical cosine centroid, SRP169576 sample holdout")},
            {"method": "Seurat transfer", "protocol": "exported train/test split", "status": audit_status("Seurat label transfer")},
            {"method": "scPlantLLM probe", "protocol": "official input contract", "status": audit_status("scPlantLLM frozen embedding nearest-centroid probe")},
            {"method": "scPlantAnnotate", "protocol": "official access route", "status": audit_status("scPlantAnnotate")},
        ]
    )
    color_by_status = {"completed": TEAL, "contract_ready_metric_pending": ORANGE, "contract_ready_auth_limited": PURPLE}
    x_by_status = {"completed": .78, "contract_ready_metric_pending": .48, "contract_ready_auth_limited": .27}
    y = np.arange(len(status))[::-1]
    for ypos, row in zip(y, status.itertuples(index=False), strict=True):
        xvalue = x_by_status[row.status]
        ax_d.hlines(ypos, 0, xvalue, color="#D9E2E5", lw=2)
        ax_d.scatter(xvalue, ypos, s=38, color=color_by_status[row.status], edgecolor="white", linewidth=.5, zorder=3)
        ax_d.text(.02, ypos+.18, row.method, fontsize=5.0, color=INK)
        ax_d.text(.02, ypos-.16, row.protocol, fontsize=4.4, color=MUTED)
    ax_d.set(xlim=(0, 1.02), ylim=(-.55, len(status)-.25), yticks=[])
    ax_d.set_xticks([.27, .48, .78], ["auth", "input", "metric"], fontsize=5.0)
    ax_d.set_xlabel("evidence closure", fontsize=5.7)
    clean(ax_d, "x")
    panel(ax_d, "d", "Comparison evidence audit")
    fig.text(.985, .017, "Only matched v3-v9 rows are numerical comparisons; the audit panel is not a performance ranking.", ha="right", va="bottom", fontsize=5.3, color=MUTED)
    save(
        fig,
        "plant_cellfm_v3_fig3_matched_comparisons",
        {"matched_checkpoint_metrics": metrics, "protocol_coverage": coverage_values, "external_comparison_status": status},
    )


def render_fig4() -> None:
    payload = json.loads((ROOT / "release_metadata" / "revision_v11_fewshot_adapter_benchmark.json").read_text(encoding="utf-8"))
    summaries = pd.DataFrame(payload["summaries"])
    budgeted = summaries[summaries["mode"].eq("budgeted_random")].sort_values("support_value").copy()
    budgeted["support_per_species"] = budgeted.support_value.astype(int)
    representative = pd.DataFrame(
        [
            {**record, "support_per_species": int(row.support_value), "seed": int(row.representative_seed)}
            for row in budgeted.itertuples(index=False)
            for record in row.representative_per_species
        ]
    )
    eight = representative[representative.support_per_species.eq(8)].copy().sort_values("accuracy_all_query")
    fig = plt.figure(figsize=(7.2, 5.85))
    grid = fig.add_gridspec(
        2, 3, width_ratios=(.84, 1.46, 1.0), height_ratios=(1.08, 1.0),
        left=.085, right=.985, bottom=.09, top=.955, wspace=.55, hspace=.72,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, 0])
    ax_d = fig.add_subplot(grid[1, 1:])

    ax_a.set_axis_off()
    xs = [.12, .49, .84]
    heads = ["target\ncells", "labeled\nsupport", "held-out\nquery"]
    subs = ["new species", "calibrate", "scored only"]
    colors = [GREY, ORANGE, TEAL]
    for x, head, sub, color in zip(xs, heads, subs, colors, strict=True):
        ax_a.scatter([x]*5, [.72, .64, .56, .48, .40], s=20, color=color, alpha=.9, transform=ax_a.transAxes, clip_on=False)
        ax_a.text(x, .25, head, ha="center", va="center", fontsize=5.8, fontweight="bold", transform=ax_a.transAxes, linespacing=1.0)
        ax_a.text(x, .075, sub, ha="center", va="center", fontsize=4.9, color=MUTED, transform=ax_a.transAxes)
    for x0, x1 in zip(xs[:-1], xs[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((x0+.10,.57),(x1-.10,.57),transform=ax_a.transAxes,arrowstyle="-|>",mutation_scale=8,lw=.8,color="#74858E"))
    ax_a.text(.50, .91, "support and query cells never overlap", ha="center", va="center", fontsize=5.5, color=RED, fontweight="bold", transform=ax_a.transAxes)
    panel(ax_a, "a", "Few-shot protocol")

    ax_b.errorbar(
        budgeted.support_per_species,
        budgeted.mean_accuracy_all_query,
        yerr=budgeted.std_accuracy_all_query,
        color=TEAL,
        marker="o",
        markersize=5.6,
        markeredgecolor="white",
        markeredgewidth=.7,
        linewidth=1.4,
        capsize=2.4,
        zorder=3,
    )
    for row in budgeted.itertuples(index=False):
        ax_b.text(row.support_per_species, row.mean_accuracy_all_query+.031, f"{row.mean_accuracy_all_query:.3f}", ha="center", fontsize=5.7, color=INK)
    ax_b.set(xlim=(4, 68), ylim=(.49, .80), xticks=budgeted.support_per_species, xlabel="labeled support cells per target species", ylabel="query all-cell accuracy")
    ax_b.text(.98, .10, "mean +/- s.d. across 10 support draws\nall support cells excluded from query scoring", transform=ax_b.transAxes, ha="right", va="bottom", fontsize=5.2, color=MUTED)
    clean(ax_b, "y")
    panel(ax_b, "b", "Small target support steadily improves adaptation")

    ax_c.errorbar(
        budgeted.support_per_species,
        budgeted.mean_macro_f1_query,
        color=PURPLE,
        marker="o",
        markersize=5.2,
        markeredgecolor="white",
        markeredgewidth=.7,
        linewidth=1.25,
        capsize=2.1,
    )
    ax_c.set(xticks=budgeted.support_per_species, xlabel="support", ylabel="query macro-F1", ylim=(.15, .52))
    clean(ax_c, "y")
    panel(ax_c, "c", "Fine-label recovery")

    y = np.arange(len(eight))
    ax_d.scatter(eight.accuracy_all_query, y, s=34, color=[SPECIES.get(value, GREY) for value in eight.species], edgecolor="white", linewidth=.55, zorder=3)
    for row, ypos in zip(eight.itertuples(index=False), y, strict=True):
        ax_d.hlines(ypos, 0, row.accuracy_all_query, color="#DDE4E6", lw=2, zorder=1)
        label_x = row.accuracy_all_query-.035 if row.accuracy_all_query >= .88 else row.accuracy_all_query+.025
        align = "right" if row.accuracy_all_query >= .88 else "left"
        ax_d.text(label_x, ypos, f"{int(row.support_labels)} labels", ha=align, va="center", fontsize=5.2, color=MUTED)
    ax_d.set_yticks(y, [short_species(value) for value in eight.species], fontsize=5.7)
    ax_d.set(xlim=(0, 1.12), xlabel="query all-cell accuracy")
    ax_d.text(.99, .06, "representative random support draw (seed 0)\n8 labeled cells per target species", transform=ax_d.transAxes, ha="right", va="bottom", fontsize=5.2, color=MUTED)
    clean(ax_d, "x")
    panel(ax_d, "d", "Adaptation benefit remains species-dependent")
    save(
        fig,
        "plant_cellfm_v3_fig4_fewshot_target_adaptation",
        {
            "fewshot_budget_summary": budgeted.drop(columns=["representative_per_species"]),
            "fewshot_representative_species": representative,
        },
    )


def render_fig5() -> None:
    marker_path = ROOT / "supplementary_tables" / "Supplementary_Table_11_root_marker_candidates.tsv"
    markers = pd.read_csv(marker_path, sep="\t")
    markers["detection_delta"] = markers["detection_in"] - markers["detection_out"]
    root_order = [
        "Columella root cap", "Lateral root cap", "Root cap", "Root hair", "Non-hair",
        "Root cortex", "Root endodermis", "Root stele", "Phloem", "Xylem",
    ]
    markers = markers[markers.label.isin(root_order)].copy()
    markers["root_identity"] = pd.Categorical(markers.label, root_order, ordered=True)
    anchor = json.loads((ROOT / "release_metadata" / "arabidopsis_root_literature_anchor_v9.json").read_text(encoding="utf-8"))
    anchor_rows = pd.DataFrame(anchor["identity_taxonomy"])
    anchor_rows = anchor_rows[anchor_rows.plant_cellfm_label.isin(root_order)].copy()
    compartments = {
        "Columella root cap": "root cap", "Lateral root cap": "root cap", "Root cap": "root cap",
        "Root hair": "epidermis", "Non-hair": "epidermis",
        "Root cortex": "ground tissue", "Root endodermis": "ground tissue",
        "Root stele": "vascular", "Phloem": "vascular", "Xylem": "vascular",
    }
    compartment_colors = {"root cap": ORANGE, "epidermis": PURPLE, "ground tissue": TEAL, "vascular": BLUE}
    markers["compartment"] = markers.label.map(compartments)
    fig = plt.figure(figsize=(7.2, 6.15))
    grid = fig.add_gridspec(
        2, 3, width_ratios=(.82, 1.38, 1.18), height_ratios=(1.12, .88),
        left=.085, right=.985, bottom=.085, top=.955, wspace=.60, hspace=.72,
    )
    ax_a = fig.add_subplot(grid[:, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, 1])
    ax_d = fig.add_subplot(grid[1, 2])

    ax_a.set_axis_off()
    y_positions = {label: index for index, label in enumerate(root_order[::-1])}
    group_centers = {"root cap": 8.0, "epidermis": 5.5, "ground tissue": 3.5, "vascular": 1.0}
    for group, center in group_centers.items():
        ax_a.text(.00, center, group, ha="left", va="center", fontsize=6.1, fontweight="bold", color=compartment_colors[group], transform=ax_a.transData)
    for label in root_order:
        y = y_positions[label]
        color = compartment_colors[compartments[label]]
        ax_a.plot([.38, .58], [y, y], color=color, lw=1.0, solid_capstyle="round")
        ax_a.scatter(.62, y, s=38, color=color, edgecolor="white", linewidth=.6, zorder=3)
        ax_a.text(.72, y, label, va="center", fontsize=5.5, color=INK)
    ax_a.plot([.29, .29], [0, 9], color="#C6D0D4", lw=.7)
    ax_a.set(xlim=(-.02, 1.62), ylim=(-.65, 9.65))
    ax_a.text(.00, -.42, "literature-aligned identity taxonomy", fontsize=5.2, color=MUTED, transform=ax_a.transData)
    ax_a.text(-.10, 1.05, "a", transform=ax_a.transAxes, fontweight="bold", fontsize=9.2, va="top")
    ax_a.set_title("Root identity map", loc="left", fontsize=7.5, fontweight="bold", pad=10)

    top = markers[markers["rank"].le(5)].copy()
    matrix = top.pivot(index="label", columns="rank", values="log2fc").reindex(index=root_order, columns=range(1, 6))
    genes = top.pivot(index="label", columns="rank", values="gene").reindex(index=root_order, columns=range(1, 6))
    cmap = LinearSegmentedColormap.from_list("candidate_fc", ["#F4F7F8", "#AFD9D6", TEAL, "#095A6B"])
    image = ax_b.imshow(matrix.to_numpy(), aspect="auto", cmap=cmap, vmin=1.0, vmax=max(7.2, float(np.nanmax(matrix.to_numpy()))))
    for row_index, label in enumerate(root_order):
        for col_index, rank in enumerate(range(1, 6)):
            gene = genes.loc[label, rank]
            if pd.notna(gene):
                color = "white" if matrix.loc[label, rank] > 4.4 else INK
                ax_b.text(col_index, row_index, str(gene), ha="center", va="center", fontsize=5.2, color=color)
    ax_b.set_xticks(range(5), [f"rank {rank}" for rank in range(1, 6)])
    ax_b.set_yticks(range(len(root_order)), root_order, fontsize=5.8)
    ax_b.tick_params(length=0)
    for spine in ax_b.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_b, fraction=.028, pad=.018)
    colorbar.outline.set_visible(False)
    colorbar.set_label("candidate log2 fold-change", fontsize=5.5, labelpad=3)
    colorbar.ax.tick_params(labelsize=4.9, length=1.5)
    panel(ax_b, "b", "State-specific marker-candidate programs")

    colors = markers.compartment.map(compartment_colors)
    ax_c.scatter(markers.log2fc, markers.detection_delta, s=10 + 16*markers.score/markers.score.max(), c=colors, alpha=.78, linewidth=.2, edgecolor="white")
    for group, color in compartment_colors.items():
        ax_c.scatter([], [], s=20, color=color, label=group)
    ax_c.set(xlabel="candidate log2 fold-change", ylabel="detection separation")
    ax_c.legend(loc="upper left", fontsize=4.7, ncol=1, frameon=False, handletextpad=.25, labelspacing=.22)
    clean(ax_c, "both")
    panel(ax_c, "c", "Effect-size landscape")

    summary = (markers.groupby(["label", "compartment"], as_index=False)
               .agg(median_score=("score", "median"), median_log2fc=("log2fc", "median"), n_cells=("n_cells_in", "max"))
               .set_index("label").reindex(root_order).reset_index())
    y = np.arange(len(summary))
    ax_d.barh(y, summary.median_score, color=[compartment_colors[value] for value in summary.compartment], edgecolor="white", linewidth=.4)
    ax_d.set_yticks(y, [str(label).replace(" root", "") for label in summary.label], fontsize=5.0)
    ax_d.invert_yaxis()
    ax_d.set(xlabel="median marker score")
    clean(ax_d, "x")
    panel(ax_d, "d", "Candidate strength")
    fig.text(.985, .015, "Public-data computational case: marker candidates are not wet-lab validation.", ha="right", va="bottom", fontsize=5.3, color=MUTED)
    save(
        fig,
        "plant_cellfm_v3_fig5_arabidopsis_root_candidate_resource",
        {
            "root_marker_candidates": markers,
            "root_identity_taxonomy": anchor_rows,
            "root_marker_summary": summary,
        },
    )


def render_fig6() -> None:
    payload = json.loads((ROOT / "release_metadata" / "revision_v11_runtime_head_benchmark.json").read_text(encoding="utf-8"))
    runtime = payload["full_vocabulary_runtime_head"]
    confidence = pd.DataFrame(runtime["confidence_curve"])
    per_species = pd.DataFrame(runtime["per_species"])
    decomposition = pd.DataFrame(runtime["coverage_decomposition"]["per_species"])
    strict = json.loads((ROOT / "release_metadata" / "revision_v17_nested_metadata_gate.json").read_text(encoding="utf-8"))["summary"]
    protocol = pd.DataFrame(
        [
            {"setting": "strict leave-species", "target labels used": "no", "label vocabulary": "source-only", "all_cell_accuracy": strict["accuracy_all"]},
            {"setting": "runtime annotation head", "target labels used": "head vocabulary", "label vocabulary": "full runtime", "all_cell_accuracy": runtime["accuracy_all"]},
        ]
    )
    fig = plt.figure(figsize=(7.2, 6.0))
    grid = fig.add_gridspec(
        2, 3, width_ratios=(.92, 1.46, .96), height_ratios=(.96, 1.04),
        left=.085, right=.985, bottom=.09, top=.955, wspace=.57, hspace=.72,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, :2])
    ax_d = fig.add_subplot(grid[1, 2])

    ax_a.set_axis_off()
    stages = [
        (.10, "input\ncell", GREY),
        (.42, "shared\nencoder", BLUE),
        (.75, "runtime\nhead", TEAL),
    ]
    for x, label, color in stages:
        ax_a.scatter([x] * 5, [.76, .68, .60, .52, .44], s=22, color=color, alpha=.92, transform=ax_a.transAxes, clip_on=False)
        ax_a.text(x, .23, label, ha="center", va="center", fontsize=5.8, fontweight="bold", transform=ax_a.transAxes, linespacing=1.0)
    for (x0, _, _), (x1, _, _) in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((x0+.09, .60), (x1-.09, .60), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=.8, color="#74858E"))
    ax_a.text(.50, .92, "full-vocabulary deployment", ha="center", va="center", fontsize=6.0, color=TEAL, fontweight="bold", transform=ax_a.transAxes)
    ax_a.text(.50, .06, "separate from strict\nleave-species evaluation", ha="center", va="center", fontsize=4.9, color=RED, transform=ax_a.transAxes, linespacing=1.15)
    panel(ax_a, "a", "Runtime setting")

    ax_b.plot(confidence.acceptance_rate, confidence.selective_accuracy, color=TEAL, marker="o", markersize=5.1, markeredgecolor="white", markeredgewidth=.7, lw=1.4, label="selective accuracy")
    ax_b.plot(confidence.acceptance_rate, confidence.rejected_error_capture, color=ORANGE, marker="o", markersize=4.8, markeredgecolor="white", markeredgewidth=.7, lw=1.25, label="rejected-error capture")
    for row in confidence.itertuples(index=False):
        if row.acceptance_rate in {.3, .6, 1.0}:
            ax_b.text(row.acceptance_rate, row.selective_accuracy+.035, f"{row.selective_accuracy:.2f}", ha="center", fontsize=5.1, color=TEAL)
    ax_b.set(xlim=(.25, 1.03), ylim=(-.04, 1.04), xlabel="accepted-cell fraction", ylabel="fraction of cells")
    ax_b.legend(loc="lower left", fontsize=5.2, frameon=False, handletextpad=.35)
    ax_b.text(.98, .08, f"{runtime['cells']:,} aligned cells\nfull-head accuracy = {runtime['accuracy_all']:.3f}", transform=ax_b.transAxes, ha="right", va="bottom", fontsize=5.3, color=MUTED)
    clean(ax_b, "y")
    panel(ax_b, "b", "Confidence can trade coverage for reliability")

    per_species = per_species.sort_values("accuracy_all").reset_index(drop=True)
    y = np.arange(len(per_species))
    ax_c.hlines(y, 0, per_species.accuracy_all, color="#D9E2E5", lw=2.2, zorder=1)
    point_size = 22 + 90 * np.sqrt(per_species.cells / per_species.cells.max())
    ax_c.scatter(per_species.accuracy_all, y, s=point_size, color=[SPECIES.get(value, GREY) for value in per_species.species], edgecolor="white", linewidth=.55, zorder=3)
    ax_c.set_yticks(y, [short_species(value) for value in per_species.species], fontsize=5.8)
    ax_c.set(xlim=(-.02, 1.08), xlabel="runtime all-cell accuracy")
    ax_c.text(.99, .05, "point area scales with evaluated cells", transform=ax_c.transAxes, ha="right", va="bottom", fontsize=5.1, color=MUTED)
    clean(ax_c, "x")
    panel(ax_c, "c", "Runtime accuracy remains species-dependent")

    totals = decomposition.cells.to_numpy(dtype=float)
    covered_share = decomposition.covered_cells.to_numpy(dtype=float) / totals
    open_share = decomposition.open_set_cells.to_numpy(dtype=float) / totals
    y = np.arange(len(decomposition))[::-1]
    ax_d.barh(y, covered_share, color="#D9E2E5", edgecolor="white", linewidth=.35, label="seen label space")
    ax_d.barh(y, open_share, left=covered_share, color=ORANGE_LIGHT, edgecolor="white", linewidth=.35, label="open label space")
    for ypos, share in zip(y, covered_share, strict=True):
        if share >= .16:
            ax_d.text(share / 2, ypos, f"{share:.0%}", ha="center", va="center", fontsize=4.5, color=INK)
    ax_d.set_yticks(y, [short_species(value) for value in decomposition.species], fontsize=4.7)
    ax_d.set(xlim=(0, 1.05), xlabel="label-space share")
    ax_d.legend(loc="lower left", fontsize=4.4, frameon=False, handletextpad=.24, labelspacing=.20)
    clean(ax_d, "x")
    panel(ax_d, "d", "Coverage composition is explicit")
    fig.text(.985, .015, "Runtime-head results use a full annotation vocabulary and are reported separately from the strict zero-shot benchmark.", ha="right", va="bottom", fontsize=5.2, color=MUTED)
    save(
        fig,
        "plant_cellfm_v3_fig6_runtime_confidence",
        {
            "protocol_boundary": protocol,
            "runtime_confidence_curve": confidence,
            "runtime_per_species": per_species,
            "runtime_coverage_decomposition": decomposition,
        },
    )


def main() -> None:
    setup()
    render_fig1()
    render_fig2()
    render_fig3()
    render_fig4()
    render_fig5()
    render_fig6()
    print(json.dumps({"out": str(OUT), "figures": 6}, ensure_ascii=False))


if __name__ == "__main__":
    main()
