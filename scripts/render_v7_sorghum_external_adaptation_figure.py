from __future__ import annotations

"""Render the v7 data-led GSE297576 external-screen and adaptation main figure.

The page deliberately separates frozen external zero-shot behaviour from target
species adaptation. The hero is the matched recovery on a sealed library,
while the frozen external screen remains visible as the prerequisite stress
test rather than being quietly replaced by the adapted value.
"""

import hashlib
import json
from pathlib import Path

import anndata as ad
import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle
from sklearn.metrics import f1_score


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "plant_cellfm_submission_v7"
MAIN = OUT / "main"
SOURCE = OUT / "source_data"
ATLAS = ROOT / "outputs" / "external_validation" / "gse297576_bicolor_root" / "GSE297576_bicolor_root_author_atlas.h5ad"
FROZEN = ROOT / "outputs" / "external_validation" / "gse297576_bicolor_root" / "plantcellfm_frozen_bundle" / "predictions.csv"
ADAPTER = ROOT / "outputs" / "gse297576_sorghum_root_lora_adapter_4070_oughw_holdout" / "detailed_test" / "predictions.tsv"
FROZEN_AUDIT = ROOT / "release_metadata" / "gse297576_bicolor_root_frozen_external_audit_v1.json"
ADAPTER_AUDIT = ROOT / "release_metadata" / "gse297576_sorghum_root_lora_adapter_audit_v1.json"
ONTOLOGY = ROOT / "release_metadata" / "gse297576_bicolor_root_ontology_contract_v1.json"
PER_CLASS = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S26_GSE297576_sorghum_adapter_per_class.tsv"

INK = "#17232D"
MUTED = "#61778A"
GRID = "#D9E4E9"
TEAL = "#007C83"
BLUE = "#2E6FAD"
PURPLE = "#8064A7"
ORANGE = "#D97524"
RED = "#B34D5B"
GREY = "#A7B5BD"
PALE = "#F3F7F8"

LAYER_COLORS = {
    "atrichoblast": "#007C83", "cortex": "#6AA84F", "dividing cells": "#8064A7",
    "endodermis": "#2E6FAD", "exodermis": "#6C9BC4", "lateral root": "#C55A11",
    "meristem": "#8E7CC3", "pericycle": "#674EA7", "phloem": "#C27BA0",
    "root cap": "#F6B26B", "s-phase": "#A64D79", "sclerenchyma": "#7F8C8D",
    "stele": "#3D85C6", "trichoblast": "#CC0000", "xylem": "#274E13",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def setup() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 6.4, "axes.labelcolor": INK, "axes.edgecolor": INK, "axes.linewidth": 0.65,
        "xtick.color": INK, "ytick.color": INK, "xtick.major.width": 0.55, "ytick.major.width": 0.55,
        "svg.fonttype": "none", "pdf.fonttype": 42, "savefig.facecolor": "white",
    })
    MAIN.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)


def panel(ax: plt.Axes, letter: str, title: str, subtitle: str | None = None, *, letter_x: float = -0.07) -> None:
    ax.text(letter_x, 1.012, letter, transform=ax.transAxes, fontsize=8.3, fontweight="bold", va="bottom", color=INK)
    ax.text(0, 1.012, title, transform=ax.transAxes, fontsize=6.45, fontweight="bold", va="bottom", color=INK, clip_on=False)
    if subtitle:
        ax.text(0, 0.958, subtitle, transform=ax.transAxes, fontsize=5.0, va="bottom", color=MUTED)


