from __future__ import annotations

"""Render Figure 5: provenance-aware allopolyploid wheat adaptation."""

import json
import sys
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, Rectangle
from sklearn.metrics import f1_score


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_v5_top_journal_figures as v5  # noqa: E402


OUT = ROOT / "figures" / "plant_cellfm_submission_v5"
MAIN = OUT / "main"
SOURCE = OUT / "source_data"
TRAIN = ROOT / "outputs" / "gse270342_wheat_root_lora_adapter_4070"
AUDIT = ROOT / "release_metadata" / "gse270342_wheat_lora_adapter_audit_v1.json"
FROZEN_AUDIT = ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_frozen_diagnostic_v1.json"
INPUT_RECORD = ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_input_preparation_v1.json"
STEM = "plant_cellfm_v5_fig5_wheat_adapter"
INK = v5.INK
MUTED = v5.MUTED
GRID = v5.GRID
TEAL = v5.TEAL
BLUE = v5.BLUE
ORANGE = v5.ORANGE
PURPLE = v5.PURPLE
RED = v5.RED
GREY = v5.GREY
LIGHT_GREY = v5.LIGHT_GREY
DIRECT_TARGETS = ["Non-hair", "Phloem", "Root cap", "Root cortex", "Root endodermis", "Root hair", "Unknow", "Xylem"]


def short_label(label: str) -> str:
    replacements = {
        "Dividing Cells": "Dividing\ncells",
        "Endodermis/Phloem": "Endo./\nphloem",
        "Provascular cells": "Provascular\ncells",
        "Root Hair": "Root\nhair",
        "Root Cap": "Root\ncap",
        "Root cortex": "Root\ncortex",
        "Root endodermis": "Root\nendo.",
        "Root hair": "Root\nhair",
        "Root stele": "Root\nstele",
        "Root cap": "Root\ncap",
    }
    return replacements.get(label, label)


def compact_author_label(label: str) -> str:
    """Preserve author-state identity without forcing sub-5 pt matrix labels."""
    replacements = {
        "Cortex": "Cortex",
        "Dividing Cells": "Dividing",
        "Endodermis": "Endodermis",
        "Endodermis/Phloem": "Endo./phloem",
        "Epidermis": "Epidermis",
        "Meristems": "Meristems",
        "Pericycle": "Pericycle",
        "Phloem": "Phloem",
        "Provascular cells": "Provascular",
        "Root Cap": "Root cap",
        "Root Hair": "Root hair",
        "Unknown": "Unknown",
        "Xylem": "Xylem",
    }
    return replacements.get(label, label)


def bootstrap(frame: pd.DataFrame, column: str, *, seed: int) -> pd.DataFrame:
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
                "macro_f1": float(f1_score(truth[take], predicted[take], labels=DIRECT_TARGETS, average="macro", zero_division=0)),
            }
        )
    return pd.DataFrame(rows)


