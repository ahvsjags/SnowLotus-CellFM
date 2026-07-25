from __future__ import annotations

import csv
import math
import random
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, f1_score
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR
from torch.utils.data import DataLoader, WeightedRandomSampler

from .artifacts import (
    checkpoint_payload,
    load_checkpoint,
    model_from_checkpoint,
    read_json,
    save_checkpoint,
    vocabs_from_checkpoint,
    write_json,
)
from .config import DataConfig, ExperimentConfig
from .data import (
    ExpressionDataset,
    PreparedData,
    make_demo_data,
    prepare_data,
    prepare_inference_data,
)
from .model import ModelConfig, SnowCellModel, load_matching_state_dict


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def default_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_model_config(config: ExperimentConfig, prepared: PreparedData) -> ModelConfig:
    fine_classes = len(prepared.fine_vocab) if prepared.fine_vocab is not None else 1
    coarse_classes = len(prepared.coarse_vocab) if prepared.coarse_vocab is not None else 1
    return ModelConfig(
        vocab_size=len(prepared.gene_vocab),
        num_fine_classes=fine_classes,
        num_coarse_classes=coarse_classes,
        num_species=len(prepared.species_vocab),
        num_tissues=len(prepared.tissue_vocab),
        d_model=config.architecture.d_model,
        n_layers=config.architecture.n_layers,
        n_heads=config.architecture.n_heads,
        ffn_dim=config.architecture.ffn_dim,
        dropout=config.architecture.dropout,
        value_bins=config.architecture.value_bins,
        lora_rank=config.architecture.lora_rank,
        lora_alpha=config.architecture.lora_alpha,
        lora_dropout=config.architecture.lora_dropout,
        gradient_checkpointing=config.architecture.gradient_checkpointing,
        pad_id=prepared.gene_vocab.pad_id,
        cls_id=prepared.gene_vocab.cls_id,
        mask_id=prepared.gene_vocab.mask_id,
    )


def make_dataset(prepared: PreparedData, split: str, config: ExperimentConfig) -> ExpressionDataset:
    indices = getattr(prepared.split, split)
    return ExpressionDataset(
        prepared.matrix,
        indices,
        config.data,
        prepared.gene_vocab,
        fine_vocab=prepared.fine_vocab,
        coarse_vocab=prepared.coarse_vocab,
        species_vocab=prepared.species_vocab,
        tissue_vocab=prepared.tissue_vocab,
    )


def make_loader(
    dataset: ExpressionDataset,
    batch_size: int,
    shuffle: bool,
    num_workers: int,
    class_balance: bool = False,
) -> DataLoader[dict[str, torch.Tensor]]:
    sampler = None
    if class_balance and np.all(dataset.fine_ids[dataset.indices] >= 0):
        labels = dataset.fine_ids[dataset.indices]
        counts = np.bincount(labels)
        weights = 1.0 / np.maximum(counts[labels], 1)
        sampler = WeightedRandomSampler(weights.tolist(), len(weights), replacement=True)
        shuffle = False
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        sampler=sampler,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )


def move_batch(batch: dict[str, torch.Tensor], device: torch.device) -> dict[str, torch.Tensor]:
    return {key: value.to(device, non_blocking=True) for key, value in batch.items()}


def autocast_context(device: torch.device, precision: str):
    if device.type != "cuda" or precision == "no":
        return nullcontext()
    dtype = torch.float16 if precision == "fp16" else torch.bfloat16
    return torch.autocast(device_type="cuda", dtype=dtype)


