from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.checkpoint import checkpoint


@dataclass
class ModelConfig:
    vocab_size: int
    num_fine_classes: int
    num_coarse_classes: int
    num_species: int = 1
    num_tissues: int = 1
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
    pad_id: int = 0
    cls_id: int = 1
    mask_id: int = 2

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "ModelConfig":
        return cls(**values)


class LoRALinear(nn.Module):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True,
        rank: int = 0,
        alpha: float = 1.0,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        self.base = nn.Linear(in_features, out_features, bias=bias)
        self.rank = int(rank)
        self.scaling = float(alpha / rank) if rank > 0 else 0.0
        self.lora_dropout = nn.Dropout(dropout)
        if rank > 0:
            self.lora_a = nn.Linear(in_features, rank, bias=False)
            self.lora_b = nn.Linear(rank, out_features, bias=False)
            nn.init.kaiming_uniform_(self.lora_a.weight, a=math.sqrt(5))
            nn.init.zeros_(self.lora_b.weight)
        else:
            self.lora_a = None
            self.lora_b = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        result = self.base(x)
        if self.lora_a is not None and self.lora_b is not None:
            result = result + self.lora_b(self.lora_a(self.lora_dropout(x))) * self.scaling
        return result


class SetSelfAttention(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        if config.d_model % config.n_heads:
            raise ValueError("d_model 必须能被 n_heads 整除")
        self.n_heads = config.n_heads
        self.head_dim = config.d_model // config.n_heads
        self.dropout = config.dropout
        common = {
            "rank": config.lora_rank,
            "alpha": config.lora_alpha,
            "dropout": config.lora_dropout,
        }
        self.qkv = LoRALinear(config.d_model, config.d_model * 3, bias=False, **common)
        self.out_proj = LoRALinear(config.d_model, config.d_model, bias=False, **common)

    def forward(self, x: torch.Tensor, padding_mask: torch.Tensor) -> torch.Tensor:
        batch, length, width = x.shape
        qkv = self.qkv(x).reshape(
            batch, length, 3, self.n_heads, self.head_dim
        )
        query, key, value = qkv.unbind(dim=2)
        query = query.transpose(1, 2)
        key = key.transpose(1, 2)
        value = value.transpose(1, 2)

        # SDPA 的浮点 mask 加到注意力分数；这里只屏蔽 key，pad query 随后置零。
        attention_bias = torch.zeros(
            (batch, 1, 1, length),
            device=x.device,
            dtype=query.dtype,
        )
        attention_bias = attention_bias.masked_fill(
            padding_mask[:, None, None, :],
            torch.finfo(query.dtype).min,
        )
        attended = F.scaled_dot_product_attention(
            query,
            key,
            value,
            attn_mask=attention_bias,
            dropout_p=self.dropout if self.training else 0.0,
        )
        attended = attended.transpose(1, 2).reshape(batch, length, width)
        attended = self.out_proj(attended)
        return attended.masked_fill(padding_mask.unsqueeze(-1), 0.0)


class SwiGLU(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        common = {
            "rank": config.lora_rank,
            "alpha": config.lora_alpha,
            "dropout": config.lora_dropout,
        }
        self.gate = LoRALinear(config.d_model, config.ffn_dim, **common)
        self.up = LoRALinear(config.d_model, config.ffn_dim, **common)
        self.down = LoRALinear(config.ffn_dim, config.d_model, **common)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(self.dropout(F.silu(self.gate(x)) * self.up(x)))


class EncoderBlock(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.attention_norm = nn.LayerNorm(config.d_model)
        self.attention = SetSelfAttention(config)
        self.ffn_norm = nn.LayerNorm(config.d_model)
        self.ffn = SwiGLU(config)
        self.residual_dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor, padding_mask: torch.Tensor) -> torch.Tensor:
        x = x + self.residual_dropout(
            self.attention(self.attention_norm(x), padding_mask)
        )
        x = x + self.residual_dropout(self.ffn(self.ffn_norm(x)))
        return x.masked_fill(padding_mask.unsqueeze(-1), 0.0)


class ClassificationHead(nn.Module):
    def __init__(self, d_model: int, num_classes: int, dropout: float) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, num_classes),
        )

    def forward(self, embedding: torch.Tensor) -> torch.Tensor:
        return self.layers(embedding)


