from __future__ import annotations

"""Run a matched partial scPlantLLM adaptation baseline on the wheat stress test.

The protocol deliberately follows the released Plant-CellFM wheat case: the
same prepared GSE270342 object, author orthogroup mapping, GroupShuffleSplit
and exact locked test barcode set.  The official scPlantLLM checkpoint is
loaded cleanly, a new 13-class head is fitted, and only the final transformer
block is unfrozen.  Epoch selection reads validation macro-F1 only; the locked
test is evaluated once after the selected adapter is restored.
"""

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

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
OUTPUT_DIR = ROOT / "outputs" / "external_benchmarks" / "scplantllm_gse270342_partial_finetune"
OUTPUT_JSON = ROOT / "release_metadata" / "scplantllm_gse270342_partial_finetune_v1.json"
OUTPUT_TABLE = ROOT / "supplementary_tables" / "submission_v4" / "Supplementary_Table_S23_scPlantLLM_GSE270342_partial_finetune.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_modules() -> tuple[Any, Any]:
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import run_scplantllm_embedding_centroid_probe as probe
    import run_scplantllm_gse270342_matched_baseline as matched

    return probe, matched


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


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


def metric_payload(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[dict[str, Any], pd.DataFrame]:
    labels = np.asarray(sorted(set(y_true.tolist()) | set(y_pred.tolist()), key=str), dtype=object)
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return (
        {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
            "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
            "class_count": int(len(labels)),
            "class_counts": {str(label): int(count) for label, count in Counter(y_true.tolist()).items()},
        },
        pd.DataFrame({"author_label": labels, "precision": precision, "recall": recall, "f1": f1, "support": support.astype(int)}),
    )


def make_head(d_model: int, n_classes: int) -> torch.nn.Module:
    return torch.nn.Sequential(torch.nn.LayerNorm(d_model), torch.nn.Linear(d_model, n_classes))


def configure_partial_adaptation(model: torch.nn.Module, head: torch.nn.Module, *, last_layer: int) -> tuple[list[str], int]:
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    prefix = f"transformer_encoder.layers.{last_layer}."
    trainable = []
    for name, parameter in model.named_parameters():
        if name.startswith(prefix):
            parameter.requires_grad_(True)
            trainable.append(name)
    if not trainable:
        raise ValueError(f"No parameters found for requested final transformer layer {last_layer}.")
    for parameter in head.parameters():
        parameter.requires_grad_(True)
    return trainable, int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad) + sum(parameter.numel() for parameter in head.parameters() if parameter.requires_grad))


def iter_batches(indices: np.ndarray, batch_size: int, *, seed: int) -> Iterator[np.ndarray]:
    permutation = np.random.default_rng(seed).permutation(indices)
    for start in range(0, len(permutation), batch_size):
        yield permutation[start : start + batch_size]


def deterministic_label_balanced_limit(indices: np.ndarray, labels: np.ndarray, limit: int | None, *, seed: int) -> np.ndarray:
    """Keep every observed label in debug limits so the smoke protocol stays valid."""
    if limit is None or limit >= len(indices):
        return indices
    subset_labels = labels[indices]
    classes = np.asarray(sorted(set(subset_labels.tolist()), key=str), dtype=object)
    if limit < len(classes):
        raise ValueError(f"Debug limit {limit} is smaller than the {len(classes)} observed labels.")
    rng = np.random.default_rng(seed)
    selected: list[int] = []
    remaining: list[int] = []
    for label in classes:
        class_indices = indices[subset_labels == label]
        shuffled = rng.permutation(class_indices)
        selected.append(int(shuffled[0]))
        remaining.extend(int(value) for value in shuffled[1:])
    remaining_count = limit - len(selected)
    if remaining_count:
        selected.extend(int(value) for value in rng.choice(remaining, size=remaining_count, replace=False))
    return np.asarray(sorted(selected), dtype=np.int64)


def forward_logits(
    model: torch.nn.Module,
    head: torch.nn.Module,
    gene_ids: np.ndarray,
    values: np.ndarray,
    *,
    probe: Any,
    shape: Any,
    device: torch.device,
) -> torch.Tensor:
    src, val, padding_mask = probe.prepare_batch(gene_ids, values, shape=shape, device=device, cls_value=0)
    encoded = model._encode(src, val, padding_mask, None)
    cell_embedding = model._get_cell_emb_from_layer(encoded, val)
    return head(cell_embedding)


