from __future__ import annotations

import sys
from pathlib import Path

import torch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_scplantllm_gse270342_full_finetune as finetune


def test_full_backbone_adaptation_marks_all_backbone_and_head_parameters_trainable() -> None:
    model = torch.nn.Module()
    model.transformer_encoder = torch.nn.Module()
    model.transformer_encoder.layers = torch.nn.ModuleList([torch.nn.Linear(2, 2), torch.nn.Linear(2, 2)])
    head = finetune.make_head(2, 3)

    names, parameter_count = finetune.configure_full_backbone_adaptation(model, head)

    assert names == [
        "transformer_encoder.layers.0.weight",
        "transformer_encoder.layers.0.bias",
        "transformer_encoder.layers.1.weight",
        "transformer_encoder.layers.1.bias",
    ]
    assert all(parameter.requires_grad for parameter in model.parameters())
    assert all(parameter.requires_grad for parameter in head.parameters())
    assert parameter_count == sum(parameter.numel() for parameter in model.parameters()) + sum(parameter.numel() for parameter in head.parameters())


def test_full_backbone_runner_has_a_publish_gate_and_records_scope() -> None:
    source = (SCRIPTS / "run_scplantllm_gse270342_full_finetune.py").read_text(encoding="utf-8")

    assert 'parser.add_argument("--publish"' in source
    assert "--publish cannot be combined with debug limits" in source
    assert "COMPLETED_MATCHED_FULL_BACKBONE_ADAPTATION" in source
    assert "new_13_class_head_plus_full_scplantllm_backbone" in source
    assert "train_only_class_balanced_cross_entropy" in source
