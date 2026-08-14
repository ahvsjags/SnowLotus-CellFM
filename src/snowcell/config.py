from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, TypeVar

import yaml


T = TypeVar("T")


def _from_dict_strict(cls: type[T], values: dict[str, Any] | None) -> T:
    values = values or {}
    allowed = {item.name for item in fields(cls)}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"{cls.__name__} 存在未知配置项: {sorted(unknown)}")
    return cls(**values)


@dataclass
class DataConfig:
    path: str = "data/demo.npz"
    layer: str | None = None
    label_key: str = "cell_type"
    coarse_label_key: str = "cell_type_coarse"
    group_key: str = "sample_id"
    batch_key: str = "batch"
    species_key: str = "species"
    tissue_key: str = "tissue"
    cell_id_key: str = "cell_id"
    ortholog_map: str | None = None
    ortholog_source_column: str = "source_gene"
    ortholog_target_column: str = "target_gene"
    ortholog_confidence_column: str | None = "confidence"
    min_ortholog_confidence: float = 0.0
    ortholog_keep_unmapped: bool = False
    ortholog_aggregation: str = "first"
    ontology_contract: str | None = None
    ontology_unknown_policy: str = "keep"
    normalize_total: float = 10_000.0
    log1p: bool = True
    max_genes: int = 512
    min_genes_per_cell: int = 10
    min_cells_per_gene: int = 3
    validation_fraction: float = 0.15
    test_fraction: float = 0.15
    split_strategy: str = "group_random"
    leaveout_key: str | None = None
    leaveout_test_values: list[str] = field(default_factory=list)
    leaveout_validation_values: list[str] = field(default_factory=list)


@dataclass
class ArchitectureConfig:
    d_model: int = 256
    n_layers: int = 6
    n_heads: int = 8
    ffn_dim: int = 768
    dropout: float = 0.10
    value_bins: int = 64
    lora_rank: int = 0
    lora_alpha: float = 16.0
    lora_dropout: float = 0.05
    gradient_checkpointing: bool = False
    contrastive_dim: int = 128
    marker_prior_weight: float = 0.0


@dataclass
class TrainConfig:
    stage: str = "supervised"
    seed: int = 42
    epochs: int = 20
    batch_size: int = 32
    eval_batch_size: int = 64
    learning_rate: float = 3e-4
    head_learning_rate: float | None = None
    weight_decay: float = 0.05
    warmup_fraction: float = 0.05
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    mixed_precision: str = "bf16"
    tuning_mode: str = "full"
    train_last_n_layers: int = 2
    init_checkpoint: str | None = None
    resume_checkpoint: str | None = None
    label_smoothing: float = 0.05
    coarse_loss_weight: float = 0.35
    hierarchy_loss_weight: float = 0.10
    mlm_loss_weight: float = 0.50
    value_loss_weight: float = 0.25
    contrastive_loss_weight: float = 0.0
    cross_species_contrastive_loss_weight: float = 0.0
    contrastive_temperature: float = 0.10
    hard_negative_loss_weight: float = 0.0
    hard_negative_margin: float = 0.20
    validation_metric: str = "fine_macro_f1"
    mask_ratio: float = 0.15
    class_balance: bool = True
    species_balance: bool = False
    early_stopping_patience: int = 5
    max_train_batches_per_epoch: int | None = None
    max_eval_batches: int | None = None
    heartbeat_steps: int = 0
    latest_checkpoint_every_updates: int = 0
    unknown_calibration_alpha: float = 0.05
    marker_genes_per_class: int = 30
    num_workers: int = 0
    compile_model: bool = False


@dataclass
class OutputConfig:
    directory: str = "outputs/smoke"
    save_every_epochs: int = 0


