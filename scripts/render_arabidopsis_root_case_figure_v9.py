from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib.colors import Normalize


ROOT = Path(__file__).resolve().parents[1]
MARKER_TSV = ROOT / "release_metadata" / "strict_benchmarks" / "public_sprint.marker_candidates.tsv"
TOP_MARKER_TSV = ROOT / "release_metadata" / "plant_biology_case_study_top_markers_v9.tsv"
ADAPTER_JSON = ROOT / "release_metadata" / "plant_species_adapters.json"
OUT_DIR = ROOT / "figures" / "plant_cellfm_v9_arabidopsis_root_case"
SOURCE_DIR = OUT_DIR / "source_data"
FIG_STEM = OUT_DIR / "plant_cellfm_v9_arabidopsis_root_case"

ROOT_IDENTITY_LABELS = [
    "Columella root cap",
    "Lateral root cap",
    "Root cap",
    "Root hair",
    "Non-hair",
    "Root cortex",
    "Root endodermis",
    "Root stele",
    "Phloem",
    "Xylem",
]

DISPLAY_LABELS = {
    "Unknow": "Unknown",
}

PALETTE = {
    "ink": "#25313b",
    "muted": "#6c7884",
    "line": "#c9d2d9",
    "root": "#2d7f73",
    "other": "#9aa6b2",
    "accent": "#bc5a45",
    "blue": "#3c6e91",
    "panel": "#f6f8f8",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.size": 7,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.7,
            "axes.edgecolor": PALETTE["ink"],
            "xtick.color": PALETTE["ink"],
            "ytick.color": PALETTE["ink"],
            "text.color": PALETTE["ink"],
            "legend.frameon": False,
        }
    )


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    markers = pd.read_csv(MARKER_TSV, sep="\t")
    top_markers = pd.read_csv(TOP_MARKER_TSV, sep="\t")
    adapters = json.loads(ADAPTER_JSON.read_text(encoding="utf-8"))
    for frame in (markers, top_markers):
        frame["display_label"] = frame["label"].map(DISPLAY_LABELS).fillna(frame["label"])
        frame["category"] = np.where(
            frame["label"].isin(ROOT_IDENTITY_LABELS), "root_identity", "cell_cycle_or_other"
        )
        frame["detection_delta"] = frame["detection_in"] - frame["detection_out"]
    return markers, top_markers, adapters


def write_source_data(markers: pd.DataFrame, top_markers: pd.DataFrame, adapters: dict) -> dict:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    root_markers = markers[markers["label"].isin(ROOT_IDENTITY_LABELS)].copy()
    root_top = top_markers[top_markers["label"].isin(ROOT_IDENTITY_LABELS)].copy()

    summary = (
        root_markers.groupby(["label", "display_label"], as_index=False)
        .agg(
            marker_rows=("gene", "count"),
            unique_genes=("gene", "nunique"),
            n_cells_in=("n_cells_in", "max"),
            median_score=("score", "median"),
            median_log2fc=("log2fc", "median"),
            median_detection_delta=("detection_delta", "median"),
        )
        .sort_values("display_label")
    )

    full_source = markers[
        [
            "label_key",
            "label",
            "display_label",
            "category",
            "rank",
            "gene",
            "score",
            "log2fc",
            "mean_in",
            "mean_out",
            "detection_in",
            "detection_out",
            "detection_delta",
            "n_cells_in",
            "n_cells_out",
        ]
    ].copy()
    top_source = root_top[
        [
            "label",
            "display_label",
            "rank",
            "gene",
            "score",
            "log2fc",
            "detection_delta",
            "detection_in",
            "detection_out",
            "n_cells_in",
            "n_cells_out",
        ]
    ].copy()

    full_path = SOURCE_DIR / "arabidopsis_root_marker_candidates_figure_source_v9.tsv"
    top_path = SOURCE_DIR / "arabidopsis_root_top_marker_matrix_source_v9.tsv"
    summary_path = SOURCE_DIR / "arabidopsis_root_identity_summary_source_v9.tsv"
    full_source.to_csv(full_path, sep="\t", index=False)
    top_source.to_csv(top_path, sep="\t", index=False)
    summary.to_csv(summary_path, sep="\t", index=False)

    adapter_count = len(adapters.get("adapters", []))
    arabidopsis_adapter = next(
        (item for item in adapters.get("adapters", []) if item.get("adapter_id") == "plant_arabidopsis_thaliana"),
        {},
    )
    metadata = {
        "schema_version": "plant_cellfm_v9_arabidopsis_root_figure_v1",
        "figure": rel(FIG_STEM),
        "input_marker_tsv": rel(MARKER_TSV),
        "input_top_marker_tsv": rel(TOP_MARKER_TSV),
        "input_adapter_registry": rel(ADAPTER_JSON),
        "source_data": [rel(full_path), rel(top_path), rel(summary_path)],
        "adapter_count": adapter_count,
        "arabidopsis_adapter": arabidopsis_adapter.get("adapter_id", "plant_arabidopsis_thaliana"),
        "marker_rows": int(len(markers)),
        "root_identity_marker_rows": int(len(root_markers)),
        "root_identity_labels": len(ROOT_IDENTITY_LABELS),
        "all_cell_states": int(markers["label"].nunique()),
    }
    metadata_path = OUT_DIR / "plant_cellfm_v9_arabidopsis_root_case_figure_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metadata