def clean(ax: plt.Axes, axis: str | None = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if axis:
        ax.grid(axis=axis, color=GRID, linewidth=0.58, zorder=0)
    ax.tick_params(length=2.0, pad=1.8)


def bootstrap(frame: pd.DataFrame, label_column: str, *, iterations: int = 2000, seed: int = 20260801) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    truth = frame["expected_label"].to_numpy(dtype=str)
    predicted = frame[label_column].to_numpy(dtype=str)
    labels = sorted(set(truth.tolist()))
    rows: list[dict[str, float | int | str]] = []
    for iteration in range(iterations):
        sample = rng.integers(0, len(frame), len(frame))
        rows.append({
            "iteration": iteration,
            "method": label_column,
            "accuracy": float(np.mean(truth[sample] == predicted[sample])),
            "macro_f1": float(f1_score(truth[sample], predicted[sample], labels=labels, average="macro", zero_division=0)),
        })
    return pd.DataFrame(rows)


def exact_metrics(frame: pd.DataFrame, column: str) -> dict[str, float]:
    labels = sorted(set(frame.expected_label.astype(str)))
    return {
        "accuracy": float(np.mean(frame.expected_label.astype(str).to_numpy() == frame[column].astype(str).to_numpy())),
        "macro_f1": float(f1_score(frame.expected_label, frame[column], labels=labels, average="macro", zero_division=0)),
    }


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], dict[str, object], pd.DataFrame, pd.DataFrame]:
    frozen_audit = json.loads(FROZEN_AUDIT.read_text(encoding="utf-8"))
    adapter_audit = json.loads(ADAPTER_AUDIT.read_text(encoding="utf-8"))
    ontology = json.loads(ONTOLOGY.read_text(encoding="utf-8"))["labels"]
    atlas = ad.read_h5ad(ATLAS, backed="r")
    obs = atlas.obs.loc[:, ["cellBC", "celltype", "layer", "library"]].reset_index(drop=True).copy()
    obs["cell_id"] = obs["cellBC"].astype(str)
    umap = np.asarray(atlas.obsm["X_umap_author"])
    obs["UMAP1"] = umap[:, 0]
    obs["UMAP2"] = umap[:, 1]
    frozen = pd.read_csv(FROZEN, dtype={"cell_id": str})
    adapter = pd.read_csv(ADAPTER, sep="\t", dtype=str)
    adapter = adapter.merge(obs, on="cell_id", how="left", validate="one_to_one")
    if adapter[["celltype", "layer", "library", "UMAP1", "UMAP2"]].isna().any().any():
        raise ValueError("The sealed adapter-test prediction table does not exactly join the author atlas.")
    frozen_test = adapter[["cell_id", "celltype", "layer", "library", "UMAP1", "UMAP2"]].merge(
        frozen[["cell_id", "fine_label"]], on="cell_id", how="left", validate="one_to_one"
    )
    if frozen_test["fine_label"].isna().any():
        raise ValueError("Frozen prediction table is missing sealed adapter-test cells.")
    adapter["expected_label"] = adapter["celltype"].map(lambda value: ontology[str(value)]["model_label"])
    adapter["adapter_broad_prediction"] = adapter["pred_fine"].map(
        lambda value: ontology[str(value)]["model_label"] if str(value) in ontology else None
    ).fillna("not_in_frozen_ontology")
    frozen_test["expected_label"] = frozen_test["celltype"].map(lambda value: ontology[str(value)]["model_label"])
    frozen_test["frozen_broad_prediction"] = frozen_test["fine_label"].astype(str)
    adapter_eval = adapter.loc[adapter["expected_label"].notna()].copy()
    frozen_eval = frozen_test.loc[frozen_test["expected_label"].notna()].copy()
    if adapter_eval.cell_id.tolist() != frozen_eval.cell_id.tolist():
        raise ValueError("Frozen and adapter matched recovery cells differ after ontology filtering.")
    raw_to_layer = obs.groupby("celltype", observed=True)["layer"].agg(lambda values: values.mode().iloc[0]).to_dict()
    adapter["predicted_layer"] = adapter["pred_fine"].map(raw_to_layer).fillna("not mapped")
    return adapter, frozen_test, frozen_audit, adapter_audit, adapter_eval, frozen_eval


def export(fig: plt.Figure, stem: str, tables: dict[str, pd.DataFrame]) -> None:
    for name, table in tables.items():
        table.to_csv(SOURCE / f"{stem}_{name}.tsv", sep="\t", index=False)
    for suffix, options in (("svg", {}), ("pdf", {}), ("png", {"dpi": 400}), ("tiff", {"dpi": 600})):
        fig.savefig(MAIN / f"{stem}.{suffix}", bbox_inches="tight", pad_inches=0.025, **options)
    plt.close(fig)