class SnowCellModel(nn.Module):
    """无位置编码的基因集合 Transformer。

    输入是每个细胞中表达最高的一组基因及其归一化表达值。没有绝对位置编码，
    因而模型对同一组基因 token 的排列保持不变。
    """

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.config = config
        self.gene_embedding = nn.Embedding(
            config.vocab_size,
            config.d_model,
            padding_idx=config.pad_id,
        )
        self.value_embedding = nn.Embedding(config.value_bins, config.d_model)
        self.value_projection = nn.Sequential(
            nn.Linear(1, config.d_model),
            nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.species_embedding = nn.Embedding(max(config.num_species, 1), config.d_model)
        self.tissue_embedding = nn.Embedding(max(config.num_tissues, 1), config.d_model)
        self.covariate_scale = nn.Parameter(torch.tensor(0.10))
        self.input_norm = nn.LayerNorm(config.d_model)
        self.input_dropout = nn.Dropout(config.dropout)
        self.blocks = nn.ModuleList(
            [EncoderBlock(config) for _ in range(config.n_layers)]
        )
        self.final_norm = nn.LayerNorm(config.d_model)
        self.fine_head = ClassificationHead(
            config.d_model, config.num_fine_classes, config.dropout
        )
        self.coarse_head = ClassificationHead(
            config.d_model, config.num_coarse_classes, config.dropout
        )
        self.value_decoder = nn.Linear(config.d_model, 1)
        self._reset_parameters()

    def _reset_parameters(self) -> None:
        nn.init.normal_(self.gene_embedding.weight, mean=0.0, std=0.02)
        with torch.no_grad():
            self.gene_embedding.weight[self.config.pad_id].zero_()
        nn.init.normal_(self.value_embedding.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.species_embedding.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.tissue_embedding.weight, mean=0.0, std=0.02)

    def _embed_inputs(
        self,
        gene_ids: torch.Tensor,
        values: torch.Tensor,
        padding_mask: torch.Tensor,
        species_id: torch.Tensor | None,
        tissue_id: torch.Tensor | None,
    ) -> torch.Tensor:
        max_log_value = math.log1p(10_000.0)
        scaled = torch.clamp(values / max_log_value, 0.0, 1.0)
        value_bins = torch.clamp(
            (scaled * (self.config.value_bins - 1)).long(),
            0,
            self.config.value_bins - 1,
        )
        x = self.gene_embedding(gene_ids)
        x = x + self.value_embedding(value_bins)
        x = x + self.value_projection(scaled.unsqueeze(-1))
        if species_id is not None:
            species_id = species_id.clamp(0, self.species_embedding.num_embeddings - 1)
            x = x + self.covariate_scale * self.species_embedding(species_id)[:, None, :]
        if tissue_id is not None:
            tissue_id = tissue_id.clamp(0, self.tissue_embedding.num_embeddings - 1)
            x = x + self.covariate_scale * self.tissue_embedding(tissue_id)[:, None, :]
        x = self.input_dropout(self.input_norm(x))
        return x.masked_fill(padding_mask.unsqueeze(-1), 0.0)

    def encode(
        self,
        gene_ids: torch.Tensor,
        values: torch.Tensor,
        padding_mask: torch.Tensor,
        species_id: torch.Tensor | None = None,
        tissue_id: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        x = self._embed_inputs(
            gene_ids, values, padding_mask, species_id, tissue_id
        )
        for block in self.blocks:
            if self.config.gradient_checkpointing and self.training:
                x = checkpoint(block, x, padding_mask, use_reentrant=False)
            else:
                x = block(x, padding_mask)
        token_states = self.final_norm(x)
        embedding = token_states[:, 0]
        return embedding, token_states

    def forward(
        self,
        gene_ids: torch.Tensor,
        values: torch.Tensor,
        padding_mask: torch.Tensor,
        species_id: torch.Tensor | None = None,
        tissue_id: torch.Tensor | None = None,
        mlm_positions: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        embedding, token_states = self.encode(
            gene_ids,
            values,
            padding_mask,
            species_id=species_id,
            tissue_id=tissue_id,
        )
        output = {
            "embedding": embedding,
            "fine_logits": self.fine_head(embedding),
            "coarse_logits": self.coarse_head(embedding),
        }
        if mlm_positions is not None:
            masked_states = token_states[mlm_positions]
            output["gene_logits"] = F.linear(
                masked_states,
                self.gene_embedding.weight,
            )
            output["value_prediction"] = self.value_decoder(masked_states).squeeze(-1)
        return output

    def configure_tuning(self, mode: str, last_n_layers: int = 2) -> None:
        for parameter in self.parameters():
            parameter.requires_grad = mode == "full"
        if mode == "full":
            return
        if mode == "head":
            modules = [self.fine_head, self.coarse_head]
            for module in modules:
                for parameter in module.parameters():
                    parameter.requires_grad = True
            return
        if mode == "lora":
            if self.config.lora_rank <= 0:
                raise ValueError("模型没有 LoRA adapter，请将 lora_rank 设为正数")
            for name, parameter in self.named_parameters():
                if (
                    "lora_a" in name
                    or "lora_b" in name
                    or "norm" in name
                    or name.startswith("gene_embedding")
                    or name.startswith("value_embedding")
                    or name.startswith("species_embedding")
                    or name.startswith("tissue_embedding")
                    or name.startswith("fine_head")
                    or name.startswith("coarse_head")
                    or name == "covariate_scale"
                ):
                    parameter.requires_grad = True
            return
        if mode == "last_n":
            last_n_layers = max(1, min(last_n_layers, len(self.blocks)))
            for block in self.blocks[-last_n_layers:]:
                for parameter in block.parameters():
                    parameter.requires_grad = True
            for module in [self.final_norm, self.fine_head, self.coarse_head]:
                for parameter in module.parameters():
                    parameter.requires_grad = True
            return
        raise ValueError(f"未知 tuning mode: {mode}")

    def parameter_report(self) -> dict[str, int | float]:
        total = sum(parameter.numel() for parameter in self.parameters())
        trainable = sum(
            parameter.numel() for parameter in self.parameters() if parameter.requires_grad
        )
        return {
            "total_parameters": int(total),
            "trainable_parameters": int(trainable),
            "trainable_fraction": float(trainable / max(total, 1)),
        }


def load_matching_state_dict(
    model: nn.Module,
    state_dict: dict[str, torch.Tensor],
) -> dict[str, list[str]]:
    current = model.state_dict()
    compatible = {
        key: value
        for key, value in state_dict.items()
        if key in current and current[key].shape == value.shape
    }
    incompatible_shapes = [
        key
        for key, value in state_dict.items()
        if key in current and current[key].shape != value.shape
    ]
    missing, unexpected = model.load_state_dict(compatible, strict=False)
    return {
        "missing_keys": list(missing),
        "unexpected_keys": list(unexpected),
        "incompatible_shape_keys": incompatible_shapes,
    }

