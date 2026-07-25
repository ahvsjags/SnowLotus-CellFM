from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support


@dataclass
class StateDictConversion:
    converted_wqkv_weight_count: int
    converted_wqkv_bias_count: int
    skipped_key_count: int
    skipped_key_prefixes: list[str]


@dataclass
class ModelShape:
    ntoken: int
    d_model: int
    nhead: int
    d_hid: int
    nlayers: int
    nlayers_cls: int
    n_cls: int
    n_input_bins: int
    pad_token_id: int
    value_pad_index: int
    cls_token_id: int


def json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )
    return output


def unwrap_state_dict(payload: Any) -> dict[str, torch.Tensor]:
    if not isinstance(payload, dict):
        raise TypeError(f"Unsupported checkpoint payload type: {type(payload)!r}")
    for key in ("state_dict", "model_state_dict", "model"):
        maybe = payload.get(key)
        if isinstance(maybe, dict) and any(torch.is_tensor(v) for v in maybe.values()):
            return dict(maybe)
    if any(torch.is_tensor(value) for value in payload.values()):
        return dict(payload)
    raise ValueError("Could not find tensor state_dict in checkpoint payload.")


def convert_flashmha_state_dict(
    raw_state: dict[str, torch.Tensor],
) -> tuple[dict[str, torch.Tensor], StateDictConversion]:
    converted: dict[str, torch.Tensor] = {}
    skipped_prefixes = {"grad_reverse_discriminator."}
    converted_weight = 0
    converted_bias = 0
    skipped = 0
    for key, value in raw_state.items():
        clean_key = key.removeprefix("module.")
        if any(clean_key.startswith(prefix) for prefix in skipped_prefixes):
            skipped += 1
            continue
        if ".self_attn.Wqkv.weight" in clean_key:
            clean_key = clean_key.replace(".self_attn.Wqkv.weight", ".self_attn.in_proj_weight")
            converted_weight += 1
        elif ".self_attn.Wqkv.bias" in clean_key:
            clean_key = clean_key.replace(".self_attn.Wqkv.bias", ".self_attn.in_proj_bias")
            converted_bias += 1
        converted[clean_key] = value
    return converted, StateDictConversion(
        converted_wqkv_weight_count=converted_weight,
        converted_wqkv_bias_count=converted_bias,
        skipped_key_count=skipped,
        skipped_key_prefixes=sorted(skipped_prefixes),
    )


def infer_model_shape(
    state: dict[str, torch.Tensor],
    *,
    nhead: int,
    pad_token_id: int,
    value_pad_index: int | None,
    cls_token_id: int | None,
) -> ModelShape:
    encoder_weight = state["encoder.embedding.weight"]
    value_weight = state["value_encoder.embedding.weight"]
    layer_ids = []
    for key in state:
        match = re.search(r"transformer_encoder\.layers\.(\d+)\.", key)
        if match:
            layer_ids.append(int(match.group(1)))
    nlayers = max(layer_ids) + 1 if layer_ids else 6
    d_hid = int(state.get("transformer_encoder.layers.0.linear1.weight").shape[0])
    cls_weight = state.get("cls_decoder.out_layer.weight")
    if cls_weight is None:
        cls_weight = state.get("cls_decoder.4.weight")
    n_cls = int(cls_weight.shape[0]) if cls_weight is not None else 44
    ntoken = int(encoder_weight.shape[0])
    n_input_bins = int(value_weight.shape[0])
    resolved_value_pad = value_pad_index if value_pad_index is not None else n_input_bins - 2
    resolved_cls = cls_token_id if cls_token_id is not None else ntoken - 1
    return ModelShape(
        ntoken=ntoken,
        d_model=int(encoder_weight.shape[1]),
        nhead=nhead,
        d_hid=d_hid,
        nlayers=nlayers,
        nlayers_cls=3,
        n_cls=n_cls,
        n_input_bins=n_input_bins,
        pad_token_id=pad_token_id,
        value_pad_index=resolved_value_pad,
        cls_token_id=resolved_cls,
    )


def decode_array(values: np.ndarray) -> np.ndarray:
    if values.dtype.kind in {"S", "O", "U"}:
        return np.asarray(
            [item.decode("utf-8") if isinstance(item, bytes) else str(item) for item in values]
        )
    return values


