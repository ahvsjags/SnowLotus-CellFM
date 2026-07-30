from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


UNKNOWN_ONTOLOGY = "unknown_or_unannotated"


def canonicalize_species_label(label: Any) -> str:
    return " ".join(str(label).replace("_", " ").split())


def label_text(label: Any) -> str:
    value = str(label or "").strip()
    value = value.replace("_", " ").replace("-", " ").replace("/", " ")
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    value = re.sub(r"[^0-9A-Za-z]+", " ", value)
    return " ".join(value.lower().split())


def canonical_ontology(label: Any) -> str:
    text = label_text(label)
    if not text:
        return UNKNOWN_ONTOLOGY
    if text.isdigit() or re.fullmatch(r"rna\s*\d+", text):
        return UNKNOWN_ONTOLOGY
    if any(token in text for token in ("unannotated", "unknown", "unknow", "not assigned")):
        return UNKNOWN_ONTOLOGY
    if "hydathode" in text:
        return "hydathode"
    if "idioblast" in text or "glandular" in text or "secretory" in text:
        return "secretory_or_specialized_epidermis"
    if "root hair" in text or "trichoblast" in text:
        return "root_hair_or_trichoblast"
    if "atrichoblast" in text or "non hair" in text or "nonhair" in text:
        return "nonhair_or_atrichoblast"
    if "lateral root cap" in text:
        return "lateral_root_cap"
    if "root cap" in text or "columella" in text:
        return "root_cap"
    if "cortex" in text or "cortical" in text:
        return "cortex"
    if "endodermis" in text or "endodermal" in text:
        return "endodermis"
    if "pericycle" in text or "pericyle" in text or "pericylce" in text:
        return "pericycle"
    if "xylem" in text:
        return "xylem"
    if "phloem" in text or "companion" in text or "sieve" in text:
        return "phloem"
    if "procamb" in text:
        return "procambium"
    if "vascular" in text or "vasculature" in text or "stele" in text:
        return "vascular_stele"
    if "meristem" in text or "stem cell niche" in text or text == "scn":
        return "meristem_or_stem_cell_niche"
    if "mesophyll" in text:
        return "mesophyll"
    if "guard" in text or "stomatal" in text or "stoma" in text:
        return "guard_or_stomatal_cell"
    if "epiderm" in text or "pavement" in text:
        return "epidermis"
    if "s phase" in text or "g2" in text or "g1" in text or "cell cycle" in text:
        return "cell_cycle_state"
    if "callus" in text:
        return "callus"
    if "parenchyma" in text:
        return "parenchyma"
    if "precursor" in text:
        return "developmental_precursor"
    return text.replace(" ", "_")


def pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{100 * value:.2f}%"