def make_mlm_inputs(
    batch: dict[str, torch.Tensor],
    mask_ratio: float,
    mask_id: int,
    cls_id: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    gene_ids = batch["gene_ids"].clone()
    values = batch["values"]
    padding_mask = batch["padding_mask"]
    candidates = (~padding_mask) & (gene_ids != cls_id)
    mask = (torch.rand(gene_ids.shape, device=gene_ids.device) < mask_ratio) & candidates

    missing = candidates.any(dim=1) & (~mask.any(dim=1))
    if missing.any():
        rows = torch.nonzero(missing, as_tuple=False).flatten()
        for row in rows.tolist():
            first = torch.nonzero(candidates[row], as_tuple=False)[0].item()
            mask[row, first] = True

    target_gene_ids = gene_ids[mask].clone()
    target_values = values[mask].clone()
    gene_ids[mask] = mask_id
    return gene_ids, values, mask, target_gene_ids, target_values


def hierarchy_loss(
    fine_logits: torch.Tensor,
    coarse_labels: torch.Tensor,
    fine_to_coarse: torch.Tensor | None,
    num_coarse: int,
    fine_labels: torch.Tensor | None = None,
) -> torch.Tensor:
    coarse_labels = coarse_labels.to(fine_logits.device)
    valid = coarse_labels >= 0
    if fine_to_coarse is None or not torch.any(valid):
        return fine_logits.sum() * 0.0
    mapping = fine_to_coarse.to(fine_logits.device)
    known_fine = mapping >= 0
    if not torch.any(known_fine):
        return fine_logits.sum() * 0.0
    if fine_labels is not None:
        fine_labels = fine_labels.to(fine_logits.device)
        valid = valid.to(fine_logits.device) & (fine_labels >= 0)
        if not torch.any(valid):
            return fine_logits.sum() * 0.0
        valid_indices = torch.nonzero(valid, as_tuple=False).flatten()
        valid_known = mapping[fine_labels[valid_indices]] >= 0
        if not torch.any(valid_known):
            return fine_logits.sum() * 0.0
        filtered_indices = valid_indices[valid_known]
        valid = torch.zeros_like(valid, dtype=torch.bool)
        valid[filtered_indices] = True
    fine_probs = torch.softmax(fine_logits[valid], dim=-1)
    known_mapping = mapping[known_fine]
    fine_probs = fine_probs[:, known_fine]
    coarse_probs = torch.zeros(
        fine_probs.shape[0],
        num_coarse,
        dtype=fine_probs.dtype,
        device=fine_probs.device,
    )
    coarse_probs.scatter_add_(1, known_mapping[None, :].expand_as(fine_probs), fine_probs)
    coarse_targets = coarse_labels[valid]
    coarse_has_known_fine = torch.zeros(
        num_coarse,
        dtype=torch.bool,
        device=fine_logits.device,
    )
    coarse_has_known_fine[known_mapping] = True
    target_known = coarse_has_known_fine[coarse_targets]
    if not torch.any(target_known):
        return fine_logits.sum() * 0.0
    return F.nll_loss(
        torch.log(coarse_probs[target_known].clamp_min(1e-8)),
        coarse_targets[target_known],
    )


def classification_losses(
    outputs: dict[str, torch.Tensor],
    batch: dict[str, torch.Tensor],
    config: ExperimentConfig,
    fine_to_coarse: torch.Tensor | None,
) -> dict[str, torch.Tensor]:
    losses: dict[str, torch.Tensor] = {}
    fine_labels = batch["fine_label"]
    coarse_labels = batch["coarse_label"]
    if torch.any(fine_labels >= 0):
        losses["fine_loss"] = F.cross_entropy(
            outputs["fine_logits"],
            fine_labels,
            ignore_index=-1,
            label_smoothing=config.train.label_smoothing,
        )
    if torch.any(coarse_labels >= 0):
        losses["coarse_loss"] = F.cross_entropy(
            outputs["coarse_logits"],
            coarse_labels,
            ignore_index=-1,
            label_smoothing=config.train.label_smoothing,
        )
        losses["hierarchy_loss"] = hierarchy_loss(
            outputs["fine_logits"],
            coarse_labels,
            fine_to_coarse,
            outputs["coarse_logits"].shape[-1],
            fine_labels,
        )
    return losses


def unwrap_model(model: nn.Module) -> SnowCellModel:
    return getattr(model, "_orig_mod", model)


def compute_batch_loss(
    model: nn.Module,
    batch: dict[str, torch.Tensor],
    config: ExperimentConfig,
    fine_to_coarse: torch.Tensor | None,
) -> tuple[torch.Tensor, dict[str, float], dict[str, torch.Tensor]]:
    stage = config.train.stage
    use_mlm = stage in {"pretrain", "hybrid"}
    base_model = unwrap_model(model)
    if use_mlm:
        gene_ids, values, mlm_positions, target_gene_ids, target_values = make_mlm_inputs(
            batch,
            config.train.mask_ratio,
            base_model.config.mask_id,
            base_model.config.cls_id,
        )
    else:
        gene_ids = batch["gene_ids"]
        values = batch["values"]
        mlm_positions = None
        target_gene_ids = torch.empty(0, dtype=torch.long, device=gene_ids.device)
        target_values = torch.empty(0, dtype=values.dtype, device=values.device)

    outputs = model(
        gene_ids=gene_ids,
        values=values,
        padding_mask=batch["padding_mask"],
        species_id=batch["species_id"],
        tissue_id=batch["tissue_id"],
        mlm_positions=mlm_positions,
    )

    losses: dict[str, torch.Tensor] = {}
    if stage in {"supervised", "hybrid"}:
        losses.update(classification_losses(outputs, batch, config, fine_to_coarse))

    if use_mlm and target_gene_ids.numel() > 0:
        losses["mlm_gene_loss"] = F.cross_entropy(outputs["gene_logits"], target_gene_ids)
        losses["mlm_value_loss"] = F.smooth_l1_loss(outputs["value_prediction"], target_values)

    if not losses:
        raise ValueError("当前训练阶段没有可计算的损失，请检查配置与数据标签")

    total = torch.zeros((), dtype=values.dtype, device=values.device)
    total = total + losses.get("fine_loss", total * 0.0)
    total = total + config.train.coarse_loss_weight * losses.get("coarse_loss", total * 0.0)
    total = total + config.train.hierarchy_loss_weight * losses.get(
        "hierarchy_loss",
        total * 0.0,
    )
    total = total + config.train.mlm_loss_weight * losses.get("mlm_gene_loss", total * 0.0)
    total = total + config.train.value_loss_weight * losses.get(
        "mlm_value_loss",
        total * 0.0,
    )

    scalar_losses = {"loss": float(total.detach().cpu())}
    scalar_losses.update({key: float(value.detach().cpu()) for key, value in losses.items()})
    return total, scalar_losses, outputs


def create_optimizer(model: nn.Module, config: ExperimentConfig) -> AdamW:
    head_lr = config.train.head_learning_rate
    if head_lr is None:
        parameters = [item for item in model.parameters() if item.requires_grad]
        return AdamW(parameters, lr=config.train.learning_rate, weight_decay=config.train.weight_decay)

    head_names = ("fine_head", "coarse_head")
    head_params = []
    base_params = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if name.startswith(head_names):
            head_params.append(parameter)
        else:
            base_params.append(parameter)
    return AdamW(
        [
            {"params": base_params, "lr": config.train.learning_rate},
            {"params": head_params, "lr": head_lr},
        ],
        weight_decay=config.train.weight_decay,
    )


def create_scheduler(optimizer: AdamW, steps: int, warmup_fraction: float) -> LambdaLR:
    warmup = max(1, int(steps * warmup_fraction))

    def lr_lambda(step: int) -> float:
        if step < warmup:
            return float(step + 1) / float(warmup)
        progress = (step - warmup) / max(1, steps - warmup)
        return 0.5 * (1.0 + math.cos(math.pi * min(progress, 1.0)))

    return LambdaLR(optimizer, lr_lambda)


def summarize_losses(items: list[dict[str, float]]) -> dict[str, float]:
    if not items:
        return {}
    keys = sorted({key for item in items for key in item})
    return {
        key: float(np.mean([item[key] for item in items if key in item]))
        for key in keys
    }


def write_training_progress(output_dir: Path, record: dict[str, Any]) -> None:
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    progress_log = output_dir / "progress.jsonl"
    with progress_log.open("a", encoding="utf-8") as handle:
        handle.write(json_line(payload))
    write_json(output_dir / "progress_latest.json", payload)


def json_line(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader[dict[str, torch.Tensor]],
    config: ExperimentConfig,
    device: torch.device,
    fine_to_coarse: torch.Tensor | None,
    max_batches: int | None = None,
) -> dict[str, float]:
    model.eval()
    losses = []
    fine_true: list[int] = []
    fine_pred: list[int] = []
    coarse_true: list[int] = []
    coarse_pred: list[int] = []
    for batch_index, raw_batch in enumerate(loader, start=1):
        if max_batches is not None and batch_index > max_batches:
            break
        batch = move_batch(raw_batch, device)
        with autocast_context(device, config.train.mixed_precision):
            _, batch_losses, outputs = compute_batch_loss(model, batch, config, fine_to_coarse)
        losses.append(batch_losses)
        fine_labels = batch["fine_label"].detach().cpu().numpy()
        coarse_labels = batch["coarse_label"].detach().cpu().numpy()
        fine_predictions = outputs["fine_logits"].argmax(dim=-1).detach().cpu().numpy()
        coarse_predictions = outputs["coarse_logits"].argmax(dim=-1).detach().cpu().numpy()
        fine_mask = fine_labels >= 0
        coarse_mask = coarse_labels >= 0
        fine_true.extend(fine_labels[fine_mask].tolist())
        fine_pred.extend(fine_predictions[fine_mask].tolist())
        coarse_true.extend(coarse_labels[coarse_mask].tolist())
        coarse_pred.extend(coarse_predictions[coarse_mask].tolist())

    metrics = {f"eval_{key}": value for key, value in summarize_losses(losses).items()}
    metrics["eval_batches"] = float(len(losses))
    if fine_true:
        metrics["fine_accuracy"] = float(accuracy_score(fine_true, fine_pred))
        metrics["fine_macro_f1"] = float(f1_score(fine_true, fine_pred, average="macro"))
    if coarse_true:
        metrics["coarse_accuracy"] = float(accuracy_score(coarse_true, coarse_pred))
        metrics["coarse_macro_f1"] = float(f1_score(coarse_true, coarse_pred, average="macro"))
    return metrics


def _copy_named_rows(
    target: torch.Tensor,
    source: torch.Tensor,
    source_names: list[str] | tuple[str, ...],
    target_names: list[str] | tuple[str, ...],
) -> tuple[torch.Tensor | None, int]:
    if source.ndim != target.ndim or source.shape[1:] != target.shape[1:]:
        return None, 0
    target_lookup = {str(name): index for index, name in enumerate(target_names)}
    source_indices: list[int] = []
    target_indices: list[int] = []
    for source_index, name in enumerate(source_names):
        target_index = target_lookup.get(str(name))
        if target_index is None:
            continue
        if source_index >= source.shape[0] or target_index >= target.shape[0]:
            continue
        source_indices.append(source_index)
        target_indices.append(target_index)
    if not source_indices:
        return None, 0
    adapted = target.detach().clone()
    source_index_tensor = torch.as_tensor(source_indices, dtype=torch.long, device=source.device)
    target_index_tensor = torch.as_tensor(target_indices, dtype=torch.long, device=target.device)
    adapted[target_index_tensor] = source.index_select(0, source_index_tensor).to(
        device=target.device,
        dtype=target.dtype,
    )
    return adapted, len(source_indices)


def _adapt_checkpoint_state_for_current_vocabs(
    model: SnowCellModel,
    state: dict[str, torch.Tensor],
    checkpoint: dict[str, Any],
    prepared: PreparedData,
) -> dict[str, int]:
    current = model.state_dict()
    transfers: dict[str, int] = {}

    def adapt_rows(
        key: str,
        source_names: list[str] | tuple[str, ...],
        target_names: list[str] | tuple[str, ...],
    ) -> None:
        if key not in state or key not in current:
            return
        if state[key].shape == current[key].shape:
            return
        adapted, copied = _copy_named_rows(
            current[key],
            state[key],
            source_names,
            target_names,
        )
        if adapted is None:
            return
        state[key] = adapted
        transfers[key] = copied

    adapt_rows(
        "gene_embedding.weight",
        list(checkpoint.get("gene_vocab") or []),
        list(prepared.gene_vocab.tokens),
    )
    adapt_rows(
        "species_embedding.weight",
        list(checkpoint.get("species_vocab") or []),
        list(prepared.species_vocab.labels),
    )
    adapt_rows(
        "tissue_embedding.weight",
        list(checkpoint.get("tissue_vocab") or []),
        list(prepared.tissue_vocab.labels),
    )
    if prepared.fine_vocab is not None:
        fine_names = list(checkpoint.get("fine_vocab") or [])
        target_fine = list(prepared.fine_vocab.labels)
        adapt_rows("fine_head.layers.4.weight", fine_names, target_fine)
        adapt_rows("fine_head.layers.4.bias", fine_names, target_fine)
    if prepared.coarse_vocab is not None:
        coarse_names = list(checkpoint.get("coarse_vocab") or [])
        target_coarse = list(prepared.coarse_vocab.labels)
        adapt_rows("coarse_head.layers.4.weight", coarse_names, target_coarse)
        adapt_rows("coarse_head.layers.4.bias", coarse_names, target_coarse)
    return transfers


def maybe_load_init_checkpoint(
    model: SnowCellModel,
    path: str | None,
    device: torch.device,
    prepared: PreparedData | None = None,
) -> None:
    if not path:
        return
    checkpoint = load_checkpoint(path, map_location=device)
    state = checkpoint.get("model_state", checkpoint)
    transfers = (
        _adapt_checkpoint_state_for_current_vocabs(model, state, checkpoint, prepared)
        if prepared is not None and isinstance(checkpoint, dict)
        else {}
    )
    report = load_matching_state_dict(model, state)
    skipped = len(report["incompatible_shape_keys"]) + len(report["unexpected_keys"])
    if transfers:
        transfer_text = ", ".join(f"{key}:{count}" for key, count in sorted(transfers.items()))
        print(f"Loaded init checkpoint with {skipped} skipped keys; vocab row transfers: {transfer_text}")
    else:
        print(f"Loaded init checkpoint with {skipped} skipped keys")


def _load_checkpoint_sidecar_history(path: str | Path) -> list[dict[str, Any]]:
    history_path = Path(path).parent / "history.json"
    if not history_path.exists():
        return []
    try:
        payload = read_json(history_path)
    except (OSError, TypeError, ValueError):
        return []
    epochs = payload.get("epochs", [])
    return epochs if isinstance(epochs, list) else []


def _max_completed_epoch(history: list[dict[str, Any]]) -> int:
    completed_epochs = [
        int(row.get("epoch", 0) or 0)
        for row in history
        if isinstance(row, dict)
    ]
    return max(completed_epochs, default=0)


def maybe_load_resume_checkpoint(
    model: SnowCellModel,
    optimizer: AdamW,
    scheduler: LambdaLR,
    scaler: torch.amp.GradScaler,
    path: str | None,
    device: torch.device,
) -> dict[str, Any]:
    if not path:
        return {"start_epoch": 1, "optimizer_updates": 0, "history": []}
    checkpoint = load_checkpoint(path, map_location=device)
    state = checkpoint.get("model_state", checkpoint)
    report = load_matching_state_dict(model, state)
    skipped = len(report["incompatible_shape_keys"]) + len(report["unexpected_keys"])
    if "optimizer_state" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state"])
    if "scheduler_state" in checkpoint:
        scheduler.load_state_dict(checkpoint["scheduler_state"])
    if "scaler_state" in checkpoint:
        scaler.load_state_dict(checkpoint["scaler_state"])
    metrics = checkpoint.get("metrics", {})
    trainer_state = checkpoint.get("trainer_state", {})
    epoch = int(trainer_state.get("epoch", checkpoint.get("epoch", metrics.get("epoch", 0))) or 0)
    step = int(trainer_state.get("step", metrics.get("step", 0)) or 0)
    train_batches_per_epoch = int(
        trainer_state.get("train_batches_per_epoch", metrics.get("train_batches_per_epoch", 0)) or 0
    )
    optimizer_updates = int(trainer_state.get("optimizer_updates", metrics.get("optimizer_updates", 0)) or 0)
    history = checkpoint.get("history", [])
    if not isinstance(history, list):
        history = []
    sidecar_history = _load_checkpoint_sidecar_history(path)
    if len(sidecar_history) > len(history):
        history = sidecar_history
    completed_epoch = _max_completed_epoch(history)
    is_mid_epoch_latest = (
        trainer_state.get("checkpoint_kind") == "latest"
        and step > 0
        and train_batches_per_epoch > 0
        and step < train_batches_per_epoch
        and completed_epoch < epoch
    )
    start_epoch = epoch if is_mid_epoch_latest else max(epoch + 1, completed_epoch + 1)
    resume_mode = "mid-epoch latest" if is_mid_epoch_latest else "completed checkpoint"
    print(
        "Loaded resume checkpoint "
        f"from epoch {epoch}; next epoch {start_epoch}; "
        f"mode={resume_mode}; "
        f"optimizer_updates={optimizer_updates}; skipped={skipped}"
    )
    return {
        "start_epoch": max(1, start_epoch),
        "optimizer_updates": optimizer_updates,
        "history": history,
        "path": path,
        "skipped": skipped,
    }


def train_from_config(config_path: str | Path, device: torch.device | None = None) -> dict[str, Any]:
    config = ExperimentConfig.load(config_path)
    set_seed(config.train.seed)
    device = device or default_device()
    require_labels = config.train.stage in {"supervised", "hybrid"}
    prepared = prepare_data(config.data, config.train.seed, require_labels=require_labels)
    output_dir = Path(config.output.directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "preprocessing_stats.json", prepared.preprocessing_stats)
    write_json(output_dir / "config.resolved.json", config.to_dict())

    base_model = SnowCellModel(build_model_config(config, prepared)).to(device)
    if not config.train.resume_checkpoint:
        maybe_load_init_checkpoint(base_model, config.train.init_checkpoint, device, prepared)
    base_model.configure_tuning(config.train.tuning_mode, config.train.train_last_n_layers)
    model: nn.Module = base_model
    if config.train.compile_model:
        model = torch.compile(base_model)

    train_dataset = make_dataset(prepared, "train", config)
    validation_dataset = make_dataset(prepared, "validation", config)
    test_dataset = make_dataset(prepared, "test", config)
    train_loader = make_loader(
        train_dataset,
        config.train.batch_size,
        shuffle=True,
        num_workers=config.train.num_workers,
        class_balance=config.train.class_balance and require_labels,
    )
    validation_loader = make_loader(
        validation_dataset,
        config.train.eval_batch_size,
        shuffle=False,
        num_workers=config.train.num_workers,
    )
    test_loader = make_loader(
        test_dataset,
        config.train.eval_batch_size,
        shuffle=False,
        num_workers=config.train.num_workers,
    )

    optimizer = create_optimizer(base_model, config)
    train_batches_per_epoch = len(train_loader)
    if config.train.max_train_batches_per_epoch is not None:
        train_batches_per_epoch = min(
            train_batches_per_epoch,
            config.train.max_train_batches_per_epoch,
        )
    update_steps = math.ceil(train_batches_per_epoch / config.train.gradient_accumulation_steps)
    scheduler = create_scheduler(
        optimizer,
        max(1, update_steps * config.train.epochs),
        config.train.warmup_fraction,
    )
    scaler = torch.amp.GradScaler(
        "cuda",
        enabled=device.type == "cuda" and config.train.mixed_precision == "fp16"
    )
    fine_to_coarse = (
        torch.as_tensor(prepared.fine_to_coarse, dtype=torch.long, device=device)
        if prepared.fine_to_coarse is not None
        else None
    )
    resume_state = maybe_load_resume_checkpoint(
        base_model,
        optimizer,
        scheduler,
        scaler,
        config.train.resume_checkpoint,
        device,
    )

    best_metric = float("inf")
    best_epoch = -1
    bad_epochs = 0
    history: list[dict[str, Any]] = list(resume_state["history"])
    optimizer_updates = int(resume_state["optimizer_updates"])
    start_epoch = int(resume_state["start_epoch"])
    print(f"Device: {device}; parameters: {base_model.parameter_report()}")
    write_training_progress(
        output_dir,
        {
            "status": "started",
            "epochs": config.train.epochs,
            "start_epoch": start_epoch,
            "resume_checkpoint": config.train.resume_checkpoint,
            "train_batches_per_epoch": train_batches_per_epoch,
            "full_train_loader_batches": len(train_loader),
            "validation_batches": len(validation_loader),
            "test_batches": len(test_loader),
            "max_eval_batches": config.train.max_eval_batches,
            "parameters": base_model.parameter_report(),
        },
    )

    def make_checkpoint(
        metrics: dict[str, Any],
        epoch: int,
        trainer_state: dict[str, Any] | None = None,
        include_trainer_state: bool = False,
    ) -> dict[str, Any]:
        return checkpoint_payload(
            base_model,
            config,
            prepared.gene_vocab,
            prepared.fine_vocab,
            prepared.coarse_vocab,
            prepared.species_vocab,
            prepared.tissue_vocab,
            prepared.fine_to_coarse.tolist() if prepared.fine_to_coarse is not None else None,
            metrics,
            epoch,
            trainer_state=trainer_state,
            optimizer_state=optimizer.state_dict() if include_trainer_state else None,
            scheduler_state=scheduler.state_dict() if include_trainer_state else None,
            scaler_state=scaler.state_dict() if include_trainer_state else None,
            history=history if include_trainer_state else None,
        )

    for epoch in range(start_epoch, config.train.epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        train_losses = []
        for step, raw_batch in enumerate(train_loader, start=1):
            if step > train_batches_per_epoch:
                break
            batch = move_batch(raw_batch, device)
            with autocast_context(device, config.train.mixed_precision):
                loss, batch_losses, _ = compute_batch_loss(model, batch, config, fine_to_coarse)
                loss = loss / config.train.gradient_accumulation_steps
            scaler.scale(loss).backward()
            train_losses.append(batch_losses)

            if config.train.heartbeat_steps and step % config.train.heartbeat_steps == 0:
                write_training_progress(
                    output_dir,
                    {
                        "status": "training",
                        "epoch": epoch,
                        "step": step,
                        "train_batches_per_epoch": train_batches_per_epoch,
                        "optimizer_updates": optimizer_updates,
                        "latest_batch_losses": batch_losses,
                        "running_train_losses": summarize_losses(train_losses),
                    },
                )

            if (
                step % config.train.gradient_accumulation_steps == 0
                or step == train_batches_per_epoch
            ):
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(base_model.parameters(), config.train.max_grad_norm)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                scheduler.step()
                optimizer_updates += 1
                if (
                    config.train.latest_checkpoint_every_updates
                    and optimizer_updates % config.train.latest_checkpoint_every_updates == 0
                ):
                    progress_metrics = {
                        "epoch": epoch,
                        "step": step,
                        "optimizer_updates": optimizer_updates,
                        "train_batches_per_epoch": train_batches_per_epoch,
                        **{f"train_{key}": value for key, value in summarize_losses(train_losses).items()},
                    }
                    trainer_state = {
                        "epoch": epoch,
                        "step": step,
                        "optimizer_updates": optimizer_updates,
                        "train_batches_per_epoch": train_batches_per_epoch,
                        "checkpoint_kind": "latest",
                    }
                    save_checkpoint(
                        output_dir / "latest.pt",
                        make_checkpoint(
                            progress_metrics,
                            epoch,
                            trainer_state=trainer_state,
                            include_trainer_state=True,
                        ),
                    )
                    write_training_progress(
                        output_dir,
                        {
                            "status": "latest_checkpoint_saved",
                            **progress_metrics,
                            "checkpoint": "latest.pt",
                        },
                    )

        train_summary = {f"train_{key}": value for key, value in summarize_losses(train_losses).items()}
        validation_metrics = evaluate(
            model,
            validation_loader,
            config,
            device,
            fine_to_coarse,
            max_batches=config.train.max_eval_batches,
        )
        epoch_metrics = {"epoch": epoch, **train_summary, **validation_metrics}
        history.append(epoch_metrics)
        write_json(output_dir / "history.json", {"epochs": history})
        print(epoch_metrics)
        write_training_progress(
            output_dir,
            {
                "status": "epoch_completed",
                "epoch": epoch,
                "optimizer_updates": optimizer_updates,
                **epoch_metrics,
            },
        )

        monitor = validation_metrics.get("fine_macro_f1")
        score = -monitor if monitor is not None else validation_metrics["eval_loss"]
        if score < best_metric:
            best_metric = score
            best_epoch = epoch
            bad_epochs = 0
            save_checkpoint(output_dir / "best.pt", make_checkpoint(epoch_metrics, epoch))
        else:
            bad_epochs += 1

        if config.output.save_every_epochs and epoch % config.output.save_every_epochs == 0:
            save_checkpoint(output_dir / f"epoch_{epoch:04d}.pt", make_checkpoint(epoch_metrics, epoch))

        if bad_epochs >= config.train.early_stopping_patience:
            print(f"Early stopping at epoch {epoch}; best epoch was {best_epoch}")
            break

    best_checkpoint = load_checkpoint(output_dir / "best.pt", map_location=device)
    best_model = model_from_checkpoint(best_checkpoint, device=device)
    test_metrics = evaluate(
        best_model,
        test_loader,
        config,
        device,
        fine_to_coarse,
        max_batches=config.train.max_eval_batches,
    )
    write_json(output_dir / "test_metrics.json", test_metrics)
    return {
        "output_dir": str(output_dir),
        "best_epoch": best_epoch,
        "test_metrics": test_metrics,
    }


@torch.no_grad()
def predict_to_csv(
    checkpoint_path: str | Path,
    data_path: str | Path,
    output_path: str | Path,
    layer: str | None = None,
    batch_size: int = 128,
    device: torch.device | None = None,
) -> Path:
    device = device or default_device()
    checkpoint = load_checkpoint(checkpoint_path, map_location=device)
    model = model_from_checkpoint(checkpoint, device=device)
    gene_vocab, fine_vocab, coarse_vocab, species_vocab, tissue_vocab = vocabs_from_checkpoint(checkpoint)

    exp_config = ExperimentConfig.from_dict(checkpoint["experiment_config"])
    data_config = DataConfig(
        **{
            **exp_config.data.__dict__,
            "path": str(data_path),
            "layer": exp_config.data.layer if layer is None else layer,
        }
    )
    inference = prepare_inference_data(data_config, gene_vocab, species_vocab, tissue_vocab)
    dataset = ExpressionDataset(
        inference.matrix,
        inference.indices,
        data_config,
        gene_vocab,
        fine_vocab=None,
        coarse_vocab=None,
        species_vocab=species_vocab,
        tissue_vocab=tissue_vocab,
    )
    loader = make_loader(dataset, batch_size, shuffle=False, num_workers=0)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cell_ids = inference.matrix.obs.get(
        data_config.cell_id_key,
        np.asarray([str(index) for index in range(inference.matrix.n_cells)], dtype=str),
    )
    model.eval()
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "cell_id",
                "fine_label",
                "fine_confidence",
                "coarse_label",
                "coarse_confidence",
            ]
        )
        cursor = 0
        for raw_batch in loader:
            batch = move_batch(raw_batch, device)
            outputs = model(
                batch["gene_ids"],
                batch["values"],
                batch["padding_mask"],
                species_id=batch["species_id"],
                tissue_id=batch["tissue_id"],
            )
            fine_probs = torch.softmax(outputs["fine_logits"], dim=-1)
            coarse_probs = torch.softmax(outputs["coarse_logits"], dim=-1)
            fine_score, fine_id = fine_probs.max(dim=-1)
            coarse_score, coarse_id = coarse_probs.max(dim=-1)
            for row in range(fine_id.shape[0]):
                fine_label = fine_vocab.labels[int(fine_id[row])] if fine_vocab else "unknown"
                coarse_label = coarse_vocab.labels[int(coarse_id[row])] if coarse_vocab else "unknown"
                writer.writerow(
                    [
                        str(cell_ids[cursor]),
                        fine_label,
                        f"{float(fine_score[row]):.6f}",
                        coarse_label,
                        f"{float(coarse_score[row]):.6f}",
                    ]
                )
                cursor += 1
    return output