def load_data() -> tuple[dict[str, object], dict[str, object], dict[str, object], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    frozen_audit = json.loads(FROZEN_AUDIT.read_text(encoding="utf-8"))
    input_record = json.loads(INPUT_RECORD.read_text(encoding="utf-8"))
    matched = pd.read_csv(TRAIN / "audit" / "matched_direct_root_locked_test.tsv", sep="\t", dtype=str)
    for column in ("expected_root_label", "adapted_root_label", "frozen_fine_label"):
        if column not in matched.columns:
            raise ValueError(f"Missing matched-direct column: {column}")
    per_class = pd.read_csv(TRAIN / "audit" / "locked_test_per_class.tsv", sep="\t")
    confusion = pd.read_csv(TRAIN / "detailed_test" / "fine_confusion_matrix.tsv", sep="\t")
    history = pd.DataFrame(json.loads((TRAIN / "history.json").read_text(encoding="utf-8"))["epochs"])
    modes = pd.DataFrame(
        [
            {
                "projection": item["mode"],
                "direct_accuracy": item["direct_anatomical_map"]["accuracy"],
                "direct_macro_f1": item["direct_anatomical_map"]["macro_f1_declared_targets"],
            }
            for item in frozen_audit["modes"]
        ]
    )
    return audit, frozen_audit, input_record, matched, per_class, confusion, history, modes


def export(fig: plt.Figure, tables: dict[str, pd.DataFrame]) -> None:
    MAIN.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{STEM}_{name}.tsv", sep="\t", index=False)
    v5.base.enforce_minimum_text_size(fig)
    for suffix, kwargs in (("svg", {}), ("pdf", {}), ("png", {"dpi": 350}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{STEM}.{suffix}", bbox_inches="tight", pad_inches=0.025, **kwargs)
    plt.close(fig)


def main() -> None:
    v5.setup()
    audit, frozen_audit, input_record, matched, per_class, confusion, history, modes = load_data()
    matched = matched.copy()
    first_bootstrap = bootstrap(matched, "frozen_fine_label", seed=20260811)
    adapted_bootstrap = bootstrap(matched, "adapted_root_label", seed=20260812)
    bootstrap_table = pd.concat(
        [first_bootstrap.assign(method="Frozen first projection"), adapted_bootstrap.assign(method="Wheat LoRA adapter")],
        ignore_index=True,
    )
    intervals = bootstrap_table.groupby("method", as_index=False).agg(
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
    per_class = per_class.sort_values("f1-score", ascending=True, kind="mergesort").reset_index(drop=True)
    labels = confusion.true_label.tolist()
    matrix = confusion.drop(columns="true_label").to_numpy(dtype=float)
    normalised = np.divide(matrix, matrix.sum(axis=1, keepdims=True), out=np.zeros_like(matrix), where=matrix.sum(axis=1, keepdims=True) > 0)
    best = history.loc[history.fine_macro_f1.idxmax()]

    fig = plt.figure(figsize=(7.25, 6.55))
    grid = fig.add_gridspec(
        3,
        7,
        height_ratios=(0.80, 1.45, 0.90),
        width_ratios=(1.00, 1.00, 1.02, 1.00, 0.96, 0.96, 0.96),
        left=0.062,
        right=0.99,
        bottom=0.058,
        top=0.967,
        hspace=0.60,
        wspace=0.60,
    )
    ax_a = fig.add_subplot(grid[0, :3])
    ax_b = fig.add_subplot(grid[0, 3:])
    ax_c = fig.add_subplot(grid[1, :3])
    ax_d = fig.add_subplot(grid[1, 3:])
    ax_e = fig.add_subplot(grid[2, :3])
    ax_f = fig.add_subplot(grid[2, 3:])

    ax_a.set_axis_off()
    v5.panel(ax_a, "a", "A provenance gate prevents reuse of prior strict-transfer cells", "GSE270342 wheat-root author object; labels remain unseen by frozen inference")
    stages = [
        (0.02, 0.56, 0.20, "author object", "7,388 cells", GREY),
        (0.28, 0.56, 0.20, "overlap removal", "224 prior cells", RED),
        (0.54, 0.56, 0.20, "diagnostic input", "7,164 cells", BLUE),
        (0.80, 0.56, 0.18, "LoRA test", "1,433 locked", TEAL),
    ]
    for x, y, width, headline, subline, color in stages:
        ax_a.add_patch(Rectangle((x, y), width, 0.23, transform=ax_a.transAxes, facecolor="#F5F8F8", edgecolor=color, linewidth=.82))
        ax_a.add_patch(Rectangle((x, y + .184), width, .046, transform=ax_a.transAxes, facecolor=color, edgecolor=color))
        ax_a.text(x + width / 2, y + .120, headline, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.1, fontweight="bold", color=INK)
        ax_a.text(x + width / 2, y + .052, subline, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, color=MUTED)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((left[0] + left[2] + .008, .675), (right[0] - .008, .675), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=.72, color=MUTED))
    split = [
        ("train", int(audit["split"]["train_cells"]), ORANGE),
        ("validation", int(audit["split"]["validation_cells"]), PURPLE),
        ("locked test", int(audit["split"]["test_cells"]), TEAL),
    ]
    total = sum(value for _, value, _ in split)
    cursor = .02
    for label, value, color in split:
        width = .96 * value / total
        ax_a.add_patch(Rectangle((cursor, .25), width, .10, transform=ax_a.transAxes, facecolor=color, edgecolor="white", linewidth=.55))
        display_label = {
            "train": f"train {value:,}",
            "validation": f"val. {value:,}",
            "locked test": f"test {value:,}",
        }[label]
        ax_a.text(cursor + width / 2, .17, display_label, transform=ax_a.transAxes, ha="center", fontsize=5.0, color=INK)
        cursor += width
    ax_a.text(.02, .055, "Same study remains explicit; barcode removal prevents reuse of the recorded strict-transfer cells.", transform=ax_a.transAxes, fontsize=5.0, color=RED, fontweight="bold")

    ax_b.set_axis_off()
    v5.panel(ax_b, "b", "An author orthogroup contract preserves most counted expression", "Many-to-many groups are recorded; frozen inference uses a deterministic first target")
    coverage = input_record["mapping_coverage"]
    rows = [
        ("source features", coverage["checkpoint_compatible_gene_fraction"], "53.75%", "41,987 / 78,115", BLUE),
        ("source UMI", coverage["checkpoint_compatible_umi_fraction"], "76.33%", "68.8M / 90.2M", TEAL),
    ]
    for index, (label, value, headline, subline, color) in enumerate(rows):
        y = .58 - index * .22
        ax_b.text(.02, y + .07, label, transform=ax_b.transAxes, fontsize=5.05, color=MUTED, va="center")
        ax_b.add_patch(Rectangle((.26, y), .46, .12, transform=ax_b.transAxes, facecolor="#EBF0F1", edgecolor="none"))
        ax_b.add_patch(Rectangle((.26, y), .46 * value, .12, transform=ax_b.transAxes, facecolor=color, edgecolor="none"))
        ax_b.text(.75, y + .073, headline, transform=ax_b.transAxes, fontsize=6.0, fontweight="bold", color=INK, va="center")
        ax_b.text(.75, y + .015, subline, transform=ax_b.transAxes, fontsize=5.0, color=MUTED, va="center")
    ax_b.text(.02, .19, "Frozen mapping sensitivity (direct anatomical score)", transform=ax_b.transAxes, fontsize=5.0, color=MUTED)
    for index, row in modes.iterrows():
        x = .05 + index * .39
        color = GREY if row.projection == "first" else ORANGE
        ax_b.add_patch(Rectangle((x, .045), .30, .085, transform=ax_b.transAxes, facecolor=color, edgecolor="none"))
        ax_b.text(x + .15, .087, f"{row.projection}: {row.direct_accuracy:.1%}", transform=ax_b.transAxes, ha="center", va="center", fontsize=5.0, color="white", fontweight="bold")

    methods = comparison.method.tolist()
    y = np.arange(len(methods))
    colors = [GREY, TEAL]
    ax_c.hlines(y, comparison.accuracy_low, comparison.accuracy_high, color=colors, lw=3.0, zorder=1)
    ax_c.scatter(comparison.accuracy, y, s=66, color=colors, edgecolor="white", linewidth=.75, zorder=3)
    for index, row in comparison.iterrows():
        label_y = index - .11 if index == 0 else index - .11
        ax_c.text(float(row.accuracy) + .035, label_y, f"{row.accuracy:.3f}", fontsize=5.9, fontweight="bold", color=INK)
        ax_c.text(.01, label_y - .16, f"macro-F1 {row.macro_f1:.3f}", fontsize=5.0, color=MUTED)
    ax_c.set(yticks=y, yticklabels=methods, xlim=(-.04, .82), xlabel="matched direct-root accuracy")
    ax_c.tick_params(axis="y", labelsize=5.25, length=0)
    v5.clean(ax_c, "x")
    ax_c.set_ylim(-.40, 1.30)
    v5.panel(ax_c, "c", "Labelled wheat adaptation improves matched direct-root states", "964 direct-root cells; fixed-bootstrap 95% intervals")
    ax_c.text(.99, .035, f"+{audit['matched_direct_root_subset']['accuracy_gain_percentage_points']:.1f} percentage points; supervised adapter", transform=ax_c.transAxes, ha="right", fontsize=5.0, color=RED, fontweight="bold")

    image = ax_d.imshow(normalised, cmap=LinearSegmentedColormap.from_list("wheat_adapter", ["#F7F9F9", "#B5DCD9", TEAL]), vmin=0, vmax=1, aspect="auto")
    ax_d.set(xticks=range(len(labels)), xticklabels=[compact_author_label(label) for label in labels], yticks=range(len(labels)), yticklabels=[compact_author_label(label) for label in labels], xlabel="predicted author state")
    ax_d.tick_params(axis="x", labelsize=5.0, rotation=35, length=0, pad=1.4)
    for tick in ax_d.get_xticklabels():
        tick.set_horizontalalignment("right")
    ax_d.tick_params(axis="y", labelsize=5.0, length=0, pad=1.4)
    for spine in ax_d.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_d, fraction=.025, pad=.018)
    colorbar.ax.tick_params(labelsize=5.0, length=1.1)
    v5.panel(ax_d, "d", "The adapted head resolves all 13 author labels", "Row-normalized locked-test confusion matrix; 1,433 cells; complete values in source TSV")

    y = np.arange(len(per_class))
    point_colors = [TEAL if value >= .65 else ORANGE for value in per_class["f1-score"]]
    ax_e.hlines(y, 0, per_class["f1-score"], color=LIGHT_GREY, lw=2.6, zorder=1)
    ax_e.scatter(per_class["f1-score"], y, s=21 + per_class.support.to_numpy() / 11, color=point_colors, edgecolor="white", linewidth=.48, zorder=3)
    for index, row in per_class.iterrows():
        ax_e.text(min(float(row["f1-score"]) + .036, 1.02), index, f"{row['f1-score']:.2f}", va="center", fontsize=5.0)
    ax_e.set(yticks=y, yticklabels=[compact_author_label(label) for label in per_class.author_label], xlim=(0, 1.10), xlabel="locked-test per-class F1")
    ax_e.tick_params(axis="y", labelsize=5.0, length=0, pad=1.0)
    v5.clean(ax_e, "x")
    v5.panel(ax_e, "e", "Rare and mixed root states remain visible", "Point area scales with class support; no author classes are hidden")

    ax_f.plot(history.epoch, history.fine_macro_f1, color=PURPLE, marker="o", markersize=4.4, markeredgecolor="white", markeredgewidth=.55, lw=1.25, label="validation macro-F1")
    ax_f.plot(history.epoch, history.fine_accuracy, color=TEAL, marker="o", markersize=4.1, markeredgecolor="white", markeredgewidth=.55, lw=1.05, label="validation accuracy")
    ax_f.axvline(best.epoch, color=ORANGE, lw=.85, ls="--")
    ax_f.annotate(f"selected\nepoch {int(best.epoch)}", xy=(best.epoch, best.fine_macro_f1), xytext=(best.epoch - 3.7, .46), arrowprops={"arrowstyle": "-|>", "lw": .62, "color": ORANGE}, fontsize=5.0, color=INK)
    ax_f.set(xticks=history.epoch.tolist(), ylim=(.16, .78), xlabel="training epoch", ylabel="validation score")
    ax_f.legend(loc="lower right", fontsize=5.0, frameon=False, handlelength=1.75)
    v5.clean(ax_f, "y")
    v5.panel(ax_f, "f", "Selection is isolated from locked testing", "Best validation epoch: 8; 13-class locked test: 62.25% accuracy and 0.6660 macro-F1")
    fig.text(.99, .012, "One study, supervised cell-level split: report as an adaptation module, not external validation.", ha="right", fontsize=5.0, color=RED, fontweight="bold")

    split_table = pd.DataFrame(
        [
            {"set": "train", "cells": audit["split"]["train_cells"]},
            {"set": "validation", "cells": audit["split"]["validation_cells"]},
            {"set": "locked_test", "cells": audit["split"]["test_cells"]},
        ]
    )
    mapping_table = pd.DataFrame(
        [
            {"quantity": "checkpoint_compatible_feature_fraction", "value": coverage["checkpoint_compatible_gene_fraction"]},
            {"quantity": "checkpoint_compatible_umi_fraction", "value": coverage["checkpoint_compatible_umi_fraction"]},
            {"quantity": "excluded_historical_barcode_overlap", "value": input_record["overlap_audit"]["exact_cs1_barcode_overlap_excluded"]},
        ]
    )
    export(
        fig,
        {
            "provenance_split": split_table,
            "mapping_contract": mapping_table,
            "frozen_projection_sensitivity": modes,
            "matched_direct_root_test_cells": matched,
            "matched_direct_root_bootstrap": bootstrap_table,
            "matched_direct_root_summary": comparison,
            "locked_test_confusion": confusion,
            "locked_test_per_class": per_class,
            "validation_history": history,
        },
    )
    for path in OUT.rglob("*.svg"):
        text = path.read_text(encoding="utf-8")
        path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")
    print(json.dumps({"figure": STEM, "test_cells": 1433, "matched_direct_cells": len(matched)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