def evaluate(
    model: torch.nn.Module,
    head: torch.nn.Module,
    gene_ids: np.ndarray,
    values: np.ndarray,
    target_ids: np.ndarray,
    label_names: np.ndarray,
    *,
    probe: Any,
    shape: Any,
    device: torch.device,
    batch_size: int,
    amp: bool,
) -> tuple[dict[str, Any], pd.DataFrame]:
    model.eval()
    head.eval()
    predicted_ids = []
    with torch.inference_mode():
        for start in range(0, len(target_ids), batch_size):
            stop = min(start + batch_size, len(target_ids))
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp and device.type == "cuda"):
                logits = forward_logits(model, head, gene_ids[start:stop], values[start:stop], probe=probe, shape=shape, device=device)
            predicted_ids.append(logits.argmax(dim=1).detach().cpu().numpy())
    prediction_ids = np.concatenate(predicted_ids)
    return metric_payload(label_names[target_ids], label_names[prediction_ids])


def snapshot_adapter(model: torch.nn.Module, head: torch.nn.Module, *, last_layer: int) -> dict[str, Any]:
    prefix = f"transformer_encoder.layers.{last_layer}."
    return {
        "last_layer": last_layer,
        "backbone_last_block": {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items() if name.startswith(prefix)},
        "classification_head": {name: tensor.detach().cpu().clone() for name, tensor in head.state_dict().items()},
    }