def annotate_to_bundle(
    checkpoint_path: str | Path,
    data_path: str | Path,
    output_dir: str | Path,
    layer: str | None = None,
    batch_size: int = 128,
    device: torch.device | None = None,
) -> dict[str, Any]:
    device = device or default_device()
    checkpoint = load_checkpoint(checkpoint_path, map_location=device)
    model = model_from_checkpoint(checkpoint, device=device)
    gene_vocab, fine_vocab, coarse_vocab, species_vocab, tissue_vocab = vocabs_from_checkpoint(checkpoint)

    exp_config = ExperimentConfig.from_dict(checkpoint["experiment_config"])
    data_config = DataConfig(
        **{
            **exp_config.data.__dict__,
            "path": str(data_path),
            "layer": exp_config.data.layer if layer is None else layer,
        }
    )
    inference = prepare_inference_data(data_config, gene_vocab, species_vocab, tissue_vocab)
    dataset = ExpressionDataset(
        inference.matrix,
        inference.indices,
        data_config,
        gene_vocab,
        fine_vocab=None,
        coarse_vocab=None,
        species_vocab=species_vocab,
        tissue_vocab=tissue_vocab,
    )
    loader = make_loader(dataset, batch_size, shuffle=False, num_workers=0)

    bundle_dir = Path(output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = bundle_dir / "predictions.csv"
    embedding_path = bundle_dir / "embeddings.npy"
    metadata_path = bundle_dir / "annotation_metadata.json"
    cell_ids = inference.matrix.obs.get(
        data_config.cell_id_key,
        np.asarray([str(index) for index in range(inference.matrix.n_cells)], dtype=str),
    )

    embeddings: list[np.ndarray] = []
    model.eval()
    with prediction_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "cell_id",
                "cell_index",
                "fine_label",
                "fine_confidence",
                "coarse_label",
                "coarse_confidence",
            ]
        )
        cursor = 0
        with torch.no_grad():
            for raw_batch in loader:
                batch = move_batch(raw_batch, device)
                outputs = model(
                    batch["gene_ids"],
                    batch["values"],
                    batch["padding_mask"],
                    species_id=batch["species_id"],
                    tissue_id=batch["tissue_id"],
                )
                embeddings.append(outputs["embedding"].detach().cpu().numpy().astype(np.float32))
                fine_probs = torch.softmax(outputs["fine_logits"], dim=-1)
                coarse_probs = torch.softmax(outputs["coarse_logits"], dim=-1)
                fine_score, fine_id = fine_probs.max(dim=-1)
                coarse_score, coarse_id = coarse_probs.max(dim=-1)
                cell_indices = raw_batch["cell_index"].detach().cpu().numpy()
                for row in range(fine_id.shape[0]):
                    fine_label = fine_vocab.labels[int(fine_id[row])] if fine_vocab else "unknown"
                    coarse_label = coarse_vocab.labels[int(coarse_id[row])] if coarse_vocab else "unknown"
                    cell_index = int(cell_indices[row])
                    writer.writerow(
                        [
                            str(cell_ids[cursor]),
                            cell_index,
                            fine_label,
                            f"{float(fine_score[row]):.6f}",
                            coarse_label,
                            f"{float(coarse_score[row]):.6f}",
                        ]
                    )
                    cursor += 1

    embedding_matrix = (
        np.concatenate(embeddings, axis=0)
        if embeddings
        else np.zeros((0, model.config.d_model), dtype=np.float32)
    )
    np.save(embedding_path, embedding_matrix)
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint_path": str(checkpoint_path),
        "data_path": str(data_path),
        "checkpoint_epoch": checkpoint.get("epoch"),
        "checkpoint_metrics": checkpoint.get("metrics", {}),
        "n_cells": int(inference.matrix.n_cells),
        "n_genes": int(inference.matrix.n_genes),
        "embedding_dim": int(embedding_matrix.shape[1]),
        "prediction_csv": prediction_path.name,
        "embedding_npy": embedding_path.name,
        "fine_vocab_size": len(fine_vocab.labels) if fine_vocab else 0,
        "coarse_vocab_size": len(coarse_vocab.labels) if coarse_vocab else 0,
        "species_vocab_size": len(species_vocab.labels),
        "tissue_vocab_size": len(tissue_vocab.labels),
        "preprocessing_stats": inference.preprocessing_stats,
    }
    write_json(metadata_path, metadata)
    return {
        "output_dir": str(bundle_dir),
        "prediction_csv": str(prediction_path),
        "embedding_npy": str(embedding_path),
        "metadata_json": str(metadata_path),
        "n_cells": metadata["n_cells"],
        "embedding_dim": metadata["embedding_dim"],
    }


def create_demo_dataset(output: str | Path, cells: int, genes: int, samples: int, seed: int) -> Path:
    return make_demo_data(output, n_cells=cells, n_genes=genes, n_samples=samples, seed=seed)