def draw_panel_a(ax: plt.Axes, metadata: dict) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    steps = [
        ("Public Arabidopsis root matrices", "12 manifest rows; 10 datasets"),
        ("Plant-CellFM v9 adapter resolution", "plant_arabidopsis_thaliana"),
        ("Annotation and marker mining", "13 cell states; 260 marker rows"),
    ]
    ys = [0.72, 0.48, 0.24]
    for idx, (title, subtitle) in enumerate(steps):
        box = patches.FancyBboxPatch(
            (0.08, ys[idx]),
            0.82,
            0.15,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            facecolor="#ffffff",
            edgecolor=PALETTE["line"],
            linewidth=0.8,
        )
        ax.add_patch(box)
        ax.text(0.49, ys[idx] + 0.095, title, ha="center", va="center", weight="bold", fontsize=7.1)
        ax.text(0.49, ys[idx] + 0.045, subtitle, ha="center", va="center", color=PALETTE["muted"], fontsize=6.2)
        if idx < len(steps) - 1:
            ax.annotate(
                "",
                xy=(0.49, ys[idx + 1] + 0.17),
                xytext=(0.49, ys[idx] - 0.01),
                arrowprops=dict(arrowstyle="-|>", lw=0.75, color=PALETTE["muted"]),
            )

    ax.text(
        0.08,
        0.07,
        "Case scale: 24 known adapters; 10 root identities;\n"
        "260 marker candidates; 256-dimensional embeddings.",
        ha="left",
        va="bottom",
        fontsize=6.4,
        color=PALETTE["ink"],
    )


def draw_panel_b(ax: plt.Axes, top_markers: pd.DataFrame) -> None:
    root_top = top_markers[top_markers["label"].isin(ROOT_IDENTITY_LABELS) & (top_markers["rank"] <= 5)].copy()
    root_top["label_order"] = root_top["label"].map({label: idx for idx, label in enumerate(ROOT_IDENTITY_LABELS)})
    root_top = root_top.sort_values(["label_order", "rank"])

    matrix = np.full((len(ROOT_IDENTITY_LABELS), 5), np.nan)
    gene_matrix = np.empty((len(ROOT_IDENTITY_LABELS), 5), dtype=object)
    for _, row in root_top.iterrows():
        y = ROOT_IDENTITY_LABELS.index(row["label"])
        x = int(row["rank"]) - 1
        matrix[y, x] = float(row["log2fc"])
        gene_matrix[y, x] = row["gene"]

    cmap = mpl.colormaps["YlGnBu"].copy()
    cmap.set_bad("#f2f4f5")
    im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=1.2, vmax=max(7.2, np.nanmax(matrix)))

    for y in range(matrix.shape[0]):
        for x in range(matrix.shape[1]):
            gene = gene_matrix[y, x]
            if gene:
                color = "#ffffff" if matrix[y, x] > 4.7 else PALETTE["ink"]
                ax.text(x, y, gene, ha="center", va="center", fontsize=5.3, color=color)

    ax.set_xticks(np.arange(5), labels=[f"rank {i}" for i in range(1, 6)])
    ax.set_yticks(np.arange(len(ROOT_IDENTITY_LABELS)), labels=ROOT_IDENTITY_LABELS)
    ax.tick_params(axis="x", rotation=0, length=0, labelsize=6)
    ax.tick_params(axis="y", length=0, labelsize=6)
    ax.set_title("Top marker candidates by root identity", loc="left", fontsize=7.5, weight="bold")
    ax.set_xlabel("Candidate rank", fontsize=6.5)
    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("log2 fold-change", fontsize=6)
    cbar.ax.tick_params(labelsize=5.5, length=2)