def restore_adapter(model: torch.nn.Module, head: torch.nn.Module, state: dict[str, Any]) -> None:
    model_state = model.state_dict()
    model_state.update(state["backbone_last_block"])
    model.load_state_dict(model_state, strict=True)
    head.load_state_dict(state["classification_head"], strict=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument("--backbone-lr", type=float, default=2e-5)
    parser.add_argument("--head-lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-2)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--limit-train", type=int, default=None, help="Deterministic smoke-test limit; never emits a release record.")
    parser.add_argument("--limit-validation", type=int, default=None, help="Deterministic smoke-test limit; never emits a release record.")
    parser.add_argument("--limit-test", type=int, default=None, help="Deterministic smoke-test limit; never emits a release record.")
    args = parser.parse_args()
    if args.batch_size < 1 or args.epochs < 1:
        raise ValueError("--batch-size and --epochs must be positive.")
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
    release_mode = all(value is None for value in (args.limit_train, args.limit_validation, args.limit_test))
    seed_everything(args.seed)
    probe, matched = import_modules()
    device = torch.device(args.device)

    raw_state = probe.unwrap_state_dict(torch.load(CHECKPOINT, map_location="cpu"))
    state, conversion = probe.convert_flashmha_state_dict(raw_state)
    shape = probe.infer_model_shape(state, nhead=8, pad_token_id=0, value_pad_index=None, cls_token_id=None)
    model, missing_keys, unexpected_keys = probe.build_model(SCPLANTLLM, state, shape, device)
    if missing_keys or unexpected_keys:
        raise ValueError("Official scPlantLLM checkpoint did not load cleanly before partial adaptation.")

    adata = ad.read_h5ad(DATA, backed=None)
    cell_ids = adata.obs["cell_id"].astype(str).to_numpy() if "cell_id" in adata.obs else adata.obs_names.astype(str).to_numpy()
    labels = adata.obs["expert_annotation_raw"].astype(str).to_numpy()
    split = group_split(cell_ids, validation_fraction=0.10, test_fraction=0.20, seed=args.seed)
    plantcellm_test = pd.read_csv(PLANTCELLM_TEST, sep="\t", dtype={"cell_id": str})
    locked_test_ids = cell_ids[split.test]
    if set(locked_test_ids.tolist()) != set(plantcellm_test.cell_id.tolist()) or len(locked_test_ids) != len(plantcellm_test):
        raise ValueError("Reconstructed test split does not match Plant-CellFM locked test barcodes.")
    raw_label_lookup = dict(zip(cell_ids, labels, strict=True))
    expected_locked_labels = np.asarray([raw_label_lookup[cell_id] for cell_id in plantcellm_test.cell_id], dtype=str)
    if not np.array_equal(plantcellm_test.true_fine.to_numpy(str), expected_locked_labels):
        raise ValueError("Plant-CellFM locked-test labels do not match the author-labelled source object.")

    train_indices = deterministic_label_balanced_limit(split.train, labels, args.limit_train, seed=args.seed)
    validation_indices = deterministic_label_balanced_limit(split.validation, labels, args.limit_validation, seed=args.seed + 1)
    test_indices = deterministic_label_balanced_limit(split.test, labels, args.limit_test, seed=args.seed + 2)
    label_names = np.asarray(sorted(set(labels[train_indices].tolist()), key=str), dtype=object)
    label_to_id = {label: index for index, label in enumerate(label_names.tolist())}
    if not set(labels[validation_indices].tolist()).issubset(label_to_id) or not set(labels[test_indices].tolist()).issubset(label_to_id):
        raise ValueError("Validation or test contains an author label absent from the training split.")
    target_ids = np.asarray([label_to_id[label] for label in labels], dtype=np.int64)

    mapping, mapping_stats = first_target_scplantllm_mapping()
    lookup = np.asarray([mapping.get(str(gene), 0) for gene in adata.var_names], dtype=np.int64)
    matrix = adata.X.tocsr() if sparse.issparse(adata.X) else sparse.csr_matrix(adata.X)
    max_tokens = int(1500 * 0.75)
    train_gene_ids, train_values, train_sequence_stats = matched.build_sequences(matrix, lookup, train_indices, sequence_length=1500, max_tokens=max_tokens, value_pad=shape.value_pad_index, seed=args.seed)
    validation_gene_ids, validation_values, validation_sequence_stats = matched.build_sequences(matrix, lookup, validation_indices, sequence_length=1500, max_tokens=max_tokens, value_pad=shape.value_pad_index, seed=args.seed + 1)
    test_gene_ids, test_values, test_sequence_stats = matched.build_sequences(matrix, lookup, test_indices, sequence_length=1500, max_tokens=max_tokens, value_pad=shape.value_pad_index, seed=args.seed + 2)
    train_targets = target_ids[train_indices]
    validation_targets = target_ids[validation_indices]
    test_targets = target_ids[test_indices]

    last_layer = shape.nlayers - 1
    head = make_head(shape.d_model, len(label_names)).to(device)
    trainable_names, trainable_parameters = configure_partial_adaptation(model, head, last_layer=last_layer)
    optimizer = torch.optim.AdamW(
        [
            {"params": [parameter for name, parameter in model.named_parameters() if parameter.requires_grad], "lr": args.backbone_lr},
            {"params": list(head.parameters()), "lr": args.head_lr},
        ],
        weight_decay=args.weight_decay,
    )
    criterion = torch.nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler(enabled=device.type == "cuda")
    history: list[dict[str, Any]] = []
    best_state: dict[str, Any] | None = None
    best_epoch = -1
    best_validation_macro_f1 = float("-inf")
    torch.cuda.reset_peak_memory_stats(device) if device.type == "cuda" else None
    started = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        model.train()
        head.train()
        losses = []
        for positions in iter_batches(np.arange(len(train_indices)), args.batch_size, seed=args.seed + epoch):
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                logits = forward_logits(model, head, train_gene_ids[positions], train_values[positions], probe=probe, shape=shape, device=device)
                loss = criterion(logits, torch.as_tensor(train_targets[positions], dtype=torch.long, device=device))
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_([parameter for group in optimizer.param_groups for parameter in group["params"]], args.grad_clip)
            scaler.step(optimizer)
            scaler.update()
            losses.append(float(loss.detach().cpu()))
        validation_metrics, _ = evaluate(model, head, validation_gene_ids, validation_values, validation_targets, label_names, probe=probe, shape=shape, device=device, batch_size=args.batch_size, amp=True)
        record = {"epoch": epoch, "train_cross_entropy": float(np.mean(losses)), **{f"validation_{key}": value for key, value in validation_metrics.items() if key in {"accuracy", "macro_f1", "weighted_f1"}}}
        history.append(record)
        if validation_metrics["macro_f1"] > best_validation_macro_f1:
            best_validation_macro_f1 = float(validation_metrics["macro_f1"])
            best_epoch = epoch
            best_state = snapshot_adapter(model, head, last_layer=last_layer)
    if best_state is None:
        raise RuntimeError("No validation epoch was selected.")
    restore_adapter(model, head, best_state)
    test_metrics, per_class = evaluate(model, head, test_gene_ids, test_values, test_targets, label_names, probe=probe, shape=shape, device=device, batch_size=args.batch_size, amp=True)
    elapsed = time.perf_counter() - started

    output_dir = OUTPUT_DIR if release_mode else OUTPUT_DIR / "debug"
    output_dir.mkdir(parents=True, exist_ok=True)
    adapter_path = output_dir / "best_partial_adapter.pt"
    torch.save(
        {
            "schema_version": "scplantllm_partial_wheat_adapter_v1",
            "base_checkpoint_sha256": sha256(CHECKPOINT),
            "label_names": label_names.tolist(),
            "last_layer": last_layer,
            "best_epoch": best_epoch,
            "best_validation_macro_f1": best_validation_macro_f1,
            "adapter_state": best_state,
        },
        adapter_path,
    )
    pd.DataFrame(history).to_csv(output_dir / "validation_history.tsv", sep="\t", index=False)
    model.eval()
    head.eval()
    prediction_ids = []
    with torch.inference_mode():
        for start in range(0, len(test_indices), args.batch_size):
            stop = min(start + args.batch_size, len(test_indices))
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                logits = forward_logits(model, head, test_gene_ids[start:stop], test_values[start:stop], probe=probe, shape=shape, device=device)
            prediction_ids.append(logits.argmax(dim=1).detach().cpu().numpy())
    test_predictions = label_names[np.concatenate(prediction_ids)]
    predictions = pd.DataFrame({"cell_id": cell_ids[test_indices], "author_label": labels[test_indices], "scplantllm_partial_finetune_prediction": test_predictions})
    predictions.to_csv(output_dir / "locked_test_predictions.tsv", sep="\t", index=False)
    per_class.to_csv(output_dir / "locked_test_per_class.tsv", sep="\t", index=False)

    record = {
        "schema_version": "plant_cellfm_scplantllm_gse270342_partial_finetune_v1",
        "status": "COMPLETED_MATCHED_PARTIAL_BACKBONE_ADAPTATION" if release_mode else "DEBUG_NOT_RELEASE_ELIGIBLE",
        "claim_boundary": (
            "This is a matched-data partial scPlantLLM adaptation baseline on the GSE270342 wheat stress test. "
            "It uses the same author object, first-target orthogroup mapping and exact released Plant-CellFM locked test barcodes. "
            "Only the final scPlantLLM transformer block and a new 13-class head are trainable; all earlier backbone layers stay frozen. "
            "It is an adaptation reference, not a strict leave-species result, independent external validation or full-backbone fine-tuning reproduction."
        ),
        "input_contract": {
            "dataset": "GSE270342",
            "species": "Triticum aestivum",
            "prepared_cells": int(adata.n_obs),
            "prepared_genes": int(adata.n_vars),
            "author_label_key": "expert_annotation_raw",
            "orthology": mapping_stats,
            "scplantllm_tokenization": {"sequence_length": 1500, "selected_nonpadding_tokens_when_available": max_tokens, "selection": "deterministic seeded 75% nonzero-token selection", "value_handling": f"raw collapsed UMI counts rounded and clipped to [0, {shape.value_pad_index - 1}]"},
        },
        "split_contract": {
            "strategy": "GroupShuffleSplit over unique cell_id values, seed 20260801 then seed+1 for validation",
            "train_cells": int(len(split.train)),
            "validation_cells": int(len(split.validation)),
            "locked_test_cells": int(len(split.test)),
            "locked_test_barcode_match_to_plantcellm": True,
            "debug_limits": {"train": args.limit_train, "validation": args.limit_validation, "test": args.limit_test},
        },
        "model": {
            "official_checkpoint": CHECKPOINT.relative_to(ROOT).as_posix(),
            "checkpoint_sha256": sha256(CHECKPOINT),
            "checkpoint_load": {"missing_keys": len(missing_keys), "unexpected_keys": len(unexpected_keys), "conversion": conversion.__dict__},
            "shape": shape.__dict__,
            "adaptation": {"mode": "new_13_class_head_plus_final_transformer_block", "trainable_final_transformer_layer": last_layer, "trainable_backbone_parameter_names": trainable_names, "trainable_parameter_count": trainable_parameters, "frozen_backbone_layers": list(range(last_layer))},
        },
        "selection": {"metric": "validation_macro_f1", "best_epoch": best_epoch, "best_validation_macro_f1": best_validation_macro_f1, "epochs_considered": args.epochs},
        "execution": {"device": str(device), "batch_size": args.batch_size, "epochs": args.epochs, "elapsed_seconds": elapsed, "peak_cuda_memory_mb": float(torch.cuda.max_memory_allocated(device) / 1024**2) if device.type == "cuda" else None, "train_sequence_stats": train_sequence_stats, "validation_sequence_stats": validation_sequence_stats, "test_sequence_stats": test_sequence_stats},
        "locked_test": test_metrics,
        "artifacts": {"adapter_checkpoint": adapter_path.relative_to(ROOT).as_posix(), "adapter_checkpoint_sha256": sha256(adapter_path), "validation_history": (output_dir / "validation_history.tsv").relative_to(ROOT).as_posix(), "locked_test_predictions": (output_dir / "locked_test_predictions.tsv").relative_to(ROOT).as_posix(), "locked_test_per_class": (output_dir / "locked_test_per_class.tsv").relative_to(ROOT).as_posix()},
    }
    if release_mode:
        OUTPUT_JSON.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        per_class.to_csv(OUTPUT_TABLE, sep="\t", index=False)
    print(json.dumps({"status": record["status"], "best_epoch": best_epoch, "validation_macro_f1": best_validation_macro_f1, "locked_test_accuracy": test_metrics["accuracy"], "locked_test_macro_f1": test_metrics["macro_f1"], "peak_cuda_memory_mb": record["execution"]["peak_cuda_memory_mb"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
