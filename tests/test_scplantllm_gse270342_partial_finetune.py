from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_scplantllm_gse270342_partial_finetune as finetune


def test_partial_adaptation_only_marks_the_requested_backbone_layer_and_new_head() -> None:
    model = torch.nn.Module()
    model.transformer_encoder = torch.nn.Module()
    model.transformer_encoder.layers = torch.nn.ModuleList([torch.nn.Linear(2, 2), torch.nn.Linear(2, 2)])
    head = finetune.make_head(2, 3)
    names, parameter_count = finetune.configure_partial_adaptation(model, head, last_layer=1)
    assert names == ["transformer_encoder.layers.1.weight", "transformer_encoder.layers.1.bias"]
    assert not model.transformer_encoder.layers[0].weight.requires_grad
    assert model.transformer_encoder.layers[1].weight.requires_grad
    assert parameter_count == sum(parameter.numel() for parameter in model.transformer_encoder.layers[1].parameters()) + sum(parameter.numel() for parameter in head.parameters())


def test_metric_payload_preserves_author_label_support() -> None:
    metrics, table = finetune.metric_payload(
        np.asarray(["Cortex", "Cortex", "Xylem"], dtype=object),
        np.asarray(["Cortex", "Xylem", "Xylem"], dtype=object),
    )
    assert metrics["accuracy"] == 2 / 3
    assert int(table.support.sum()) == 3


def test_debug_limit_keeps_every_observed_class() -> None:
    indices = np.arange(12)
    labels = np.asarray(["A", "A", "A", "A", "B", "B", "B", "B", "C", "C", "C", "C"], dtype=object)
    selected = finetune.deterministic_label_balanced_limit(indices, labels, 6, seed=17)
    assert len(selected) == 6
    assert set(labels[selected]) == {"A", "B", "C"}
