from __future__ import annotations

"""Replay and audit the matched full-backbone scPlantLLM wheat baseline."""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import torch
from scipy import sparse

from snowcell.data import group_split


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "outputs" / "external_validation" / "gse270342" / "GSE270342_wheat_root_author_annotated_nonoverlap_diagnostic.h5ad"
ORTHOLOGS = ROOT / "data" / "orthologs" / "gse270342_wheat_to_arabidopsis_author_orthogroups.tsv"
SCPLANTLLM = ROOT / "external" / "scPlantLLM"
CHECKPOINT = SCPLANTLLM / "model_params" / "scPlantLLM_model.pth"
RECORD_PATH = ROOT / "release_metadata" / "scplantllm_gse270342_full_finetune_v1.json"
OUTPUT_PATH = ROOT / "release_metadata" / "scplantllm_gse270342_full_finetune_audit_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_modules() -> tuple[Any, Any, Any]:
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import run_scplantllm_embedding_centroid_probe as probe
    import run_scplantllm_gse270342_matched_baseline as matched
    import run_scplantllm_gse270342_full_finetune as finetune

    return probe, matched, finetune


def audit(device: str = "cuda", batch_size: int = 16) -> dict[str, Any]:
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    if record["status"] != "COMPLETED_MATCHED_FULL_BACKBONE_ADAPTATION":
        raise ValueError("Full-backbone fine-tune record is not release eligible.")
    adapter_path = ROOT / record["artifacts"]["full_finetune_checkpoint"]
    prediction_path = ROOT / record["artifacts"]["locked_test_predictions"]
    if not adapter_path.is_file() or not prediction_path.is_file():
        raise FileNotFoundError("Full-backbone scPlantLLM checkpoint or prediction artifact is missing.")
    if sha256(adapter_path) != record["artifacts"]["full_finetune_checkpoint_sha256"]:
        raise ValueError("Full-backbone scPlantLLM checkpoint checksum does not match the release record.")
    if sha256(CHECKPOINT) != record["model"]["checkpoint_sha256"]:
        raise ValueError("Official scPlantLLM checkpoint checksum does not match the release record.")
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but unavailable for replay audit.")
    probe, matched, finetune = import_modules()
    torch_device = torch.device(device)
    raw_state = probe.unwrap_state_dict(torch.load(CHECKPOINT, map_location="cpu"))
    state, conversion = probe.convert_flashmha_state_dict(raw_state)
    shape = probe.infer_model_shape(state, nhead=8, pad_token_id=0, value_pad_index=None, cls_token_id=None)
    model, missing_keys, unexpected_keys = probe.build_model(SCPLANTLLM, state, shape, torch_device)
    if missing_keys or unexpected_keys:
        raise ValueError("Official scPlantLLM checkpoint did not load cleanly in replay audit.")
    adapter = torch.load(adapter_path, map_location="cpu")
    label_names = np.asarray(adapter["label_names"], dtype=object)
    head = finetune.make_head(shape.d_model, len(label_names)).to(torch_device)
    finetune.configure_full_backbone_adaptation(model, head)
    finetune.restore_full_model(model, head, adapter["full_finetune_state"])

    adata = ad.read_h5ad(DATA, backed=None)
    cell_ids = adata.obs["cell_id"].astype(str).to_numpy() if "cell_id" in adata.obs else adata.obs_names.astype(str).to_numpy()
    labels = adata.obs["expert_annotation_raw"].astype(str).to_numpy()
    split = group_split(cell_ids, validation_fraction=0.10, test_fraction=0.20, seed=20260801)
    if len(split.test) != record["split_contract"]["locked_test_cells"]:
        raise ValueError("Replay test split denominator does not match the release record.")
    label_to_id = {label: index for index, label in enumerate(label_names.tolist())}
    target_ids = np.asarray([label_to_id[label] for label in labels], dtype=np.int64)
    mapping, _ = finetune.first_target_scplantllm_mapping()
    lookup = np.asarray([mapping.get(str(gene), 0) for gene in adata.var_names], dtype=np.int64)
    matrix = adata.X.tocsr() if sparse.issparse(adata.X) else sparse.csr_matrix(adata.X)
    token_ids, values, _ = matched.build_sequences(
        matrix,
        lookup,
        split.test,
        sequence_length=1500,
        max_tokens=1125,
        value_pad=shape.value_pad_index,
        seed=20260803,
    )
    metrics, _ = finetune.evaluate(
        model,
        head,
        token_ids,
        values,
        target_ids[split.test],
        label_names,
        probe=probe,
        shape=shape,
        device=torch_device,
        batch_size=batch_size,
        amp=True,
    )
    model.eval()
    head.eval()
    predictions = []
    with torch.inference_mode():
        for start in range(0, len(split.test), batch_size):
            stop = min(start + batch_size, len(split.test))
            with torch.autocast(device_type=torch_device.type, dtype=torch.float16, enabled=torch_device.type == "cuda"):
                logits = finetune.forward_logits(model, head, token_ids[start:stop], values[start:stop], probe=probe, shape=shape, device=torch_device)
            predictions.append(logits.argmax(dim=1).detach().cpu().numpy())
    replay = pd.DataFrame(
        {
            "cell_id": cell_ids[split.test],
            "author_label": labels[split.test],
            "scplantllm_full_finetune_prediction": label_names[np.concatenate(predictions)],
        }
    )
    released = pd.read_csv(prediction_path, sep="\t", dtype=str)
    exact_prediction_match = replay.equals(released)
    expected_metrics = record["locked_test"]
    metric_match = all(abs(float(metrics[key]) - float(expected_metrics[key])) < 1e-12 for key in ("accuracy", "macro_f1", "weighted_f1"))
    return {
        "schema_version": "plant_cellfm_scplantllm_gse270342_full_finetune_audit_v1",
        "state": "REPLAY_CONFIRMED" if exact_prediction_match and metric_match else "REPLAY_MISMATCH",
        "claim_boundary": record["claim_boundary"],
        "replay": {
            "device": str(torch_device),
            "batch_size": batch_size,
            "official_checkpoint_sha256": sha256(CHECKPOINT),
            "full_finetune_checkpoint_sha256": sha256(adapter_path),
            "official_checkpoint_load": {"missing_keys": len(missing_keys), "unexpected_keys": len(unexpected_keys), "conversion": conversion.__dict__},
            "locked_test_cells": int(len(split.test)),
            "exact_prediction_match": bool(exact_prediction_match),
            "metric_match": bool(metric_match),
        },
        "metrics": metrics,
    }


def main() -> int:
    report = audit()
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"state": report["state"], "metrics": report["metrics"]}, ensure_ascii=False))
    return 0 if report["state"] == "REPLAY_CONFIRMED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
