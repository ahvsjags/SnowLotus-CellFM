from __future__ import annotations

"""Render Extended Data 6: the labelled GSE270140 secondary-root adapter audit."""

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


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_v5_top_journal_figures as v5  # noqa: E402


OUT = ROOT / "figures" / "plant_cellfm_submission_v5"
EXTENDED = OUT / "extended_data"
SOURCE = OUT / "source_data"
ADAPTER_ROOT = ROOT / "outputs" / "gse270140_secondary_root_lora_adapter_4070"
MAPPING = ROOT / "release_metadata" / "gse270140_external_label_mapping_v1.tsv"
BASE = ROOT / "outputs" / "external_validation" / "gse270140" / "annotation_bundle_srp169576_1024" / "predictions.csv"
AUDIT = ROOT / "release_metadata" / "gse270140_secondary_root_adapter_audit_v1.json"
STEM = "plant_cellfm_v5_ed_fig6_secondary_root_adapter"
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


def short_label(label: str) -> str:
    replacements = {
        "Conductive phloem parenchyma": "Conductive\nphloem par.",
        "Mature phloem parenchyma": "Mature\nphloem par.",
        "Mature xylem parenchyma": "Mature\nxylem par.",
        "Maturing xylem parenchyma": "Maturing\nxylem par.",
        "Young xylem parenchyma": "Young\nxylem par.",
        "Late differentiating vessel": "Late\nvessel",
        "Vessel identity cell/expanding vessel": "Expanding\nvessel",
        "Lateral root primordium/meristem": "LR\nprimordium",
        "Myrosin idioblasts": "Myrosin\nidioblasts",
        "Vascular cambium": "Vascular\ncambium",
        "Companion cell": "Companion\ncell",
        "Sieve element": "Sieve\nelement",
    }
    return replacements.get(label, label)


def compact_label(label: str) -> str:
    """Retain all author classes while keeping the 14-class audit printable."""
    replacements = {
        "Companion cell": "Companion",
        "Conductive phloem parenchyma": "Conductive",
        "Fiber": "Fiber",
        "Late differentiating vessel": "Late vessel",
        "Lateral root primordium/meristem": "LR primordium",
        "Mature phloem parenchyma": "Mature phloem",
        "Mature xylem parenchyma": "Mature xylem",
        "Maturing xylem parenchyma": "Maturing xylem",
        "Myrosin idioblasts": "Myrosin",
        "Periderm": "Periderm",
        "Sieve element": "Sieve",
        "Vascular cambium": "Vascular cambium",
        "Vessel identity cell/expanding vessel": "Expanding vessel",
        "Young xylem parenchyma": "Young xylem",
    }
    return replacements.get(label, label)