@dataclass
class ExperimentConfig:
    data: DataConfig = field(default_factory=DataConfig)
    architecture: ArchitectureConfig = field(default_factory=ArchitectureConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "ExperimentConfig":
        allowed = {"data", "architecture", "train", "output"}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"ExperimentConfig 存在未知配置段: {sorted(unknown)}")
        return cls(
            data=_from_dict_strict(DataConfig, values.get("data")),
            architecture=_from_dict_strict(ArchitectureConfig, values.get("architecture")),
            train=_from_dict_strict(TrainConfig, values.get("train")),
            output=_from_dict_strict(OutputConfig, values.get("output")),
        )

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentConfig":
        config_path = Path(path)
        with config_path.open("r", encoding="utf-8") as handle:
            values = yaml.safe_load(handle) or {}
        config = cls.from_dict(values)
        config.validate()
        return config

    def validate(self) -> None:
        if self.train.stage not in {"pretrain", "supervised", "hybrid"}:
            raise ValueError("train.stage 必须是 pretrain、supervised 或 hybrid")
        if self.train.tuning_mode not in {"full", "head", "lora", "last_n"}:
            raise ValueError("train.tuning_mode 必须是 full、head、lora 或 last_n")
        if self.train.mixed_precision not in {"no", "fp16", "bf16"}:
            raise ValueError("train.mixed_precision 必须是 no、fp16 或 bf16")
        if self.data.split_strategy not in {"group_random", "explicit_leaveout"}:
            raise ValueError("data.split_strategy 必须是 group_random 或 explicit_leaveout")
        if self.data.ortholog_aggregation not in {"first", "mean"}:
            raise ValueError("data.ortholog_aggregation 必须是 first 或 mean")
        if self.data.ontology_unknown_policy not in {"keep", "unknown"}:
            raise ValueError("data.ontology_unknown_policy 必须是 keep 或 unknown")
        if self.data.split_strategy == "explicit_leaveout":
            if not self.data.leaveout_key:
                raise ValueError("explicit_leaveout 需要设置 data.leaveout_key")
            if not self.data.leaveout_test_values:
                raise ValueError("explicit_leaveout 需要设置 data.leaveout_test_values")
            overlap = set(self.data.leaveout_test_values) & set(
                self.data.leaveout_validation_values
            )
            if overlap:
                raise ValueError(
                    f"leaveout_test_values 与 leaveout_validation_values 不能重叠: {sorted(overlap)}"
                )
        if self.data.max_genes < 8:
            raise ValueError("data.max_genes 不能小于 8")
        if self.architecture.d_model % self.architecture.n_heads != 0:
            raise ValueError("architecture.d_model 必须能被 n_heads 整除")
        if self.architecture.contrastive_dim < 8:
            raise ValueError("architecture.contrastive_dim 不能小于 8")
        if self.architecture.marker_prior_weight < 0:
            raise ValueError("architecture.marker_prior_weight 不能为负数")
        if self.train.contrastive_loss_weight < 0:
            raise ValueError("train.contrastive_loss_weight 不能为负数")
        if self.train.cross_species_contrastive_loss_weight < 0:
            raise ValueError("train.cross_species_contrastive_loss_weight 不能为负数")
        if self.train.contrastive_temperature <= 0:
            raise ValueError("train.contrastive_temperature 必须大于 0")
        if self.train.hard_negative_loss_weight < 0:
            raise ValueError("train.hard_negative_loss_weight 不能为负数")
        if self.train.hard_negative_margin < 0:
            raise ValueError("train.hard_negative_margin 不能为负数")
        if self.train.validation_metric not in {
            "fine_accuracy",
            "fine_macro_f1",
            "species_accuracy",
            "species_macro_f1",
        }:
            raise ValueError(
                "train.validation_metric 必须是 fine_accuracy、fine_macro_f1、"
                "species_accuracy 或 species_macro_f1"
            )
        fractions = self.data.validation_fraction + self.data.test_fraction
        if not 0.0 < fractions < 0.9:
            raise ValueError("验证集与测试集比例之和必须位于 (0, 0.9)")
        if self.train.tuning_mode == "lora" and self.architecture.lora_rank <= 0:
            raise ValueError("LoRA 微调时 architecture.lora_rank 必须大于 0")
        if self.train.stage == "pretrain" and self.train.tuning_mode != "full":
            raise ValueError("从零预训练应使用 train.tuning_mode=full")

        if self.train.init_checkpoint and self.train.resume_checkpoint:
            raise ValueError("train.init_checkpoint and train.resume_checkpoint cannot both be set")

        if (
            self.train.max_train_batches_per_epoch is not None
            and self.train.max_train_batches_per_epoch < 1
        ):
            raise ValueError("train.max_train_batches_per_epoch must be empty or > 0")
        if self.train.max_eval_batches is not None and self.train.max_eval_batches < 1:
            raise ValueError("train.max_eval_batches must be empty or > 0")
        if self.train.heartbeat_steps < 0:
            raise ValueError("train.heartbeat_steps must be >= 0")
        if self.train.latest_checkpoint_every_updates < 0:
            raise ValueError("train.latest_checkpoint_every_updates must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