def draw_panel_c(ax: plt.Axes, markers: pd.DataFrame) -> None:
    markers = markers.copy()
    markers["is_root"] = markers["label"].isin(ROOT_IDENTITY_LABELS)
    colors = np.where(markers["is_root"], PALETTE["root"], PALETTE["other"])
    sizes = 8 + 35 * (markers["score"] - markers["score"].min()) / (markers["score"].max() - markers["score"].min())

    ax.scatter(
        markers["log2fc"],
        markers["detection_delta"],
        s=sizes,
        c=colors,
        alpha=0.72,
        linewidths=0.25,
        edgecolors="#ffffff",
    )
    ax.axhline(0, lw=0.6, color=PALETTE["line"], zorder=0)
    ax.set_xlabel("Marker log2 fold-change", fontsize=6.5)
    ax.set_ylabel("Detection-rate separation", fontsize=6.5)
    ax.set_title("Marker effect sizes across all candidate states", loc="left", fontsize=7.5, weight="bold")
    ax.grid(axis="both", color="#edf1f2", linewidth=0.45)

    top_labels = (
        markers[markers["is_root"] & (markers["rank"] == 1)]
        .sort_values("score", ascending=False)
        .head(8)
        .copy()
    )
    for _, row in top_labels.iterrows():
        ax.text(row["log2fc"] + 0.04, row["detection_delta"] + 0.006, row["gene"], fontsize=5.2)

    handles = [
        mpl.lines.Line2D([0], [0], marker="o", lw=0, color=PALETTE["root"], label="root identity"),
        mpl.lines.Line2D([0], [0], marker="o", lw=0, color=PALETTE["other"], label="cell cycle / other"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=5.8, handletextpad=0.4)


def draw_panel_d(ax: plt.Axes, markers: pd.DataFrame) -> None:
    root_markers = markers[markers["label"].isin(ROOT_IDENTITY_LABELS)].copy()
    summary = (
        root_markers.groupby("label", as_index=False)
        .agg(
            median_score=("score", "median"),
            median_log2fc=("log2fc", "median"),
            median_detection_delta=("detection_delta", "median"),
            n_cells_in=("n_cells_in", "max"),
        )
        .set_index("label")
        .loc[ROOT_IDENTITY_LABELS]
        .reset_index()
    )
    norm = Normalize(vmin=summary["median_detection_delta"].min(), vmax=summary["median_detection_delta"].max())
    colors = mpl.colormaps["BuGn"](norm(summary["median_detection_delta"].to_numpy()))

    y = np.arange(len(summary))
    ax.barh(y, summary["median_score"], color=colors, edgecolor="white", linewidth=0.4)
    ax.set_xlim(0, float(summary["median_score"].max()) + 0.85)
    ax.set_yticks(y, labels=summary["label"])
    ax.invert_yaxis()
    ax.set_xlabel("Median marker score", fontsize=6.5)
    ax.set_title("Root identity marker strength", loc="left", fontsize=7.5, weight="bold")
    ax.grid(axis="x", color="#edf1f2", linewidth=0.45)
    ax.tick_params(axis="y", labelsize=6)

    for idx, row in summary.iterrows():
        ax.text(
            row["median_score"] + 0.04,
            idx,
            f"{row['median_log2fc']:.1f} log2FC",
            va="center",
            fontsize=5.3,
            color=PALETTE["muted"],
        )

    sm = mpl.cm.ScalarMappable(cmap=mpl.colormaps["BuGn"], norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.045, pad=0.02)
    cbar.set_label("median detection separation", fontsize=6)
    cbar.ax.tick_params(labelsize=5.5, length=2)


def render() -> dict:
    configure_matplotlib()
    markers, top_markers, adapters = load_data()
    metadata = write_source_data(markers, top_markers, adapters)

    fig = plt.figure(figsize=(7.2, 6.7), constrained_layout=False)
    gs = fig.add_gridspec(
        nrows=3,
        ncols=2,
        width_ratios=[1.02, 1.35],
        height_ratios=[1.02, 0.9, 0.9],
        left=0.055,
        right=0.985,
        top=0.94,
        bottom=0.085,
        wspace=0.34,
        hspace=0.43,
    )

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[:, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[2, 0])
    draw_panel_a(ax_a, metadata)
    draw_panel_b(ax_b, top_markers)
    draw_panel_c(ax_c, markers)
    draw_panel_d(ax_d, markers)

    fig.text(0.012, 0.958, "a", fontsize=10, weight="bold")
    fig.text(0.405, 0.958, "b", fontsize=10, weight="bold")
    fig.text(0.012, 0.635, "c", fontsize=10, weight="bold")
    fig.text(0.012, 0.337, "d", fontsize=10, weight="bold")
    fig.suptitle(
        "Plant-CellFM v9 Arabidopsis root adapter and marker-candidate case",
        x=0.055,
        y=0.985,
        ha="left",
        fontsize=8.3,
        weight="bold",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_STEM.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(FIG_STEM.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(FIG_STEM.with_suffix(".png"), dpi=450, bbox_inches="tight")
    fig.savefig(
        FIG_STEM.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)

    metadata["exports"] = [
        rel(FIG_STEM.with_suffix(suffix))
        for suffix in [".svg", ".pdf", ".png", ".tiff"]
    ]
    metadata_path = OUT_DIR / "plant_cellfm_v9_arabidopsis_root_case_figure_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    metadata = render()
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