def bootstrap_interval(correct: np.ndarray, true: np.ndarray, predicted: np.ndarray, *, seed: int) -> pd.DataFrame:
    labels = np.asarray(["Phloem", "Root stele", "Xylem"], dtype=object)
    rng = np.random.default_rng(seed)
    rows: list[dict[str, float | int]] = []
    n = len(correct)
    for iteration in range(3000):
        take = rng.integers(0, n, n)
        sampled_true = true[take]
        sampled_pred = predicted[take]
        f1_values = []
        for label in labels:
            tp = int(np.sum((sampled_true == label) & (sampled_pred == label)))
            fp = int(np.sum((sampled_true != label) & (sampled_pred == label)))
            fn = int(np.sum((sampled_true == label) & (sampled_pred != label)))
            denominator = 2 * tp + fp + fn
            f1_values.append(0.0 if denominator == 0 else 2 * tp / denominator)
        rows.append(
            {
                "iteration": iteration,
                "accuracy": float(correct[take].mean()),
                "macro_f1": float(np.mean(f1_values)),
            }
        )
    return pd.DataFrame(rows)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    mapping = pd.read_csv(MAPPING, sep="\t", dtype=str).fillna("")
    detailed = json.loads((ADAPTER_ROOT / "detailed_test" / "detailed_metrics.json").read_text(encoding="utf-8"))
    predictions = pd.read_csv(ADAPTER_ROOT / "detailed_test" / "predictions.tsv", sep="\t", dtype=str)
    base = pd.read_csv(BASE, dtype={"cell_id": str})
    history = pd.DataFrame(json.loads((ADAPTER_ROOT / "history.json").read_text(encoding="utf-8"))["epochs"])
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    predictions = predictions.merge(
        mapping[["source_label", "mapped_model_label", "evaluation_tier"]],
        left_on="true_fine",
        right_on="source_label",
        how="left",
        validate="many_to_one",
    ).rename(columns={"mapped_model_label": "true_semantic", "evaluation_tier": "true_tier"})
    predictions = predictions.merge(
        mapping[["source_label", "mapped_model_label"]],
        left_on="pred_fine",
        right_on="source_label",
        how="left",
        validate="many_to_one",
        suffixes=("", "_pred"),
    ).rename(columns={"mapped_model_label": "adapter_semantic"})
    predictions = predictions.merge(
        base[["cell_id", "fine_label"]],
        on="cell_id",
        how="left",
        validate="one_to_one",
    ).rename(columns={"fine_label": "base_semantic"})
    if predictions[["true_semantic", "true_tier", "base_semantic"]].isna().any().any():
        raise ValueError("The secondary-root adapter figure requires complete frozen mapping and base predictions.")
    shared = predictions[predictions.true_tier.eq("shared_state")].copy()
    class_rows = []
    for label, values in detailed["summary"]["fine"]["classification_report"].items():
        if isinstance(values, dict) and "f1-score" in values and label not in {"macro avg", "weighted avg", "micro avg", "samples avg"}:
            class_rows.append({"label": label, "support": int(values["support"]), "precision": float(values["precision"]), "recall": float(values["recall"]), "f1": float(values["f1-score"])})
    per_class = pd.DataFrame(class_rows).sort_values("f1", ascending=True, kind="mergesort").reset_index(drop=True)
    confusion = pd.read_csv(ADAPTER_ROOT / "detailed_test" / "fine_confusion_matrix.tsv", sep="\t")
    semantic_record = audit["matched_three_state_semantic_recovery"]
    semantic = pd.DataFrame(
        [
            {"method": "Frozen base checkpoint", **semantic_record["frozen_base_checkpoint"]},
            {"method": "Secondary-root adapter", **semantic_record["secondary_root_adapter"]},
        ]
    )
    return predictions, shared, per_class, confusion, history, {"audit": audit, "semantic": semantic}


def export(fig: plt.Figure, tables: dict[str, pd.DataFrame]) -> None:
    EXTENDED.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{STEM}_{name}.tsv", sep="\t", index=False)
    v5.base.enforce_minimum_text_size(fig)
    for suffix, kwargs in (("svg", {}), ("pdf", {}), ("png", {"dpi": 350}), ("tiff", {"dpi": 600})):
        fig.savefig(EXTENDED / f"{STEM}.{suffix}", bbox_inches="tight", pad_inches=0.025, **kwargs)
    plt.close(fig)


