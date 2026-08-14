from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch

from .config import ExperimentConfig
from .model import ModelConfig, SnowCellModel, load_matching_state_dict
from .vocab import LabelVocabulary, Vocabulary


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path


def read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def checkpoint_payload(
    model: SnowCellModel,
    experiment_config: ExperimentConfig,
    gene_vocab: Vocabulary,
    fine_vocab: LabelVocabulary | None,
    coarse_vocab: LabelVocabulary | None,
    species_vocab: LabelVocabulary,
    tissue_vocab: LabelVocabulary,
    fine_to_coarse: list[int] | None,
    metrics: dict[str, Any],
    epoch: int,
    trainer_state: dict[str, Any] | None = None,
    optimizer_state: dict[str, Any] | None = None,
    scheduler_state: dict[str, Any] | None = None,
    scaler_state: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload = {
        "model_config": model.config.to_dict(),
        "experiment_config": experiment_config.to_dict(),
        "model_state": model.state_dict(),
        "gene_vocab": list(gene_vocab.tokens),
        "fine_vocab": list(fine_vocab.labels) if fine_vocab else [],
        "coarse_vocab": list(coarse_vocab.labels) if coarse_vocab else [],
        "species_vocab": list(species_vocab.labels),
        "tissue_vocab": list(tissue_vocab.labels),
        "fine_to_coarse": fine_to_coarse,
        "metrics": metrics,
        "epoch": int(epoch),
    }
    if trainer_state is not None:
        payload["trainer_state"] = trainer_state
    if optimizer_state is not None:
        payload["optimizer_state"] = optimizer_state
    if scheduler_state is not None:
        payload["scheduler_state"] = scheduler_state
    if scaler_state is not None:
        payload["scaler_state"] = scaler_state
    if history is not None:
        payload["history"] = history
    return payload


def save_checkpoint(path: str | Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, output_path)
    return output_path


def load_checkpoint(path: str | Path, map_location: str | torch.device = "cpu") -> dict[str, Any]:
    return torch.load(Path(path), map_location=map_location, weights_only=False)


def model_from_checkpoint(
    checkpoint: dict[str, Any],
    device: torch.device | str = "cpu",
) -> SnowCellModel:
    config = ModelConfig.from_dict(checkpoint["model_config"])
    model = SnowCellModel(config)
    report = load_matching_state_dict(model, checkpoint["model_state"])
    tolerated_missing = {
        key for key in report["missing_keys"] if key.startswith("contrastive_projection.")
    }
    unexpected_missing = set(report["missing_keys"]) - tolerated_missing
    if unexpected_missing or report["incompatible_shape_keys"] or report["unexpected_keys"]:
        raise RuntimeError(
            "checkpoint/model contract mismatch: "
            f"missing={sorted(unexpected_missing)}, "
            f"incompatible={sorted(report['incompatible_shape_keys'])}, "
            f"unexpected={sorted(report['unexpected_keys'])}"
        )
    model.to(device)
    model.eval()
    return model


def vocabs_from_checkpoint(
    checkpoint: dict[str, Any],
) -> tuple[Vocabulary, LabelVocabulary | None, LabelVocabulary | None, LabelVocabulary, LabelVocabulary]:
    gene_vocab = Vocabulary.from_list(list(checkpoint["gene_vocab"]))
    fine_vocab = (
        LabelVocabulary.from_list(list(checkpoint["fine_vocab"]))
        if checkpoint.get("fine_vocab")
        else None
    )
    coarse_vocab = (
        LabelVocabulary.from_list(list(checkpoint["coarse_vocab"]))
        if checkpoint.get("coarse_vocab")
        else None
    )
    species_vocab = LabelVocabulary.from_list(list(checkpoint["species_vocab"]))
    tissue_vocab = LabelVocabulary.from_list(list(checkpoint["tissue_vocab"]))
    return gene_vocab, fine_vocab, coarse_vocab, species_vocab, tissue_vocab