def num(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def normalize_embeddings(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-8)


def macro_f1_score(true: np.ndarray, pred: np.ndarray) -> float:
    labels = sorted(set(true.tolist()) | set(pred.tolist()))
    if not labels:
        return 0.0
    scores = []
    for label in labels:
        true_label = true == label
        pred_label = pred == label
        tp = float(np.logical_and(true_label, pred_label).sum())
        fp = float(np.logical_and(~true_label, pred_label).sum())
        fn = float(np.logical_and(true_label, ~pred_label).sum())
        denom = 2.0 * tp + fp + fn
        scores.append((2.0 * tp / denom) if denom else 0.0)
    return float(np.mean(scores))


def nearest_centroid_metrics(
    train_embeddings: np.ndarray,
    train_labels: np.ndarray,
    test_embeddings: np.ndarray,
    test_labels: np.ndarray,
    *,
    exclude_unknown: bool,
) -> dict[str, Any]:
    train_mask = np.asarray([bool(label) for label in train_labels], dtype=bool)
    test_mask = np.asarray([bool(label) for label in test_labels], dtype=bool)
    if exclude_unknown:
        train_mask &= train_labels != UNKNOWN_ONTOLOGY
        test_mask &= test_labels != UNKNOWN_ONTOLOGY

    n_test_total = int(len(test_labels))
    unknown_excluded = int(n_test_total - test_mask.sum()) if exclude_unknown else 0
    if not train_mask.any() or not test_mask.any():
        return {
            "status": "insufficient_labels",
            "n_test": int(test_mask.sum()),
            "n_test_total": n_test_total,
            "unknown_or_unannotated_excluded": unknown_excluded,
        }

    train_labels = train_labels[train_mask]
    train_embeddings = train_embeddings[train_mask]
    test_labels = test_labels[test_mask]
    test_embeddings = test_embeddings[test_mask]
    label_set = sorted(set(train_labels.tolist()))
    if len(label_set) < 2:
        return {
            "status": "insufficient_train_classes",
            "n_test": int(len(test_labels)),
            "n_test_total": n_test_total,
            "unknown_or_unannotated_excluded": unknown_excluded,
            "train_classes": len(label_set),
        }

    centroid_labels = []
    centroids = []
    for label in label_set:
        centroid_labels.append(label)
        centroids.append(train_embeddings[train_labels == label].mean(axis=0))
    centroid_matrix = normalize_embeddings(np.asarray(centroids, dtype=np.float32))
    test_matrix = normalize_embeddings(test_embeddings.astype(np.float32, copy=False))
    predictions = np.asarray(
        [centroid_labels[index] for index in (test_matrix @ centroid_matrix.T).argmax(axis=1)],
        dtype=str,
    )
    covered = np.asarray([label in label_set for label in test_labels], dtype=bool)
    result: dict[str, Any] = {
        "status": "ok" if covered.any() else "no_label_overlap",
        "n_test": int(len(test_labels)),
        "n_test_total": n_test_total,
        "unknown_or_unannotated_excluded": unknown_excluded,
        "n_evaluable": int(covered.sum()),
        "coverage": float(covered.mean()) if len(covered) else 0.0,
        "train_classes": len(label_set),
        "test_classes": len(set(test_labels.tolist())),
        "accuracy_all": float((predictions == test_labels).mean()) if len(test_labels) else 0.0,
        "macro_f1_all": macro_f1_score(test_labels, predictions),
    }
    if covered.any():
        result["accuracy"] = float((predictions[covered] == test_labels[covered]).mean())
        result["macro_f1"] = macro_f1_score(test_labels[covered], predictions[covered])
    return result


def run_leave_species(
    embeddings: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    *,
    exclude_unknown: bool,
) -> dict[str, Any]:
    records = []
    for group in sorted(set(species.tolist())):
        test_mask = species == group
        metrics = nearest_centroid_metrics(
            embeddings[~test_mask],
            labels[~test_mask],
            embeddings[test_mask],
            labels[test_mask],
            exclude_unknown=exclude_unknown,
        )
        metrics["held_out_group"] = str(group)
        records.append(metrics)

    attempted = [item for item in records if item.get("n_test", 0) > 0]
    evaluable = [item for item in attempted if item.get("n_evaluable", 0) > 0]
    total_test = sum(int(item.get("n_test", 0)) for item in attempted)
    total_test_total = sum(int(item.get("n_test_total", item.get("n_test", 0))) for item in records)
    total_unknown = sum(int(item.get("unknown_or_unannotated_excluded", 0)) for item in records)
    total_evaluable = sum(int(item.get("n_evaluable", 0)) for item in evaluable)
    aggregate: dict[str, Any] = {
        "groups_seen": int(len(set(species.tolist()))),
        "groups_attempted": len(records),
        "groups_with_evaluable_cells": len(evaluable),
        "n_test_total": total_test_total,
        "n_test": total_test,
        "unknown_or_unannotated_excluded": total_unknown,
        "unknown_or_unannotated_fraction": total_unknown / total_test_total if total_test_total else 0.0,
        "n_evaluable": total_evaluable,
        "records": records,
    }
    if total_test:
        aggregate["coverage"] = total_evaluable / total_test
        aggregate["accuracy_all"] = (
            sum(float(item.get("accuracy_all", 0.0)) * int(item.get("n_test", 0)) for item in attempted)
            / total_test
        )
        aggregate["macro_f1_all_weighted_by_cells"] = (
            sum(float(item.get("macro_f1_all", 0.0)) * int(item.get("n_test", 0)) for item in attempted)
            / total_test
        )
    if total_evaluable:
        aggregate["accuracy"] = (
            sum(float(item.get("accuracy", 0.0)) * int(item.get("n_evaluable", 0)) for item in evaluable)
            / total_evaluable
        )
        aggregate["macro_f1"] = (
            sum(float(item.get("macro_f1", 0.0)) * int(item.get("n_evaluable", 0)) for item in evaluable)
            / total_evaluable
        )
    return aggregate


def load_aligned_labels(predictions_path: Path, obs_path: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    predictions = read_csv(predictions_path)
    obs_rows = read_csv(obs_path, delimiter="\t")
    by_id: dict[str, dict[str, str]] = {}
    duplicate_ids = 0
    for row in obs_rows:
        for key in ("cell_id", "_index"):
            value = row.get(key, "")
            if not value:
                continue
            if value in by_id:
                duplicate_ids += 1
            by_id[value] = row

    aligned = []
    missing = []
    for item in predictions:
        cell_id = item.get("cell_id", "")
        obs = by_id.get(cell_id)
        if obs is None:
            missing.append(cell_id)
            continue
        row = {**item, **{f"obs_{key}": value for key, value in obs.items()}}
        row["species"] = canonicalize_species_label(obs.get("species", ""))
        row["fine_truth"] = obs.get("cell_type", "")
        row["ontology_truth"] = canonical_ontology(row["fine_truth"])
        aligned.append(row)

    metadata = {
        "prediction_rows": len(predictions),
        "obs_rows": len(obs_rows),
        "aligned_rows": len(aligned),
        "missing_prediction_cell_ids": len(missing),
        "duplicate_obs_ids_seen": duplicate_ids,
        "missing_examples": missing[:10],
    }
    return aligned, metadata


def write_tsv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "held_out_group",
        "status",
        "n_test_total",
        "n_test",
        "unknown_or_unannotated_excluded",
        "n_evaluable",
        "coverage",
        "accuracy_all",
        "macro_f1_all",
        "accuracy",
        "macro_f1",
        "train_classes",
        "test_classes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({key: row.get(key) for key in fields})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    exact = payload["protocols"]["leave_species_out_fine_exact_recomputed"]
    ontology = payload["protocols"]["leave_species_out_ontology_actionable"]
    frozen = payload["frozen_reference"]["leave_species_out_fine"]
    lines = [
        "# Plant-CellFM v9 Ontology-Label Species-Holdout Benchmark",
        "",
        "This benchmark reuses the frozen v9 runtime-smoke embeddings and evaluates leave-species-out nearest-centroid transfer after mapping observed fine labels into a conservative plant cell-state ontology. Unknown and unannotated labels are excluded from the ontology-actionable denominator. The frozen exact-label benchmark remains the controlling headline metric.",
        "",
        "## Alignment",
        "",
        "| Item | Value |",
        "| --- | ---: |",
        f"| Prediction rows | {payload['alignment']['prediction_rows']} |",
        f"| Obs rows | {payload['alignment']['obs_rows']} |",
        f"| Aligned rows | {payload['alignment']['aligned_rows']} |",
        f"| Missing prediction cell IDs | {payload['alignment']['missing_prediction_cell_ids']} |",
        f"| Embedding rows | {payload['embedding']['rows']} |",
        f"| Embedding dimension | {payload['embedding']['dimension']} |",
        "",
        "## Aggregate Metrics",
        "",
        "| Metric | Frozen exact-label benchmark | Recomputed exact labels | Ontology-actionable labels |",
        "| --- | ---: | ---: | ---: |",
        f"| Test cells | {frozen['n_test']} | {exact['n_test']} | {ontology['n_test']} / {ontology['n_test_total']} actionable |",
        f"| Unknown/unannotated excluded | 0 | 0 | {ontology['unknown_or_unannotated_excluded']} ({pct(ontology['unknown_or_unannotated_fraction'])}) |",
        f"| Coverage | {pct(frozen['coverage'])} | {pct(exact.get('coverage'))} | {pct(ontology.get('coverage'))} |",
        f"| All-cell/actionable accuracy | {pct(frozen['accuracy_all'])} | {pct(exact.get('accuracy_all'))} | {pct(ontology.get('accuracy_all'))} |",
        f"| Known-label accuracy | {pct(frozen['accuracy'])} | {pct(exact.get('accuracy'))} | {pct(ontology.get('accuracy'))} |",
        f"| Known-label macro-F1 | {num(frozen['macro_f1'])} | {num(exact.get('macro_f1'))} | {num(ontology.get('macro_f1'))} |",
        "",
        "## Per-Species Ontology Records",
        "",
        "| Species | actionable n | excluded unknown | coverage | action accuracy | known accuracy | macro-F1 | status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in ontology["records"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["held_out_group"]),
                    str(row.get("n_test", 0)),
                    str(row.get("unknown_or_unannotated_excluded", 0)),
                    pct(row.get("coverage")),
                    pct(row.get("accuracy_all")),
                    pct(row.get("accuracy")),
                    num(row.get("macro_f1")),
                    str(row.get("status")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The ontology-actionable benchmark is stricter than a simple coverage audit because it uses the model embeddings and a leave-species nearest-centroid protocol. It should be reported as an additional label-harmonized diagnostic, not as a replacement for the frozen exact-label species-holdout result.",
            "",
            "Large unknown/unannotated exclusions indicate that public plant single-cell labels remain a major bottleneck. A higher-tier revision should freeze both exact-label and ontology-label species-holdout protocols before making stronger cross-species claims.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ontology-label leave-species benchmark on v9 embeddings")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--obs-labels", type=Path, required=True)
    parser.add_argument("--benchmark-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-tsv", type=Path, required=True)
    args = parser.parse_args()

    embeddings = np.load(args.embeddings)
    aligned, alignment = load_aligned_labels(args.predictions, args.obs_labels)
    if embeddings.shape[0] != len(aligned):
        raise RuntimeError(f"embedding rows {embeddings.shape[0]} != aligned labels {len(aligned)}")
    species = np.asarray([row["species"] for row in aligned], dtype=str)
    fine_labels = np.asarray([row["fine_truth"] for row in aligned], dtype=str)
    ontology_labels = np.asarray([row["ontology_truth"] for row in aligned], dtype=str)

    benchmark = json.loads(args.benchmark_json.read_text(encoding="utf-8"))
    exact = run_leave_species(embeddings, species, fine_labels, exclude_unknown=False)
    ontology = run_leave_species(embeddings, species, ontology_labels, exclude_unknown=True)
    payload = {
        "schema_version": "plant_cellfm_v9_ontology_label_species_holdout_benchmark_v1",
        "source_files": {
            "embeddings": str(args.embeddings),
            "predictions": str(args.predictions),
            "obs_labels": str(args.obs_labels),
            "benchmark_json": str(args.benchmark_json),
        },
        "claim_boundary": "Additional ontology-label diagnostic; does not replace the frozen exact-label v9 species-holdout benchmark.",
        "alignment": alignment,
        "embedding": {
            "rows": int(embeddings.shape[0]),
            "dimension": int(embeddings.shape[1]),
            "dtype": str(embeddings.dtype),
            "nan_count": int(np.isnan(embeddings).sum()),
            "infinite_count": int(np.isinf(embeddings).sum()),
        },
        "frozen_reference": {
            "leave_species_out_fine": {
                key: value
                for key, value in benchmark["protocols"]["leave_species_out_fine"].items()
                if key != "records"
            }
        },
        "label_summary": {
            "species": len(set(species.tolist())),
            "fine_labels": len(set(fine_labels.tolist())),
            "ontology_labels": len(set(ontology_labels.tolist())),
            "unknown_or_unannotated_cells": int((ontology_labels == UNKNOWN_ONTOLOGY).sum()),
            "top_ontology_labels": Counter(ontology_labels.tolist()).most_common(20),
        },
        "protocols": {
            "leave_species_out_fine_exact_recomputed": exact,
            "leave_species_out_ontology_actionable": ontology,
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_tsv(args.output_tsv, ontology["records"])
    write_markdown(args.output_md, payload)
    print(args.output_json)
    print(args.output_md)
    print(args.output_tsv)


if __name__ == "__main__":
    main()