def main() -> None:
    v5.setup()
    predictions, shared, per_class, confusion, history, records = load_data()
    semantic = records["semantic"]
    base_correct = shared.base_semantic.to_numpy(dtype=str) == shared.true_semantic.to_numpy(dtype=str)
    adapter_pred = shared.adapter_semantic.fillna("not_in_frozen_ontology").to_numpy(dtype=str)
    adapter_correct = adapter_pred == shared.true_semantic.to_numpy(dtype=str)
    base_bootstrap = bootstrap_interval(base_correct, shared.true_semantic.to_numpy(dtype=str), shared.base_semantic.to_numpy(dtype=str), seed=20260801)
    adapter_bootstrap = bootstrap_interval(adapter_correct, shared.true_semantic.to_numpy(dtype=str), adapter_pred, seed=20260802)
    bootstrap = pd.concat(
        [base_bootstrap.assign(method="Frozen base checkpoint"), adapter_bootstrap.assign(method="Secondary-root adapter")],
        ignore_index=True,
    )
    intervals = bootstrap.groupby("method", as_index=False).agg(
        accuracy_low=("accuracy", lambda values: float(np.quantile(values, 0.025))),
        accuracy_high=("accuracy", lambda values: float(np.quantile(values, 0.975))),
        macro_f1_low=("macro_f1", lambda values: float(np.quantile(values, 0.025))),
        macro_f1_high=("macro_f1", lambda values: float(np.quantile(values, 0.975))),
    )
    semantic = semantic.merge(intervals, on="method", how="left", validate="one_to_one")

    fig = plt.figure(figsize=(7.25, 6.65))
    grid = fig.add_gridspec(
        3,
        6,
        height_ratios=(0.78, 1.45, 0.92),
        width_ratios=(0.94, 1.03, 1.04, 1.04, 1.04, 1.04),
        left=0.06,
        right=0.988,
        bottom=0.065,
        top=0.962,
        hspace=0.68,
        wspace=0.58,
    )
    ax_a = fig.add_subplot(grid[0, :3])
    ax_b = fig.add_subplot(grid[0, 3:])
    ax_c = fig.add_subplot(grid[1, :3])
    ax_d = fig.add_subplot(grid[1, 3:])
    ax_e = fig.add_subplot(grid[2, :3])
    ax_f = fig.add_subplot(grid[2, 3:])

    ax_a.set_axis_off()
    v5.panel(ax_a, "a", "A context-specific state layer augments the frozen checkpoint", "GSE270140/GSM8335426 author labels: 11,760 cells, 14 states, one secondary-root sample")
    stages = [
        (0.02, 0.53, 0.22, 0.28, "frozen root\ncheckpoint", "13 root states", GREY),
        (0.37, 0.53, 0.22, 0.28, "LoRA-mode\nadaptation", "80% labelled cells", ORANGE),
        (0.72, 0.53, 0.22, 0.28, "locked test\nreport", "20%: 2,352 cells", TEAL),
    ]
    for x, y, width, height, headline, subline, color in stages:
        ax_a.add_patch(Rectangle((x, y), width, height, transform=ax_a.transAxes, facecolor="#F4F7F8", edgecolor=color, linewidth=0.82, clip_on=False))
        ax_a.add_patch(Rectangle((x, y + height - 0.052), width, 0.052, transform=ax_a.transAxes, facecolor=color, edgecolor=color, clip_on=False))
        ax_a.text(x + width / 2, y + 0.158, headline, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.35, fontweight="bold", color=INK)
        ax_a.text(x + width / 2, y + 0.055, subline, transform=ax_a.transAxes, ha="center", va="center", fontsize=5.0, color=MUTED)
    for left, right in zip(stages[:-1], stages[1:], strict=True):
        ax_a.add_patch(FancyArrowPatch((left[0] + left[2] + .01, .67), (right[0] - .015, .67), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=8, lw=.75, color=MUTED))
    split_x = [0.10, 0.41, 0.72]
    split_labels = [("train", 8232, ORANGE), ("validation", 1176, PURPLE), ("test", 2352, TEAL)]
    total = sum(value for _, value, _ in split_labels)
    cursor = .02
    for label, value, color in split_labels:
        width = .92 * value / total
        ax_a.add_patch(Rectangle((cursor, .16), width, .10, transform=ax_a.transAxes, facecolor=color, edgecolor="white", linewidth=.55))
        ax_a.text(cursor + width / 2, .10, f"{label}: {value:,}", transform=ax_a.transAxes, ha="center", fontsize=5.0, color=INK)
        cursor += width
    ax_a.text(.02, .33, "The new result is supervised adaptation, not a replacement for strict zero-shot transfer.", transform=ax_a.transAxes, fontsize=5.0, color=RED, fontweight="bold")

    methods = semantic.method.tolist()
    y = np.arange(len(methods))
    colors = [GREY, TEAL]
    ax_b.hlines(y, semantic.accuracy_low, semantic.accuracy_high, color=colors, lw=2.6, zorder=1)
    ax_b.scatter(semantic.accuracy, y, s=55, color=colors, edgecolor="white", linewidth=.7, zorder=3)
    for index, row in semantic.iterrows():
        ax_b.text(min(float(row.accuracy) + .04, .99), index + .10, f"{row.accuracy:.3f}", fontsize=5.55, fontweight="bold", color=INK)
        ax_b.text(.01, index - .18, f"macro-F1 {row.macro_f1:.3f}", fontsize=5.0, color=MUTED)
    ax_b.set(yticks=y, yticklabels=methods, xlim=(-.05, 1.05), xlabel="matched three-state semantic accuracy")
    ax_b.tick_params(axis="y", labelsize=5.1, length=0)
    v5.clean(ax_b, "x")
    v5.panel(ax_b, "b", "Labelled adaptation recovers held-out vascular states", "1,885 shared-state cells; fixed-bootstrap 95% intervals")
    ax_b.text(.99, -.36, "Base head: 2.0%  |  Adapter: 90.9%  |  +88.9 percentage points", transform=ax_b.transAxes, ha="right", fontsize=5.0, color=RED, fontweight="bold")

    labels = confusion.true_label.tolist()
    matrix = confusion.drop(columns="true_label").to_numpy(dtype=float)
    row_sum = matrix.sum(axis=1, keepdims=True)
    normalised = np.divide(matrix, row_sum, out=np.zeros_like(matrix), where=row_sum > 0)
    image = ax_c.imshow(normalised, cmap=LinearSegmentedColormap.from_list("adapter", ["#F6F8F9", "#B9DFDC", TEAL]), vmin=0, vmax=1, aspect="auto")
    ax_c.set(xticks=range(len(labels)), xticklabels=[compact_label(label) for label in labels], yticks=range(len(labels)), yticklabels=[compact_label(label) for label in labels], xlabel="predicted author label")
    ax_c.tick_params(axis="x", labelsize=5.0, rotation=40, length=0, pad=1.4)
    for tick in ax_c.get_xticklabels():
        tick.set_horizontalalignment("right")
    ax_c.tick_params(axis="y", labelsize=5.0, length=0, pad=1.4)
    for spine in ax_c.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax_c, fraction=.032, pad=.02)
    colorbar.ax.tick_params(labelsize=5.0, length=1.2)
    v5.panel(ax_c, "c", "All 14 secondary-root states resolve\non the locked test", "Row-normalized locked-test matrix; complete values in source TSV")

    display = per_class.copy()
    y = np.arange(len(display))
    ax_d.hlines(y, 0, display.f1, color=LIGHT_GREY, lw=2.6, zorder=1)
    ax_d.scatter(display.f1, y, s=26 + display.support.to_numpy() / 18, color=[TEAL if value >= .84 else ORANGE for value in display.f1], edgecolor="white", linewidth=.5, zorder=3)
    for index, row in display.iterrows():
        ax_d.text(min(float(row.f1) + .038, 1.0), index, f"{row.f1:.2f}", va="center", fontsize=5.0)
    compact_f1_labels = {
        "Companion cell": "Companion",
        "Conductive phloem parenchyma": "Conductive",
        "Fiber": "Fiber",
        "Late differentiating vessel": "Late vessel",
        "Lateral root primordium/meristem": "LR prim.",
        "Mature phloem parenchyma": "Mature phl.",
        "Mature xylem parenchyma": "Mature xyl.",
        "Maturing xylem parenchyma": "Maturing xyl.",
        "Myrosin idioblasts": "Myrosin",
        "Periderm": "Periderm",
        "Sieve element": "Sieve",
        "Vascular cambium": "Cambium",
        "Vessel identity cell/expanding vessel": "Expanding vsl.",
        "Young xylem parenchyma": "Young xyl.",
    }
    # Reserve an in-panel label strip so the secondary-root names cannot
    # intrude into the neighbouring confusion-matrix colourbar.
    f1_labels = [compact_f1_labels.get(str(label), compact_label(label)) for label in display.label]
    ax_d.set(yticks=y, yticklabels=[], xlim=(-.32, 1.12), xlabel="held-out per-class F1")
    ax_d.tick_params(axis="y", length=0)
    for index, label in enumerate(f1_labels):
        ax_d.text(-.305, index, label, va="center", ha="left", fontsize=5.0, color=INK)
    v5.clean(ax_d, "x")
    v5.panel(ax_d, "d", "Per-class F1 preserves\nrare-state visibility", "Point area scales with test-cell support; no classes are omitted")

    ax_e.plot(history.epoch, history.fine_macro_f1, color=PURPLE, marker="o", markersize=4.7, markeredgecolor="white", markeredgewidth=.6, lw=1.3, label="validation macro-F1")
    ax_e.plot(history.epoch, history.fine_accuracy, color=TEAL, marker="o", markersize=4.2, markeredgecolor="white", markeredgewidth=.6, lw=1.05, label="validation accuracy")
    best = history.loc[history.fine_macro_f1.idxmax()]
    ax_e.axvline(best.epoch, color=ORANGE, lw=.85, ls="--")
    ax_e.annotate(f"selected epoch {int(best.epoch)}", xy=(best.epoch, best.fine_macro_f1), xytext=(best.epoch - 3.4, .48), arrowprops={"arrowstyle": "-|>", "lw": .65, "color": ORANGE}, fontsize=5.0, color=INK)
    ax_e.set(xticks=history.epoch.tolist(), ylim=(.20, .86), xlabel="training epoch", ylabel="validation score")
    ax_e.legend(loc="lower right", fontsize=5.0, frameon=False, handlelength=1.8)
    v5.clean(ax_e, "y")
    v5.panel(ax_e, "e", "Validation plateaus before\nlocked-test evaluation", "Best checkpoint is selected exclusively by validation macro-F1")

    ax_f.set_axis_off()
    v5.panel(ax_f, "f", "Calibrated held-out results\nsupport review-aware use", "Reported separately from strict transfer and from label-free external execution")
    rows = [
        ("fine accuracy", 0.8397, TEAL),
        ("fine macro-F1", 0.8447, PURPLE),
        ("correct mean confidence", .8948, BLUE),
        ("incorrect mean confidence", .7024, ORANGE),
    ]
    for index, (label, value, color) in enumerate(rows):
        y0 = .78 - index * .17
        ax_f.text(.02, y0 + .055, label, transform=ax_f.transAxes, fontsize=5.0, color=MUTED, va="center")
        ax_f.add_patch(Rectangle((.38, y0), .51, .10, transform=ax_f.transAxes, facecolor="#EDF2F4", edgecolor="none"))
        ax_f.add_patch(Rectangle((.38, y0), .51 * value, .10, transform=ax_f.transAxes, facecolor=color, edgecolor="none"))
        ax_f.text(.93, y0 + .05, f"{value:.3f}", transform=ax_f.transAxes, fontsize=5.15, fontweight="bold", va="center", ha="left")
    ax_f.text(.02, .05, "Test evaluator: 2,352 cells; original one-sample study design is retained in the record.", transform=ax_f.transAxes, fontsize=5.0, color=RED)

    export(
        fig,
        {
            "test_predictions": predictions,
            "shared_state_test_predictions": shared,
            "semantic_recovery": semantic,
            "semantic_bootstrap": bootstrap,
            "per_class_f1": per_class,
            "fine_confusion_matrix": confusion,
            "validation_history": history,
            "split_summary": pd.DataFrame([{"train_cells": 8232, "validation_cells": 1176, "test_cells": 2352, "seed": 20260801, "selection_epoch": 7}]),
        },
    )
    for path in OUT.rglob("*.svg"):
        text = path.read_text(encoding="utf-8")
        path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")
    print(json.dumps({"figure": STEM, "held_out_cells": len(predictions), "shared_state_cells": len(shared)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
