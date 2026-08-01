from __future__ import annotations

"""Run a matched frozen-scPlantLLM representation probe on the wheat stress test.

The input data, author orthogroup map and cell-level 5,014/717/1,433 split
match the released Plant-CellFM wheat-adapter stress test.  This script does
not fine-tune scPlantLLM or claim a full head-to-head comparison: it measures
the official frozen scPlantLLM encoder paired with a source-only cosine
nearest-centroid readout fitted on the identical 5,014 training cells.
"""

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

from snowcell.data import group_split


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "outputs" / "external_validation" / "gse270342" / "GSE270342_wheat_root_author_annotated_nonoverlap_diagnostic.h5ad"
ORTHOLOGS = ROOT / "data" / "orthologs" / "gse270342_wheat_to_arabidopsis_author_orthogroups.tsv"
SCPLANTLLM = ROOT / "external" / "scPlantLLM"
CHECKPOINT = SCPLANTLLM / "model_params" / "scPlantLLM_model.pth"
GENE_VOCAB = SCPLANTLLM / "gene_vocab.json"
PLANTCELLM_TEST = ROOT / "outputs" / "gse270342_wheat_root_lora_adapter_4070" / "detailed_test" / "predictions.tsv"
OUTPUT_DIR = ROOT / "outputs" / "external_benchmarks" / "scplantllm_gse270342_matched_embedding_probe"
OUTPUT_JSON = ROOT / "release_metadata" / "scplantllm_gse270342_matched_embedding_probe_v1.json"
OUTPUT_TABLE = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S22_scPlantLLM_GSE270342_matched_embedding_probe.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_probe_module() -> Any:
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import run_scplantllm_embedding_centroid_probe as probe

    return probe


def first_target_scplantllm_mapping() -> tuple[dict[str, int], dict[str, Any]]:
    mapping = pd.read_csv(ORTHOLOGS, sep="\t", dtype=str).drop_duplicates("source_gene", keep="first")
    vocabulary = json.loads(GENE_VOCAB.read_text(encoding="utf-8"))
    mapping = mapping.loc[mapping.target_gene.isin(vocabulary)].copy()
    mapping["token_id"] = mapping.target_gene.map(vocabulary).astype(int)
    return (
        dict(zip(mapping.source_gene.astype(str), mapping.token_id.astype(int), strict=True)),
        {
            "author_relationships": int(len(pd.read_csv(ORTHOLOGS, sep="\t", dtype=str))),
            "first_target_source_genes": int(len(mapping)),
            "scplantllm_target_vocab": int(len(vocabulary)),
            "mapping_mode": "author_orthogroups_first_target_then_scplantllm_vocabulary_intersection",
        },
    )


def build_sequences(
    matrix: sparse.spmatrix | np.ndarray,
    gene_token_lookup: np.ndarray,
    indices: np.ndarray,
    *,
    sequence_length: int,
    max_tokens: int,
    value_pad: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, float | int]]:
    """Collapse duplicate ortholog targets, then apply the official 75% token cap."""
    matrix = matrix.tocsr() if sparse.issparse(matrix) else sparse.csr_matrix(matrix)
    gene_ids = np.zeros((len(indices), sequence_length), dtype=np.int64)
    values = np.full((len(indices), sequence_length), -2, dtype=np.int64)
    rng = np.random.default_rng(seed)
    token_counts: list[int] = []
    capped_cells = 0
    for row_position, cell_index in enumerate(indices):
        row = matrix.getrow(int(cell_index))
        keep = gene_token_lookup[row.indices] > 0
        raw_ids = gene_token_lookup[row.indices[keep]]
        raw_values = row.data[keep]
        unique_ids, inverse = np.unique(raw_ids, return_inverse=True)
        collapsed_values = np.zeros(len(unique_ids), dtype=np.float64)
        np.add.at(collapsed_values, inverse, raw_values)
        if len(unique_ids) > max_tokens:
            selected = rng.choice(len(unique_ids), size=max_tokens, replace=False)
            unique_ids = unique_ids[selected]
            collapsed_values = collapsed_values[selected]
            capped_cells += 1
        count = int(len(unique_ids))
        gene_ids[row_position, :count] = unique_ids
        values[row_position, :count] = np.clip(np.rint(collapsed_values), 0, value_pad - 1).astype(np.int64)
        token_counts.append(count)
    return (
        gene_ids,
        values,
        {
            "cells": int(len(indices)),
            "min_tokens": int(min(token_counts)),
            "median_tokens": float(np.median(token_counts)),
            "max_tokens": int(max(token_counts)),
            "capped_cells": int(capped_cells),
            "sequence_length": int(sequence_length),
            "max_nonpadding_tokens": int(max_tokens),
        },
    )