def render() -> None:
    adapter, frozen_test, frozen_audit, adapter_audit, adapter_eval, frozen_eval = load_data()
    frozen_bootstrap = bootstrap(frozen_eval, "frozen_broad_prediction")
    adapter_bootstrap = bootstrap(adapter_eval, "adapter_broad_prediction")
    boot = pd.concat([frozen_bootstrap, adapter_bootstrap], ignore_index=True)
    metric_rows = []
    for name, frame, column, color in (
        ("Frozen root head", frozen_eval, "frozen_broad_prediction", ORANGE),
        ("Sorghum LoRA adapter", adapter_eval, "adapter_broad_prediction", TEAL),
    ):
        point = exact_metrics(frame, column)
        subset = boot.loc[boot.method.eq(column)]
        metric_rows.append({
            "method": name, "metric": "accuracy", "point": point["accuracy"],
            "ci_low": float(subset.accuracy.quantile(0.025)), "ci_high": float(subset.accuracy.quantile(0.975)), "colour": color,
        })
        metric_rows.append({
            "method": name, "metric": "macro-F1", "point": point["macro_f1"],
            "ci_low": float(subset.macro_f1.quantile(0.025)), "ci_high": float(subset.macro_f1.quantile(0.975)), "colour": color,
        })
    metric_table = pd.DataFrame(metric_rows)
    classes = pd.read_csv(PER_CLASS, sep="\t").sort_values("f1", ascending=True).reset_index(drop=True)

    fig = plt.figure(figsize=(7.25, 6.05))
    grid = fig.add_gridspec(3, 12, height_ratios=(1.03, 1.22, 1.0), left=0.055, right=0.988, bottom=0.075, top=0.955, hspace=0.80, wspace=0.72)
    ax_a = fig.add_subplot(grid[:2, :6])
    ax_b = fig.add_subplot(grid[:2, 6:])
    ax_c = fig.add_subplot(grid[2, :3])
    ax_d = fig.add_subplot(grid[2, 3:9])
    ax_e = fig.add_subplot(grid[2, 9:])

    # Hero: the evidence ladder from untouched frozen screen to sealed-library adaptation.
    ax_a.set_axis_off()
    panel(ax_a, "a", "Sealed-library adaptation restores external annotation", "Frozen screen and label-supervised adaptation stay on separate evidence tiers")
    boxes = [
        (0.02, 0.66, 0.88, 0.26, ORANGE, "Frozen external screen", "19,316 high-sorghum root cells\nno target labels during inference"),
        (0.02, 0.31, 0.88, 0.26, TEAL, "Locked-library Sorghum adapter", "OUGHX + OWGSC train  |  OWGSB validation\nOUGHW sealed test: 4,150 cells, 27 states"),
    ]
    for x, y, w, h, color, title, subtitle in boxes:
        ax_a.add_patch(Rectangle((x, y), w, h, transform=ax_a.transAxes, facecolor=PALE, edgecolor=color, linewidth=1.0))
        ax_a.add_patch(Rectangle((x, y + h - 0.045), w, 0.045, transform=ax_a.transAxes, facecolor=color, edgecolor="none"))
        ax_a.text(x + 0.035, y + h - 0.085, title, transform=ax_a.transAxes, fontsize=6.4, fontweight="bold", color=INK)
        ax_a.text(x + 0.035, y + 0.055, subtitle, transform=ax_a.transAxes, fontsize=5.15, color=MUTED, va="bottom")
    ax_a.add_patch(FancyArrowPatch((0.46, 0.645), (0.46, 0.585), transform=ax_a.transAxes, arrowstyle="-|>", mutation_scale=10, lw=0.85, color=INK))
    ax_a.text(0.49, 0.613, "LoRA; rank 8\n3.03M trainable", transform=ax_a.transAxes, fontsize=4.9, color=MUTED, va="center")
    frozen = frozen_audit["metrics"]
    recovery = adapter_audit["matched_broad_identity_recovery_on_sealed_test_library"]
    chips = [
        (0.04, 0.105, "frozen, full external", f"{frozen['all_evaluable_accuracy']:.1%} accuracy\n{frozen['unassigned_prediction_rate_evaluable']:.1%} Unknow", ORANGE),
        (0.47, 0.105, "matched OUGHW identities", f"{recovery['sorghum_lora_adapter']['accuracy']:.1%} accuracy\n+{recovery['absolute_accuracy_gain']:.1%} absolute", TEAL),
    ]
    for x, y, label, value, color in chips:
        ax_a.plot([x, x + 0.06], [y + 0.07, y + 0.07], transform=ax_a.transAxes, color=color, lw=3.3, solid_capstyle="round")
        ax_a.text(x + 0.08, y + 0.105, label, transform=ax_a.transAxes, fontsize=4.7, color=MUTED)
        ax_a.text(x + 0.08, y, value, transform=ax_a.transAxes, fontsize=6.2, color=INK, fontweight="bold", va="bottom")
    ax_a.text(0.02, 0.018, "Target-species adaptation; not a zero-shot or third-party ranking. Raw 27-state accuracy 76.02%, macro-F1 0.7535; test labels never used for early stopping.", transform=ax_a.transAxes, fontsize=4.1, color=RED)

    # Paired maps preserve the biological granularity without an unreadable 27-state legend.
    for column, title, x_shift in (("layer", "Author layer", 0.0), ("pred_coarse", "Adapter layer", 0.5)):
        inset = ax_b.inset_axes([x_shift + 0.015, 0.12, 0.45, 0.79])
        values = adapter[column].astype(str) if column == "layer" else adapter["pred_coarse"].astype(str)
        for state in sorted(values.unique()):
            part = adapter.loc[values.eq(state)]
            inset.scatter(part.UMAP1, part.UMAP2, s=1.7, color=LAYER_COLORS.get(state, GREY), linewidth=0, alpha=0.75, rasterized=True)
        inset.set(xticks=[], yticks=[], title=title)
        inset.title.set_fontsize(5.45)
        inset.title.set_fontweight("bold")
        for spine in inset.spines.values():
            spine.set_visible(False)
    ax_b.set_axis_off()
    panel(ax_b, "b", "Author topology is preserved in the sealed library", "OUGHW only; each point is one held-out cell; color key is shared across author and prediction", letter_x=-0.035)
    legend_states = ["cortex", "stele", "xylem", "phloem", "endodermis", "atrichoblast", "trichoblast", "root cap", "meristem", "s-phase"]
    for index, state in enumerate(legend_states):
        row, col = divmod(index, 5)
        x, y = 0.03 + col * 0.19, 0.035 + row * 0.042
        ax_b.scatter([x], [y], transform=ax_b.transAxes, s=10, color=LAYER_COLORS[state], clip_on=False)
        ax_b.text(x + 0.018, y, state, transform=ax_b.transAxes, fontsize=4.15, va="center", color=INK)

    # Matched, bootstrapped point estimates are the compact quantitative check.
    y_positions = {"Frozen root head": 0.0, "Sorghum LoRA adapter": 1.0}
    for metric, offset, marker in (("accuracy", -0.16, "o"), ("macro-F1", 0.16, "s")):
        rows = metric_table.loc[metric_table.metric.eq(metric)]
        for row in rows.itertuples(index=False):
            y = y_positions[row.method] + offset
            ax_c.hlines(y, row.ci_low, row.ci_high, color=row.colour, lw=1.25, zorder=2)
            ax_c.scatter(row.point, y, s=34, marker=marker, color=row.colour, edgecolor="white", linewidth=0.55, zorder=3)
            ax_c.text(row.ci_high + 0.013, y, f"{row.point:.3f}", va="center", fontsize=4.25, color=INK)
    ax_c.set(yticks=[0, 1], yticklabels=["frozen", "adapter"], xlim=(0, 1.05), ylim=(-0.34, 1.34), xlabel="matched broad-identity score")
    ax_c.tick_params(axis="y", labelsize=5.2, length=0)
    clean(ax_c, "x")
    panel(ax_c, "c", "Matched recovery", "points; 95% cell bootstrap")
    ax_c.text(0.00, -0.37, "circles accuracy; squares macro-F1\n3,549 same test cells", transform=ax_c.transAxes, fontsize=4.5, color=MUTED)

    # Full 27-state test detail is compact enough to remain inspectable.
    y = np.arange(len(classes))
    bars = ax_d.barh(y, classes.f1, color=[TEAL if value >= 0.75 else BLUE if value >= 0.60 else ORANGE for value in classes.f1], height=0.61)
    for index, row in enumerate(classes.itertuples(index=False)):
        ax_d.text(min(row.f1 + 0.015, 0.98), index, f"{row.f1:.2f}", va="center", fontsize=3.95, color=INK)
    ax_d.set(yticks=y, yticklabels=[str(value).replace("cortical ", "cort. ").replace("elongating ", "elong. ") for value in classes.author_annotation], xlim=(0, 1.04), xlabel="per-state F1")
    ax_d.tick_params(axis="y", labelsize=4.55, length=0, pad=1.0)
    clean(ax_d, "x")
    panel(ax_d, "d", "Every author state remains visible", "27-state OUGHW test", letter_x=-0.035)

    coverage = frozen_audit["orthology_contract"]["coverage"]
    inference = frozen_audit["frozen_inference"]["preprocessing_stats"]
    stages = [
        ("author genes", coverage["source_gene_count"], GREY),
        ("orthogroup mapped", coverage["source_genes_with_arabidopsis_target"], BLUE),
        ("checkpoint represented", inference["checkpoint_vocabulary"]["represented_gene_count"], TEAL),
    ]
    max_value = stages[0][1]
    for index, (label, count, color) in enumerate(stages):
        y0 = 0.72 - index * 0.26
        ax_e.barh(y0, count / max_value, height=0.105, color=color, zorder=2)
        ax_e.text(0, y0 + 0.085, label, fontsize=4.85, color=MUTED, va="bottom")
        ax_e.text(1.01, y0, f"{count:,}", fontsize=5.4, color=INK, fontweight="bold", va="center")
    ax_e.set(xlim=(0, 1.30), ylim=(0.02, 0.98), xticks=[], yticks=[])
    for spine in ax_e.spines.values():
        spine.set_visible(False)
    panel(ax_e, "e", "Feature-transfer audit", "Author-pinned 10-species orthogroups", letter_x=-0.035)
    ax_e.text(0.0, 0.03, "62.60% source features map; 97.37%\nof retained targets are in checkpoint vocabulary.", transform=ax_e.transAxes, fontsize=4.55, color=RED)

    full_prediction = adapter[["cell_id", "library", "celltype", "layer", "pred_fine", "pred_coarse", "predicted_layer", "UMAP1", "UMAP2"]].copy()
    full_prediction["fine_correct"] = full_prediction.celltype.eq(full_prediction.pred_fine)
    full_prediction["coarse_correct"] = full_prediction.layer.eq(full_prediction.pred_coarse)
    provenance = pd.DataFrame([
        {"field": "frozen_external_role", "value": "GSE297576 author-labelled Sorghum bicolor root; no target labels during inference"},
        {"field": "adapter_train_libraries", "value": "OUGHX; OWGSC"},
        {"field": "adapter_validation_library", "value": "OWGSB"},
        {"field": "sealed_test_library", "value": "OUGHW"},
        {"field": "adapter_selection", "value": "validation fine macro-F1; epoch 10"},
        {"field": "claim_boundary", "value": "within-atlas library-held-out species adaptation; not zero-shot or third-party ranking"},
    ])
    export(fig, "plant_cellfm_v7_fig5_sorghum_external_adaptation", {
        "matched_recovery_bootstrap": boot,
        "matched_recovery_metrics": metric_table.drop(columns="colour"),
        "sealed_test_predictions_and_umap": full_prediction,
        "sealed_test_per_class": classes,
        "feature_transfer_audit": pd.DataFrame(stages, columns=["stage", "gene_count", "colour_role"]),
        "evidence_provenance": provenance,
        "claim_boundary": pd.DataFrame([{"boundary": adapter_audit["claim_boundary"]}]),
    })


def main() -> None:
    setup()
    render()
    outputs = [MAIN / f"plant_cellfm_v7_fig5_sorghum_external_adaptation.{suffix}" for suffix in ("svg", "pdf", "png", "tiff")]
    print(json.dumps({"figure": "v7_fig5_sorghum_external_adaptation", "outputs": {path.suffix: sha256(path) for path in outputs}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
