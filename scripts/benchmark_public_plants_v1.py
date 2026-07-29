from __future__ import annotations

import argparse
import csv
import hashlib
import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score
from torch.utils.data import DataLoader

from snowcell.artifacts import load_checkpoint, model_from_checkpoint, vocabs_from_checkpoint
from snowcell.config import ExperimentConfig
from snowcell.data import ExpressionDataset, prepare_inference_data


def read_manifest(path: Path) -> dict[str, Any]:
    rows = []
    if path.is_file():
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
    datasets = sorted({row.get("dataset_id", "") for row in rows if row.get("dataset_id")})
    raw_species = sorted({row.get("species", "") for row in rows if row.get("species")})
    species = sorted({" ".join(label.replace("_", " ").split()) for label in raw_species})
    return {
        "path": str(path),
        "manifest_rows": len(rows),
        "datasets": len(datasets),
        "species": len(species),
        "dataset_ids": datasets,
        "species_labels": species,
        "raw_species_labels": raw_species,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_embeddings(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-8)


def nearest_centroid_metrics(
    train_embeddings: np.ndarray,
    train_labels: np.ndarray,
    test_embeddings: np.ndarray,
    test_labels: np.ndarray,
) -> dict[str, Any]:
    train_mask = np.asarray([bool(label) for label in train_labels], dtype=bool)
    test_mask = np.asarray([bool(label) for label in test_labels], dtype=bool)
    if not train_mask.any() or not test_mask.any():
        return {"status": "insufficient_labels", "n_test": int(test_mask.sum())}

    train_labels = train_labels[train_mask]
    train_embeddings = train_embeddings[train_mask]
    test_labels = test_labels[test_mask]
    test_embeddings = test_embeddings[test_mask]
    label_set = sorted(set(train_labels.tolist()))
    if len(label_set) < 2:
        return {
            "status": "insufficient_train_classes",
            "n_test": int(len(test_labels)),
            "train_classes": len(label_set),
        }

    centroids = []
    centroid_labels = []
    for label in label_set:
        centroid = train_embeddings[train_labels == label].mean(axis=0)
        centroids.append(centroid)
        centroid_labels.append(label)
    centroid_matrix = normalize_embeddings(np.asarray(centroids, dtype=np.float32))
    test_matrix = normalize_embeddings(test_embeddings.astype(np.float32, copy=False))
    predictions = np.asarray(
        [centroid_labels[index] for index in (test_matrix @ centroid_matrix.T).argmax(axis=1)],
        dtype=str,
    )
    covered = np.asarray([label in label_set for label in test_labels], dtype=bool)
    covered_true = test_labels[covered]
    covered_pred = predictions[covered]
    result: dict[str, Any] = {
        "status": "ok" if covered.any() else "no_label_overlap",
        "n_test": int(len(test_labels)),
        "n_evaluable": int(covered.sum()),
        "coverage": float(covered.mean()),
        "train_classes": len(label_set),
        "test_classes": len(set(test_labels.tolist())),
    }
    if covered.any():
        result["accuracy"] = float(accuracy_score(covered_true, covered_pred))
        result["macro_f1"] = float(
            f1_score(covered_true, covered_pred, average="macro", zero_division=0)
        )
    return result


def run_leaveout_protocol(
    embeddings: np.ndarray,
    groups: np.ndarray,
    labels: np.ndarray,
    min_test_cells: int,
) -> dict[str, Any]:
    records = []
    for group in sorted(set(groups.tolist())):
        test_mask = groups == group
        if int(test_mask.sum()) < min_test_cells:
            continue
        metrics = nearest_centroid_metrics(
            embeddings[~test_mask],
            labels[~test_mask],
            embeddings[test_mask],
            labels[test_mask],
        )
        metrics["held_out_group"] = str(group)
        records.append(metrics)

    evaluable = [item for item in records if item.get("n_evaluable", 0) > 0]
    total_evaluable = sum(int(item["n_evaluable"]) for item in evaluable)
    aggregate: dict[str, Any] = {
        "groups_seen": int(len(set(groups.tolist()))),
        "groups_attempted": len(records),
        "groups_with_evaluable_cells": len(evaluable),
        "n_evaluable": total_evaluable,
        "records": records,
    }
    if total_evaluable:
        for key in ("accuracy", "macro_f1", "coverage"):
            aggregate[key] = float(
                sum(float(item.get(key, 0.0)) * int(item["n_evaluable"]) for item in evaluable)
                / total_evaluable
            )
    return aggregate


def select_indices(groups: np.ndarray, max_cells_per_group: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    selected = []
    for group in sorted(set(groups.tolist())):
        candidates = np.flatnonzero(groups == group)
        if len(candidates) > max_cells_per_group:
            candidates = rng.choice(candidates, size=max_cells_per_group, replace=False)
        selected.append(np.sort(candidates))
    if not selected:
        return np.empty(0, dtype=np.int64)
    return np.sort(np.concatenate(selected).astype(np.int64))


def encode_embeddings(
    model: torch.nn.Module,
    dataset: ExpressionDataset,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )
    chunks = []
    model.eval()
    with torch.no_grad():
        for batch_index, batch in enumerate(loader, start=1):
            batch = {key: value.to(device, non_blocking=True) for key, value in batch.items()}
            batch["species_id"] = batch["species_id"].clamp_min(0)
            batch["tissue_id"] = batch["tissue_id"].clamp_min(0)
            autocast = (
                torch.autocast(device_type="cuda", dtype=torch.bfloat16)
                if device.type == "cuda"
                else nullcontext()
            )
            with autocast:
                output = model(
                    gene_ids=batch["gene_ids"],
                    values=batch["values"],
                    padding_mask=batch["padding_mask"],
                    species_id=batch["species_id"],
                    tissue_id=batch["tissue_id"],
                )
            chunks.append(output["embedding"].detach().float().cpu().numpy())
            if batch_index % 10 == 0:
                print(f"embedded_batches={batch_index}", flush=True)
    if not chunks:
        return np.empty((0, model.config.d_model), dtype=np.float32)
    return np.concatenate(chunks, axis=0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the all-plant public_plants_v1 backbone")
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("outputs/plant_general_foundation_public_plants_v1_4090/best.pt"),
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/plant_foundation_corpus_public_plants_v1.h5ad"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/corpus_manifest_public_plants_v1.tsv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/benchmarks/public_plants_v1_cross_species.json"),
    )
    parser.add_argument("--max-cells-per-dataset", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--min-test-cells", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260729)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    root = args.project_dir.resolve()
    checkpoint_path = (root / args.checkpoint).resolve()
    data_path = (root / args.data).resolve()
    manifest_path = (root / args.manifest).resolve()
    output_path = (root / args.output).resolve()
    device = torch.device(args.device if args.device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu"))
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but torch.cuda.is_available() is false")
    torch.set_float32_matmul_precision("high")

    checkpoint = load_checkpoint(checkpoint_path, map_location="cpu")
    gene_vocab, _, _, species_vocab, tissue_vocab = vocabs_from_checkpoint(checkpoint)
    config = ExperimentConfig.from_dict(checkpoint["experiment_config"])
    config.data.path = str(data_path)
    inference = prepare_inference_data(config.data, gene_vocab, species_vocab, tissue_vocab)
    obs = inference.matrix.obs
    dataset_values = np.asarray(
        obs.get("dataset_id", np.repeat("unknown_dataset", inference.matrix.n_cells)), dtype=str
    )
    species_values = np.asarray(
        obs.get("species", np.repeat("unknown_species", inference.matrix.n_cells)), dtype=str
    )
    sample_values_raw = np.asarray(
        obs.get("sample_id", np.repeat("unknown_sample", inference.matrix.n_cells)), dtype=str
    )
    sample_values = np.asarray(
        [f"{dataset}::{sample}" for dataset, sample in zip(dataset_values, sample_values_raw, strict=True)],
        dtype=str,
    )
    fine_values = np.asarray(
        obs.get(config.data.label_key, np.repeat("", inference.matrix.n_cells)), dtype=str
    )
    coarse_values = np.asarray(
        obs.get(config.data.coarse_label_key, np.repeat("", inference.matrix.n_cells)), dtype=str
    )
    selected = select_indices(dataset_values, args.max_cells_per_dataset, args.seed)
    if not len(selected):
        raise RuntimeError("no cells selected for benchmark")
    dataset = ExpressionDataset(
        inference.matrix,
        selected,
        config.data,
        gene_vocab,
        species_vocab=species_vocab,
        tissue_vocab=tissue_vocab,
    )
    model = model_from_checkpoint(checkpoint, device=device)
    embeddings = encode_embeddings(model, dataset, device, args.batch_size)
    selected_datasets = dataset_values[selected]
    selected_species = species_values[selected]
    selected_samples = sample_values[selected]
    selected_fine = fine_values[selected]
    selected_coarse = coarse_values[selected]
    norm = np.linalg.norm(embeddings, axis=1)
    result = {
        "schema_version": "plant-general-v1-cross-species-benchmark-v1",
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": sha256(checkpoint_path),
        "checkpoint_epoch": checkpoint.get("epoch"),
        "checkpoint_metrics": checkpoint.get("metrics", {}),
        "data": str(data_path),
        "manifest": read_manifest(manifest_path),
        "device": str(device),
        "selection": {
            "seed": args.seed,
            "max_cells_per_dataset": args.max_cells_per_dataset,
            "selected_cells": int(len(selected)),
            "datasets": int(len(set(selected_datasets.tolist()))),
            "species": int(len(set(selected_species.tolist()))),
            "samples": int(len(set(selected_samples.tolist()))),
        },
        "embedding": {
            "dimension": int(embeddings.shape[1]),
            "nan_count": int(np.isnan(embeddings).sum()),
            "infinite_count": int(np.isinf(embeddings).sum()),
            "mean_l2_norm": float(norm.mean()),
            "std_l2_norm": float(norm.std()),
        },
        "protocols": {
            "leave_dataset_out_fine": run_leaveout_protocol(
                embeddings, selected_datasets, selected_fine, args.min_test_cells
            ),
            "leave_dataset_out_coarse": run_leaveout_protocol(
                embeddings, selected_datasets, selected_coarse, args.min_test_cells
            ),
            "leave_sample_out_fine": run_leaveout_protocol(
                embeddings, selected_samples, selected_fine, args.min_test_cells
            ),
            "leave_sample_out_coarse": run_leaveout_protocol(
                embeddings, selected_samples, selected_coarse, args.min_test_cells
            ),
            "leave_species_out_fine": run_leaveout_protocol(
                embeddings, selected_species, selected_fine, args.min_test_cells
            ),
            "leave_species_out_coarse": run_leaveout_protocol(
                embeddings, selected_species, selected_coarse, args.min_test_cells
            ),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    print(json.dumps(result["embedding"], ensure_ascii=False))
    for name, metrics in result["protocols"].items():
        print(name, json.dumps({key: value for key, value in metrics.items() if key != "records"}))


if __name__ == "__main__":
    main()
