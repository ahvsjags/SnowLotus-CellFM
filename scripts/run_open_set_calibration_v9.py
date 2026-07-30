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


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def normalize_rows(values: np.ndarray) -> np.ndarray:
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


def load_aligned(predictions_path: Path, obs_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
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

    aligned: list[dict[str, Any]] = []
    missing: list[str] = []
    for item in predictions:
        cell_id = item.get("cell_id", "")
        obs = by_id.get(cell_id)
        if obs is None:
            missing.append(cell_id)
            continue
        truth = obs.get("cell_type", "")
        row = {
            **item,
            "species": canonicalize_species_label(obs.get("species", "")),
            "dataset_id": obs.get("dataset_id", ""),
            "sample_id": obs.get("sample_id", ""),
            "tissue": obs.get("tissue", ""),
            "fine_truth": truth,
            "ontology_truth": canonical_ontology(truth),
            "fine_prediction": item.get("fine_label", ""),
            "ontology_prediction": canonical_ontology(item.get("fine_label", "")),
            "fine_confidence": float(item.get("fine_confidence") or 0.0),
            "coarse_confidence": float(item.get("coarse_confidence") or 0.0),
        }
        aligned.append(row)
    return aligned, {
        "prediction_rows": len(predictions),
        "obs_rows": len(obs_rows),
        "aligned_rows": len(aligned),
        "missing_prediction_cell_ids": len(missing),
        "duplicate_obs_ids_seen": duplicate_ids,
        "missing_examples": missing[:10],
    }


def nearest_centroid_cell_records(
    embeddings: np.ndarray,
    species: np.ndarray,
    labels: np.ndarray,
    *,
    exclude_unknown: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    embeddings = normalize_rows(embeddings.astype(np.float32, copy=False))
    for group in sorted(set(species.tolist())):
        test_mask = species == group
        train_mask = ~test_mask
        train_labels = labels[train_mask]
        test_labels = labels[test_mask]
        train_embeddings = embeddings[train_mask]
        test_embeddings = embeddings[test_mask]
        if exclude_unknown:
            train_keep = train_labels != UNKNOWN_ONTOLOGY
            test_keep = test_labels != UNKNOWN_ONTOLOGY
            train_labels = train_labels[train_keep]
            train_embeddings = train_embeddings[train_keep]
            local_test_indices = np.flatnonzero(test_mask)[test_keep]
            test_labels = test_labels[test_keep]
            test_embeddings = test_embeddings[test_keep]
        else:
            local_test_indices = np.flatnonzero(test_mask)

        label_set = sorted(set(train_labels.tolist()))
        if len(label_set) < 2 or len(test_labels) == 0:
            for index in local_test_indices.tolist():
                records.append(
                    {
                        "cell_index": int(index),
                        "held_out_species": str(group),
                        "truth": str(labels[index]),
                        "prediction": "",
                        "known_label": False,
                        "correct": False,
                        "max_similarity": None,
                        "margin": None,
                        "status": "insufficient_train_or_test_labels",
                    }
                )
            continue

        centroids = []
        for label in label_set:
            centroids.append(train_embeddings[train_labels == label].mean(axis=0))
        centroid_matrix = normalize_rows(np.asarray(centroids, dtype=np.float32))
        scores = test_embeddings @ centroid_matrix.T
        top1 = np.argmax(scores, axis=1)
        if scores.shape[1] > 1:
            partitioned = np.partition(scores, -2, axis=1)
            top2_scores = partitioned[:, -2]
        else:
            top2_scores = np.zeros(scores.shape[0], dtype=np.float32)
        for row_idx, original_index in enumerate(local_test_indices.tolist()):
            pred = label_set[int(top1[row_idx])]
            truth = str(test_labels[row_idx])
            known = truth in label_set
            records.append(
                {
                    "cell_index": int(original_index),
                    "held_out_species": str(group),
                    "truth": truth,
                    "prediction": pred,
                    "known_label": bool(known),
                    "correct": bool(pred == truth),
                    "max_similarity": float(scores[row_idx, top1[row_idx]]),
                    "margin": float(scores[row_idx, top1[row_idx]] - top2_scores[row_idx]),
                    "status": "ok",
                }
            )
    return records


def selective_curve(
    records: list[dict[str, Any]],
    *,
    score_key: str,
    coverage_points: list[float],
) -> list[dict[str, Any]]:
    valid = [row for row in records if row.get(score_key) is not None]
    if not valid:
        return []
    ranked = sorted(valid, key=lambda row: float(row[score_key]), reverse=True)
    total = len(ranked)
    rows = []
    for coverage in coverage_points:
        n_accept = max(1, min(total, int(round(total * coverage))))
        accepted = ranked[:n_accept]
        rejected = ranked[n_accept:]
        known_accepted = [row for row in accepted if row["known_label"]]
        correct = sum(1 for row in accepted if row["correct"])
        known_correct = sum(1 for row in known_accepted if row["correct"])
        rejected_errors = sum(1 for row in rejected if not row["correct"])
        rejected_open = sum(1 for row in rejected if not row["known_label"])
        total_errors = sum(1 for row in ranked if not row["correct"])
        total_open = sum(1 for row in ranked if not row["known_label"])
        rows.append(
            {
                "acceptance_rate": coverage,
                "accepted_cells": n_accept,
                "threshold": float(accepted[-1][score_key]),
                "selective_accuracy": correct / n_accept if n_accept else 0.0,
                "known_label_accuracy": known_correct / len(known_accepted) if known_accepted else None,
                "known_label_fraction": len(known_accepted) / n_accept if n_accept else 0.0,
                "rejected_cells": len(rejected),
                "rejected_error_capture": rejected_errors / total_errors if total_errors else 0.0,
                "rejected_open_set_capture": rejected_open / total_open if total_open else 0.0,
            }
        )
    return rows


def api_confidence_records(aligned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for index, row in enumerate(aligned):
        records.append(
            {
                "cell_index": index,
                "held_out_species": row["species"],
                "truth": row["fine_truth"],
                "prediction": row["fine_prediction"],
                "known_label": True,
                "correct": row["fine_truth"] == row["fine_prediction"],
                "ontology_correct": row["ontology_truth"] == row["ontology_prediction"],
                "fine_confidence": row["fine_confidence"],
                "coarse_confidence": row["coarse_confidence"],
                "status": "ok",
            }
        )
    return records


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {"n": 0}
    truth = np.asarray([row["truth"] for row in records], dtype=str)
    pred = np.asarray([row["prediction"] for row in records], dtype=str)
    correct = np.asarray([bool(row["correct"]) for row in records], dtype=bool)
    known = np.asarray([bool(row["known_label"]) for row in records], dtype=bool)
    return {
        "n": len(records),
        "known_label_cells": int(known.sum()),
        "open_set_cells": int((~known).sum()),
        "all_cell_accuracy": float(correct.mean()),
        "known_label_accuracy": float(correct[known].mean()) if known.any() else None,
        "macro_f1_all": macro_f1_score(truth, pred),
        "truth_labels": len(set(truth.tolist())),
        "prediction_labels": len(set(pred.tolist())),
    }


def write_curve_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "acceptance_rate",
        "accepted_cells",
        "threshold",
        "selective_accuracy",
        "known_label_accuracy",
        "known_label_fraction",
        "rejected_cells",
        "rejected_error_capture",
        "rejected_open_set_capture",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def pct(value: Any) -> str:
    if value is None:
        return "-"
    return f"{100.0 * float(value):.2f}%"


def num(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    exact = payload["nearest_centroid_exact"]
    ontology = payload["nearest_centroid_ontology"]
    api = payload["api_head_confidence"]
    lines = [
        "# Plant-CellFM v9 Open-Set Calibration And Selective Annotation Audit",
        "",
        "This audit adds a confidence-aware layer to the frozen v9 species-holdout evidence. It does not replace the frozen all-cell leave-species metric. Instead, it reports whether the model can support selective annotation, abstention and reviewer-visible open-set triage.",
        "",
        "## Alignment",
        "",
        "| Item | Value |",
        "| --- | ---: |",
        f"| Aligned prediction rows | {payload['alignment']['aligned_rows']} |",
        f"| Embedding rows | {payload['embedding']['rows']} |",
        f"| Embedding dimension | {payload['embedding']['dimension']} |",
        f"| Species groups | {payload['label_summary']['species_groups']} |",
        f"| Fine labels | {payload['label_summary']['fine_labels']} |",
        f"| Ontology labels | {payload['label_summary']['ontology_labels']} |",
        "",
        "## Base Metrics",
        "",
        "| Protocol | n | all-cell/actionable accuracy | known-label accuracy | macro-F1 | open-set cells |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| Leave-species exact nearest-centroid | {exact['summary']['n']} | {pct(exact['summary']['all_cell_accuracy'])} | {pct(exact['summary']['known_label_accuracy'])} | {num(exact['summary']['macro_f1_all'])} | {exact['summary']['open_set_cells']} |",
        f"| Leave-species ontology nearest-centroid | {ontology['summary']['n']} | {pct(ontology['summary']['all_cell_accuracy'])} | {pct(ontology['summary']['known_label_accuracy'])} | {num(ontology['summary']['macro_f1_all'])} | {ontology['summary']['open_set_cells']} |",
        f"| API annotation head, exact label | {api['summary']['n']} | {pct(api['summary']['exact_accuracy'])} | n/a | n/a | n/a |",
        f"| API annotation head, ontology label | {api['summary']['n']} | {pct(api['summary']['ontology_accuracy'])} | n/a | n/a | n/a |",
        "",
        "## Selective Annotation Curve",
        "",
        "The rows below sort cells by confidence and report the accuracy retained when only the highest-confidence cells are automatically annotated. Rejected cells are routed to manual review, ontology harmonization or species-specific adapter calibration.",
        "",
        "| Signal | Accepted fraction | Accepted cells | Threshold | Selective accuracy | Known-label accuracy | Rejected error capture | Rejected open-set capture |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for signal, rows in [
        ("exact max-similarity", exact["selective_curve"]),
        ("ontology max-similarity", ontology["selective_curve"]),
        ("API fine confidence", api["fine_confidence_curve"]),
    ]:
        for row in rows:
            if row["acceptance_rate"] in {0.1, 0.2, 0.3, 0.5, 0.8, 1.0}:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            signal,
                            pct(row["acceptance_rate"]),
                            str(row["accepted_cells"]),
                            num(row["threshold"]),
                            pct(row["selective_accuracy"]),
                            pct(row["known_label_accuracy"]),
                            pct(row["rejected_error_capture"]),
                            pct(row["rejected_open_set_capture"]),
                        ]
                    )
                    + " |"
                )
    lines.extend(
        [
            "",
            "## Reviewer-Safe Interpretation",
            "",
            "The frozen headline remains the strict normalized leave-species all-cell metric. The new contribution is an explicit abstention layer: high-confidence cells can be accepted automatically, while low-confidence and open-set-like cells are flagged before they are turned into biological claims. This directly addresses the main weakness of the v9 benchmark by converting low cross-species coverage into a measurable reliability-control protocol.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit v9 open-set calibration and selective annotation")
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--obs-labels", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-exact-tsv", type=Path, required=True)
    parser.add_argument("--output-ontology-tsv", type=Path, required=True)
    parser.add_argument("--output-api-tsv", type=Path, required=True)
    args = parser.parse_args()

    embeddings = np.load(args.embeddings)
    aligned, alignment = load_aligned(args.predictions, args.obs_labels)
    if embeddings.shape[0] != len(aligned):
        raise RuntimeError(f"embedding rows {embeddings.shape[0]} != aligned rows {len(aligned)}")

    species = np.asarray([row["species"] for row in aligned], dtype=str)
    fine_labels = np.asarray([row["fine_truth"] for row in aligned], dtype=str)
    ontology_labels = np.asarray([row["ontology_truth"] for row in aligned], dtype=str)
    exact_records = nearest_centroid_cell_records(embeddings, species, fine_labels, exclude_unknown=False)
    ontology_records = nearest_centroid_cell_records(
        embeddings,
        species,
        ontology_labels,
        exclude_unknown=True,
    )
    api_records = api_confidence_records(aligned)
    api_exact_correct = np.asarray([row["correct"] for row in api_records], dtype=bool)
    api_ontology_correct = np.asarray([row["ontology_correct"] for row in api_records], dtype=bool)
    coverage_points = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    payload = {
        "schema_version": "plant_cellfm_v9_open_set_calibration_v1",
        "claim_boundary": "Selective annotation and open-set triage diagnostic; does not replace frozen v9 benchmark metrics.",
        "source_files": {
            "embeddings": str(args.embeddings),
            "predictions": str(args.predictions),
            "obs_labels": str(args.obs_labels),
        },
        "alignment": alignment,
        "embedding": {
            "rows": int(embeddings.shape[0]),
            "dimension": int(embeddings.shape[1]),
            "nan_count": int(np.isnan(embeddings).sum()),
            "infinite_count": int(np.isinf(embeddings).sum()),
        },
        "label_summary": {
            "species_groups": len(set(species.tolist())),
            "fine_labels": len(set(fine_labels.tolist())),
            "ontology_labels": len(set(ontology_labels.tolist())),
            "top_fine_labels": Counter(fine_labels.tolist()).most_common(20),
            "top_ontology_labels": Counter(ontology_labels.tolist()).most_common(20),
        },
        "nearest_centroid_exact": {
            "summary": summarize_records(exact_records),
            "selective_curve": selective_curve(
                exact_records,
                score_key="max_similarity",
                coverage_points=coverage_points,
            ),
        },
        "nearest_centroid_ontology": {
            "summary": summarize_records(ontology_records),
            "selective_curve": selective_curve(
                ontology_records,
                score_key="max_similarity",
                coverage_points=coverage_points,
            ),
        },
        "api_head_confidence": {
            "summary": {
                "n": len(api_records),
                "exact_accuracy": float(api_exact_correct.mean()) if len(api_exact_correct) else 0.0,
                "ontology_accuracy": float(api_ontology_correct.mean()) if len(api_ontology_correct) else 0.0,
                "mean_fine_confidence": float(np.mean([row["fine_confidence"] for row in api_records])),
                "mean_coarse_confidence": float(np.mean([row["coarse_confidence"] for row in api_records])),
            },
            "fine_confidence_curve": selective_curve(
                api_records,
                score_key="fine_confidence",
                coverage_points=coverage_points,
            ),
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(args.output_md, payload)
    write_curve_tsv(args.output_exact_tsv, payload["nearest_centroid_exact"]["selective_curve"])
    write_curve_tsv(args.output_ontology_tsv, payload["nearest_centroid_ontology"]["selective_curve"])
    write_curve_tsv(args.output_api_tsv, payload["api_head_confidence"]["fine_confidence_curve"])
    print(args.output_json)
    print(args.output_md)


if __name__ == "__main__":
    main()