def read_chunk(path: Path, label_key: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with h5py.File(path, "r") as handle:
        if "gid" not in handle or "ex" not in handle:
            raise KeyError(f"{path} does not contain gid/ex datasets.")
        if label_key not in handle:
            candidates = [key for key in ("major_ctype", "celltype", "cell_type", "labels", "y") if key in handle]
            if not candidates:
                raise KeyError(f"{path} does not contain label dataset {label_key!r}.")
            label_key = candidates[0]
        gids = np.asarray(handle["gid"])
        values = np.asarray(handle["ex"])
        labels = decode_array(np.asarray(handle[label_key]).reshape(-1))
    if gids.shape[0] != values.shape[0] or gids.shape[0] != labels.shape[0]:
        raise ValueError(f"{path} has inconsistent cell dimensions.")
    return gids, values, labels


def valid_label_mask(labels: np.ndarray) -> np.ndarray:
    if labels.dtype.kind in {"i", "u"}:
        return labels >= 0
    if labels.dtype.kind == "f":
        return np.isfinite(labels) & (labels >= 0)
    lowered = np.char.lower(labels.astype(str))
    return ~np.isin(lowered, ["", "nan", "na", "unknown", "unannotated", "none"])


def stratified_sample_indices(labels: np.ndarray, max_count: int | None, seed: int) -> np.ndarray:
    labels = np.asarray(labels)
    total = labels.shape[0]
    if max_count is None or max_count <= 0 or total <= max_count:
        return np.arange(total)
    rng = np.random.default_rng(seed)
    unique = np.asarray(sorted(set(labels.tolist()), key=lambda item: str(item)))
    if len(unique) >= max_count:
        chosen_labels = rng.choice(unique, size=max_count, replace=False)
        picks = [
            int(rng.choice(np.flatnonzero(labels == label), size=1)[0])
            for label in chosen_labels
        ]
        return np.asarray(sorted(picks))

    selected: list[int] = []
    leftovers: list[int] = []
    base = max(1, max_count // max(1, len(unique)))
    for label in unique:
        label_indices = np.flatnonzero(labels == label)
        shuffled = rng.permutation(label_indices)
        take = min(base, len(shuffled))
        selected.extend(int(index) for index in shuffled[:take])
        leftovers.extend(int(index) for index in shuffled[take:])
    remaining = max_count - len(selected)
    if remaining > 0 and leftovers:
        selected.extend(int(index) for index in rng.choice(leftovers, size=min(remaining, len(leftovers)), replace=False))
    return np.asarray(sorted(selected[:max_count]))


def load_split(
    chunks_dir: Path,
    split: str,
    *,
    label_key: str,
    max_cells: int | None,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], dict[str, int]]:
    paths = sorted(chunks_dir.glob(f"{split}_chunk_*.h5"))
    if not paths:
        raise FileNotFoundError(f"No {split}_chunk_*.h5 files found in {chunks_dir}.")
    gids_list = []
    values_list = []
    labels_list = []
    for path in paths:
        gids, values, labels = read_chunk(path, label_key)
        mask = valid_label_mask(labels)
        gids_list.append(gids[mask])
        values_list.append(values[mask])
        labels_list.append(labels[mask])
    gids = np.concatenate(gids_list, axis=0)
    values = np.concatenate(values_list, axis=0)
    labels = np.concatenate(labels_list, axis=0)
    original_counts = label_counts(labels)
    indices = stratified_sample_indices(labels, max_cells, seed)
    return (
        gids[indices],
        values[indices],
        labels[indices],
        [path.as_posix() for path in paths],
        original_counts,
    )


def label_counts(labels: np.ndarray) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(Counter(labels.tolist()).items())}


def resolve_device(device: str) -> torch.device:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    resolved = torch.device(device)
    if resolved.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
    return resolved