def metric_payload(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[dict[str, Any], pd.DataFrame]:
    labels = np.asarray(sorted(set(y_true.tolist()) | set(y_pred.tolist()), key=str), dtype=object)
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    per_class = pd.DataFrame(
        {
            "author_label": labels,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support.astype(int),
        }
    )
    return (
        {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
            "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
            "test_class_counts": {str(label): int(count) for label, count in Counter(y_true.tolist()).items()},
        },
        per_class,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the matched frozen scPlantLLM wheat representation baseline.")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument("--limit-train", type=int, default=None, help="Optional deterministic debugging limit; never use for the release result.")
    parser.add_argument("--limit-test", type=int, default=None, help="Optional deterministic debugging limit; never use for the release result.")
    args = parser.parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable.")

    probe = import_probe_module()
    device = torch.device(args.device)
    raw_state = probe.unwrap_state_dict(torch.load(CHECKPOINT, map_location="cpu"))
    state, conversion = probe.convert_flashmha_state_dict(raw_state)
    shape = probe.infer_model_shape(state, nhead=8, pad_token_id=0, value_pad_index=None, cls_token_id=None)
    model, missing_keys, unexpected_keys = probe.build_model(SCPLANTLLM, state, shape, device)
    if missing_keys or unexpected_keys:
        raise ValueError("Official scPlantLLM checkpoint did not load cleanly.")

    adata = ad.read_h5ad(DATA, backed=None)
    cell_ids = adata.obs["cell_id"].astype(str).to_numpy() if "cell_id" in adata.obs else adata.obs_names.astype(str).to_numpy()
    labels = adata.obs["expert_annotation_raw"].astype(str).to_numpy()
    split = group_split(cell_ids, validation_fraction=0.10, test_fraction=0.20, seed=args.seed)
    plantcellm_test = pd.read_csv(PLANTCELLM_TEST, sep="\t", dtype={"cell_id": str})
    test_ids = cell_ids[split.test]
    if set(test_ids.tolist()) != set(plantcellm_test.cell_id.tolist()) or len(test_ids) != len(plantcellm_test):
        raise ValueError("Reconstructed split does not exactly match the released Plant-CellFM locked test barcodes.")
    raw_label_lookup = dict(zip(cell_ids, labels, strict=True))
    if not np.array_equal(plantcellm_test.true_fine.to_numpy(str), np.asarray([raw_label_lookup[cell_id] for cell_id in plantcellm_test.cell_id], dtype=str)):
        raise ValueError("Plant-CellFM locked-test labels do not match the author-labelled source object.")

    train_indices = split.train if args.limit_train is None else split.train[: args.limit_train]
    test_indices = split.test if args.limit_test is None else split.test[: args.limit_test]
    mapping, mapping_stats = first_target_scplantllm_mapping()
    lookup = np.asarray([mapping.get(str(gene), 0) for gene in adata.var_names], dtype=np.int64)
    if not sparse.issparse(adata.X):
        matrix = sparse.csr_matrix(adata.X)
    else:
        matrix = adata.X.tocsr()
    max_tokens = int(shape.cls_token_id and int(1500 * 0.75))
    train_ids, train_values, train_sequence_stats = build_sequences(
        matrix,
        lookup,
        train_indices,
        sequence_length=1500,
        max_tokens=max_tokens,
        value_pad=shape.value_pad_index,
        seed=args.seed,
    )
    test_ids_tokens, test_values, test_sequence_stats = build_sequences(
        matrix,
        lookup,
        test_indices,
        sequence_length=1500,
        max_tokens=max_tokens,
        value_pad=shape.value_pad_index,
        seed=args.seed + 1,
    )
    torch.cuda.reset_peak_memory_stats(device) if device.type == "cuda" else None
    started = time.perf_counter()
    train_embeddings = probe.encode_embeddings(model, train_ids, train_values, shape=shape, device=device, batch_size=args.batch_size, cls_value=0)
    test_embeddings = probe.encode_embeddings(model, test_ids_tokens, test_values, shape=shape, device=device, batch_size=args.batch_size, cls_value=0)
    elapsed = time.perf_counter() - started
    predictions, centroid_counts = probe.nearest_centroid_predictions(train_embeddings, labels[train_indices], test_embeddings)
    metrics, per_class = metric_payload(labels[test_indices], predictions)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_DIR / "train_embeddings.npy", train_embeddings)
    np.save(OUTPUT_DIR / "locked_test_embeddings.npy", test_embeddings)
    pd.DataFrame(
        {
            "cell_id": cell_ids[test_indices],
            "author_label": labels[test_indices],
            "scplantllm_frozen_centroid_prediction": predictions,
        }
    ).to_csv(OUTPUT_DIR / "locked_test_predictions.tsv", sep="\t", index=False)
    per_class.to_csv(OUTPUT_TABLE, sep="\t", index=False)

    record = {
        "schema_version": "plant_cellfm_scplantllm_gse270342_matched_embedding_probe_v1",
        "status": "COMPLETED_FROZEN_ENCODER_REPRESENTATION_BASELINE",
        "claim_boundary": (
            "This is a matched-data frozen-encoder representation baseline on the GSE270342 wheat stress test. "
            "It uses the identical author object, first-target author orthogroup mapping and released Plant-CellFM "
            "cell-level train/validation/test split. scPlantLLM itself is not fine-tuned, so the result is not a full "
            "fine-tuning head-to-head ranking and cannot replace the strict leave-species benchmark."
        ),
        "input_contract": {
            "dataset": "GSE270342",
            "species": "Triticum aestivum",
            "prepared_cells": int(adata.n_obs),
            "prepared_genes": int(adata.n_vars),
            "author_label_key": "expert_annotation_raw",
            "orthology": mapping_stats,
            "scplantllm_tokenization": {
                "sequence_length": 1500,
                "selected_nonpadding_tokens_when_available": max_tokens,
                "selection": "deterministic seeded 75% nonzero-token selection, matching the official preprocessing cap",
                "value_handling": f"raw collapsed UMI counts rounded and clipped to [0, {shape.value_pad_index - 1}] for the official categorical value embedding",
            },
        },
        "split_contract": {
            "strategy": "GroupShuffleSplit over unique cell_id values, seed 20260801 then seed+1 for validation",
            "train_cells": int(len(split.train)),
            "validation_cells": int(len(split.validation)),
            "locked_test_cells": int(len(split.test)),
            "locked_test_barcode_match_to_plantcellm": True,
            "debug_limits": {"train": args.limit_train, "test": args.limit_test},
        },
        "model": {
            "official_checkpoint": CHECKPOINT.relative_to(ROOT).as_posix(),
            "checkpoint_sha256": sha256(CHECKPOINT),
            "checkpoint_bytes": int(CHECKPOINT.stat().st_size),
            "checkpoint_load": {"missing_keys": len(missing_keys), "unexpected_keys": len(unexpected_keys), "conversion": conversion.__dict__},
            "shape": shape.__dict__,
            "frozen_encoder_readout": "cosine nearest centroid fitted on the 5,014 training cells only",
            "centroid_train_counts": centroid_counts,
        },
        "execution": {
            "device": str(device),
            "batch_size": int(args.batch_size),
            "embedding_elapsed_seconds": float(elapsed),
            "peak_cuda_memory_mb": float(torch.cuda.max_memory_allocated(device) / 1024**2) if device.type == "cuda" else None,
            "train_sequence_stats": train_sequence_stats,
            "test_sequence_stats": test_sequence_stats,
        },
        "metrics": metrics,
        "artifacts": {
            "train_embeddings": (OUTPUT_DIR / "train_embeddings.npy").relative_to(ROOT).as_posix(),
            "locked_test_embeddings": (OUTPUT_DIR / "locked_test_embeddings.npy").relative_to(ROOT).as_posix(),
            "locked_test_predictions": (OUTPUT_DIR / "locked_test_predictions.tsv").relative_to(ROOT).as_posix(),
            "per_class_table": OUTPUT_TABLE.relative_to(ROOT).as_posix(),
        },
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "accuracy": metrics["accuracy"], "macro_f1": metrics["macro_f1"], "locked_test_cells": len(test_indices)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