def prepare_batch(
    gids: np.ndarray,
    values: np.ndarray,
    *,
    shape: ModelShape,
    device: torch.device,
    cls_value: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    gids = gids.astype(np.int64, copy=False)
    raw_values = values.astype(np.int64, copy=False)
    pad_mask = raw_values < 0
    prepared_values = np.where(pad_mask, shape.value_pad_index, raw_values)
    if gids.min(initial=0) < 0 or gids.max(initial=0) >= shape.ntoken:
        raise ValueError(
            f"Gene id range [{gids.min()}, {gids.max()}] exceeds ntoken={shape.ntoken}."
        )
    if prepared_values.min(initial=0) < 0 or prepared_values.max(initial=0) >= shape.n_input_bins:
        raise ValueError(
            "Expression bin range "
            f"[{prepared_values.min()}, {prepared_values.max()}] exceeds n_input_bins="
            f"{shape.n_input_bins}."
        )
    batch_size = gids.shape[0]
    cls_src = np.full((batch_size, 1), shape.cls_token_id, dtype=np.int64)
    cls_values = np.full((batch_size, 1), cls_value, dtype=np.int64)
    cls_mask = np.zeros((batch_size, 1), dtype=bool)
    src = np.concatenate([cls_src, gids], axis=1)
    val = np.concatenate([cls_values, prepared_values], axis=1)
    mask = np.concatenate([cls_mask, pad_mask], axis=1)
    return (
        torch.as_tensor(src, dtype=torch.long, device=device),
        torch.as_tensor(val, dtype=torch.long, device=device),
        torch.as_tensor(mask, dtype=torch.bool, device=device),
    )


def import_transformer_model(scplantllm_dir: Path) -> type:
    (Path.cwd() / "log").mkdir(exist_ok=True)
    (scplantllm_dir / "log").mkdir(exist_ok=True)
    sys.path.insert(0, scplantllm_dir.as_posix())
    from scplantllm.model import TransformerModel  # type: ignore

    return TransformerModel


def build_model(
    scplantllm_dir: Path,
    state: dict[str, torch.Tensor],
    shape: ModelShape,
    device: torch.device,
) -> tuple[torch.nn.Module, list[str], list[str]]:
    TransformerModel = import_transformer_model(scplantllm_dir)
    model = TransformerModel(
        ntoken=shape.ntoken,
        d_model=shape.d_model,
        nhead=shape.nhead,
        d_hid=shape.d_hid,
        nlayers=shape.nlayers,
        nlayers_cls=shape.nlayers_cls,
        n_cls=shape.n_cls,
        dropout=0.2,
        pad_value=shape.value_pad_index,
        pad_token_id=shape.pad_token_id,
        input_emb_style="category",
        n_input_bins=shape.n_input_bins,
        cell_emb_style="cls",
        use_fast_transformer=False,
    )
    incompatible = model.load_state_dict(state, strict=False)
    model.to(device)
    model.eval()
    return model, list(incompatible.missing_keys), list(incompatible.unexpected_keys)


def encode_embeddings(
    model: torch.nn.Module,
    gids: np.ndarray,
    values: np.ndarray,
    *,
    shape: ModelShape,
    device: torch.device,
    batch_size: int,
    cls_value: int,
) -> np.ndarray:
    embeddings = []
    with torch.inference_mode():
        for start in range(0, gids.shape[0], batch_size):
            stop = min(start + batch_size, gids.shape[0])
            src, val, mask = prepare_batch(
                gids[start:stop],
                values[start:stop],
                shape=shape,
                device=device,
                cls_value=cls_value,
            )
            output = model(src, val, mask, CLS=False)
            embeddings.append(output["cell_emb"].detach().cpu().float().numpy())
    return np.concatenate(embeddings, axis=0)


def l2_normalize(matrix: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    norm = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norm, eps)


def nearest_centroid_predictions(
    train_embeddings: np.ndarray,
    train_labels: np.ndarray,
    test_embeddings: np.ndarray,
) -> tuple[np.ndarray, dict[str, int]]:
    train_norm = l2_normalize(train_embeddings.astype(np.float64, copy=False))
    test_norm = l2_normalize(test_embeddings.astype(np.float64, copy=False))
    labels = np.asarray(sorted(set(train_labels.tolist()), key=lambda item: str(item)))
    centroids = []
    centroid_counts: dict[str, int] = {}
    for label in labels:
        label_matrix = train_norm[train_labels == label]
        centroid = label_matrix.mean(axis=0)
        centroid = centroid / max(float(np.linalg.norm(centroid)), 1e-12)
        centroids.append(centroid)
        centroid_counts[str(label)] = int(label_matrix.shape[0])
    centroid_matrix = np.vstack(centroids)
    scores = test_norm @ centroid_matrix.T
    return labels[np.argmax(scores, axis=1)], centroid_counts


def metric_payload(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    labels = np.asarray(sorted(set(y_true.tolist()) | set(y_pred.tolist()), key=lambda item: str(item)))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "micro_f1": float(f1_score(y_true, y_pred, average="micro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "per_class": [
            {
                "label": str(label),
                "precision": float(p),
                "recall": float(r),
                "f1": float(f),
                "support": int(s),
            }
            for label, p, r, f, s in zip(labels, precision, recall, f1, support, strict=True)
        ],
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    project_dir = args.project_dir.resolve()
    chunks_dir = (project_dir / args.chunks_dir).resolve()
    scplantllm_dir = (project_dir / args.scplantllm_dir).resolve()
    weight_path = (scplantllm_dir / args.weight_path).resolve()
    device = resolve_device(args.device)

    raw_checkpoint = torch.load(weight_path, map_location="cpu")
    raw_state = unwrap_state_dict(raw_checkpoint)
    converted_state, conversion = convert_flashmha_state_dict(raw_state)
    shape = infer_model_shape(
        converted_state,
        nhead=args.nhead,
        pad_token_id=args.pad_token_id,
        value_pad_index=args.value_pad_index,
        cls_token_id=args.cls_token_id,
    )
    model, missing_keys, unexpected_keys = build_model(
        scplantllm_dir,
        converted_state,
        shape,
        device,
    )

    train_gids, train_values, train_labels, train_files, train_original_counts = load_split(
        chunks_dir,
        args.train_split,
        label_key=args.label_key,
        max_cells=args.max_train,
        seed=args.seed,
    )
    test_gids, test_values, test_labels, test_files, test_original_counts = load_split(
        chunks_dir,
        args.test_split,
        label_key=args.label_key,
        max_cells=args.max_test,
        seed=args.seed + 1,
    )

    train_embeddings = encode_embeddings(
        model,
        train_gids,
        train_values,
        shape=shape,
        device=device,
        batch_size=args.batch_size,
        cls_value=args.cls_value,
    )
    test_embeddings = encode_embeddings(
        model,
        test_gids,
        test_values,
        shape=shape,
        device=device,
        batch_size=args.batch_size,
        cls_value=args.cls_value,
    )
    predictions, centroid_counts = nearest_centroid_predictions(
        train_embeddings,
        train_labels,
        test_embeddings,
    )
    metrics = metric_payload(test_labels, predictions)
    unseen_test_labels = sorted(
        {str(label) for label in test_labels.tolist()} - {str(label) for label in train_labels.tolist()}
    )

    return {
        "method": "scplantllm_frozen_embedding_nearest_centroid_probe",
        "status": "completed",
        "interpretation": (
            "Frozen scPlantLLM encoder embeddings are evaluated with a nearest-centroid "
            "probe trained on the local train chunk labels. This is a reproducible "
            "external-model representation baseline, not a full supervised reproduction "
            "of the scPlantLLM classifier head."
        ),
        "limitations": [
            "Official FlashMHA checkpoint keys are mapped to PyTorch MultiheadAttention keys.",
            "The public sprint label vocabulary is local to the prepared chunks.",
            "Metrics depend on the configured max_train/max_test subset sizes.",
        ],
        "device": str(device),
        "model": {
            "scplantllm_dir": scplantllm_dir.relative_to(project_dir).as_posix(),
            "checkpoint": weight_path.relative_to(project_dir).as_posix(),
            "checkpoint_bytes": weight_path.stat().st_size,
            "shape": asdict(shape),
            "state_dict_conversion": asdict(conversion),
            "missing_keys_count": len(missing_keys),
            "unexpected_keys_count": len(unexpected_keys),
            "missing_keys": missing_keys[:50],
            "unexpected_keys": unexpected_keys[:50],
        },
        "data": {
            "chunks_dir": chunks_dir.relative_to(project_dir).as_posix(),
            "train_split": args.train_split,
            "test_split": args.test_split,
            "train_files": [Path(path).relative_to(project_dir).as_posix() for path in train_files],
            "test_files": [Path(path).relative_to(project_dir).as_posix() for path in test_files],
            "selected_train_cells": int(train_labels.shape[0]),
            "selected_test_cells": int(test_labels.shape[0]),
            "original_train_label_counts": train_original_counts,
            "original_test_label_counts": test_original_counts,
            "selected_train_label_counts": label_counts(train_labels),
            "selected_test_label_counts": label_counts(test_labels),
            "unseen_test_labels": unseen_test_labels,
        },
        "probe": {
            "classifier": "cosine_nearest_centroid",
            "centroid_train_counts": centroid_counts,
        },
        "metrics": metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a frozen scPlantLLM embedding nearest-centroid probe."
    )
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument(
        "--chunks-dir",
        default="outputs/external_benchmarks/scplantllm_public_sprint_input/reference_preprocess/chunks",
        type=Path,
    )
    parser.add_argument("--scplantllm-dir", default="external/scPlantLLM", type=Path)
    parser.add_argument("--weight-path", default="model_params/scPlantLLM_model.pth", type=Path)
    parser.add_argument(
        "--output",
        default="outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json",
        type=Path,
    )
    parser.add_argument("--label-key", default="major_ctype")
    parser.add_argument("--train-split", default="train")
    parser.add_argument("--test-split", default="test")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", default=2, type=int)
    parser.add_argument("--max-train", default=512, type=int)
    parser.add_argument("--max-test", default=512, type=int)
    parser.add_argument("--seed", default=1234, type=int)
    parser.add_argument("--nhead", default=8, type=int)
    parser.add_argument("--pad-token-id", default=0, type=int)
    parser.add_argument("--value-pad-index", default=None, type=int)
    parser.add_argument("--cls-token-id", default=None, type=int)
    parser.add_argument("--cls-value", default=0, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1.")
    payload = run_probe(args)
    output = args.output
    if not output.is_absolute():
        output = args.project_dir / output
    write_json(payload, output)
    print(output)


if __name__ == "__main__":
    main()
