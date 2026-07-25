from __future__ import annotations

import argparse
from pathlib import Path
import gzip
import importlib.util
import json
import os
import sys

import numpy as np
import torch
import h5py
from scipy import io
from scipy import sparse

from snowcell.config import ExperimentConfig
from snowcell.collect import write_manifest_download_scripts
from snowcell.data import ExpressionDataset, load_matrix, make_demo_data, prepare_data
from snowcell.markers import run_marker_candidates
from snowcell.model import SnowCellModel
from snowcell.artifacts import checkpoint_payload, save_checkpoint
from snowcell.train import (
    annotate_to_bundle,
    build_model_config,
    compute_batch_loss,
    maybe_load_init_checkpoint,
    train_from_config,
)


def test_prepare_data_and_forward(tmp_path: Path) -> None:
    data_path = tmp_path / "demo.npz"
    make_demo_data(data_path, n_cells=120, n_genes=96, n_samples=6, seed=13)
    config = ExperimentConfig.from_dict(
        {
            "data": {
                "path": str(data_path),
                "max_genes": 32,
                "min_genes_per_cell": 5,
                "min_cells_per_gene": 2,
                "validation_fraction": 0.15,
                "test_fraction": 0.15,
            },
            "architecture": {
                "d_model": 32,
                "n_layers": 1,
                "n_heads": 4,
                "ffn_dim": 64,
            },
            "train": {
                "stage": "hybrid",
                "epochs": 1,
                "batch_size": 8,
                "mixed_precision": "no",
            },
        }
    )
    config.validate()
    prepared = prepare_data(config.data, seed=42, require_labels=True)
    model = SnowCellModel(build_model_config(config, prepared))
    dataset = ExpressionDataset(
        prepared.matrix,
        prepared.split.train[:8],
        config.data,
        prepared.gene_vocab,
        fine_vocab=prepared.fine_vocab,
        coarse_vocab=prepared.coarse_vocab,
        species_vocab=prepared.species_vocab,
        tissue_vocab=prepared.tissue_vocab,
    )
    batch = {
        key: torch.stack([dataset[index][key] for index in range(len(dataset))])
        for key in dataset[0]
    }
    fine_to_coarse = torch.as_tensor(prepared.fine_to_coarse, dtype=torch.long)
    loss, losses, outputs = compute_batch_loss(model, batch, config, fine_to_coarse)
    assert loss.isfinite()
    assert losses["loss"] > 0
    assert outputs["fine_logits"].shape[0] == len(dataset)


def test_prepare_data_allows_ambiguous_fine_to_coarse_labels(tmp_path: Path) -> None:
    data_path = tmp_path / "ambiguous_labels.npz"
    n_cells = 12
    np.savez(
        data_path,
        X=np.ones((n_cells, 8), dtype=np.float32),
        genes=np.asarray([f"gene_{index}" for index in range(8)]),
        cell_type=np.asarray(
            [
                "procambium",
                "procambium",
                "cortex",
                "cortex",
                "xylem",
                "xylem",
                "phloem",
                "phloem",
                "epidermis",
                "epidermis",
                "companion",
                "companion",
            ]
        ),
        cell_type_coarse=np.asarray(
            [
                "meristem",
                "vascular",
                "ground",
                "ground",
                "vascular",
                "vascular",
                "vascular",
                "vascular",
                "dermal",
                "dermal",
                "vascular",
                "vascular",
            ]
        ),
        sample_id=np.asarray([f"sample_{index % 4}" for index in range(n_cells)]),
        species=np.asarray(["Arabidopsis thaliana"] * n_cells),
        tissue=np.asarray(["root"] * n_cells),
    )
    config = ExperimentConfig.from_dict(
        {
            "data": {
                "path": str(data_path),
                "max_genes": 8,
                "min_genes_per_cell": 1,
                "min_cells_per_gene": 1,
                "validation_fraction": 0.25,
                "test_fraction": 0.25,
            },
            "architecture": {
                "d_model": 24,
                "n_layers": 1,
                "n_heads": 4,
                "ffn_dim": 48,
            },
            "train": {
                "stage": "hybrid",
                "epochs": 1,
                "batch_size": 4,
                "mixed_precision": "no",
            },
        }
    )

    prepared = prepare_data(config.data, seed=7, require_labels=True)
    procambium_id = prepared.fine_vocab.stoi["procambium"]

    assert prepared.fine_to_coarse[procambium_id] == -1
    assert prepared.preprocessing_stats["label_hierarchy"][
        "ambiguous_fine_label_count"
    ] == 1
    assert prepared.preprocessing_stats["label_hierarchy"]["ambiguous_fine_labels"][
        "procambium"
    ] == ["meristem", "vascular"]

    model = SnowCellModel(build_model_config(config, prepared))
    dataset = ExpressionDataset(
        prepared.matrix,
        np.arange(prepared.matrix.n_cells),
        config.data,
        prepared.gene_vocab,
        fine_vocab=prepared.fine_vocab,
        coarse_vocab=prepared.coarse_vocab,
        species_vocab=prepared.species_vocab,
        tissue_vocab=prepared.tissue_vocab,
    )
    batch = {
        key: torch.stack([dataset[index][key] for index in range(len(dataset))])
        for key in dataset[0]
    }
    fine_to_coarse = torch.as_tensor(prepared.fine_to_coarse, dtype=torch.long)
    loss, losses, _ = compute_batch_loss(model, batch, config, fine_to_coarse)

    assert loss.isfinite()
    assert losses["hierarchy_loss"] >= 0


def test_train_writes_heartbeat_and_latest_checkpoint(tmp_path: Path) -> None:
    data_path = tmp_path / "demo.npz"
    output_dir = tmp_path / "outputs" / "limited_train"
    config_path = tmp_path / "limited_train.yaml"
    make_demo_data(data_path, n_cells=96, n_genes=96, n_samples=6, seed=17)
    config_path.write_text(
        f"""
data:
  path: {data_path.as_posix()}
  max_genes: 24
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  validation_fraction: 0.15
  test_fraction: 0.15
architecture:
  d_model: 24
  n_layers: 1
  n_heads: 4
  ffn_dim: 48
train:
  stage: pretrain
  epochs: 1
  batch_size: 8
  eval_batch_size: 8
  mixed_precision: "no"
  tuning_mode: full
  gradient_accumulation_steps: 1
  max_train_batches_per_epoch: 2
  max_eval_batches: 1
  heartbeat_steps: 1
  latest_checkpoint_every_updates: 1
  num_workers: 0
output:
  directory: {output_dir.as_posix()}
""".lstrip(),
        encoding="utf-8",
    )

    result = train_from_config(config_path, device=torch.device("cpu"))
    progress_lines = (output_dir / "progress.jsonl").read_text(encoding="utf-8").splitlines()
    progress_latest = json.loads((output_dir / "progress_latest.json").read_text(encoding="utf-8"))
    history = json.loads((output_dir / "history.json").read_text(encoding="utf-8"))

    assert result["best_epoch"] == 1
    assert (output_dir / "latest.pt").exists()
    assert (output_dir / "best.pt").exists()
    assert len(progress_lines) >= 3
    assert progress_latest["status"] == "epoch_completed"
    assert history["epochs"][0]["eval_batches"] == 1.0


def test_init_checkpoint_copies_overlapping_gene_rows_by_name(tmp_path: Path) -> None:
    source_path = tmp_path / "source.npz"
    target_path = tmp_path / "target.npz"
    n_cells = 18
    obs = {
        "cell_type": np.asarray(["cell"] * n_cells),
        "cell_type_coarse": np.asarray(["coarse"] * n_cells),
        "sample_id": np.asarray([f"sample_{index % 6}" for index in range(n_cells)]),
        "species": np.asarray(["Arabidopsis"] * n_cells),
        "tissue": np.asarray(["root"] * n_cells),
    }
    np.savez(
        source_path,
        X=np.ones((n_cells, 3), dtype=np.float32),
        genes=np.asarray(["gene_a", "gene_b", "gene_c"]),
        **obs,
    )
    np.savez(
        target_path,
        X=np.ones((n_cells, 3), dtype=np.float32),
        genes=np.asarray(["gene_new", "gene_b", "gene_a"]),
        **obs,
    )

    def make_config(path: Path) -> ExperimentConfig:
        return ExperimentConfig.from_dict(
            {
                "data": {
                    "path": str(path),
                    "max_genes": 8,
                    "min_genes_per_cell": 1,
                    "min_cells_per_gene": 1,
                    "validation_fraction": 0.2,
                    "test_fraction": 0.2,
                },
                "architecture": {
                    "d_model": 8,
                    "n_layers": 1,
                    "n_heads": 2,
                    "ffn_dim": 16,
                },
                "train": {
                    "stage": "pretrain",
                    "epochs": 1,
                    "mixed_precision": "no",
                },
            }
        )

    source_config = make_config(source_path)
    target_config = make_config(target_path)
    source_prepared = prepare_data(source_config.data, seed=7, require_labels=False)
    target_prepared = prepare_data(target_config.data, seed=7, require_labels=False)
    source_model = SnowCellModel(build_model_config(source_config, source_prepared))
    target_model = SnowCellModel(build_model_config(target_config, target_prepared))

    with torch.no_grad():
        for index in range(source_model.gene_embedding.weight.shape[0]):
            source_model.gene_embedding.weight[index].fill_(float(index + 1))

    checkpoint = checkpoint_payload(
        source_model,
        source_config,
        source_prepared.gene_vocab,
        None,
        None,
        source_prepared.species_vocab,
        source_prepared.tissue_vocab,
        None,
        metrics={"eval_loss": 1.0},
        epoch=1,
    )
    checkpoint_path = save_checkpoint(tmp_path / "source.pt", checkpoint)

    maybe_load_init_checkpoint(
        target_model,
        str(checkpoint_path),
        torch.device("cpu"),
        target_prepared,
    )

    source_lookup = source_prepared.gene_vocab.stoi
    target_lookup = target_prepared.gene_vocab.stoi
    assert torch.allclose(
        target_model.gene_embedding.weight[target_lookup["gene_a"]],
        source_model.gene_embedding.weight[source_lookup["gene_a"]],
    )
    assert torch.allclose(
        target_model.gene_embedding.weight[target_lookup["gene_b"]],
        source_model.gene_embedding.weight[source_lookup["gene_b"]],
    )
    assert not torch.allclose(
        target_model.gene_embedding.weight[target_lookup["gene_new"]],
        source_model.gene_embedding.weight[source_lookup["gene_a"]],
    )


def test_train_can_warm_resume_from_latest_checkpoint(tmp_path: Path) -> None:
    data_path = tmp_path / "demo_resume.npz"
    first_output = tmp_path / "outputs" / "first"
    resume_output = tmp_path / "outputs" / "resume"
    first_config = tmp_path / "first.yaml"
    resume_config = tmp_path / "resume.yaml"
    make_demo_data(data_path, n_cells=96, n_genes=96, n_samples=6, seed=19)
    common = f"""
data:
  path: {data_path.as_posix()}
  max_genes: 24
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  validation_fraction: 0.15
  test_fraction: 0.15
architecture:
  d_model: 24
  n_layers: 1
  n_heads: 4
  ffn_dim: 48
train:
  stage: pretrain
  batch_size: 8
  eval_batch_size: 8
  mixed_precision: "no"
  tuning_mode: full
  gradient_accumulation_steps: 1
  max_train_batches_per_epoch: 1
  max_eval_batches: 1
  heartbeat_steps: 1
  latest_checkpoint_every_updates: 1
  num_workers: 0
"""
    first_config.write_text(
        common
        + f"""
  epochs: 1
output:
  directory: {first_output.as_posix()}
""",
        encoding="utf-8",
    )
    train_from_config(first_config, device=torch.device("cpu"))
    latest = first_output / "latest.pt"

    resume_config.write_text(
        common
        + f"""
  epochs: 2
  resume_checkpoint: {latest.as_posix()}
output:
  directory: {resume_output.as_posix()}
""",
        encoding="utf-8",
    )

    result = train_from_config(resume_config, device=torch.device("cpu"))
    progress_lines = [
        json.loads(line)
        for line in (resume_output / "progress.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    history = json.loads((resume_output / "history.json").read_text(encoding="utf-8"))

    assert result["best_epoch"] == 2
    assert progress_lines[0]["start_epoch"] == 2
    assert progress_lines[0]["resume_checkpoint"] == latest.as_posix()
    assert [row["epoch"] for row in history["epochs"]] == [1, 2]
    assert (resume_output / "latest.pt").exists()


def test_train_resumes_mid_epoch_latest_without_skipping_epoch(tmp_path: Path) -> None:
    data_path = tmp_path / "demo_resume_mid_epoch.npz"
    first_output = tmp_path / "outputs" / "first_mid_epoch"
    resume_output = tmp_path / "outputs" / "resume_mid_epoch"
    first_config = tmp_path / "first_mid_epoch.yaml"
    resume_config = tmp_path / "resume_mid_epoch.yaml"
    make_demo_data(data_path, n_cells=96, n_genes=96, n_samples=6, seed=29)
    common = f"""
data:
  path: {data_path.as_posix()}
  max_genes: 24
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  validation_fraction: 0.15
  test_fraction: 0.15
architecture:
  d_model: 24
  n_layers: 1
  n_heads: 4
  ffn_dim: 48
train:
  stage: pretrain
  batch_size: 8
  eval_batch_size: 8
  mixed_precision: "no"
  tuning_mode: full
  gradient_accumulation_steps: 1
  max_train_batches_per_epoch: 2
  max_eval_batches: 1
  heartbeat_steps: 1
  latest_checkpoint_every_updates: 1
  num_workers: 0
"""
    first_config.write_text(
        common
        + f"""
  epochs: 1
output:
  directory: {first_output.as_posix()}
""",
        encoding="utf-8",
    )
    train_from_config(first_config, device=torch.device("cpu"))
    latest = first_output / "latest.pt"

    checkpoint = torch.load(latest, map_location="cpu", weights_only=False)
    checkpoint["epoch"] = 2
    checkpoint["history"] = []
    checkpoint.setdefault("metrics", {}).update({"epoch": 2, "step": 1, "train_batches_per_epoch": 2})
    checkpoint.setdefault("trainer_state", {}).update(
        {
            "epoch": 2,
            "step": 1,
            "train_batches_per_epoch": 2,
            "checkpoint_kind": "latest",
        }
    )
    torch.save(checkpoint, latest)

    resume_config.write_text(
        common
        + f"""
  epochs: 2
  resume_checkpoint: {latest.as_posix()}
output:
  directory: {resume_output.as_posix()}
""",
        encoding="utf-8",
    )

    result = train_from_config(resume_config, device=torch.device("cpu"))
    progress_lines = [
        json.loads(line)
        for line in (resume_output / "progress.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    history = json.loads((resume_output / "history.json").read_text(encoding="utf-8"))

    assert result["best_epoch"] == 2
    assert progress_lines[0]["start_epoch"] == 2
    assert history["epochs"][0]["epoch"] == 1
    assert history["epochs"][-1]["epoch"] == 2
    assert len(history["epochs"]) == 2


def test_annotate_bundle_writes_predictions_embeddings_and_metadata(tmp_path: Path) -> None:
    data_path = tmp_path / "demo_annotate.npz"
    output_dir = tmp_path / "outputs" / "annotate_train"
    config_path = tmp_path / "annotate_train.yaml"
    bundle_dir = tmp_path / "annotation_bundle"
    make_demo_data(data_path, n_cells=96, n_genes=96, n_samples=6, seed=23)
    config_path.write_text(
        f"""
data:
  path: {data_path.as_posix()}
  max_genes: 24
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  validation_fraction: 0.15
  test_fraction: 0.15
architecture:
  d_model: 16
  n_layers: 1
  n_heads: 4
  ffn_dim: 32
train:
  stage: hybrid
  epochs: 1
  batch_size: 8
  eval_batch_size: 8
  mixed_precision: "no"
  tuning_mode: full
  gradient_accumulation_steps: 1
  max_train_batches_per_epoch: 1
  max_eval_batches: 1
  heartbeat_steps: 1
  latest_checkpoint_every_updates: 1
  num_workers: 0
output:
  directory: {output_dir.as_posix()}
""".lstrip(),
        encoding="utf-8",
    )
    train_from_config(config_path, device=torch.device("cpu"))

    payload = annotate_to_bundle(
        checkpoint_path=output_dir / "best.pt",
        data_path=data_path,
        output_dir=bundle_dir,
        batch_size=16,
        device=torch.device("cpu"),
    )
    predictions = (bundle_dir / "predictions.csv").read_text(encoding="utf-8").splitlines()
    embeddings = np.load(bundle_dir / "embeddings.npy")
    metadata = json.loads((bundle_dir / "annotation_metadata.json").read_text(encoding="utf-8"))

    assert payload["n_cells"] == metadata["n_cells"]
    assert payload["embedding_dim"] == 16
    assert len(predictions) == metadata["n_cells"] + 1
    assert "fine_confidence" in predictions[0]
    assert embeddings.shape == (metadata["n_cells"], 16)
    assert metadata["preprocessing_stats"]["quality_control"]["retained_cells"] == metadata["n_cells"]


def test_detailed_checkpoint_evaluation_writes_review_artifacts(tmp_path: Path) -> None:
    data_path = tmp_path / "demo_detailed_eval.npz"
    output_dir = tmp_path / "outputs" / "detailed_eval_train"
    config_path = tmp_path / "detailed_eval_train.yaml"
    eval_dir = tmp_path / "outputs" / "detailed_evaluations" / "demo_test"
    make_demo_data(data_path, n_cells=96, n_genes=96, n_samples=6, seed=31)
    config_path.write_text(
        f"""
data:
  path: {data_path.as_posix()}
  max_genes: 24
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  validation_fraction: 0.15
  test_fraction: 0.15
architecture:
  d_model: 16
  n_layers: 1
  n_heads: 4
  ffn_dim: 32
train:
  stage: hybrid
  epochs: 1
  batch_size: 8
  eval_batch_size: 8
  mixed_precision: "no"
  tuning_mode: full
  gradient_accumulation_steps: 1
  max_train_batches_per_epoch: 1
  max_eval_batches: 1
  heartbeat_steps: 1
  latest_checkpoint_every_updates: 1
  num_workers: 0
output:
  directory: {output_dir.as_posix()}
""".lstrip(),
        encoding="utf-8",
    )
    train_from_config(config_path, device=torch.device("cpu"))

    module_path = Path(__file__).parents[1] / "scripts" / "evaluate_checkpoint_detailed.py"
    spec = importlib.util.spec_from_file_location("evaluate_checkpoint_detailed", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    payload = module.run_detailed_evaluation(
        config_path=config_path,
        checkpoint_path=output_dir / "best.pt",
        split="test",
        output_dir=eval_dir,
        device=torch.device("cpu"),
        batch_size=8,
        max_batches=1,
    )
    metrics = json.loads((eval_dir / "detailed_metrics.json").read_text(encoding="utf-8"))
    prediction_header = (eval_dir / "predictions.tsv").read_text(
        encoding="utf-8"
    ).splitlines()[0]

    assert payload["summary"]["evaluated_cells"] == metrics["summary"]["evaluated_cells"]
    assert metrics["summary"]["evaluated_cells"] > 0
    assert metrics["summary"]["fine"]["macro_f1"] is not None
    assert "fine_confidence" in prediction_header
    assert (eval_dir / "detailed_evaluation.md").exists()
    assert (eval_dir / "fine_confusion_matrix.tsv").exists()
    assert (eval_dir / "coarse_confusion_matrix.tsv").exists()


def test_training_curve_summary_reports_eval_improvement(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_training_curve_summary.py"
    spec = importlib.util.spec_from_file_location("write_training_curve_summary", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    run_dir = tmp_path / "outputs" / "foundation_5090_mlm_public_late_refresh_safe"
    run_dir.mkdir(parents=True)
    (run_dir / "history.json").write_text(
        json.dumps(
            {
                "epochs": [
                    {"epoch": 1, "train_loss": 11.0, "eval_loss": 10.0, "eval_batches": 2.0},
                    {"epoch": 2, "train_loss": 9.0, "eval_loss": 8.0, "eval_batches": 2.0},
                ]
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "progress_latest.json").write_text(
        json.dumps({"status": "training", "epoch": 3, "step": 100}),
        encoding="utf-8",
    )
    (run_dir / "latest.pt").write_bytes(b"checkpoint")

    payload = module.build_summary(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "training_curve_summary.md"
    output_json = tmp_path / "outputs" / "publication_package" / "training_curve_summary.json"
    output_tsv = tmp_path / "outputs" / "publication_package" / "training_curve_summary.tsv"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    module.write_tsv(payload, output_tsv)

    run = payload["runs"][0]
    assert payload["summary"]["runs_with_eval_improvement"] == 1
    assert run["eval_loss_delta"]["absolute"] == 2.0
    assert run["best_epoch"] == 2
    assert run["best_eval_loss"] == 8.0
    assert run["latest_minus_best_eval_loss"] == 0.0
    assert run["eval_loss_nonincreasing"] is True
    output_text = output_md.read_text(encoding="utf-8")
    assert "foundation_5090_mlm_public_late_refresh_safe" in output_text
    assert "Best eval" in output_text
    assert "eval_loss" in output_tsv.read_text(encoding="utf-8")
    assert "runs_with_eval_improvement" in output_json.read_text(encoding="utf-8")


def test_training_curve_summary_includes_progress_only_run(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_training_curve_summary.py"
    spec = importlib.util.spec_from_file_location("write_training_curve_summary_progress", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    run_dir = tmp_path / "outputs" / "foundation_5090_mlm_public_expansion_continuation"
    run_dir.mkdir(parents=True)
    (run_dir / "config.resolved.json").write_text("{}", encoding="utf-8")
    (run_dir / "progress_latest.json").write_text(
        json.dumps(
            {
                "status": "training",
                "epoch": 1,
                "step": 1500,
                "train_batches_per_epoch": 34676,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "latest.pt").write_bytes(b"checkpoint")

    payload = module.build_summary(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "training_curve_summary.md"
    output_json = tmp_path / "outputs" / "publication_package" / "training_curve_summary.json"
    output_tsv = tmp_path / "outputs" / "publication_package" / "training_curve_summary.tsv"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    module.write_tsv(payload, output_tsv)

    continuation = next(
        run
        for run in payload["runs"]
        if run["run_id"] == "foundation_5090_mlm_public_expansion_continuation"
    )
    assert continuation["latest_progress"]["status"] == "training"
    assert continuation["latest_checkpoint"]["exists"] is True
    assert continuation["best_epoch"] is None
    assert continuation["best_eval_loss"] is None
    assert "foundation_5090_mlm_public_expansion_continuation" in output_md.read_text(
        encoding="utf-8"
    )
    assert "training" in output_json.read_text(encoding="utf-8")


def test_submission_action_plan_marks_hard_publication_blockers(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_submission_action_plan.py"
    spec = importlib.util.spec_from_file_location("write_submission_action_plan", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    package_dir = tmp_path / "outputs" / "publication_package"
    external_dir = tmp_path / "outputs" / "external_benchmarks"
    package_dir.mkdir(parents=True)
    external_dir.mkdir(parents=True)
    (package_dir / "status_summary.json").write_text(
        json.dumps(
            {
                "benchmark_readiness": {
                    "external_missing_methods": ["scplantannotate"],
                },
                "runs": [
                    {
                        "path": str(
                            tmp_path
                            / "outputs"
                            / "foundation_5090_mlm_public_late_refresh_safe"
                        )
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "training_health_audit.json").write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": "foundation_5090_mlm_public_late_refresh_safe",
                        "epochs_recorded": 3,
                    },
                    {
                        "run_id": "foundation_5090_mlm_public_expansion_continuation",
                        "status": "running_with_checkpoint",
                        "epochs_recorded": 5,
                        "latest_epoch": {"eval_loss": 8.149},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "training_curve_summary.json").write_text(
        json.dumps({"summary": {"runs_with_eval_improvement": 1, "checkpoint_runs": 1}}),
        encoding="utf-8",
    )
    (package_dir / "saussurea_h5ad_contract.json").write_text(
        json.dumps(
            {
                "path": "data/saussurea_involucrata.h5ad",
                "summary": {
                    "exists": False,
                    "readable": False,
                    "contract_ready": False,
                    "top_journal_primary_data_ready": False,
                },
                "errors": ["Missing required file: data/saussurea_involucrata.h5ad"],
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "scplantannotate_access_audit.json").write_text(
        json.dumps(
            {
                "summary": {
                    "comparison_ready": False,
                    "anonymous_api_accessible": False,
                    "auth_required_endpoint_count": 4,
                }
            }
        ),
        encoding="utf-8",
    )
    (external_dir / "scplantannotate_authenticated_benchmark_plan.json").write_text(
        json.dumps(
            {
                "readiness_gates": {
                    "input_h5ad_available": True,
                    "truth_labels_available": True,
                    "prediction_export_available": False,
                }
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "benchmark_gap_audit.json").write_text(
        json.dumps({"summary": {"top_journal_benchmark_ready": False}}),
        encoding="utf-8",
    )
    (package_dir / "download_progress_audit.json").write_text(
        json.dumps({"targets": []}),
        encoding="utf-8",
    )
    (package_dir / "transfer_queue_health_audit.json").write_text(
        json.dumps(
            {
                "summary": {
                    "running_count": 1,
                    "missing_not_started_count": 2,
                    "partial_without_active_session_count": 0,
                    "stale_partial_count": 1,
                    "provisional_payload_count": 1,
                    "complete_manifest_count": 7,
                }
            }
        ),
        encoding="utf-8",
    )
    public_discovery_dir = package_dir / "public_discovery"
    public_discovery_dir.mkdir()
    (public_discovery_dir / "public_discovery_gap_audit.json").write_text(
        json.dumps(
            {
                "summary": {
                    "requires_downloader_or_manifest_followup": True,
                    "requires_manual_manifest_review": True,
                    "new_high_priority_candidate_count": 3,
                    "new_review_candidate_count": 5,
                    "geo_download_ready_unknown_manifest_count": 18,
                    "manifest_download_ready_without_corpus_count": 2,
                    "manifest_download_ready_queued_count": 2,
                    "manifest_download_ready_unqueued_count": 0,
                }
            }
        ),
        encoding="utf-8",
    )
    (public_discovery_dir / "geo_manifest_promotion_candidates.json").write_text(
        json.dumps(
            {
                "summary": {
                    "candidate_count": 18,
                    "promote_download_candidate_count": 13,
                    "manual_review_count": 2,
                    "hold_non_plant_count": 3,
                },
                "candidates": [],
            }
        ),
        encoding="utf-8",
    )
    (public_discovery_dir / "geo_promotion_download_queue.json").write_text(
        json.dumps(
            {
                "summary": {
                    "job_count": 13,
                    "queue_script": "scripts/generated_geo_promotion_downloads/queue_geo_promotion_downloads.sh",
                    "start_script": "scripts/generated_geo_promotion_downloads/start_geo_promotion_queue.sh",
                },
                "jobs": [],
            }
        ),
        encoding="utf-8",
    )

    payload = module.build_actions(tmp_path)
    output_md = package_dir / "submission_action_plan.md"
    output_json = package_dir / "submission_action_plan.json"
    output_tsv = package_dir / "submission_action_plan.tsv"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    module.write_tsv(payload, output_tsv)
    by_id = {item["id"]: item for item in payload["actions"]}

    assert by_id["complete_safe_mlm_refresh"]["status"] == "IN_PROGRESS"
    assert (
        by_id["complete_foundation_5090_mlm_public_expansion_continuation"]["status"]
        == "IN_PROGRESS"
    )
    assert by_id["complete_reviewed_geo_transfer_queue"]["status"] == "IN_PROGRESS"
    assert by_id["triage_public_discovery_candidates"]["status"] == "IN_PROGRESS"
    assert by_id["obtain_saussurea_h5ad"]["status"] == "BLOCKED_USER_DATA"
    assert by_id["run_scplantannotate_authorized_benchmark"]["status"] == "BLOCKED_AUTH"
    assert by_id["include_training_curve_evidence"]["status"] == "READY"
    assert payload["summary"]["in_progress_count"] == 4
    assert payload["summary"]["blocked_count"] == 2
    action_md = output_md.read_text(encoding="utf-8")
    assert "BLOCKED_USER_DATA" in action_md
    assert "contract_ready=False" in action_md
    assert "data/saussurea_involucrata.h5ad" in action_md
    assert "complete_reviewed_geo_transfer_queue" in action_md
    assert "triage_public_discovery_candidates" in action_md
    assert "stale_partial_count=1" in action_md
    assert "provisional_payload_count=1" in action_md
    assert "geo_ready_unknown_manifest_count=18" in action_md
    assert "promotion_download_candidate_count=13" in action_md
    assert "promotion_manual_review_count=2" in action_md
    assert "promotion_download_job_count=13" in action_md
    assert "queued_download_ready_count=2" in action_md
    assert "unqueued_download_ready_count=0" in action_md
    assert "run_scplantannotate_authorized_benchmark" in output_tsv.read_text(encoding="utf-8")
    assert "input_h5ad_available=True" in action_md
    assert "truth_labels_available=True" in action_md
    assert "prediction_export_available=False" in action_md
    assert "scplantannotate_public_sprint_input/scplantannotate_input.h5ad" in action_md
    assert "submission_action_plan" in output_json.as_posix()


def test_manifest_scripts_keep_figshare_fallback(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.tsv"
    manifest.write_text(
        "\t".join(
            [
                "dataset_id",
                "species",
                "tissue_or_scope",
                "data_type",
                "priority",
                "accession_or_doi",
                "source_url",
                "why_use",
                "status",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "catharanthus",
                "Catharanthus roseus",
                "leaf",
                "scRNA",
                "B",
                "figshare 20255094",
                "https://figshare.com/articles/dataset/Single-cell_multi-omics_of_Catharanthus_roseus/20255094",
                "medicinal plant comparator",
                "download_candidate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_figshare(_: str) -> list[dict]:
        raise RuntimeError("offline")

    monkeypatch.setattr("snowcell.collect.list_figshare_files", fail_figshare)
    paths = write_manifest_download_scripts(manifest, tmp_path / "scripts")
    figshare_script = tmp_path / "scripts" / "download_figshare_20255094.sh"

    assert figshare_script in paths
    assert "Figshare API file listing failed" in figshare_script.read_text(encoding="utf-8")


def test_manifest_scripts_include_geo_filelists_and_generic_figshare(
    tmp_path: Path, monkeypatch
) -> None:
    manifest = tmp_path / "manifest.tsv"
    manifest.write_text(
        "\t".join(
            [
                "dataset_id",
                "species",
                "tissue_or_scope",
                "data_type",
                "priority",
                "accession_or_doi",
                "source_url",
                "why_use",
                "status",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "brassicaceae",
                "Brassicaceae",
                "root",
                "scRNA",
                "A",
                "GSE268881 / PRJNA1113801",
                "https://www.nature.com/articles/s41467-026-73270-2",
                "external adaptation benchmark",
                "download_candidate",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "figshare_generic",
                "Plant",
                "leaf",
                "scRNA",
                "B",
                "figshare 1234567",
                "https://figshare.com/articles/dataset/example/1234567",
                "generic figshare parser",
                "download_candidate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_figshare(_: str) -> list[dict]:
        raise RuntimeError("offline")

    monkeypatch.setattr("snowcell.collect.list_figshare_files", fail_figshare)
    paths = write_manifest_download_scripts(manifest, tmp_path / "scripts")
    geo_filelist_script = tmp_path / "scripts" / "download_geo_filelists.sh"
    figshare_script = tmp_path / "scripts" / "download_figshare_1234567.sh"

    assert geo_filelist_script in paths
    assert figshare_script in paths
    assert "GSE268881/suppl/filelist.txt" in geo_filelist_script.read_text(
        encoding="utf-8"
    )


def test_sparse_npz_loader(tmp_path: Path) -> None:
    matrix = sparse.csr_matrix([[0, 2, 0], [3, 0, 1]], dtype="float32")
    path = tmp_path / "sparse.npz"
    npz_payload = {
        "X_data": matrix.data,
        "X_indices": matrix.indices,
        "X_indptr": matrix.indptr,
        "X_shape": matrix.shape,
        "genes": ["AT1G01010", "AT1G01020", "AT1G01030"],
        "cell_type": ["root cortex", "root stele"],
        "cell_type_coarse": ["root cortex", "root stele"],
        "sample_id": ["sample_a", "sample_b"],
    }
    import numpy as np

    np.savez_compressed(path, **npz_payload)
    loaded = load_matrix(path, ExperimentConfig().data)

    assert sparse.isspmatrix_csr(loaded.X)
    assert loaded.X.shape == (2, 3)
    assert loaded.obs["cell_type"].tolist() == ["root cortex", "root stele"]


def test_explicit_leaveout_split_uses_requested_groups(tmp_path: Path) -> None:
    data_path = tmp_path / "demo.npz"
    make_demo_data(data_path, n_cells=180, n_genes=96, n_samples=6, seed=19)
    config = ExperimentConfig.from_dict(
        {
            "data": {
                "path": str(data_path),
                "max_genes": 32,
                "min_genes_per_cell": 5,
                "min_cells_per_gene": 2,
                "split_strategy": "explicit_leaveout",
                "leaveout_key": "sample_id",
                "leaveout_test_values": ["sample_00"],
                "leaveout_validation_values": ["sample_01"],
            },
            "architecture": {
                "d_model": 32,
                "n_layers": 1,
                "n_heads": 4,
                "ffn_dim": 64,
            },
            "train": {
                "stage": "hybrid",
                "epochs": 1,
                "batch_size": 8,
                "mixed_precision": "no",
            },
        }
    )
    prepared = prepare_data(config.data, seed=42, require_labels=True)
    split = prepared.preprocessing_stats["split"]

    assert split["test_leaveout_values"] == ["sample_00"]
    assert split["validation_leaveout_values"] == ["sample_01"]
    assert "sample_00" not in split["train_leaveout_values"]
    assert "sample_01" not in split["train_leaveout_values"]


def test_geo_10x_converter_writes_sparse_npz(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "geo_10x_to_npz.py"
    spec = importlib.util.spec_from_file_location("geo_10x_to_npz", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    sample = "GSM000001_Ath_Root_Ctrl_scRNAseq_R1"
    input_dir = tmp_path / "tenx"
    input_dir.mkdir()
    (input_dir / f"{sample}_barcodes.tsv.gz").write_bytes(
        gzip.compress(b"cell_a\ncell_b\n")
    )
    (input_dir / f"{sample}_features.tsv.gz").write_bytes(
        gzip.compress(b"AT1G01010\tGENE_A\nAT1G01020\tGENE_B\nAT1G01030\tGENE_C\n")
    )
    matrix = sparse.csr_matrix([[1, 0], [0, 2], [3, 0]], dtype="float32")
    with gzip.open(input_dir / f"{sample}_matrix.mtx.gz", "wb") as handle:
        io.mmwrite(handle, matrix)

    manifest = tmp_path / "manifest.tsv"
    paths = module.convert_directory(
        input_dir=input_dir,
        output_dir=tmp_path / "npz",
        dataset_id="brassicaceae_multi_species_root_atlas",
        manifest_output=manifest,
    )
    loaded = load_matrix(paths[0], ExperimentConfig().data)

    assert loaded.X.shape == (2, 3)
    assert loaded.obs["species"].tolist() == [
        "Arabidopsis thaliana",
        "Arabidopsis thaliana",
    ]
    assert loaded.obs["treatment"].tolist() == ["Ctrl", "Ctrl"]
    assert "brassicaceae_multi_species_root_atlas" in manifest.read_text(encoding="utf-8")


def test_geo_10x_converter_skips_invalid_gzip_when_requested(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "geo_10x_to_npz.py"
    spec = importlib.util.spec_from_file_location("geo_10x_to_npz_valid", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    input_dir = tmp_path / "tenx"
    input_dir.mkdir()
    good_sample = "GSM000001_Ath_Root_Ctrl_scRNAseq_R1"
    bad_sample = "GSM000002_Esa_Root_Ctrl_scRNAseq_R1"
    for sample in [good_sample, bad_sample]:
        (input_dir / f"{sample}_barcodes.tsv.gz").write_bytes(gzip.compress(b"cell_a\ncell_b\n"))
        (input_dir / f"{sample}_features.tsv.gz").write_bytes(
            gzip.compress(b"AT1G01010\tGENE_A\nAT1G01020\tGENE_B\n")
        )
    matrix = sparse.csr_matrix([[1, 0], [0, 2]], dtype="float32")
    with gzip.open(input_dir / f"{good_sample}_matrix.mtx.gz", "wb") as handle:
        io.mmwrite(handle, matrix)
    (input_dir / f"{bad_sample}_matrix.mtx.gz").write_text("<html>partial</html>", encoding="utf-8")

    triples = module.discover_triples(input_dir, require_valid_gzip=True)
    manifest = tmp_path / "manifest.tsv"
    outputs = module.convert_directory(
        input_dir=input_dir,
        output_dir=tmp_path / "npz",
        dataset_id="brassicaceae_multi_species_root_atlas",
        require_valid_gzip=True,
        manifest_output=manifest,
    )

    assert [triple.sample_id for triple in triples] == [good_sample]
    assert len(outputs) == 1
    assert bad_sample not in manifest.read_text(encoding="utf-8")


def test_geo_mtx_tar_converter_does_not_duplicate_nested_sample_dirs(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "geo_mtx_tar_to_npz.py"
    spec = importlib.util.spec_from_file_location("geo_mtx_tar_to_npz_nested", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    sample_dir = tmp_path / "extracted" / "GSM000001_sample"
    sample_dir.mkdir(parents=True)
    (sample_dir / "barcodes.tsv.gz").write_bytes(gzip.compress(b"cell_a\ncell_b\n"))
    (sample_dir / "features.tsv.gz").write_bytes(
        gzip.compress(b"AT1G01010\tGENE_A\nAT1G01020\tGENE_B\n")
    )
    matrix = sparse.csr_matrix([[1, 0], [0, 2]], dtype="float32")
    with gzip.open(sample_dir / "matrix.mtx.gz", "wb") as handle:
        io.mmwrite(handle, matrix)

    sample_dirs = module.discover_sample_dirs(tmp_path / "extracted")
    manifest = tmp_path / "manifest.tsv"
    outputs = [
        module.convert_one(
            sample_dirs[0],
            output_dir=tmp_path / "npz",
            dataset_id="nested_geo_mtx",
            species="Arabidopsis thaliana",
            tissue="root",
            feature_column=0,
            label="unannotated",
            coarse_label="unannotated",
        )
    ]
    module.write_manifest(outputs, manifest, "nested_geo_mtx", "Arabidopsis thaliana", "root")

    assert sample_dirs == [sample_dir]
    assert len(outputs) == 1
    assert manifest.read_text(encoding="utf-8").count("nested_geo_mtx") == 1


def test_create_leaveout_config_outputs_valid_experiment(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "create_leaveout_config.py"
    spec = importlib.util.spec_from_file_location("create_leaveout_config", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    base = tmp_path / "base.yaml"
    output = tmp_path / "leaveout.yaml"
    base.write_text(
        """
data:
  path: data/demo.npz
architecture:
  d_model: 32
  n_heads: 4
train:
  mixed_precision: "no"
output:
  directory: outputs/base
""".lstrip(),
        encoding="utf-8",
    )

    module.create_leaveout_config(
        base_config=base,
        output=output,
        leaveout_key="dataset_id",
        test_values=["dataset_a"],
        validation_values=["dataset_b"],
        data_path="data/strict_corpus.h5ad",
        output_dir="outputs/leaveout_dataset_a",
    )
    config = ExperimentConfig.load(output)

    assert config.data.split_strategy == "explicit_leaveout"
    assert config.data.leaveout_key == "dataset_id"
    assert config.data.path == "data/strict_corpus.h5ad"
    assert config.data.leaveout_test_values == ["dataset_a"]
    assert config.output.directory == "outputs/leaveout_dataset_a"


def test_audit_leaveout_splits_reports_supervised_ready(tmp_path: Path) -> None:
    audit_module_path = Path(__file__).parents[1] / "scripts" / "audit_leaveout_splits.py"
    spec = importlib.util.spec_from_file_location("audit_leaveout_splits", audit_module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_path = tmp_path / "demo.npz"
    config_path = tmp_path / "leaveout.yaml"
    make_demo_data(data_path, n_cells=240, n_genes=96, n_samples=8, seed=23)
    config_path.write_text(
        f"""
data:
  path: {data_path.as_posix()}
  max_genes: 32
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  split_strategy: explicit_leaveout
  leaveout_key: sample_id
  leaveout_test_values: ["sample_00"]
  leaveout_validation_values: ["sample_01"]
architecture:
  d_model: 32
  n_layers: 1
  n_heads: 4
  ffn_dim: 64
train:
  stage: hybrid
  mixed_precision: "no"
""".lstrip(),
        encoding="utf-8",
    )
    result = module.audit_config(config_path)

    assert result["supervised_benchmark_ready"] is True
    assert result["group_leakage"]["train_test_overlap"] == []
    assert list(result["leaveout_values"]["test"]) == ["sample_00"]


def test_tenx_h5_converter_writes_sparse_npz(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "tenx_h5_to_npz.py"
    spec = importlib.util.spec_from_file_location("tenx_h5_to_npz", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    input_dir = tmp_path / "h5"
    input_dir.mkdir()
    h5_path = input_dir / "GSM000001_rep1_filtered_feature_bc_matrix.h5"
    csc = sparse.csc_matrix([[1, 0], [0, 2], [3, 0]], dtype="float32")
    with h5py.File(h5_path, "w") as handle:
        group = handle.create_group("matrix")
        group.create_dataset("data", data=csc.data)
        group.create_dataset("indices", data=csc.indices.astype("int32"))
        group.create_dataset("indptr", data=csc.indptr.astype("int32"))
        group.create_dataset("shape", data=csc.shape)
        group.create_dataset("barcodes", data=[b"cell_a", b"cell_b"])
        features = group.create_group("features")
        features.create_dataset("id", data=[b"TraesCS1A01G000100", b"TraesCS1A01G000200", b"TraesCS1A01G000300"])
        features.create_dataset("name", data=[b"gene_a", b"gene_b", b"gene_c"])

    manifest = tmp_path / "manifest.tsv"
    outputs = module.convert_directory(
        input_dir=input_dir,
        output_dir=tmp_path / "npz",
        dataset_id="wheat_soil_root_atlas",
        species="Triticum aestivum",
        tissue="root",
        manifest_output=manifest,
    )
    loaded = load_matrix(outputs[0], ExperimentConfig().data)

    assert loaded.X.shape == (2, 3)
    assert loaded.obs["species"].tolist() == ["Triticum aestivum", "Triticum aestivum"]
    assert "wheat_soil_root_atlas" in manifest.read_text(encoding="utf-8")


def test_marker_candidate_mining_outputs_ranked_genes(tmp_path: Path) -> None:
    data_path = tmp_path / "demo.npz"
    config_path = tmp_path / "markers.yaml"
    output = tmp_path / "markers.tsv"
    summary = tmp_path / "markers.json"
    make_demo_data(data_path, n_cells=180, n_genes=120, n_samples=6, seed=31)
    config_path.write_text(
        f"""
data:
  path: {data_path.as_posix()}
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  normalize_total: 10000
  log1p: true
architecture:
  d_model: 32
  n_layers: 1
  n_heads: 4
  ffn_dim: 64
train:
  mixed_precision: "no"
""".lstrip(),
        encoding="utf-8",
    )

    run_marker_candidates(
        config_path=config_path,
        output=output,
        top_n=3,
        min_cells=5,
        summary_output=summary,
    )

    text = output.read_text(encoding="utf-8")
    assert "label_key\tlabel\trank\tgene" in text
    assert "guard_cell" in text
    assert summary.exists()


def test_data_availability_package_lists_public_data_and_gaps(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_data_availability_package.py"
    spec = importlib.util.spec_from_file_location("write_data_availability_package", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    status_summary = tmp_path / "status_summary.json"
    public_manifest = tmp_path / "public_dataset_manifest.tsv"
    output = tmp_path / "data_availability_and_fair.md"
    status_summary.write_text(
        """
{
  "corpora": [
    {"path": "data/plant_foundation_corpus_public_mlm_available.h5ad", "exists": true, "bytes": 1024},
    {"path": "data/plant_foundation_corpus_public_mlm.h5ad", "exists": false, "bytes": 0}
  ],
  "publication_gates": {
    "public_data_ingested": true,
    "snow_lotus_scRNA_present": false
  },
  "public_data_targets": [
    {
      "dataset_id": "arabidopsis_root_atlas",
      "stage": "manifest_ready",
      "manifest": {"rows": 2},
      "raw_files": {"file_count": 1},
      "npz_files": {"file_count": 2}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    public_manifest.write_text(
        "\t".join(
            [
                "dataset_id",
                "species",
                "tissue_or_scope",
                "data_type",
                "priority",
                "accession_or_doi",
                "source_url",
                "why_use",
                "status",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "arabidopsis_root_atlas",
                "Arabidopsis thaliana",
                "root",
                "scRNA",
                "A",
                "GSE152766",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE152766",
                "root benchmark",
                "download_candidate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    module.write_data_availability_package(status_summary, public_manifest, output)

    text = output.read_text(encoding="utf-8")
    assert "Data Availability Draft" in text
    assert "GSE152766" in text
    assert "saussurea_involucrata.h5ad" in text
    assert "FAIR Audit" in text


def test_artifact_checksum_writer_records_size_and_sha256(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_artifact_checksums.py"
    spec = importlib.util.spec_from_file_location("write_artifact_checksums", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    manifest = data_dir / "corpus_manifest.demo.tsv"
    manifest.write_text("path\tdataset_id\nx\tdemo\n", encoding="utf-8")
    output = tmp_path / "outputs" / "publication_package" / "artifact_checksums.tsv"

    module.write_checksums(
        project_dir=tmp_path,
        output=output,
        patterns=["data/corpus_manifest*.tsv"],
    )

    text = output.read_text(encoding="utf-8")
    assert "path\tbytes\tsha256" in text
    assert "data/corpus_manifest.demo.tsv" in text
    assert module.sha256_file(manifest) in text


def test_environment_snapshot_writer_records_reproduction_commands(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_environment_snapshot.py"
    spec = importlib.util.spec_from_file_location("write_environment_snapshot", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    def fake_runner(command: list[str], cwd: Path) -> dict:
        stdout = "snowcell==0.1" if command[-2:] == ["pip", "freeze"] else "ok"
        return {"command": command, "returncode": 0, "stdout": stdout, "stderr": ""}

    markdown = tmp_path / "environment_snapshot.md"
    json_output = tmp_path / "environment_snapshot.json"
    module.write_snapshot(tmp_path, markdown, json_output, runner=fake_runner)

    text = markdown.read_text(encoding="utf-8")
    assert "SnowLotus-CellFM Environment Snapshot" in text
    assert "bash scripts/generate_publication_package.sh" in text
    assert "bash scripts/start_public_mlm_continuation_training.sh" in text
    assert "bash scripts/start_public_mlm_continuation_watchdog.sh" in text
    assert "bash scripts/start_public_mlm_continuation_package_watchdog.sh" in text
    assert "snowcell==0.1" in text
    assert json_output.exists()


def test_ncbi_public_discovery_scores_geo_single_cell_candidate(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "discover_ncbi_public_datasets.py"
    spec = importlib.util.spec_from_file_location("discover_ncbi_public_datasets", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    record = module.record_from_summary(
        "gds",
        "plant_single_cell_gds",
        {
            "uid": "123456",
            "accession": "GSE999999",
            "title": "Arabidopsis root single-cell RNA-seq with 10x matrix files",
            "taxon": "Arabidopsis thaliana",
            "n_samples": "12",
            "summary": "Supplementary matrix.mtx.gz files are available for root cells.",
            "pdat": "2026/07/01",
        },
    )

    assert record.accession == "GSE999999"
    assert record.priority == "A"
    assert record.score >= 8
    assert record.url.endswith("acc=GSE999999")
    assert "fetch GEO" in record.recommended_action


def test_ncbi_public_discovery_dedupes_and_writes_outputs(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "discover_ncbi_public_datasets.py"
    spec = importlib.util.spec_from_file_location("discover_ncbi_public_datasets_dedupe", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    base_item = {
        "uid": "42",
        "accession": "GSE888888",
        "title": "Saussurea involucrata single-cell atlas",
        "taxon": "Saussurea involucrata",
        "summary": "single-cell RNA-seq data from snow lotus",
    }
    records = [
        module.record_from_summary("gds", "saussurea_single_cell_gds", base_item),
        module.record_from_summary("gds", "plant_single_cell_gds", base_item),
    ]
    deduped = module.dedupe_records(records)
    tsv_output = tmp_path / "discovery.tsv"
    json_output = tmp_path / "discovery.json"

    module.write_tsv(deduped, tsv_output)
    module.write_json(deduped, json_output)

    assert len(deduped) == 1
    assert deduped[0].priority == "S"
    assert "plant_single_cell_gds" in deduped[0].matched_queries
    assert "saussurea_single_cell_gds" in deduped[0].matched_queries
    assert "GSE888888" in tsv_output.read_text(encoding="utf-8")
    assert "Saussurea involucrata" in json_output.read_text(encoding="utf-8")


def test_ncbi_public_discovery_expands_snow_lotus_and_woody_queries() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "discover_ncbi_public_datasets.py"
    spec = importlib.util.spec_from_file_location("discover_ncbi_public_datasets_expanded", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    query_labels = {query.label for query in module.DEFAULT_QUERIES}
    assert "saussurea_alpine_evidence_sra" in query_labels
    assert "woody_legume_cereal_single_cell_gds" in query_labels
    assert "plant_spatial_single_cell_gds" in query_labels

    saussurea_record = module.record_from_summary(
        "sra",
        "saussurea_alpine_evidence_sra",
        {
            "uid": "77",
            "accession": "PRJNA777777",
            "title": "Saussurea medusa alpine low temperature RNA-Seq",
            "taxon": "Saussurea medusa",
            "summary": "Transcriptome profiles under low pressure and hypoxia stress.",
        },
    )
    assert saussurea_record.priority == "A"
    assert saussurea_record.score >= 8
    assert "Snow Lotus evidence layer" in saussurea_record.recommended_action

    populus_record = module.record_from_summary(
        "gds",
        "woody_legume_cereal_single_cell_gds",
        {
            "uid": "88",
            "accession": "GSE777888",
            "title": "Populus xylem single nucleus spatial transcriptomics with 10x matrix",
            "taxon": "Populus trichocarpa",
            "summary": "snRNA-seq matrix.mtx files for woody stem cells.",
        },
    )
    assert populus_record.priority == "A"
    assert "fetch GEO" in populus_record.recommended_action


def test_validate_experiment_configs_script_accepts_valid_yaml(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "validate_experiment_configs.py"
    spec = importlib.util.spec_from_file_location("validate_experiment_configs", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    config_path = tmp_path / "valid.yaml"
    config_path.write_text(
        """
data:
  path: data/demo.npz
  max_genes: 32
architecture:
  d_model: 32
  n_layers: 1
  n_heads: 4
  ffn_dim: 64
train:
  mixed_precision: "no"
output:
  directory: outputs/demo
""".lstrip(),
        encoding="utf-8",
    )

    assert module.validate_configs([config_path]) == [config_path]


def test_geo_supplementary_reviewer_detects_downloadable_matrix_files(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "review_geo_supplementary_candidates.py"
    spec = importlib.util.spec_from_file_location("review_geo_supplementary_candidates", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    manifest = tmp_path / "public_dataset_manifest.tsv"
    manifest.write_text(
        "\t".join(
            [
                "dataset_id",
                "species",
                "tissue_or_scope",
                "data_type",
                "priority",
                "accession_or_doi",
                "source_url",
                "why_use",
                "status",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "stevia_leaf_secondary_metabolism_snuc",
                "Stevia rebaudiana",
                "leaf",
                "snRNA",
                "A",
                "GSE311951",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE311951",
                "secondary metabolism comparator",
                "discovery_candidate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    html_text = """
<a href="ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM999nnn/GSM999001/suppl/GSM999001_leaf_filtered_feature_bc_matrix.h5">h5</a>
<a href="ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM999nnn/GSM999002/suppl/GSM999002_leaf_seurat.rds.gz">rds</a>
GSE311951_RAW.tar
"""

    reviews, file_reviews = module.review_manifest_with_files(
        manifest,
        statuses={"discovery_candidate"},
        fetcher=lambda _: html_text,
        throttle_seconds=0,
    )
    file_tsv = tmp_path / "geo_files.tsv"
    module.write_file_tsv(file_reviews, file_tsv)

    assert len(reviews) == 1
    assert reviews[0].accession == "GSE311951"
    assert reviews[0].download_ready is True
    assert reviews[0].matrix_file_count == 3
    assert "tenx_h5:1" in reviews[0].file_type_counts
    assert "seurat_rds:1" in reviews[0].file_type_counts
    assert "GSM999001_leaf_filtered_feature_bc_matrix.h5" in file_tsv.read_text(
        encoding="utf-8"
    )


def test_geo_supplementary_reviewer_adds_unknown_discovery_gse_candidates(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "review_geo_supplementary_candidates.py"
    spec = importlib.util.spec_from_file_location("review_geo_supplementary_candidates_discovery", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    manifest = tmp_path / "public_dataset_manifest.tsv"
    manifest.write_text(
        "dataset_id\tspecies\ttissue_or_scope\tdata_type\tpriority\taccession_or_doi\t"
        "source_url\twhy_use\tstatus\n"
        "known_leaf\tZea mays\tleaf\tscRNA\tA\tGSE1\thttps://example.org/GSE1\tknown\t"
        "discovery_candidate\n",
        encoding="utf-8",
    )
    discovery = tmp_path / "ncbi_discovery.tsv"
    discovery.write_text(
        "accession\ttitle\torganism\tpriority\tscore\turl\tmatched_queries\trecommended_action\n"
        "GSE196882\tSpatial transcriptomics of maize embryonic leaves\tZea mays\tA\t8\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE196882\tspatial plant\t"
        "review GEO supplementary files\n"
        "GSE1\tKnown duplicate\tZea mays\tA\t9\thttps://example.org/GSE1\tplant\tduplicate\n"
        "PRJNA1\tNot GEO\tZea mays\tA\t9\thttps://example.org/PRJNA1\tplant\tsra\n",
        encoding="utf-8",
    )
    html_text = "GSE196882_RAW.tar"

    reviews, _ = module.review_manifest_with_files(
        manifest,
        statuses={"download_candidate"},
        fetcher=lambda _: html_text,
        throttle_seconds=0,
        discovery_tsv=discovery,
        discovery_priorities={"A"},
        max_discovery_gse=5,
    )

    assert len(reviews) == 1
    assert reviews[0].dataset_id == "discovered_gse196882"
    assert reviews[0].status == "ncbi_discovery_candidate"
    assert reviews[0].download_ready is True
    assert reviews[0].matrix_file_count == 1


def test_geo_supplementary_reviewer_keeps_atac_h5ad_out_of_expression_corpus() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "review_geo_supplementary_candidates.py"
    spec = importlib.util.spec_from_file_location("review_geo_supplementary_candidates_atac", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    files = [
        module.GeoFile(
            url="https://example.org/snATAC.h5ad",
            filename="GSE332675_anndata_object.snATAC_Athaliana_seedling_combined.h5ad",
            file_type="h5ad",
        )
    ]

    action, ready = module.recommended_action(files)

    assert ready is False
    assert "ATAC-only" in action
    assert "do not add to expression corpus" in action


def test_geo_supplementary_review_shell_includes_download_candidates() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "review_geo_supplementary_candidates.sh").read_text(
        encoding="utf-8"
    )

    assert "--status discovery_candidate" in script
    assert "--status download_candidate" in script
    assert "--discovery-tsv" in script
    assert "SNOWCELL_GEO_REVIEW_MAX_DISCOVERY_GSE" in script


def test_status_summary_includes_public_discovery_reviews(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_discovery", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    discovery_dir = tmp_path / "data" / "public_discovery"
    discovery_dir.mkdir(parents=True)
    (discovery_dir / "ncbi_discovery_20260723_000000.tsv").write_text(
        "accession\ttitle\nGSE1\tdemo\n",
        encoding="utf-8",
    )
    (discovery_dir / "geo_supplementary_review_20260723_000000.tsv").write_text(
        "\t".join(
            [
                "dataset_id",
                "accession",
                "download_ready",
                "matrix_file_count",
                "recommended_action",
            ]
        )
        + "\n"
        + "\t".join(["demo_dataset", "GSE1", "True", "2", "download 10x H5 subset"])
        + "\n",
        encoding="utf-8",
    )
    (discovery_dir / "geo_supplementary_files_20260723_000000.tsv").write_text(
        "dataset_id\taccession\tfilename\n"
        "demo_dataset\tGSE1\tGSM1_filtered_feature_bc_matrix.h5\n",
        encoding="utf-8",
    )
    (discovery_dir / "scplantdb_dataset_catalog.tsv").write_text(
        "dataset\tspecies\ttissue\tcells\n"
        "SRP169576\tArabidopsis thaliana\tWhole root\t35665\n",
        encoding="utf-8",
    )
    (discovery_dir / "scplantdb_h5ad_size_probe.tsv").write_text(
        "dataset\tspecies\ttissue\tcells\tcontent_length\tsize_mb\tok\tselected_for_download\n"
        "SRP169576\tArabidopsis thaliana\tWhole root\t35665\t108802218\t103.762\tTrue\tTrue\n",
        encoding="utf-8",
    )
    (discovery_dir / "scplantdb_selected_h5ad_datasets.txt").write_text(
        "SRP169576\n",
        encoding="utf-8",
    )
    package_discovery_dir = tmp_path / "outputs" / "publication_package" / "public_discovery"
    package_discovery_dir.mkdir(parents=True)
    (package_discovery_dir / "public_discovery_gap_audit.json").write_text(
        json.dumps(
            {
                "summary": {
                    "new_high_priority_candidate_count": 1,
                    "requires_manual_manifest_review": True,
                }
            }
        ),
        encoding="utf-8",
    )

    summary = module.public_discovery_summary(tmp_path)

    assert summary["latest_geo_review_rows"] == 1
    assert summary["download_ready_rows"] == 1
    assert summary["download_ready_accessions"][0]["accession"] == "GSE1"
    assert summary["latest_geo_file_index"].endswith("geo_supplementary_files_20260723_000000.tsv")
    assert summary["scplantdb_catalog"]["rows"] == 1
    assert summary["scplantdb_h5ad_probe"]["reachable_rows"] == 1
    assert summary["scplantdb_h5ad_probe"]["selected_dataset_ids"] == ["SRP169576"]
    assert summary["gap_audit"]["exists"] is True
    assert summary["gap_audit"]["summary"]["new_high_priority_candidate_count"] == 1


def test_public_discovery_gap_audit_flags_unmanifested_candidates(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_public_discovery_gap_audit.py"
    spec = importlib.util.spec_from_file_location("write_public_discovery_gap_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    discovery_dir = data_dir / "public_discovery"
    discovery_dir.mkdir(parents=True)
    data_dir.mkdir(exist_ok=True)
    (data_dir / "public_dataset_manifest.tsv").write_text(
        "\t".join(
            [
                "dataset_id",
                "species",
                "tissue_or_scope",
                "data_type",
                "priority",
                "accession_or_doi",
                "source_url",
                "why_use",
                "status",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "arabidopsis_root_atlas",
                "Arabidopsis thaliana",
                "root",
                "scRNA",
                "A",
                "GSE152766",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE152766",
                "root benchmark",
                "download_candidate",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "tomato_rice_root_tip_celltype_atlas",
                "Solanum lycopersicum; Oryza sativa",
                "root tip",
                "scRNA",
                "B",
                "GSE149217",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149217",
                "root tip benchmark",
                "download_candidate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_dir / "corpus_manifest.gse152766.tsv").write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/GSE152766_npz/root.npz\tarabidopsis_root_atlas\tArabidopsis thaliana\n",
        encoding="utf-8",
    )
    (data_dir / "corpus_manifest.gse777777.tsv").write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/GSE777777_npz/root.npz\tdynamic_only_root_atlas\tCatharanthus roseus\n",
        encoding="utf-8",
    )
    (discovery_dir / "ncbi_discovery_20260724_000000.tsv").write_text(
        "\t".join(
            [
                "query_label",
                "db",
                "uid",
                "accession",
                "title",
                "organism",
                "sample_count",
                "publication_date",
                "url",
                "priority",
                "score",
                "recommended_action",
                "matched_queries",
                "summary",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "plant_single_cell_gds",
                "gds",
                "1",
                "GSE999999",
                "Medicinal plant single-cell atlas with 10x matrix",
                "Catharanthus roseus",
                "8",
                "2026/07/01",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE999999",
                "A",
                "9",
                "fetch GEO supplementary filelist; add downloader if matrix/RDS/H5 exists",
                "plant_single_cell_gds",
                "single-cell RNA-seq matrix files",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "plant_single_cell_gds",
                "gds",
                "2",
                "GSE152766",
                "Known Arabidopsis root atlas",
                "Arabidopsis thaliana",
                "12",
                "2020/01/01",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE152766",
                "A",
                "8",
                "fetch GEO supplementary filelist",
                "plant_single_cell_gds",
                "known single-cell matrix",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "plant_single_cell_gds",
                "gds",
                "3",
                "GSE777777",
                "Dynamic manifest-only medicinal plant atlas",
                "Catharanthus roseus",
                "6",
                "2025/01/01",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE777777",
                "A",
                "7",
                "fetch GEO supplementary filelist",
                "plant_single_cell_gds",
                "already converted dynamic corpus manifest",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "plant_single_cell_gds",
                "gds",
                "4",
                "GSE234704",
                "Mouse pancreatic endocrine single-cell atlas",
                "Mus musculus",
                "10",
                "2024/01/01",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE234704",
                "A",
                "8",
                "hold non-plant",
                "plant_single_cell_gds",
                "non-plant matrix candidate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (discovery_dir / "geo_supplementary_review_20260724_000000.tsv").write_text(
        "\t".join(
            [
                "dataset_id",
                "accession",
                "priority",
                "download_ready",
                "matrix_file_count",
                "file_type_counts",
                "recommended_action",
                "page_url",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "new_medicinal_atlas",
                "GSE999999",
                "A",
                "True",
                "2",
                "tenx_h5:2",
                "download 10x H5 subset",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE999999",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "tomato_rice_root_tip_celltype_atlas",
                "GSE149217",
                "B",
                "True",
                "1",
                "mtx_archive:1",
                "download MTX/10x archive",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE149217",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "mouse_pancreas_holdout",
                "GSE234704",
                "A",
                "True",
                "1",
                "metadata_table:8;mtx_archive:1",
                "download MTX/10x archive",
                "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE234704",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (discovery_dir / "geo_manifest_promotion_candidates.tsv").write_text(
        "accession\tdiscovered_dataset_id\tsuggested_dataset_id\torganism\t"
        "title\tpriority\tscore\tmatrix_file_count\tfile_type_counts\t"
        "promotion_status\treason\trecommended_downloader\tsource_url\tgeo_page_url\n"
        "GSE234704\tdiscovered_gse234704\tgeo_gse234704_mus_musculus_pancreas\t"
        "Mus musculus\tMouse pancreatic endocrine single-cell atlas\tA\t8\t1\t"
        "metadata_table:8;mtx_archive:1\tHOLD_NON_PLANT\t"
        "Organism terms indicate a non-plant dataset.\t"
        "download_geo_raw_tar_mtx_subset.sh\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE234704\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE234704\n",
        encoding="utf-8",
    )
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    generated_dir = scripts_dir / "generated_geo_promotion_downloads"
    generated_dir.mkdir()
    (scripts_dir / "queue_reviewed_geo_downloads.sh").write_text(
        'jobs=(\n'
        '  "snowcell_gse149217_tomato_rice_root_tip_subset|data/corpus_manifest.gse149217.tsv|bash scripts/download_gse149217_tomato_rice_root_tip_mtx_subset.sh|logs/gse149217_tomato_rice_root_tip_subset.log"\n'
        ')\n',
        encoding="utf-8",
    )
    (generated_dir / "queue_geo_promotion_downloads.sh").write_text(
        'jobs=(\n'
        '  "snowcell_geo_promotion_gse999999|data/corpus_manifest.gse999999.tsv|bash scripts/generated_geo_promotion_downloads/download_gse999999.sh|logs/geo_promotion_gse999999.log"\n'
        ')\n',
        encoding="utf-8",
    )
    output_md = tmp_path / "outputs" / "publication_package" / "public_discovery" / "gap.md"
    output_json = tmp_path / "outputs" / "publication_package" / "public_discovery" / "gap.json"

    payload = module.build_audit(tmp_path)
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    assert payload["summary"]["public_manifest_accession_count"] == 2
    assert payload["summary"]["dynamic_corpus_manifest_accession_count"] == 2
    assert payload["summary"]["known_manifest_accession_count"] == 3
    assert payload["summary"]["queued_geo_job_count"] == 2
    assert payload["summary"]["promotion_hold_accession_count"] == 1
    assert payload["summary"]["new_high_priority_candidate_count"] == 0
    assert payload["summary"]["geo_download_ready_unknown_manifest_count"] == 1
    assert payload["summary"]["geo_download_ready_unknown_manifest_queued_count"] == 1
    assert payload["summary"]["geo_download_ready_unknown_manifest_unqueued_count"] == 0
    assert payload["summary"]["manifest_download_ready_without_corpus_count"] == 1
    assert payload["summary"]["manifest_download_ready_queued_count"] == 1
    assert payload["summary"]["manifest_download_ready_unqueued_count"] == 0
    assert payload["summary"]["requires_manual_manifest_review"] is False
    assert payload["summary"]["requires_downloader_or_manifest_followup"] is False
    assert payload["summary"]["requires_queued_download_completion"] is True
    assert payload["new_high_priority_candidates"] == []
    assert payload["geo_download_ready_unknown_manifest_queued"][0]["accession"] == "GSE999999"
    assert payload["geo_download_ready_unknown_manifest_queued"][0]["queued_download"] is True
    assert "download_gse999999.sh" in (
        payload["geo_download_ready_unknown_manifest_queued"][0]["queue_job"]["command"]
    )
    assert payload["manifest_download_ready_without_corpus"][0]["queued_download"] is True
    assert "download_gse149217_tomato_rice_root_tip_mtx_subset.sh" in (
        payload["manifest_download_ready_without_corpus"][0]["queue_job"]["command"]
    )
    assert "GSE999999" in output_md.read_text(encoding="utf-8")
    assert "Queued" in output_md.read_text(encoding="utf-8")


def test_geo_manifest_promotion_candidates_classifies_unknown_geo_rows(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_geo_manifest_promotion_candidates.py"
    spec = importlib.util.spec_from_file_location("write_geo_manifest_promotion_candidates", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    discovery_dir = data_dir / "public_discovery"
    discovery_dir.mkdir(parents=True)
    (data_dir / "public_dataset_manifest.tsv").write_text(
        "dataset_id\tspecies\ttissue_or_scope\tdata_type\tpriority\taccession_or_doi\t"
        "source_url\twhy_use\tstatus\n"
        "known_root\tArabidopsis thaliana\troot\tscRNA\tA\tGSE1\thttps://example.org/GSE1\tknown\tdownload_candidate\n",
        encoding="utf-8",
    )
    (discovery_dir / "ncbi_discovery_20260725_000000.tsv").write_text(
        "accession\ttitle\torganism\tpriority\tscore\turl\tsummary\tmatched_queries\trecommended_action\n"
        "GSE303996\tArabidopsis root regeneration single-cell atlas\tArabidopsis thaliana\tA\t7\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE303996\tplant root\tarabidopsis root\treview\n"
        "GSE182507\tSingle-cell RNA sequencing of Medicago truncatula roots\tMedicago truncatula\tA\t8\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182507\tlegume root scRNA\tmedicago root\treview\n"
        "GSE267159\tSingle-Cell and Spatial Multi-Omics Reveal Xylem Development in Populus\tPopulus trichocarpa\tA\t7\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE267159\tpopulus xylem single-cell\tpopulus stem\treview\n"
        "GSE270392\tA spatially resolved multiomic single-cell atlas of soybean development\tGlycine max\tA\t7\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE270392\tsoybean spatial atlas\tglycine max\treview\n"
        "GSE90142\tDivergent cytosine DNA methylation patterns in single-cell soybean root hairs (MethylC-seq)\tGlycine max\tA\t7\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE90142\tmethylation profiles with RNA-Seq sibling links\tsoybean root hairs\treview\n"
        "GSE273478\tThe genetic architecture of cell-type-specific cis-regulation [ATAC-seq]\tZea mays\tA\t6\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE273478\tmaize cis regulation\tmaize atac\treview\n"
        "GSE256014\tSingle cell-RNA datasets from mouse and maize tissues\tHomo sapiens; Zea mays; Mus musculus\tA\t6\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE256014\tmixed organisms\tmaize scRNA\treview\n"
        "GSE214016\tGene expression profile at single cell level of nervous system in sea cucumber\tApostichopus japonicus\tA\t6\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE214016\tsea cucumber nervous system\tsea cucumber\treview\n"
        "GSE259427\tMouse early embryogenesis scRNAseq\tMus musculus\tA\t6\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE259427\tmouse\tmouse\treview\n",
        encoding="utf-8",
    )
    (discovery_dir / "geo_supplementary_review_20260725_000000.tsv").write_text(
        "dataset_id\taccession\tpriority\tstatus\tdownload_ready\tmatrix_file_count\tfile_type_counts\tpage_url\n"
        "discovered_gse303996\tGSE303996\tA\tncbi_discovery_candidate\tTrue\t17\tmtx_archive:1;seurat_rds:16\thttps://geo/GSE303996\n"
        "discovered_gse182507\tGSE182507\tA\tncbi_discovery_candidate\tTrue\t1\tmtx_archive:1\thttps://geo/GSE182507\n"
        "discovered_gse267159\tGSE267159\tA\tncbi_discovery_candidate\tTrue\t1\tmtx_archive:1\thttps://geo/GSE267159\n"
        "discovered_gse270392\tGSE270392\tA\tncbi_discovery_candidate\tTrue\t46\tmtx_archive:1;seurat_rds:45\thttps://geo/GSE270392\n"
        "discovered_gse90142\tGSE90142\tA\tncbi_discovery_candidate\tTrue\t1\tmtx_archive:1\thttps://geo/GSE90142\n"
        "discovered_gse273478\tGSE273478\tA\tncbi_discovery_candidate\tTrue\t2\tarchive:1;seurat_rds:2\thttps://geo/GSE273478\n"
        "discovered_gse256014\tGSE256014\tA\tncbi_discovery_candidate\tTrue\t2\th5ad:1;mtx_archive:1\thttps://geo/GSE256014\n"
        "discovered_gse214016\tGSE214016\tA\tncbi_discovery_candidate\tTrue\t1\tmtx_archive:1\thttps://geo/GSE214016\n"
        "discovered_gse259427\tGSE259427\tA\tncbi_discovery_candidate\tTrue\t2\th5ad:1;mtx_archive:1\thttps://geo/GSE259427\n",
        encoding="utf-8",
    )

    payload = module.build_candidates(tmp_path)
    output_md = discovery_dir / "geo_manifest_promotion_candidates.md"
    output_json = discovery_dir / "geo_manifest_promotion_candidates.json"
    output_tsv = discovery_dir / "geo_manifest_promotion_candidates.tsv"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    module.write_tsv(payload, output_tsv)
    by_accession = {item["accession"]: item for item in payload["candidates"]}

    assert payload["summary"]["candidate_count"] == 9
    assert payload["summary"]["promote_download_candidate_count"] == 4
    assert payload["summary"]["manual_review_count"] == 1
    assert payload["summary"]["hold_non_plant_count"] == 2
    assert by_accession["GSE303996"]["promotion_status"] == "PROMOTE_DOWNLOAD_CANDIDATE"
    assert by_accession["GSE182507"]["promotion_status"] == "PROMOTE_DOWNLOAD_CANDIDATE"
    assert by_accession["GSE267159"]["promotion_status"] == "PROMOTE_DOWNLOAD_CANDIDATE"
    assert by_accession["GSE270392"]["promotion_status"] == "PROMOTE_DOWNLOAD_CANDIDATE"
    assert by_accession["GSE90142"]["promotion_status"] == "HOLD_REGULATORY_ONLY"
    assert by_accession["GSE273478"]["promotion_status"] == "HOLD_REGULATORY_ONLY"
    assert by_accession["GSE256014"]["promotion_status"] == "MANUAL_REVIEW_MIXED_ORGANISM"
    assert by_accession["GSE214016"]["promotion_status"] == "HOLD_NON_PLANT"
    assert by_accession["GSE259427"]["promotion_status"] == "HOLD_NON_PLANT"
    assert "download_geo_raw_tar_mtx_subset.sh" in output_md.read_text(encoding="utf-8")
    assert "PROMOTE_DOWNLOAD_CANDIDATE" in output_tsv.read_text(encoding="utf-8")
    assert "geo_manifest_promotion_candidates" in output_json.as_posix()


def test_geo_promotion_download_wrapper_generator_writes_safe_queue(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_geo_promotion_download_wrappers.py"
    spec = importlib.util.spec_from_file_location("write_geo_promotion_download_wrappers", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    discovery_dir = tmp_path / "data" / "public_discovery"
    discovery_dir.mkdir(parents=True)
    promotion_tsv = discovery_dir / "geo_manifest_promotion_candidates.tsv"
    promotion_tsv.write_text(
        "accession\tsuggested_dataset_id\torganism\ttitle\tpromotion_status\tfile_type_counts\t"
        "recommended_downloader\tsource_url\n"
        "GSE303996\tgeo_gse303996_arabidopsis_root_regeneration\tArabidopsis thaliana\t"
        "Arabidopsis root regeneration\tPROMOTE_DOWNLOAD_CANDIDATE\tmtx_archive:1;seurat_rds:16\t"
        "download_geo_raw_tar_mtx_subset.sh\thttps://geo/GSE303996\n"
        "GSE273875\tgeo_gse273875_oryza_single_cell_multiomics\tOryza sativa\t"
        "A single-cell multiomics atlas of rice\tPROMOTE_DOWNLOAD_CANDIDATE\tseurat_rds:1\t"
        "download_geo_rds_subset.sh\thttps://geo/GSE273875\n"
        "GSE201931\tgeo_gse201931_tomato_leaf\tSolanum lycopersicum\t"
        "High-throughput single-cell transcriptome profiling of tomato leaf\tPROMOTE_DOWNLOAD_CANDIDATE\t"
        "metadata_table:4;mtx_component:2\tdownload_geo_raw_tar_mtx_subset.sh\thttps://geo/GSE201931\n"
        "GSE253665\tgeo_gse253665_bombyx\tBombyx mori\tSilkworm\tHOLD_NON_PLANT\tmtx_archive:1\t"
        "download_geo_raw_tar_mtx_subset.sh\thttps://geo/GSE253665\n",
        encoding="utf-8",
    )
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "queue_reviewed_geo_downloads.sh").write_text(
        'jobs=(\n'
        '  "snowcell_gse325371_tomato_salt_idioblast_subset|data/corpus_manifest.gse325371.tsv|'
        'bash scripts/download_gse325371_tomato_salt_idioblast_mtx_subset.sh|'
        'logs/gse325371_tomato_salt_idioblast_subset.log"\n'
        ')\n',
        encoding="utf-8",
    )

    jobs = module.build_jobs(
        tmp_path,
        Path("data/public_discovery/geo_manifest_promotion_candidates.tsv"),
        Path("scripts/generated_geo_promotion_downloads"),
    )
    for job in jobs:
        module.write_wrapper(job, tmp_path)
    queue_script = module.write_queue_script(
        jobs,
        tmp_path,
        Path("scripts/generated_geo_promotion_downloads/queue_geo_promotion_downloads.sh"),
    )
    start_script = module.write_start_script(
        tmp_path,
        Path("scripts/generated_geo_promotion_downloads/queue_geo_promotion_downloads.sh"),
        Path("scripts/generated_geo_promotion_downloads/start_geo_promotion_queue.sh"),
    )
    payload = {
        "summary": {
            "generated_at_utc": "2026-07-24T00:00:00+00:00",
            "promotion_tsv": "data/public_discovery/geo_manifest_promotion_candidates.tsv",
            "job_count": len(jobs),
            "queue_script": "scripts/generated_geo_promotion_downloads/queue_geo_promotion_downloads.sh",
            "start_script": "scripts/generated_geo_promotion_downloads/start_geo_promotion_queue.sh",
        },
        "jobs": [module.asdict(job) for job in jobs],
    }
    output_md = discovery_dir / "geo_promotion_download_queue.md"
    output_json = discovery_dir / "geo_promotion_download_queue.json"
    output_tsv = discovery_dir / "geo_promotion_download_queue.tsv"
    module.write_report(payload, output_md, output_json, output_tsv)

    assert len(jobs) == 3
    assert {job.accession for job in jobs} == {"GSE303996", "GSE273875", "GSE201931"}
    jobs_by_accession = {job.accession: job for job in jobs}
    mtx_wrapper = (tmp_path / jobs_by_accession["GSE303996"].wrapper_script).read_text(encoding="utf-8")
    rds_wrapper = (tmp_path / jobs_by_accession["GSE273875"].wrapper_script).read_text(encoding="utf-8")
    component_wrapper = (tmp_path / jobs_by_accession["GSE201931"].wrapper_script).read_text(encoding="utf-8")
    queue_text = queue_script.read_text(encoding="utf-8")
    start_text = start_script.read_text(encoding="utf-8")

    assert "SNOWCELL_GEO_ACCESSION=GSE303996" in mtx_wrapper
    assert "download_geo_raw_tar_mtx_subset.sh" in mtx_wrapper
    assert "download_geo_page_rds_subset.sh" in rds_wrapper
    assert "download_geo_mtx_component_subset.sh" in component_wrapper
    assert module.infer_tissue("Populus xylem stem single-cell atlas") == "stem"
    assert "has_active_reviewed_transfer" in queue_text
    assert "reviewed_manifests=(" in queue_text
    assert "data/corpus_manifest.gse325371.tsv" in queue_text
    assert "unsupported_report_for_manifest" in queue_text
    assert "find_transfer_file_for_manifest" in queue_text
    assert "mtx_components" in queue_text
    assert "promotion_manifest_done" in queue_text
    assert "promotion GEO job unsupported" in queue_text
    assert "partial_download_for_manifest" in queue_text
    assert "reviewed_queue_pending" in queue_text
    assert "reviewed GEO queue still has pending static jobs" in queue_text
    assert "snowcell_gse[0-9].*_subset" in queue_text
    assert "has_active_unfinished_promotion_transfer" in queue_text
    assert "snowcell_geo_promotion_gse[0-9]*" in queue_text
    assert 'active_manifest="data/corpus_manifest.${active_accession}.tsv"' in queue_text
    assert "another promotion GEO job is already active" in queue_text
    assert "promotion GEO transfer active; waiting before starting" in queue_text
    assert "snowcell_geo_promotion_download_queue" in start_text
    assert "SNOWCELL_GEO_PROMOTION_QUEUE_RESTART" in start_text
    assert "tmux kill-session -t \"$session\"" in start_text
    assert "GSE253665" not in output_tsv.read_text(encoding="utf-8")
    assert "geo_promotion_download_queue" in output_json.as_posix()


def test_public_discovery_gap_audit_skips_unsupported_expression_targets(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_public_discovery_gap_audit.py"
    spec = importlib.util.spec_from_file_location("write_public_discovery_gap_audit_unsupported", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    discovery_dir = data_dir / "public_discovery"
    unsupported_dir = data_dir / "public" / "GSE336751_raw_tar"
    discovery_dir.mkdir(parents=True)
    unsupported_dir.mkdir(parents=True)
    (data_dir / "public_dataset_manifest.tsv").write_text(
        "dataset_id\tspecies\ttissue_or_scope\tdata_type\tpriority\taccession_or_doi\tsource_url\twhy_use\tstatus\n"
        "marchantia_spore_asymmetry_single_cell\tMarchantia polymorpha\tspore\tsingle-cell developmental transcriptomics\tC\tGSE336751\thttps://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE336751\toutgroup\t"
        "download_candidate\n",
        encoding="utf-8",
    )
    (data_dir / "corpus_manifest.gse336751.tsv").write_text(
        "path\tdataset_id\tspecies\n",
        encoding="utf-8",
    )
    (unsupported_dir / "unsupported_single_cell_matrix.json").write_text(
        json.dumps(
            {
                "accession": "GSE336751",
                "dataset_id": "marchantia_spore_asymmetry_single_cell",
                "status": "unsupported_for_single_cell_matrix_corpus",
            }
        ),
        encoding="utf-8",
    )
    (discovery_dir / "geo_supplementary_review_20260724_000000.tsv").write_text(
        "dataset_id\taccession\tpriority\tdownload_ready\tmatrix_file_count\tfile_type_counts\trecommended_action\tpage_url\n"
        "marchantia_spore_asymmetry_single_cell\tGSE336751\tC\tTrue\t1\tmtx_archive:1\tdownload MTX/10x archive\thttps://example.org/GSE336751\n",
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)

    assert payload["summary"]["unsupported_expression_corpus_target_count"] == 2
    assert payload["summary"]["manifest_download_ready_without_corpus_count"] == 0
    assert payload["manifest_download_ready_without_corpus"] == []


def test_pending_corpus_additions_marks_missing_public_rows(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_pending_corpus_additions.py"
    spec = importlib.util.spec_from_file_location("write_pending_corpus_additions", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    base_public = data_dir / "corpus_manifest_public_mlm.tsv"
    public_corpus = data_dir / "plant_foundation_corpus_public_mlm.h5ad"
    gse_manifest = data_dir / "corpus_manifest.gse243419.tsv"
    base_public.write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/old.npz\told_dataset\tArabidopsis thaliana\n",
        encoding="utf-8",
    )
    public_corpus.write_bytes(b"old")
    gse_manifest.write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/GSE243419_npz/GSE243419_mtx_extracted.npz\tcotton_glandular_terpenoid_atlas\tGossypium hirsutum\n",
        encoding="utf-8",
    )

    items = module.collect_pending(tmp_path, base_public, public_corpus)
    output_md = tmp_path / "pending.md"
    output_json = tmp_path / "pending.json"
    module.write_markdown(items, output_md)
    module.write_json(items, output_json)

    assert len(items) == 1
    assert items[0].pending_refresh is True
    assert items[0].rows_missing_from_public_mlm_manifest == 1
    assert "cotton_glandular_terpenoid_atlas" in output_md.read_text(encoding="utf-8")
    assert "corpus_manifest.gse243419.tsv" in output_json.read_text(encoding="utf-8")


def test_pending_corpus_additions_includes_scplantdb_manifests(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_pending_corpus_additions.py"
    spec = importlib.util.spec_from_file_location("write_pending_corpus_additions_scplantdb", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    base_public = data_dir / "corpus_manifest_public_mlm.tsv"
    public_corpus = data_dir / "plant_foundation_corpus_public_mlm.h5ad"
    scplantdb_manifest = data_dir / "corpus_manifest.scplantdb.tsv"
    base_public.write_text("path\tdataset_id\tspecies\n", encoding="utf-8")
    public_corpus.write_bytes(b"old")
    scplantdb_manifest.write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/scPlantDB_h5ad/SRP169576.h5ad\tscplantdb_SRP169576\tArabidopsis thaliana\n",
        encoding="utf-8",
    )

    items = module.collect_pending(tmp_path, base_public, public_corpus)

    assert len(items) == 1
    assert items[0].manifest.endswith("corpus_manifest.scplantdb.tsv")
    assert items[0].dataset_ids == "scplantdb_SRP169576"
    assert items[0].pending_refresh is True


def test_status_summary_dynamically_includes_new_gse_manifests(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_dynamic", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "corpus_manifest.gse338572.tsv").write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/GSE338572_npz/sample.npz\tmaize_easy_multiome_seedling\tZea mays\n",
        encoding="utf-8",
    )

    manifests = module.manifest_paths(tmp_path)

    assert data_dir / "corpus_manifest.gse338572.tsv" in manifests


def test_status_summary_dynamically_includes_scplantdb_manifests(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_scplantdb", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    manifest = data_dir / "corpus_manifest.scplantdb.tsv"
    manifest.write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/scPlantDB_h5ad/SRP169576.h5ad\tscplantdb_SRP169576\tArabidopsis thaliana\n",
        encoding="utf-8",
    )

    manifests = module.manifest_paths(tmp_path)

    assert manifest in manifests
    assert any(target["dataset_id"] == "scplantdb_global" for target in module.PUBLIC_DATA_TARGETS)


def test_status_summary_reads_scplantdb_manifest_audit(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_scplantdb_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    package_dir = tmp_path / "outputs" / "publication_package"
    package_dir.mkdir(parents=True)
    (package_dir / "scplantdb_manifest_audit.json").write_text(
        json.dumps(
            {
                "summary": {
                    "rows": 11,
                    "ready_rows": 11,
                    "issue_rows": 0,
                    "missing_training_obs_key_rows": 0,
                    "total_cells": 124928,
                    "species_count": 10,
                    "species": ["Arabidopsis thaliana", "Oryza sativa"],
                }
            }
        ),
        encoding="utf-8",
    )

    summary = module.scplantdb_manifest_audit_summary(tmp_path)

    assert summary["rows"] == 11
    assert summary["ready_rows"] == 11
    assert summary["species_count"] == 10
    assert summary["missing_training_obs_key_rows"] == 0


def test_scplantdb_catalog_extractor_parses_download_urls(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "extract_scplantdb_catalog.py"
    spec = importlib.util.spec_from_file_location("extract_scplantdb_catalog", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    chunks = tmp_path / "chunks"
    chunks.mkdir()
    chunks.joinpath("255.demo.js").write_text(
        "x=JSON.parse('[{\"bioproject\":\"PRJNA1\",\"species\":\"Arabidopsis thaliana\","
        "\"tissue\":\"Root tip\",\"condition\":[{\"name\":\"Normal\",\"value\":1}],"
        "\"genotype\":[{\"name\":\"Col-0\",\"value\":1}],\"libraries\":\"10x Genomics\","
        "\"age\":\"5 days\",\"experiments\":1,\"cells\":42,"
        "\"article\":{\"pmid\":\"123\",\"info\":\"Demo\"},\"picname\":\"SRP1.png\","
        "\"dataset\":\"SRP169576\"}]')",
        encoding="utf-8",
    )
    output_tsv = tmp_path / "catalog.tsv"
    output_json = tmp_path / "catalog.json"
    output_md = tmp_path / "catalog.md"

    rows = module.extract_catalog(chunks)
    module.write_tsv(rows, output_tsv)
    module.write_json(rows, output_json)
    module.write_markdown(rows, output_md)

    assert len(rows) == 1
    assert rows[0]["h5ad_gz_url"].endswith("/SRP169576.h5ad.gz")
    assert rows[0]["rds_gz_url"].endswith("/SRP169576.rds.gz")
    assert rows[0]["cellxgene_url"].endswith("/SRP169576.h5ad")
    assert "scPlantDB Acquisition Catalog" in output_md.read_text(encoding="utf-8")
    assert "SRP169576" in output_tsv.read_text(encoding="utf-8")


def test_scplantdb_h5ad_size_probe_selects_bounded_candidates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "probe_scplantdb_h5ad_sizes.py"
    spec = importlib.util.spec_from_file_location("probe_scplantdb_h5ad_sizes", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    catalog = tmp_path / "scplantdb_dataset_catalog.tsv"
    catalog.write_text(
        "dataset\tspecies\ttissue\tcells\tbioproject\tpmid\th5ad_gz_url\n"
        "SRP169576\tArabidopsis thaliana\tWhole root\t35665\tPRJNA1\t123\t"
        "https://biobigdata.nju.edu.cn/scplantdb/datasets/SRP169576.h5ad.gz\n"
        "SRP999999\tOryza sativa\tRoot tip\t12000\tPRJNA2\t456\t"
        "https://biobigdata.nju.edu.cn/scplantdb/datasets/SRP999999.h5ad.gz\n"
        "SRP000000\tZea mays\tLeaf\t99000\tPRJNA3\t789\t"
        "https://biobigdata.nju.edu.cn/scplantdb/datasets/SRP000000.h5ad.gz\n",
        encoding="utf-8",
    )

    def fake_probe(url: str, timeout: float = 20.0) -> dict:
        sizes = {
            "SRP169576": 108_802_218,
            "SRP999999": 1_200_000_000,
            "SRP000000": 200_000_000,
        }
        dataset = url.rsplit("/", 1)[-1].split(".", 1)[0]
        return {
            "ok": True,
            "status_code": 200,
            "error": "",
            "content_length": sizes[dataset],
            "content_type": "application/octet-stream",
            "accept_ranges": "bytes",
            "etag": "",
            "last_modified": "",
        }

    monkeypatch.setattr(module, "probe_url", fake_probe)
    rows = module.ranked_rows(
        module.read_catalog(catalog),
        max_bytes=750_000_000,
        max_total_bytes=1_000_000_000,
        min_cells=0,
        max_datasets=2,
        timeout=1.0,
    )
    output_tsv = tmp_path / "probe.tsv"
    output_json = tmp_path / "probe.json"
    output_md = tmp_path / "probe.md"
    selected = tmp_path / "selected.txt"
    module.write_tsv(rows, output_tsv)
    module.write_json(rows, output_json)
    module.write_markdown(rows, output_md)
    module.write_selected_ids(rows, selected)

    selected_ids = selected.read_text(encoding="utf-8").splitlines()
    assert selected_ids == ["SRP169576", "SRP000000"]
    assert rows[0]["dataset"] == "SRP169576"
    assert rows[0]["selected_for_download"] is True
    assert any(row["dataset"] == "SRP999999" and not row["eligible_for_download"] for row in rows)
    assert "scPlantDB H5AD Size Probe" in output_md.read_text(encoding="utf-8")
    assert "content_length" in output_tsv.read_text(encoding="utf-8")
    assert "SRP000000" in output_json.read_text(encoding="utf-8")


def test_scplantdb_h5ad_size_probe_respects_total_byte_budget(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "probe_scplantdb_h5ad_sizes.py"
    spec = importlib.util.spec_from_file_location("probe_scplantdb_h5ad_sizes_budget", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    catalog = tmp_path / "scplantdb_dataset_catalog.tsv"
    catalog.write_text(
        "dataset\tspecies\ttissue\tcells\tbioproject\tpmid\th5ad_gz_url\n"
        "SRP1\tArabidopsis thaliana\tRoot\t1000\tPRJNA1\t1\thttps://example.org/SRP1.h5ad.gz\n"
        "SRP2\tOryza sativa\tRoot\t1000\tPRJNA2\t2\thttps://example.org/SRP2.h5ad.gz\n"
        "SRP3\tZea mays\tLeaf\t1000\tPRJNA3\t3\thttps://example.org/SRP3.h5ad.gz\n",
        encoding="utf-8",
    )

    def fake_probe(url: str, timeout: float = 20.0) -> dict:
        dataset = url.rsplit("/", 1)[-1].split(".", 1)[0]
        sizes = {"SRP1": 150_000_000, "SRP2": 200_000_000, "SRP3": 200_000_000}
        return {
            "ok": True,
            "status_code": 200,
            "error": "",
            "content_length": sizes[dataset],
            "content_type": "application/octet-stream",
            "accept_ranges": "bytes",
            "etag": "",
            "last_modified": "",
        }

    monkeypatch.setattr(module, "probe_url", fake_probe)
    rows = module.ranked_rows(
        module.read_catalog(catalog),
        max_bytes=750_000_000,
        max_total_bytes=360_000_000,
        min_cells=0,
        max_datasets=3,
        timeout=1.0,
    )
    output_tsv = tmp_path / "probe.tsv"
    output_md = tmp_path / "probe.md"
    module.write_tsv(rows, output_tsv)
    module.write_markdown(rows, output_md)

    selected_ids = [row["dataset"] for row in rows if row["selected_for_download"]]
    skipped = {row["dataset"]: row["selection_skip_reason"] for row in rows}

    assert selected_ids == ["SRP1", "SRP2"]
    assert skipped["SRP3"] == "max_total_bytes_reached"
    assert "selection_skip_reason" in output_tsv.read_text(encoding="utf-8")
    assert "Selected gzip size total MB" in output_md.read_text(encoding="utf-8")


def test_scplantdb_manifest_audit_validates_training_obs_keys(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_scplantdb_manifest_audit.py"
    spec = importlib.util.spec_from_file_location("write_scplantdb_manifest_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    h5ad_dir = data_dir / "public" / "scPlantDB_h5ad"
    h5ad_dir.mkdir(parents=True)
    h5ad = h5ad_dir / "SRP169576.h5ad"
    h5ad.write_bytes(b"h5ad")
    manifest = data_dir / "corpus_manifest.scplantdb.tsv"
    manifest.write_text(
        "path\tdataset_id\tspecies\ttissue\tlayer\tlabel_key\tcoarse_label_key\tsample_key\n"
        "data/public/scPlantDB_h5ad/SRP169576.h5ad\tscplantdb_SRP169576\t"
        "Arabidopsis thaliana\tWhole root\t\tCelltype\tCelltype\tOrig.ident\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "inspect_h5ad",
        lambda path: (35665, 49106, ["Orig.ident", "Celltype", "Dataset"], ""),
    )

    payload = module.build_audit(tmp_path, Path("data/corpus_manifest.scplantdb.tsv"))
    output_md = tmp_path / "outputs" / "publication_package" / "scplantdb_manifest_audit.md"
    output_json = tmp_path / "outputs" / "publication_package" / "scplantdb_manifest_audit.json"
    output_tsv = tmp_path / "outputs" / "publication_package" / "scplantdb_manifest_audit.tsv"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    module.write_tsv(payload, output_tsv)

    assert payload["summary"]["rows"] == 1
    assert payload["summary"]["ready_rows"] == 1
    assert payload["summary"]["missing_training_obs_key_rows"] == 0
    assert payload["datasets"][0]["label_key_present"] is True
    assert payload["datasets"][0]["sample_key_present"] is True
    assert "scPlantDB Manifest Audit" in output_md.read_text(encoding="utf-8")
    assert "scplantdb_SRP169576" in output_tsv.read_text(encoding="utf-8")
    assert "Arabidopsis thaliana" in output_json.read_text(encoding="utf-8")


def test_scplantdb_download_and_corpus_scripts_include_scplantdb_manifest() -> None:
    download_script = (
        Path(__file__).parents[1] / "scripts" / "download_scplantdb_h5ad_subset.sh"
    ).read_text(encoding="utf-8")
    build_script = (
        Path(__file__).parents[1] / "scripts" / "build_public_mlm_corpus.sh"
    ).read_text(encoding="utf-8")
    queue_script = (
        Path(__file__).parents[1] / "scripts" / "queue_late_public_mlm_refresh.sh"
    ).read_text(encoding="utf-8")
    public_queue_script = (
        Path(__file__).parents[1] / "scripts" / "queue_public_mlm_expansion.sh"
    ).read_text(encoding="utf-8")
    package_script = (
        Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh"
    ).read_text(encoding="utf-8")

    assert "SRP169576" in download_script
    assert ".h5ad.gz" in download_script
    assert "gzip -t" in download_script
    assert "SNOWCELL_SCPLANTDB_DATASETS_FILE" in download_script
    assert "SNOWCELL_SCPLANTDB_INCLUDE_EXISTING" in download_script
    assert "data/corpus_manifest.scplantdb.tsv" in download_script
    assert '"label_key": "Celltype"' in download_script
    assert '"sample_key": "Orig.ident"' in download_script
    assert "corpus_manifest.scplantdb*.tsv" in build_script
    assert "corpus_manifest.scplantdb*.tsv" in queue_script
    assert "corpus_manifest.scplantdb*.tsv" in public_queue_script
    assert "SNOWCELL_MLM_CONTINUATION_SESSION" in public_queue_script
    assert "exit_if_continuation_exists" in public_queue_script
    assert "write_pending_corpus_additions.py" in public_queue_script
    assert "extract_scplantdb_catalog.py" in package_script
    assert "probe_scplantdb_h5ad_sizes.py" in package_script
    assert "download_scplantdb_h5ad_subset.sh" in package_script
    assert "write_scplantdb_manifest_audit.py" in package_script
    assert "queue_scplantdb_budgeted_h5ad_download.sh" in package_script
    assert "start_scplantdb_budgeted_h5ad_queue.sh" in package_script
    assert "data/public_discovery/*.md" in package_script
    assert "data/public_discovery/*.txt" in package_script


def test_scplantdb_budgeted_queue_scripts_are_reproducible() -> None:
    queue_script = (
        Path(__file__).parents[1] / "scripts" / "queue_scplantdb_budgeted_h5ad_download.sh"
    ).read_text(encoding="utf-8")
    start_script = (
        Path(__file__).parents[1] / "scripts" / "start_scplantdb_budgeted_h5ad_queue.sh"
    ).read_text(encoding="utf-8")

    assert "SNOWCELL_SCPLANTDB_MAX_TOTAL_BYTES" in queue_script
    assert "--max-total-bytes" in queue_script
    assert "SNOWCELL_SCPLANTDB_DATASETS_FILE" in queue_script
    assert "download_scplantdb_h5ad_subset.sh" in queue_script
    assert "write_scplantdb_manifest_audit.py" in queue_script
    assert "audit_data_integrity.py" in queue_script
    assert "write_pending_corpus_additions.py" in queue_script
    assert "generate_publication_package.sh" in queue_script
    assert "snowcell_scplantdb_budgeted_h5ad_queue" in start_script
    assert "tmux new-session" in start_script
    assert "SNOWCELL_SCPLANTDB_MAX_BYTES='$max_bytes'" in start_script
    assert "SNOWCELL_SCPLANTDB_MAX_TOTAL_BYTES='$max_total_bytes'" in start_script
    assert "SNOWCELL_SCPLANTDB_MAX_DATASETS='$max_datasets'" in start_script
    assert "SNOWCELL_SCPLANTDB_PROBE_TIMEOUT='$probe_timeout'" in start_script
    assert "scplantdb_budgeted_h5ad_queue.log" in start_script


def test_start_public_queues_includes_scplantdb_budgeted_queue() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "start_public_queues.sh").read_text(
        encoding="utf-8"
    )

    assert "SNOWCELL_ENABLE_SCPLANTDB_QUEUE" in script
    assert "snowcell_scplantdb_budgeted_h5ad_queue" in script
    assert "start_scplantdb_budgeted_h5ad_queue.sh" in script
    assert "tmux kill-session -t \"$scplantdb_session\"" in script
    assert "scPlantDB budgeted queue disabled" in script


def test_status_summary_counts_latest_checkpoint_for_running_run(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_latest", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    run_dir = tmp_path / "outputs" / "foundation_5090_mlm_public_expansion_continuation"
    run_dir.mkdir(parents=True)
    (run_dir / "latest.pt").write_bytes(b"checkpoint")
    (run_dir / "progress_latest.json").write_text(
        json.dumps({"status": "training", "epoch": 1, "step": 3000}),
        encoding="utf-8",
    )

    summary = module.run_summary(run_dir)

    assert summary["has_checkpoint"] is True
    assert summary["checkpoint_kind"] == "latest"
    assert summary["checkpoint_bytes"] == len(b"checkpoint")
    assert summary["latest_checkpoint"]["exists"] is True
    assert summary["best_checkpoint"]["exists"] is False
    assert summary["latest_progress"]["status"] == "training"


def test_status_summary_tracks_regulatory_multiome_holdout_target() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_targets", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    target_ids = {target["dataset_id"] for target in module.PUBLIC_DATA_TARGETS}
    regulatory = next(
        target
        for target in module.PUBLIC_DATA_TARGETS
        if target["dataset_id"] == "brassicaceae_regulatory_multiome"
    )

    assert "brassicaceae_regulatory_multiome" in target_ids
    assert regulatory["manifest"] == "data/corpus_manifest.gse332675.tsv"
    assert "GSE332675" in regulatory["raw_glob"]


def test_status_summary_marks_unsupported_public_target(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_unsupported", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    raw_dir = tmp_path / "data" / "public" / "GSE336751_raw_tar"
    raw_dir.mkdir(parents=True)
    (raw_dir / "GSE336751_RAW.tar").write_bytes(b"raw")
    (raw_dir / "unsupported_single_cell_matrix.json").write_text(
        json.dumps({"status": "unsupported_for_single_cell_matrix_corpus"}),
        encoding="utf-8",
    )

    targets = module.public_data_target_summary(tmp_path)
    marchantia = next(
        item
        for item in targets
        if item["dataset_id"] == "marchantia_spore_asymmetry_single_cell"
    )

    assert marchantia["stage"] == "unsupported_for_matrix_corpus"
    assert marchantia["raw_files"]["unsupported_report_count"] == 1


def test_data_integrity_audit_reads_sparse_npz_manifest(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "audit_data_integrity.py"
    spec = importlib.util.spec_from_file_location("audit_data_integrity", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    import numpy as np

    data_dir = tmp_path / "data" / "public" / "demo_npz"
    data_dir.mkdir(parents=True)
    matrix_path = data_dir / "sample.npz"
    matrix = sparse.csr_matrix([[1, 0, 2], [0, 3, 0]], dtype="float32")
    np.savez_compressed(
        matrix_path,
        X_data=matrix.data,
        X_indices=matrix.indices,
        X_indptr=matrix.indptr,
        X_shape=matrix.shape,
        genes=np.array(["gene_a", "gene_b", "gene_c"]),
        cell_type=np.array(["root cortex", "root stele"]),
        cell_type_coarse=np.array(["root", "root"]),
        sample_id=np.array(["sample_a", "sample_b"]),
        species=np.array(["Arabidopsis thaliana", "Arabidopsis thaliana"]),
        tissue=np.array(["root", "root"]),
        cell_id=np.array(["cell_a", "cell_b"]),
    )
    manifest = tmp_path / "data" / "corpus_manifest.demo.tsv"
    manifest.write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/demo_npz/sample.npz\tdemo_dataset\tArabidopsis thaliana\n",
        encoding="utf-8",
    )

    payload = module.audit_project(tmp_path, [manifest])
    output_md = tmp_path / "outputs" / "publication_package" / "data_integrity_audit.md"
    output_json = tmp_path / "outputs" / "publication_package" / "data_integrity_audit.json"
    output_tsv = tmp_path / "outputs" / "publication_package" / "data_integrity_audit.tsv"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    module.write_manifest_tsv(payload, output_tsv)

    assert payload["summary"]["manifest_count"] == 1
    assert payload["summary"]["missing_files"] == 0
    assert payload["summary"]["total_cells"] == 2
    assert payload["manifests"][0]["status"] == "ready"
    assert payload["matrices"][0]["missing_recommended_obs"] == ""
    assert "demo_dataset" in output_md.read_text(encoding="utf-8")
    assert "data/corpus_manifest.demo.tsv" in output_tsv.read_text(encoding="utf-8")


def test_data_integrity_audit_marks_missing_matrix(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "audit_data_integrity.py"
    spec = importlib.util.spec_from_file_location("audit_data_integrity_missing", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    manifest = data_dir / "corpus_manifest.missing.tsv"
    manifest.write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/missing.npz\tmissing_dataset\tSaussurea involucrata\n",
        encoding="utf-8",
    )

    payload = module.audit_project(tmp_path, [manifest])

    assert payload["summary"]["missing_files"] == 1
    assert payload["summary"]["issue_manifests"] == 1
    assert payload["manifests"][0]["status"] == "matrix_issues"
    assert payload["matrices"][0]["error"] == "missing file"


def test_data_integrity_default_manifests_exclude_templates(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "audit_data_integrity.py"
    spec = importlib.util.spec_from_file_location("audit_data_integrity_templates", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    active = data_dir / "corpus_manifest.demo.tsv"
    template = data_dir / "corpus_manifest.template.tsv"
    active.write_text("path\tdataset_id\tspecies\n", encoding="utf-8")
    template.write_text("path\tdataset_id\tspecies\n", encoding="utf-8")

    manifests = module.default_manifest_paths(tmp_path)

    assert manifests == [active]


def test_corpus_provenance_audit_links_manifest_rows_to_public_sources(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_corpus_provenance_audit.py"
    spec = importlib.util.spec_from_file_location("write_corpus_provenance_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    matrix_dir = data_dir / "public" / "GSE000001_npz"
    matrix_dir.mkdir(parents=True)
    matrix_path = matrix_dir / "registered.npz"
    matrix_path.write_bytes(b"matrix")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "public_dataset_manifest.tsv").write_text(
        "dataset_id\tspecies\ttissue_or_scope\tdata_type\tpriority\taccession_or_doi\t"
        "source_url\twhy_use\tstatus\n"
        "registered_dataset\tArabidopsis thaliana\troot\tscRNA\tA\tGSE000001\t"
        "https://example.org/GSE000001\tannotation evidence\tdownload_candidate\n",
        encoding="utf-8",
    )
    with (data_dir / "public_dataset_manifest.tsv").open("a", encoding="utf-8") as handle:
        handle.write(
            "scplantdb_global\tMixed plants\tdatabase\tdatabase\tA\tscPlantDB\t"
            "https://example.org/scplantdb\tglobal source\tmanual_index\n"
            "scplantllm_srp169576_benchmark\tMixed plants\tbenchmark\tscRNA\tA\tSRP169576\t"
            "https://example.org/SRP169576\tbenchmark source\tdownload_candidate\n"
        )
    scplantdb_file = matrix_dir / "scplantdb.npz"
    scplantdb_file.write_bytes(b"scplantdb")
    scplantllm_file = matrix_dir / "scplantllm.npz"
    scplantllm_file.write_bytes(b"scplantllm")
    (data_dir / "corpus_manifest.gse000001.tsv").write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/GSE000001_npz/registered.npz\tregistered_dataset\tArabidopsis thaliana\n"
        "data/public/GSE000001_npz/scplantdb.npz\tscplantdb_SRP169576\tArabidopsis thaliana\n"
        "data/public/GSE000001_npz/scplantllm.npz\tscplantllm_srp169576_SRX5025979_seurat0\tArabidopsis thaliana\n",
        encoding="utf-8",
    )
    (data_dir / "corpus_manifest.unregistered.tsv").write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/missing.npz\tunregistered_dataset\tOryza sativa\n",
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "corpus_provenance_audit.md"
    output_json = tmp_path / "outputs" / "publication_package" / "corpus_provenance_audit.json"
    output_tsv = tmp_path / "outputs" / "publication_package" / "corpus_provenance_audit.tsv"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    module.write_tsv(payload, output_tsv)
    by_dataset = {item["dataset_id"]: item for item in payload["datasets"]}

    assert payload["summary"]["manifest_count"] == 2
    assert payload["summary"]["registered_dataset_entries"] == 3
    assert payload["summary"]["unregistered_dataset_entries"] == 1
    assert payload["summary"]["existing_matrix_rows"] == 3
    assert payload["summary"]["missing_matrix_rows"] == 1
    assert by_dataset["registered_dataset"]["status"] == "ready_registered_source"
    assert by_dataset["registered_dataset"]["inferred_accessions"] == "GSE000001"
    assert by_dataset["scplantdb_SRP169576"]["source_registration_method"] == "scplantdb_global_scope"
    assert by_dataset["scplantllm_srp169576_SRX5025979_seurat0"][
        "source_registration_method"
    ] == "accession_match"
    assert by_dataset["scplantllm_srp169576_SRX5025979_seurat0"][
        "inferred_accessions"
    ] == "SRP169576;SRX5025979"
    assert by_dataset["unregistered_dataset"]["status"] == "missing_matrix_files"
    assert "ready_registered_source" in output_md.read_text(encoding="utf-8")
    assert "unregistered_dataset" in output_json.read_text(encoding="utf-8")
    assert "corpus_manifest.gse000001.tsv" in output_tsv.read_text(encoding="utf-8")


def test_status_summary_reads_data_integrity_audit(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_integrity", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    package_dir = tmp_path / "outputs" / "publication_package"
    package_dir.mkdir(parents=True)
    (package_dir / "data_integrity_audit.json").write_text(
        json.dumps(
            {
                "summary": {
                    "manifest_count": 2,
                    "ready_manifests": 1,
                    "issue_manifests": 1,
                    "matrix_count": 3,
                    "missing_files": 1,
                    "unreadable_files": 0,
                    "total_cells": 120,
                },
                "manifests": [
                    {"manifest": "data/corpus_manifest.ready.tsv", "status": "ready"},
                    {
                        "manifest": "data/corpus_manifest.missing.tsv",
                        "status": "matrix_issues",
                        "missing_files": 1,
                        "unreadable_files": 0,
                        "missing_columns": "",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = module.data_integrity_summary(tmp_path)

    assert summary["exists"] is True
    assert summary["manifest_count"] == 2
    assert summary["missing_files"] == 1
    assert summary["issue_manifests_detail"][0]["manifest"] == "data/corpus_manifest.missing.tsv"


def test_saussurea_supporting_evidence_summarizes_runinfo(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_supporting_evidence.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_supporting_evidence", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    discovery_dir = data_dir / "public_discovery"
    runinfo_dir = data_dir / "public" / "sra_runinfo"
    source_dir = data_dir / "public" / "source_pages"
    discovery_dir.mkdir(parents=True)
    runinfo_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    (data_dir / "public_dataset_manifest.tsv").write_text(
        "\t".join(
            [
                "dataset_id",
                "species",
                "tissue_or_scope",
                "data_type",
                "priority",
                "accession_or_doi",
                "source_url",
                "why_use",
                "status",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "saussurea_low_pressure",
                "Saussurea involucrata",
                "leaf low-pressure treatment",
                "bulk RNA-seq",
                "B",
                "PRJNA1218246",
                "https://example.org/PRJNA1218246",
                "stress evidence",
                "download_candidate",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "saussurea_involucrata_private",
                "Saussurea involucrata",
                "user data",
                "scRNA",
                "S",
                "data/saussurea_involucrata.h5ad",
                "local",
                "primary data",
                "required_user_data",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (runinfo_dir / "PRJNA1218246.runinfo.csv").write_text(
        "Run,ScientificName,LibraryStrategy,LibrarySource,size_MB\n"
        "SRR1,Saussurea involucrata,RNA-Seq,TRANSCRIPTOMIC,12.5\n"
        "SRR2,Saussurea involucrata,RNA-Seq,TRANSCRIPTOMIC,7.5\n",
        encoding="utf-8",
    )
    (runinfo_dir / "PRJEB82787.runinfo.csv").write_text(
        "Run,ScientificName,LibraryStrategy,LibrarySource,size_MB\n"
        "ERR1,Saussurea involucrata,RNA-Seq,TRANSCRIPTOMIC,30\n",
        encoding="utf-8",
    )
    broad_rows = "\n".join(
        f"ERR{index + 10},Species {index},WGS,GENOMIC,1"
        for index in range(60)
    )
    (runinfo_dir / "PRJEB43865.runinfo.csv").write_text(
        "Run,ScientificName,LibraryStrategy,LibrarySource,size_MB\n"
        "ERR2,Saussurea alpina,WGS,GENOMIC,1\n"
        f"{broad_rows}\n",
        encoding="utf-8",
    )
    (source_dir / "saussurea_low_pressure.html").write_text("<html>ok</html>", encoding="utf-8")
    (source_dir / "saussurea_discovered_prjeb82787.html").write_text(
        "<html>discovered</html>",
        encoding="utf-8",
    )
    (source_dir / "saussurea_discovered_prjeb43865.html").write_text(
        "<html>broad</html>",
        encoding="utf-8",
    )
    (discovery_dir / "ncbi_discovery_20260725_000000.tsv").write_text(
        "query_label\tdb\tuid\taccession\ttitle\torganism\turl\tpriority\tscore\trecommended_action\tmatched_queries\tsummary\n"
        "saussurea_transcriptome_sra\tsra\t1\tPRJEB82787\tSaussurea involucrata transcriptome\tSaussurea involucrata\thttps://www.ncbi.nlm.nih.gov/bioproject/PRJEB82787\tA\t9\tSnow Lotus evidence layer\tsaussurea_transcriptome_sra\tbulk RNA-seq\n"
        "saussurea_broad_mixed\tsra\t2\tPRJEB43865\tSaussurea alpine mixed plants\tSaussurea alpina\thttps://www.ncbi.nlm.nih.gov/bioproject/PRJEB43865\tA\t9\tSaussurea broad evidence\tsaussurea_transcriptome_sra\tbroad mixed WGS\n",
        encoding="utf-8",
    )

    evidence = module.build_evidence(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "saussurea_supporting_evidence.md"
    output_json = tmp_path / "outputs" / "publication_package" / "saussurea_supporting_evidence.json"
    module.write_markdown(evidence, output_md)
    module.write_json(evidence, output_json)

    assert len(evidence) == 2
    assert evidence[0].dataset_id == "saussurea_low_pressure"
    assert evidence[0].run_count == 2
    assert evidence[0].total_size_mb == 20.0
    assert evidence[0].source_page_present is True
    by_id = {item.dataset_id: item for item in evidence}
    assert by_id["saussurea_discovered_prjeb82787"].run_count == 1
    assert by_id["saussurea_discovered_prjeb82787"].status == "discovered_runinfo_candidate"
    assert by_id["saussurea_discovered_prjeb82787"].source_page_present is True
    assert "saussurea_discovered_prjeb43865" not in by_id
    assert "stress evidence" in output_md.read_text(encoding="utf-8")
    assert "PRJEB82787" in output_md.read_text(encoding="utf-8")
    assert "PRJEB43865" not in output_md.read_text(encoding="utf-8")
    assert "Saussurea involucrata" in output_json.read_text(encoding="utf-8")


def test_benchmark_gap_audit_marks_external_tool_gaps(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_benchmark_gap_audit.py"
    spec = importlib.util.spec_from_file_location("write_benchmark_gap_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    status = {
        "publication_gates": {"snow_lotus_scRNA_present": False},
        "public_data_targets": [
            {"dataset_id": f"dataset_{index}", "stage": "manifest_ready"}
            for index in range(5)
        ],
        "strict_benchmarks": [
            {
                "path": "outputs/strict_benchmarks/public_sprint_group_random.centroid_baseline.json",
                "kind": "baseline",
                "fine_test_macro_f1": 0.71,
                "coarse_test_macro_f1": 0.7,
            },
            {
                "path": "outputs/strict_benchmarks/leaveout_brassicaceae_dataset.split_audit.json",
                "kind": "split_audit",
                "supervised_benchmark_ready": False,
            },
            {
                "path": "outputs/strict_benchmarks/leaveout_eutrema_species.split_audit.json",
                "kind": "split_audit",
                "supervised_benchmark_ready": False,
            },
            {
                "path": "outputs/strict_benchmarks/public_sprint.marker_candidates.json",
                "kind": "split_audit",
            },
        ],
    }
    input_dir = tmp_path / "outputs" / "external_benchmarks" / "scplantllm_public_sprint_input"
    input_dir.mkdir(parents=True)
    (input_dir / "summary.json").write_text(
        json.dumps({"method": "scplantllm_input_export"}),
        encoding="utf-8",
    )
    payload = module.build_audit(status, tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "benchmark_gap_audit.md"
    output_json = tmp_path / "outputs" / "publication_package" / "benchmark_gap_audit.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    by_id = {item["id"]: item for item in payload["requirements"]}

    assert by_id["random_split_centroid"]["status"] == "READY"
    assert by_id["leave_dataset_split_audit"]["status"] == "READY"
    assert by_id["seurat_label_transfer"]["status"] == "MISSING"
    assert by_id["scplantllm_comparison"]["status"] == "MISSING"
    assert by_id["snow_lotus_finetune_benchmark"]["priority"] == "S"
    assert by_id["public_corpus_scale"]["status"] == "IN_PROGRESS"
    assert payload["summary"]["top_journal_benchmark_ready"] is False
    assert "scPlantLLM" in output_md.read_text(encoding="utf-8")
    assert "seurat_label_transfer" in output_json.read_text(encoding="utf-8")


def test_status_summary_includes_benchmark_readiness(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_benchmark", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    strict_dir = tmp_path / "outputs" / "strict_benchmarks"
    external_dir = tmp_path / "outputs" / "external_benchmarks"
    strict_dir.mkdir(parents=True)
    external_dir.mkdir(parents=True)
    (strict_dir / "demo.centroid_baseline.json").write_text(
        json.dumps({"method": "cosine_nearest_centroid", "fine_test_macro_f1": 0.5}),
        encoding="utf-8",
    )
    (strict_dir / "demo.split_audit.json").write_text(
        json.dumps({"supervised_benchmark_ready": True}),
        encoding="utf-8",
    )
    (strict_dir / "demo.marker_candidates.json").write_text(
        json.dumps({"marker_candidates": []}),
        encoding="utf-8",
    )
    (external_dir / "demo_seurat.json").write_text("{}", encoding="utf-8")
    (external_dir / "scplantllm_embedding_centroid_probe.json").write_text(
        json.dumps({"method": "scplantllm_probe", "macro_f1": 0.4}),
        encoding="utf-8",
    )
    (external_dir / "scplantannotate_authenticated_benchmark_plan.json").write_text(
        json.dumps({"status": "dry_run_credentials_required"}),
        encoding="utf-8",
    )

    strict = module.strict_benchmark_summary(tmp_path)
    readiness = module.benchmark_readiness_summary(tmp_path, strict)

    assert readiness["baseline_metric_count"] == 1
    assert readiness["split_audit_count"] == 2
    assert readiness["supervised_split_audit_count"] == 1
    assert readiness["marker_candidate_artifact_present"] is True
    assert readiness["external_benchmark_count"] == 3
    assert readiness["external_metric_count"] == 1
    assert readiness["external_metric_methods"] == ["scplantllm"]
    assert "scplantannotate" in readiness["external_missing_methods"]


def test_status_summary_reads_external_benchmark_metrics(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    spec = importlib.util.spec_from_file_location("write_status_summary_external", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    external_dir = tmp_path / "outputs" / "external_benchmarks"
    external_dir.mkdir(parents=True)
    (external_dir / "seurat_public_sprint.json").write_text(
        json.dumps(
            {
                "method": "seurat_label_transfer",
                "test_cells": 100,
                "fine_test_macro_f1": 0.7,
                "coarse_test_macro_f1": 0.8,
                "input_dir": "outputs/external_benchmarks/seurat_public_sprint_split",
            }
        ),
        encoding="utf-8",
    )

    items = module.external_benchmark_summary(tmp_path)

    assert len(items) == 1
    assert items[0]["method"] == "seurat_label_transfer"
    assert items[0]["has_metric"] is True
    assert items[0]["method_tag"] == "seurat"
    assert items[0]["fine_test_macro_f1"] == 0.7
    assert items[0]["test_cells"] == 100


def test_top_journal_readiness_marks_partial_external_tools(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_top_journal_readiness_matrix.py"
    spec = importlib.util.spec_from_file_location("write_top_journal_readiness_matrix", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    status_path = tmp_path / "status_summary.json"
    status_path.write_text(
        json.dumps(
            {
                "publication_gates": {
                    "ssh_remote_execution": True,
                    "gpu_training_active_or_artifacts_present": True,
                    "public_data_ingested": True,
                    "referenced_matrices_readable": True,
                    "strict_split_audit_present": True,
                    "baseline_benchmark_metric_present": True,
                    "external_tool_benchmarks_present": True,
                    "snow_lotus_scRNA_present": False,
                },
                "benchmark_readiness": {
                    "external_metric_count": 2,
                    "external_metric_methods": ["scplantllm", "seurat"],
                    "external_missing_methods": ["scplantannotate"],
                },
            }
        ),
        encoding="utf-8",
    )
    (status_path.parent / "saussurea_supporting_evidence.json").write_text(
        json.dumps(
            [
                {
                    "dataset_id": "saussurea_discovered_prjeb82787",
                    "status": "discovered_runinfo_candidate",
                    "accession_or_doi": "PRJEB82787",
                    "run_count": 1,
                    "library_strategies": "RNA-Seq",
                    "total_size_mb": 30.0,
                    "source_page_present": True,
                }
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "top_journal_readiness_matrix.md"
    output_json = tmp_path / "top_journal_readiness_matrix.json"

    module.write_matrix(status_path, output, output_json)
    text = output.read_text(encoding="utf-8")
    payload = json.loads(output_json.read_text(encoding="utf-8"))

    assert "| external_tools | External tool comparisons are present | PARTIAL |" in text
    assert "scplantannotate" in text
    assert "External metric methods missing: `scplantannotate`" in text
    assert "| snow_lotus_scrna | Snow Lotus scRNA/snRNA data exist" in text
    assert payload["summary"]["top_journal_ready"] is False
    assert payload["summary"]["partial_count"] == 1
    assert payload["summary"]["missing_count"] == 1
    assert payload["summary"]["external_missing_methods"] == ["scplantannotate"]
    assert payload["summary"]["saussurea_discovered_runinfo_candidate_count"] == 1
    assert payload["summary"]["saussurea_supporting_sra_run_count"] == 1
    assert "saussurea_discovered_prjeb82787" in text
    assert any(item["id"] == "external_tools" for item in payload["requirements"])
    assert payload["saussurea_supporting_evidence"][0]["accession_or_doi"] == "PRJEB82787"
    assert any("saussurea_involucrata.h5ad" in item for item in payload["hard_gaps"])


def test_external_tool_environment_reports_missing_packages(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_external_tool_environment.py"
    spec = importlib.util.spec_from_file_location("write_external_tool_environment", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    def fake_runner(command: list[str], cwd: Path) -> dict:
        joined = " ".join(command)
        if command == ["Rscript", "--version"]:
            return {"command": command, "returncode": 0, "stdout": "", "stderr": "R version 4.1.2"}
        if command == ["git", "lfs", "version"]:
            return {"command": command, "returncode": None, "stdout": "", "stderr": "command not found"}
        stdout = "TRUE\n" if "Matrix" in joined else "FALSE\n"
        return {"command": command, "returncode": 0, "stdout": stdout, "stderr": ""}

    payload = module.collect_environment(tmp_path, runner=fake_runner)
    output_md = tmp_path / "outputs" / "publication_package" / "external_tool_environment.md"
    output_json = tmp_path / "outputs" / "publication_package" / "external_tool_environment.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    assert payload["rscript"]["available"] is True
    assert payload["seurat_ready"] is False
    assert payload["git_lfs"]["available"] is False
    assert payload["scplantllm"]["model_weight_exists"] is False
    assert payload["r_packages"][0]["available"] is True
    assert "install_r_singlecell_tools.sh" in payload["recommended_actions"][0]
    assert "Seurat benchmark environment ready: `False`" in output_md.read_text(encoding="utf-8")
    assert "scPlantLLM model weight present: `False`" in output_md.read_text(encoding="utf-8")
    assert "SeuratObject" in output_json.read_text(encoding="utf-8")
    assert "model_params/scPlantLLM_model.pth" in output_json.read_text(encoding="utf-8")


def test_export_seurat_benchmark_split_writes_mtx_and_metadata(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "export_seurat_benchmark_split.py"
    spec = importlib.util.spec_from_file_location("export_seurat_benchmark_split", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_path = tmp_path / "demo.npz"
    config_path = tmp_path / "config.yaml"
    make_demo_data(data_path, n_cells=180, n_genes=96, n_samples=6, seed=37)
    config_path.write_text(
        f"""
data:
  path: {data_path.as_posix()}
  max_genes: 32
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  validation_fraction: 0.15
  test_fraction: 0.15
architecture:
  d_model: 32
  n_heads: 4
train:
  mixed_precision: "no"
  seed: 42
""".lstrip(),
        encoding="utf-8",
    )

    output_dir = tmp_path / "seurat_export"
    summary = module.export_split(config_path, output_dir)
    train_matrix = io.mmread(output_dir / "train.mtx")
    train_meta = (output_dir / "train_metadata.tsv").read_text(encoding="utf-8")

    assert summary["n_genes"] == 96
    assert train_matrix.shape[0] == 96
    assert train_matrix.shape[1] == summary["splits"]["train"]["cells"]
    assert (output_dir / "genes.tsv").read_text(encoding="utf-8").startswith("ORTHO_")
    assert "cell_type\tcell_type_coarse" in train_meta
    assert (output_dir / "summary.json").exists()


def test_export_scplantllm_input_writes_h5_meta_and_summary(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "export_scplantllm_input.py"
    spec = importlib.util.spec_from_file_location("export_scplantllm_input", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_path = tmp_path / "demo.npz"
    config_path = tmp_path / "config.yaml"
    vocab_path = tmp_path / "external" / "scPlantLLM" / "gene_vocab.json"
    make_demo_data(data_path, n_cells=180, n_genes=96, n_samples=6, seed=41)
    vocab_path.parent.mkdir(parents=True)
    vocab_path.write_text(
        json.dumps({f"ORTHO_{index:05d}": index for index in range(12)}),
        encoding="utf-8",
    )
    config_path.write_text(
        f"""
data:
  path: {data_path.as_posix()}
  max_genes: 32
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  validation_fraction: 0.15
  test_fraction: 0.15
architecture:
  d_model: 32
  n_heads: 4
train:
  mixed_precision: "no"
  seed: 42
""".lstrip(),
        encoding="utf-8",
    )

    output_dir = tmp_path / "outputs" / "external_benchmarks" / "scplantllm_public_sprint_input"
    summary = module.export_scplantllm_input(
        config_path=config_path,
        output_dir=output_dir,
        max_cells=40,
        gene_vocab_path=vocab_path,
    )

    with h5py.File(summary["h5_path"], "r") as handle:
        assert "count/data" in handle
        assert "count/cell_names" in handle
        assert "count/gene_names" in handle
        assert handle["count/data"].shape == (40, 96)
    meta_text = Path(summary["metadata_csv"]).read_text(encoding="utf-8")
    assert meta_text.startswith("cell,orig.ident,celltype")
    assert "snowcell_split" in meta_text
    assert summary["selected_cells"] == 40
    assert summary["retained_genes"] == 96
    assert summary["scplantllm_gene_vocab"]["overlap_count"] == 12
    assert (output_dir / "summary.json").exists()


def test_scplantllm_input_readiness_reports_prepared_input(tmp_path: Path) -> None:
    export_path = Path(__file__).parents[1] / "scripts" / "export_scplantllm_input.py"
    export_spec = importlib.util.spec_from_file_location("export_scplantllm_input_readiness", export_path)
    assert export_spec is not None and export_spec.loader is not None
    export_module = importlib.util.module_from_spec(export_spec)
    sys.modules[export_spec.name] = export_module
    export_spec.loader.exec_module(export_module)

    module_path = Path(__file__).parents[1] / "scripts" / "write_scplantllm_input_readiness.py"
    spec = importlib.util.spec_from_file_location("write_scplantllm_input_readiness", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_path = tmp_path / "demo.npz"
    config_path = tmp_path / "config.yaml"
    external_dir = tmp_path / "external" / "scPlantLLM"
    output_dir = tmp_path / "outputs" / "external_benchmarks" / "scplantllm_public_sprint_input"
    make_demo_data(data_path, n_cells=180, n_genes=96, n_samples=6, seed=43)
    external_dir.mkdir(parents=True)
    (external_dir / "gene_vocab.json").write_text(
        json.dumps({f"ORTHO_{index:05d}": index for index in range(8)}),
        encoding="utf-8",
    )
    config_path.write_text(
        f"""
data:
  path: {data_path.as_posix()}
  max_genes: 32
  min_genes_per_cell: 5
  min_cells_per_gene: 2
  validation_fraction: 0.15
  test_fraction: 0.15
architecture:
  d_model: 32
  n_heads: 4
train:
  mixed_precision: "no"
  seed: 42
""".lstrip(),
        encoding="utf-8",
    )
    export_module.export_scplantllm_input(
        config_path=config_path,
        output_dir=output_dir,
        max_cells=32,
        gene_vocab_path=external_dir / "gene_vocab.json",
    )
    reference_dir = output_dir / "reference_preprocess"
    reference_dir.mkdir()
    for name in [
        "batch_effect.meta",
        "batch_effect_vocab.meta.json",
        "cell_type.meta",
        "cell_type_vocab.meta.json",
    ]:
        (reference_dir / name).write_text("{}\n", encoding="utf-8")

    payload = module.build_audit(tmp_path, "outputs/external_benchmarks/scplantllm_public_sprint_input")
    output_md = tmp_path / "outputs" / "publication_package" / "scplantllm_input_readiness.md"
    output_json = tmp_path / "outputs" / "publication_package" / "scplantllm_input_readiness.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    assert payload["summary"]["status"] == "input_and_reference_metadata_ready"
    assert payload["summary"]["input_ready"] is True
    assert payload["scplantllm_checkout"]["gene_vocab_exists"] is True
    assert "scPlantLLM gene-vocabulary overlap rate" in output_md.read_text(encoding="utf-8")
    assert "input_and_reference_metadata_ready" in output_json.read_text(encoding="utf-8")


def test_safe_mlm_watchdog_writes_resume_config_and_uses_exact_tmux_session() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "watch_safe_mlm_refresh.sh").read_text(
        encoding="utf-8"
    )
    package_script = (
        Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh"
    ).read_text(encoding="utf-8")

    assert "resume_checkpoint" in script
    assert "init_checkpoint" in script
    assert "tmux has-session -t \"=$session\"" in script
    assert "latest.pt" in script
    assert "watch_safe_mlm_refresh.sh" in package_script


def test_publication_package_watchdog_refreshes_after_new_safe_epoch() -> None:
    watch_script = (
        Path(__file__).parents[1] / "scripts" / "watch_publication_package_refresh.sh"
    ).read_text(encoding="utf-8")
    start_script = (
        Path(__file__).parents[1] / "scripts" / "start_publication_package_watchdog.sh"
    ).read_text(encoding="utf-8")
    package_script = (
        Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh"
    ).read_text(encoding="utf-8")

    assert "history_count=\"$(history_epochs)\"" in watch_script
    assert "package_count=\"$(packaged_epochs)\"" in watch_script
    assert "[ \"$history_count\" -gt \"$package_count\" ]" in watch_script
    assert "SNOWCELL_PACKAGE_REFRESH_LOCK_DIR" in watch_script
    assert "bash scripts/generate_publication_package.sh" in watch_script
    assert "tmux has-session -t \"=$session\"" in start_script
    assert "watch_publication_package_refresh.sh" in package_script
    assert "start_publication_package_watchdog.sh" in package_script


def test_annotation_bundle_index_reports_label_ready_outputs(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_annotation_bundle_index.py"
    spec = importlib.util.spec_from_file_location("write_annotation_bundle_index", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    bundle_dir = tmp_path / "outputs" / "annotation_bundles" / "public_subset"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "annotation_metadata.json").write_text(
        json.dumps(
            {
                "checkpoint_path": "outputs/foundation_5090_public_sprint/best.pt",
                "data_path": "data/public/demo.npz",
                "checkpoint_epoch": 3,
                "n_cells": 3,
                "embedding_dim": 256,
                "fine_vocab_size": 13,
                "coarse_vocab_size": 13,
                "prediction_csv": "predictions.csv",
                "embedding_npy": "embeddings.npy",
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "predictions.csv").write_text(
        "cell_id,cell_index,fine_label,fine_confidence,coarse_label,coarse_confidence\n"
        "c1,0,cortex,0.9,root,0.8\n"
        "c2,1,cortex,0.8,root,0.7\n"
        "c3,2,epidermis,0.7,shoot,0.6\n",
        encoding="utf-8",
    )
    (bundle_dir / "embeddings.npy").write_bytes(b"npy")

    payload = module.collect_bundles(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "annotation_bundle_index.md"
    output_json = tmp_path / "outputs" / "publication_package" / "annotation_bundle_index.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    assert payload["summary"]["bundle_count"] == 1
    assert payload["summary"]["label_ready_count"] == 1
    assert payload["bundles"][0]["status"] == "label_ready"
    assert "cortex:2" in payload["bundles"][0]["top_fine_labels"]
    assert "public_subset" in output_md.read_text(encoding="utf-8")
    assert "label_ready" in output_json.read_text(encoding="utf-8")


def test_model_release_manifest_indexes_checkpoint_metadata(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_model_release_manifest.py"
    spec = importlib.util.spec_from_file_location("write_model_release_manifest", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    run_dir = tmp_path / "outputs" / "supervised_run"
    run_dir.mkdir(parents=True)
    checkpoint = {
        "epoch": 3,
        "model_config": {"d_model": 16, "n_layers": 1, "n_heads": 4},
        "experiment_config": {"train": {"stage": "hybrid"}},
        "gene_vocab": ["<pad>", "<cls>", "<mask>", "gene_a"],
        "fine_vocab": ["cortex", "epidermis"],
        "coarse_vocab": ["root", "shoot"],
        "species_vocab": ["Arabidopsis"],
        "tissue_vocab": ["root"],
        "metrics": {"eval_loss": 1.25, "fine_macro_f1": 0.5},
    }
    torch.save(checkpoint, run_dir / "best.pt")
    (run_dir / "history.json").write_text(json.dumps({"epochs": [{"epoch": 1}]}), encoding="utf-8")
    (run_dir / "config.resolved.json").write_text(json.dumps({"train": {"stage": "hybrid"}}), encoding="utf-8")

    payload = module.collect_manifest(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "model_release_manifest.md"
    output_json = tmp_path / "outputs" / "publication_package" / "model_release_manifest.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    assert payload["summary"]["checkpoint_count"] == 1
    assert payload["summary"]["label_release_candidate_count"] == 1
    assert payload["checkpoints"][0]["status"] == "label_release_candidate"
    assert payload["checkpoints"][0]["fine_vocab_size"] == 2
    assert len(payload["checkpoints"][0]["sha256"]) == 64
    assert "label_release_candidate" in output_md.read_text(encoding="utf-8")
    assert "supervised_run" in output_json.read_text(encoding="utf-8")


def test_submission_dossier_summarizes_blockers_and_repro_commands(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_submission_dossier.py"
    spec = importlib.util.spec_from_file_location("write_submission_dossier", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    package_dir = tmp_path / "outputs" / "publication_package"
    package_dir.mkdir(parents=True)
    run_dir = tmp_path / "outputs" / "foundation_5090_mlm_public_late_refresh_safe"
    run_dir.mkdir(parents=True)
    (run_dir / "config.resolved.json").write_text(
        json.dumps({"train": {"epochs": 8}}),
        encoding="utf-8",
    )
    safe_init_dir = tmp_path / "outputs" / "foundation_5090_public_safe_init"
    safe_init_dir.mkdir(parents=True)
    (safe_init_dir / "config.resolved.json").write_text(
        json.dumps({"train": {"epochs": 12}}),
        encoding="utf-8",
    )
    (safe_init_dir / "history.json").write_text(
        json.dumps(
            {
                "epochs": [
                    {"epoch": 10, "fine_macro_f1": 0.77, "coarse_macro_f1": 0.76},
                    {"epoch": 12, "fine_macro_f1": 0.75, "coarse_macro_f1": 0.74},
                ]
            }
        ),
        encoding="utf-8",
    )
    detailed_eval_dir = (
        tmp_path
        / "outputs"
        / "detailed_evaluations"
        / "foundation_5090_public_safe_init_test"
    )
    detailed_eval_dir.mkdir(parents=True)
    (detailed_eval_dir / "detailed_metrics.json").write_text(
        json.dumps(
            {
                "generated_at_utc": "2026-07-24T03:30:00+00:00",
                "checkpoint_path": "outputs/foundation_5090_public_safe_init/best.pt",
                "split": "test",
                "summary": {
                    "evaluated_cells": 14546,
                    "fine": {
                        "accuracy": 0.7122,
                        "macro_f1": 0.7013,
                        "weighted_f1": 0.7049,
                    },
                    "coarse": {
                        "accuracy": 0.7126,
                        "macro_f1": 0.7032,
                        "weighted_f1": 0.7051,
                    },
                },
                "artifacts": {
                    "predictions_tsv": (
                        "outputs/detailed_evaluations/"
                        "foundation_5090_public_safe_init_test/predictions.tsv"
                    ),
                    "fine_confusion_matrix_tsv": (
                        "outputs/detailed_evaluations/"
                        "foundation_5090_public_safe_init_test/fine_confusion_matrix.tsv"
                    ),
                    "coarse_confusion_matrix_tsv": (
                        "outputs/detailed_evaluations/"
                        "foundation_5090_public_safe_init_test/coarse_confusion_matrix.tsv"
                    ),
                },
            }
        ),
        encoding="utf-8",
    )
    (detailed_eval_dir / "detailed_evaluation.md").write_text("# detailed\n", encoding="utf-8")
    fixtures = {
        "status_summary.json": {
            "runs": [
                {"path": "outputs/foundation_5090_mlm_public_late_refresh_safe"},
                {
                    "path": "outputs/foundation_5090_public_safe_init",
                    "epochs_recorded": 12,
                    "test_metrics": {
                        "fine_macro_f1": 0.6934,
                        "coarse_macro_f1": 0.6938,
                    },
                },
            ]
        },
        "training_curve_summary.json": {
            "runs": [
                {
                    "run_id": "foundation_5090_mlm_public_late_refresh_safe",
                    "epochs_recorded": 5,
                    "latest_eval_loss": 9.778466942310333,
                    "eval_loss_delta": {"absolute": 1.4229},
                },
                {
                    "run_id": "foundation_5090_mlm_public_expansion_continuation",
                    "epochs_recorded": 1,
                    "latest_eval_loss": 8.562920331954956,
                    "latest_train_loss": 10.313495223174831,
                    "latest_progress": {"epoch": 2, "step": 500, "status": "training"},
                }
            ]
        },
        "training_health_audit.json": {
            "runs": [
                {
                    "run_id": "foundation_5090_public_safe_init",
                    "status": "running_with_checkpoint",
                    "epochs_recorded": 8,
                    "latest_epoch": {"fine_macro_f1": 0.7288854574},
                    "runtime": {"tmux_active": True, "session": "snowcell_public_safe_init"},
                }
            ]
        },
        "model_release_manifest.json": {
            "summary": {
                "checkpoint_count": 7,
                "label_release_candidate_count": 3,
                "embedding_release_candidate_count": 4,
            }
        },
        "annotation_bundle_index.json": {
            "summary": {"bundle_count": 2, "label_ready_count": 1, "annotated_cells": 1074}
        },
        "data_integrity_audit.json": {"summary": {"missing_files": 0}},
        "download_progress_audit.json": {"targets": []},
        "benchmark_gap_audit.json": {"summary": {"top_journal_benchmark_ready": False}},
        "saussurea_h5ad_contract.json": {
            "summary": {
                "contract_ready": False,
                "path": "data/saussurea_involucrata.h5ad",
            }
        },
        "saussurea_public_data_discovery.json": {
            "summary": {
                "snow_lotus_primary_scrna_publicly_found": False,
                "single_cell_literature_report_count": 1,
                "public_downloadable_saussurea_single_cell_matrix_found": False,
                "low_confidence_query_count": 2,
            }
        },
        "saussurea_data_request_package.json": {
            "summary": {
                "request_candidate_count": 1,
                "package_ready": True,
            }
        },
        "scplantannotate_access_audit.json": {"summary": {"comparison_ready": False}},
        "submission_action_plan.json": {
            "actions": [
                {
                    "id": "obtain_saussurea_h5ad",
                    "priority": "S",
                    "status": "BLOCKED_USER_DATA",
                    "evidence": "input=data/saussurea_involucrata.h5ad",
                    "next_action": "upload h5ad",
                },
                {
                    "id": "run_scplantannotate_authorized_benchmark",
                    "priority": "A",
                    "status": "BLOCKED_AUTH",
                    "evidence": "auth required",
                    "next_action": "run scPlantAnnotate benchmark",
                },
                {
                    "id": "final_top_journal_claim_audit",
                    "priority": "S",
                    "status": "MISSING",
                    "evidence": "not ready",
                    "next_action": "rerun package",
                },
                {
                    "id": "complete_safe_mlm_refresh",
                    "priority": "S",
                    "status": "IN_PROGRESS",
                    "evidence": "safe run epochs=5/8",
                    "next_action": "continue training",
                },
            ]
        },
    }
    for name, payload in fixtures.items():
        (package_dir / name).write_text(json.dumps(payload), encoding="utf-8")

    payload = module.build_dossier(tmp_path)
    output_md = package_dir / "submission_dossier.md"
    output_json = package_dir / "submission_dossier.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    text = output_md.read_text(encoding="utf-8")
    assert payload["summary"]["overall_status"] == "IN_PROGRESS"
    assert payload["summary"]["safe_training_epochs"] == 5
    assert payload["summary"]["public_safe_init_complete"] is True
    assert payload["summary"]["public_safe_init_best_epoch"] == 10
    assert payload["summary"]["public_safe_init_test_fine_macro_f1"] == 0.6934
    assert payload["summary"]["public_expansion_continuation_epochs"] == 1
    assert payload["summary"]["public_expansion_continuation_latest_eval_loss"] == 8.562920331954956
    assert payload["summary"]["public_expansion_continuation_progress_epoch"] == 2
    assert payload["summary"]["public_expansion_continuation_progress_step"] == 500
    assert payload["summary"]["detailed_evaluation_count"] == 1
    assert payload["summary"]["latest_detailed_evaluation_cells"] == 14546
    assert payload["summary"]["latest_detailed_evaluation_fine_macro_f1"] == 0.7013
    assert payload["summary"]["annotated_cell_count"] == 1074
    assert payload["summary"]["saussurea_single_cell_literature_report_count"] == 1
    assert payload["summary"]["saussurea_public_downloadable_single_cell_matrix_found"] is False
    assert payload["summary"]["saussurea_low_confidence_query_count"] == 2
    assert payload["summary"]["saussurea_data_request_candidate_count"] == 1
    assert payload["summary"]["saussurea_data_request_package_ready"] is True
    assert payload["summary"]["hard_blocker_count"] >= 2
    assert "data/saussurea_involucrata.h5ad" in text
    assert "scPlantAnnotate" in text
    assert "continue_foundation_5090_public_safe_init" in text
    assert payload["summary"]["in_progress_count"] >= 2
    assert "Public safe-init hybrid refresh" in text
    assert "Public MLM expansion continuation" in text
    assert "8.5629" in text
    assert "Detailed checkpoint evaluations" in text
    assert "foundation_5090_public_safe_init_test" in text
    assert "0.6934" in text
    assert "0.7013" in text
    assert "evaluate_checkpoint_detailed.py" in text
    assert "generate_publication_package.sh" in text
    assert "Do Not Claim Yet" in text
    assert "request-only Snow Lotus single-cell literature report" in text
    assert "Saussurea data request package" in text
    assert "write_saussurea_data_request_package.py" in text
    assert "start_gse226097_lifecycle_watchdog.sh" in text
    assert "IN_PROGRESS" in output_json.read_text(encoding="utf-8")


def test_build_npz_from_seurat_export_accepts_case_variant_metadata(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "build_npz_from_seurat_export.py"
    spec = importlib.util.spec_from_file_location("build_npz_from_seurat_export", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    sample_dir = tmp_path / "export" / "sample_a"
    sample_dir.mkdir(parents=True)
    matrix = sparse.csr_matrix([[1, 0, 2], [0, 3, 0]], dtype="float32")
    io.mmwrite(sample_dir / "matrix_cells_by_genes.mtx", matrix)
    (sample_dir / "genes.txt").write_text("gene_a\ngene_b\ngene_c\n", encoding="utf-8")
    (sample_dir / "cells.txt").write_text("cell_a\ncell_b\n", encoding="utf-8")
    (sample_dir / "metadata.csv").write_text(
        "CellType,Major_Cell_Type,Sample_ID,Species,Tissue,cell_id\n"
        "cortex,root,s1,Arabidopsis thaliana,root,cell_a\n"
        "stele,root,s1,Arabidopsis thaliana,root,cell_b\n",
        encoding="utf-8",
    )

    output = module.convert_one(
        sample_dir=sample_dir,
        output_dir=tmp_path / "npz",
        dataset_id="demo",
        species="species",
        tissue="tissue",
        label_keys=["celltype"],
        coarse_label_keys=["major_cell_type"],
        sample_keys=["sample_id"],
    )
    loaded = load_matrix(output, ExperimentConfig().data)

    assert loaded.obs["cell_type"].tolist() == ["cortex", "stele"]
    assert loaded.obs["cell_type_coarse"].tolist() == ["root", "root"]
    assert loaded.obs["sample_id"].tolist() == ["s1", "s1"]
    assert loaded.obs["species"].tolist() == ["Arabidopsis thaliana", "Arabidopsis thaliana"]


def test_build_npz_defaults_prefer_cell_annotation_metadata() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "build_npz_from_seurat_export.py"
    spec = importlib.util.spec_from_file_location("build_npz_from_seurat_export_defaults", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert module.DEFAULT_LABEL_KEYS.index("CellAnnotation") < module.DEFAULT_LABEL_KEYS.index("seurat_clusters")
    assert module.DEFAULT_LABEL_KEYS.index("annotations") < module.DEFAULT_LABEL_KEYS.index("seurat_clusters")
    assert module.DEFAULT_LABEL_KEYS.index("annotation.predicted") < module.DEFAULT_LABEL_KEYS.index("seurat_clusters")
    assert "TissueSystem" in module.DEFAULT_COARSE_LABEL_KEYS
    assert "annotation.predicted" in module.DEFAULT_COARSE_LABEL_KEYS
    assert "Condition" in module.DEFAULT_SAMPLE_KEYS


def test_seurat_rds_export_script_supports_v5_layers() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "export_seurat_rds_to_mtx.R").read_text(
        encoding="utf-8"
    )

    assert "LayerData" in script
    assert "Layers(assay_obj)" in script
    assert "slot(assay_obj, \"layers\")" in script
    assert "repair_dimnames" in script
    assert "Assays(obj)" in script
    assert "names(slot(obj, \"assays\"))" in script
    assert "No non-empty counts/data matrix found" in script


def test_geo_raw_tar_h5_script_skips_same_file_copy() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "download_geo_raw_tar_h5_subset.sh").read_text(
        encoding="utf-8"
    )

    assert "readlink -f \"$extracted\"" in script
    assert "readlink -f \"$target\"" in script
    assert "cp -f \"$extracted\" \"$target\"" in script
    assert 'rm -f "${raw_dir}/unsupported_single_cell_matrix.json"' in script


def test_gse226097_lifecycle_subset_is_queued_as_small_rds() -> None:
    script = (
        Path(__file__).parents[1] / "scripts" / "download_gse226097_arabidopsis_lifecycle_rds_subset.sh"
    ).read_text(encoding="utf-8")
    start_script = (Path(__file__).parents[1] / "scripts" / "start_gse226097_lifecycle_subset.sh").read_text(
        encoding="utf-8"
    )
    watch_script = (Path(__file__).parents[1] / "scripts" / "watch_gse226097_lifecycle_subset.sh").read_text(
        encoding="utf-8"
    )
    watchdog_script = (
        Path(__file__).parents[1] / "scripts" / "start_gse226097_lifecycle_watchdog.sh"
    ).read_text(encoding="utf-8")
    queue_script = (Path(__file__).parents[1] / "scripts" / "queue_reviewed_geo_downloads.sh").read_text(
        encoding="utf-8"
    )
    start_queue_script = (Path(__file__).parents[1] / "scripts" / "start_reviewed_geo_queue.sh").read_text(
        encoding="utf-8"
    )
    package_script = (Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh").read_text(
        encoding="utf-8"
    )

    assert "GSE226097_seedling_3d_relaxed_220711" in script
    assert "SNOWCELL_GSE226097_PATTERN" in script
    assert "snowcell_gse226097_arabidopsis_lifecycle_subset" in start_script
    assert "download_gse226097_arabidopsis_lifecycle_rds_subset.sh" in start_script
    assert "data/corpus_manifest.gse226097.tsv" in watch_script
    assert "start_gse226097_lifecycle_subset.sh" in watch_script
    assert "snowcell_gse226097_lifecycle_watchdog" in watchdog_script
    assert "data/corpus_manifest.gse226097.tsv" in queue_script
    assert "download_gse226097_arabidopsis_lifecycle_rds_subset.sh" in queue_script
    assert "start_gse226097_lifecycle_subset.sh" in package_script
    assert "start_gse226097_lifecycle_watchdog.sh" in package_script


def test_20260724_geo_refresh_candidates_are_queued_and_packaged() -> None:
    manifest = (Path(__file__).parents[1] / "data" / "public_dataset_manifest.tsv").read_text(
        encoding="utf-8"
    )
    queue_script = (Path(__file__).parents[1] / "scripts" / "queue_reviewed_geo_downloads.sh").read_text(
        encoding="utf-8"
    )
    start_queue_script = (Path(__file__).parents[1] / "scripts" / "start_reviewed_geo_queue.sh").read_text(
        encoding="utf-8"
    )
    package_script = (Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh").read_text(
        encoding="utf-8"
    )
    rice_script = (
        Path(__file__).parents[1] / "scripts" / "download_gse308757_rice_node_mtx_subset.sh"
    ).read_text(encoding="utf-8")
    tomato_script = (
        Path(__file__).parents[1]
        / "scripts"
        / "download_gse325371_tomato_salt_idioblast_mtx_subset.sh"
    ).read_text(encoding="utf-8")
    callus_script = (
        Path(__file__).parents[1] / "scripts" / "download_gse234192_plant_callus_rds_subset.sh"
    ).read_text(encoding="utf-8")
    tomato_rice_script = (
        Path(__file__).parents[1]
        / "scripts"
        / "download_gse149217_tomato_rice_root_tip_mtx_subset.sh"
    ).read_text(encoding="utf-8")

    assert "rice_node_reproductive_stage_atlas" in manifest
    assert "GSE308757" in manifest
    assert "tomato_salt_idioblast_atlas" in manifest
    assert "GSE325371" in manifest
    assert "arabidopsis_callus_regeneration_scrna" in manifest
    assert "GSE234192" in manifest
    assert "tomato_rice_root_tip_celltype_atlas" in manifest
    assert "GSE149217" in manifest
    assert "data/corpus_manifest.gse308757.tsv" in queue_script
    assert "data/corpus_manifest.gse325371.tsv" in queue_script
    assert "data/corpus_manifest.gse234192.tsv" in queue_script
    assert "data/corpus_manifest.gse149217.tsv" in queue_script
    assert "manifest_row_count" in queue_script
    assert "unsupported_report_for_manifest" in queue_script
    assert "partial_download_for_manifest" in queue_script
    assert "job_done_status" in queue_script
    assert 'done_status="$(job_done_status "$session" "$done_file")"' in queue_script
    assert 'if [ "$done_status" = "running" ]; then' in queue_script
    assert "partial=\"$(partial_download_for_manifest \"$manifest\")\"" in queue_script
    assert "reviewed GEO job unsupported for expression corpus" in queue_script
    assert 'echo "missing"\n  return 0' in queue_script
    assert "reviewed_geo_download_queue.log" in start_queue_script
    assert "queue_reviewed_geo_downloads.sh >> '$log_path' 2>&1" in start_queue_script
    assert "download_gse308757_rice_node_mtx_subset.sh" in package_script
    assert "download_gse325371_tomato_salt_idioblast_mtx_subset.sh" in package_script
    assert "download_gse234192_plant_callus_rds_subset.sh" in package_script
    assert "download_gse149217_tomato_rice_root_tip_mtx_subset.sh" in package_script
    assert "download_geo_raw_tar_mtx_subset.sh" in rice_script
    assert "download_geo_raw_tar_mtx_subset.sh" in tomato_script
    assert "tomato_rice_root_tip_celltype_atlas" in tomato_rice_script
    assert "unsupported_single_cell_matrix.json" in tomato_rice_script
    assert "TRAP-seq and ATAC-seq atlas" in tomato_rice_script
    assert "not scRNA/snRNA cell-by-gene expression matrices" in tomato_rice_script
    assert "download_geo_page_rds_subset.sh" in callus_script
    assert "Oryza sativa Japonica Group" in rice_script
    assert "Solanum lycopersicum" in tomato_script
    assert "Arabidopsis thaliana" in callus_script


def test_geo_page_rds_downloader_resumes_when_aria2_marker_exists() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "download_geo_page_rds_subset.sh").read_text(
        encoding="utf-8"
    )

    assert '[ -f "${target}.aria2" ]' in script
    assert "exists $target" in script


def test_geo_page_rds_downloader_uses_ncbi_geo_download_fallback() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "download_geo_page_rds_subset.sh").read_text(
        encoding="utf-8"
    )

    assert "geo_download_fallback_url" in script
    assert "https://www.ncbi.nlm.nih.gov/geo/download/?acc=" in script
    assert 'printf "%s\\t%s\\n" "$url" "$fallback_url"' in script
    assert "curl_download_with_fallback" in script
    assert 'SNOWCELL_GEO_CONNECTIONS:-1' in script
    assert 'SNOWCELL_GEO_SPLITS:-1' in script


def test_geo_page_rds_downloader_falls_back_to_direct_expression_export() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "download_geo_page_rds_subset.sh").read_text(
        encoding="utf-8"
    )
    direct_export = (
        Path(__file__).parents[1] / "scripts" / "export_seurat_rds_expression_slot_to_mtx.R"
    ).read_text(encoding="utf-8")

    assert "Seurat RDS export failed; trying direct expression slot export." in script
    assert "export_seurat_rds_expression_slot_to_mtx.R" in script
    assert "Using direct matrix object" in direct_export
    assert 'return(list(matrix = obj, assay = "direct", slot = "object"))' in direct_export


def test_geo_raw_tar_mtx_script_marks_quant_sf_as_unsupported() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "download_geo_raw_tar_mtx_subset.sh").read_text(
        encoding="utf-8"
    )
    h5_script = (Path(__file__).parents[1] / "scripts" / "download_geo_raw_tar_h5_subset.sh").read_text(
        encoding="utf-8"
    )
    checksum_script = (Path(__file__).parents[1] / "scripts" / "write_artifact_checksums.py").read_text(
        encoding="utf-8"
    )

    assert "unsupported_single_cell_matrix.json" in script
    assert "unsupported_for_single_cell_matrix_corpus" in script
    assert "quant.sf.gz" in script
    assert "matrix_like_file_count" in script
    assert "feature_like_file_count" in script
    assert "Matrix files were present, but no gene/features TSV files were found" in script
    assert "conversion_error_tail" in script
    assert "MTX conversion failed; wrote unsupported report" in script
    assert "tenx_h5_to_npz.py" in script
    assert "SNOWCELL_GEO_H5_SAMPLE_REGEX" in script
    assert "SNOWCELL_GEO_H5_MAX_FILES" in script
    assert "Selected {len(selected)} H5 files from RAW tar" in script
    assert "H5 conversion failed; wrote unsupported report" in script
    assert "Wrote $manifest_output from 10x H5 files embedded in $raw_tar" in script
    assert "corpus_manifest_rows" in script
    assert "https://www.ncbi.nlm.nih.gov/geo/download/?acc=" in script
    assert "SNOWCELL_GEO_RAW_FALLBACK_URL" in script
    assert "SNOWCELL_GEO_RAW_TAR_CONNECTIONS:-1" in script
    assert "SNOWCELL_GEO_RAW_TAR_SPLITS:-1" in script
    assert "SNOWCELL_GEO_RAW_TAR_ARIA2_LOWEST_SPEED:-1K" in script
    assert "--lowest-speed-limit=" in script
    assert "--auto-file-renaming=false" in script
    assert "aria2 raw tar download failed; retrying range-capable raw URL with curl resume" in script
    assert 'download_with_curl_resume "$raw_url" "GEO raw tar URL"' in script
    assert 'download_with_curl_fresh "$raw_fallback_url" "GEO download endpoint"' in script
    assert '[ ! -f "${raw_tar}.aria2" ]' in script
    assert "partial_gzip_member_quarantine" in script
    assert "quarantined_gzip_members" in script
    assert "organized_flat_mtx_triplets" in script
    assert "Organized {len(organized)} flat MTX triplet files into sample directories" in script
    assert 'rm -f "$raw_tmp"' in script
    assert 'rm -f "${raw_tar}.aria2"' in script
    assert 'rm -f "${raw_dir}/unsupported_single_cell_matrix.json"' in script
    assert "https://www.ncbi.nlm.nih.gov/geo/download/?acc=" in h5_script
    assert "SNOWCELL_GEO_RAW_TAR_CONNECTIONS:-1" in h5_script
    assert "data/public/*_raw_tar/unsupported_single_cell_matrix.json" in checksum_script


def test_geo_mtx_component_downloader_uses_latest_file_index() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "download_geo_mtx_component_subset.sh").read_text(
        encoding="utf-8"
    )

    assert "geo_supplementary_files_*.tsv" in script
    assert "matrix/features/barcodes component set" in script
    assert "GEO component files were downloaded, but conversion failed" in script
    assert "geo_mtx_tar_to_npz.py" in script
    assert "SNOWCELL_GEO_MAX_SETS" in script
    assert "--auto-file-renaming=false" in script


def test_artifact_checksums_include_scplantllm_chunks_and_weights() -> None:
    checksum_script = (Path(__file__).parents[1] / "scripts" / "write_artifact_checksums.py").read_text(
        encoding="utf-8"
    )
    package_script = (Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh").read_text(
        encoding="utf-8"
    )

    assert "scplantllm_public_sprint_input/reference_preprocess/chunks/*.h5" in checksum_script
    assert "external/scPlantLLM/model_params/*.pth" in checksum_script
    assert "scplantannotate_access_audit" in checksum_script
    assert "scplantannotate_benchmark_input_package" in checksum_script
    assert "outputs/external_benchmarks/scplantannotate_public_sprint_input/truth_labels.csv" in checksum_script
    assert "outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad" in checksum_script
    assert "saussurea_public_data_discovery" in checksum_script
    assert "saussurea_data_request_package" in checksum_script
    assert "saussurea_data_request_email" in checksum_script
    assert "saussurea_h5ad_contract" in checksum_script
    assert "outputs/publication_package/public_discovery/*.json" in checksum_script
    assert "outputs/publication_package/public_discovery/*.md" in checksum_script
    assert "scripts/generated_geo_promotion_downloads/*.sh" in checksum_script
    assert "outputs/publication_package/scripts/generated_geo_promotion_downloads/*.sh" in checksum_script
    assert "model_release_manifest" in checksum_script
    assert "annotation_bundle_index" in checksum_script
    assert "submission_dossier" in checksum_script
    assert "corpus_provenance_audit" in checksum_script
    assert "outputs/detailed_evaluations/**/*.json" in checksum_script
    assert "outputs/detailed_evaluations/**/*.tsv" in checksum_script
    assert "outputs/publication_package/status_summary.json" in checksum_script
    assert "outputs/publication_package/top_journal_readiness_matrix.md" in checksum_script
    assert "outputs/publication_package/top_journal_readiness_matrix.json" in checksum_script
    assert "outputs/publication_package/submission_action_plan.md" in checksum_script
    assert "outputs/publication_package/submission_action_plan.json" in checksum_script
    assert "outputs/publication_package/submission_action_plan.tsv" in checksum_script
    assert "outputs/publication_package/training_curve_summary.json" in checksum_script
    assert "outputs/publication_package/scplantdb_manifest_audit.json" in checksum_script
    assert "outputs/publication_package/scplantdb_manifest_audit.tsv" in checksum_script
    assert "outputs/publication_package/geo_promotion_queue_health_audit.md" in checksum_script
    assert "outputs/publication_package/geo_promotion_queue_health_audit.json" in checksum_script
    assert "write_scplantannotate_access_audit.py" in package_script
    assert "write_scplantannotate_benchmark_package.py" in package_script
    assert "run_scplantannotate_authenticated_benchmark.py" in package_script
    assert "scplantannotate_public_sprint_input/scplantannotate_input.h5ad" in package_script
    assert "--truth-csv outputs/external_benchmarks/scplantannotate_public_sprint_input/truth_labels.csv" in package_script
    assert "scplantannotate_benchmark_input_package.json" in package_script
    assert "scplantannotate_authenticated_benchmark_plan.json" in package_script
    assert "write_scplantdb_manifest_audit.py" in package_script
    assert "--max-assets 8" in package_script
    assert "--max-endpoints 6" in package_script
    assert "--output-json outputs/publication_package/top_journal_readiness_matrix.json" in package_script
    assert "write_saussurea_public_data_discovery.py" in package_script
    assert "write_public_discovery_gap_audit.py" in package_script
    assert "public_discovery_gap_audit.json" in package_script
    assert "write_geo_manifest_promotion_candidates.py" in package_script
    assert "geo_manifest_promotion_candidates.tsv" in package_script
    assert "write_geo_promotion_download_wrappers.py" in package_script
    assert "geo_promotion_download_queue.tsv" in package_script
    assert "download_geo_mtx_component_subset.sh" in package_script
    assert "write_geo_promotion_queue_health_audit.py" in package_script
    assert "geo_promotion_queue_health_audit.json" in package_script
    assert "write_corpus_provenance_audit.py" in package_script
    assert "corpus_provenance_audit.json" in package_script
    assert "generated_geo_promotion_downloads" in package_script
    assert "start_public_discovery_refresh.sh" in package_script
    assert "write_saussurea_data_request_package.py" in package_script
    assert "validate_saussurea_h5ad_contract.py" in package_script
    assert "evaluate_checkpoint_detailed.py" in package_script
    assert "run_post_training_release_artifacts.sh" in package_script
    assert "detailed_evaluation_index.txt" in package_script
    assert "write_submission_dossier.py" in package_script


def test_public_discovery_refresh_launcher_uses_tmux_and_retmax() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "start_public_discovery_refresh.sh").read_text(
        encoding="utf-8"
    )

    assert "SNOWCELL_PUBLIC_DISCOVERY_SESSION" in script
    assert "SNOWCELL_NCBI_DISCOVERY_RETMAX:-200" in script
    assert "tmux new-session -d" in script
    assert "scripts/discover_public_ncbi_data.sh" in script
    assert "scripts/review_geo_supplementary_candidates.sh" in script
    assert "scripts/generate_publication_package.sh" in script
    assert "SNOWCELL_GEO_PROMOTION_QUEUE_RESTART=1" in script
    assert "start_geo_promotion_queue.sh" in script


def test_post_training_release_artifacts_script_wires_eval_bundle_and_package() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "run_post_training_release_artifacts.sh").read_text(
        encoding="utf-8"
    )
    late_queue = (Path(__file__).parents[1] / "scripts" / "queue_late_public_mlm_refresh.sh").read_text(
        encoding="utf-8"
    )

    assert "scripts/evaluate_checkpoint_detailed.py" in script
    assert "snowcell annotate-bundle" in script
    assert "write_annotation_bundle_index.py" in script
    assert "outputs/post_training_release" in script
    assert "detailed_metrics.json" in script
    assert "bash scripts/generate_publication_package.sh" in script
    assert "SNOWCELL_RELEASE_RUN_ID" in late_queue
    assert "run_post_training_release_artifacts.sh" in late_queue


def test_scplantannotate_access_audit_detects_batch_api_terms() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_scplantannotate_access_audit.py"
    spec = importlib.util.spec_from_file_location("write_scplantannotate_access_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    text = """
    const submit = () => fetch('/api/predict', {method: 'POST', body: new FormData(form)});
    const download = '/results/job.csv';
    """
    scan = module.scan_text(text)

    assert "/api/predict" in scan["url_literals"]
    assert scan["keyword_line_count"] >= 1
    assert module.likely_batch_api(scan["url_literals"], scan["keyword_lines"]) is True


def test_scplantannotate_access_audit_processes_import_queue(monkeypatch) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_scplantannotate_access_audit.py"
    spec = importlib.util.spec_from_file_location("write_scplantannotate_access_audit_queue", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    pages = {
        "https://example.org/": '<script type="module" src="/src/index.jsx"></script>',
        "https://example.org/src/index.jsx": 'import App from "./App";',
        "https://example.org/src/App": "fetch('/api/predict', {body: new FormData(form)});",
    }

    def fake_fetch(url, timeout, max_bytes):
        result = module.FetchResult(
            url=url,
            final_url=url,
            status=200,
            content_type="text/javascript",
            bytes_read=len(pages.get(url, "")),
            error="",
            text_excerpt=pages.get(url, "")[:1000],
        )
        return result, pages.get(url, "")

    monkeypatch.setattr(module, "fetch_text", fake_fetch)
    payload = module.build_audit("https://example.org/")

    assert payload["summary"]["fetched_asset_count"] == 2
    assert payload["summary"]["batch_api_detected"] is True


def test_scplantannotate_access_audit_keeps_auth_required_api_not_ready(monkeypatch) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_scplantannotate_access_audit.py"
    spec = importlib.util.spec_from_file_location("write_scplantannotate_access_audit_auth", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    pages = {
        "https://example.org/": '<script type="module" src="/src/index.jsx"></script>',
        "https://example.org/src/index.jsx": "fetch('/api/jobs/api/job_annotate_and_plot/');",
    }

    def fake_fetch(url, timeout, max_bytes):
        if "/api/" in url:
            return (
                module.FetchResult(
                    url=url,
                    final_url=url,
                    status=403,
                    content_type="application/json",
                    bytes_read=57,
                    error="",
                    text_excerpt='{"detail":"Authentication credentials were not provided."}',
                ),
                '{"detail":"Authentication credentials were not provided."}',
            )
        result = module.FetchResult(
            url=url,
            final_url=url,
            status=200,
            content_type="text/javascript",
            bytes_read=len(pages.get(url, "")),
            error="",
            text_excerpt=pages.get(url, "")[:1000],
        )
        return result, pages.get(url, "")

    monkeypatch.setattr(module, "fetch_text", fake_fetch)
    payload = module.build_audit("https://example.org/")

    assert payload["summary"]["batch_api_detected"] is True
    assert payload["summary"]["anonymous_api_accessible"] is False
    assert payload["summary"]["auth_required_endpoint_count"] >= 1
    assert payload["summary"]["comparison_ready"] is False


def test_scplantannotate_authenticated_client_payload_templates() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "run_scplantannotate_authenticated_benchmark.py"
    spec = importlib.util.spec_from_file_location("run_scplantannotate_authenticated_benchmark", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    fields = module.build_h5ad_upload_fields(dataset_name="demo", organism_id=7, public_flag=0)
    payload = module.build_annotate_job_payload(
        predictor_id=11,
        dataset_id=23,
        dataset_name="demo",
    )

    assert fields == {
        "h5ad_dataset_name": "demo",
        "h5ad_dataset_file_extension": "h5ad",
        "h5ad_dataset_organism": "7",
        "h5ad_dataset_public_flag": "0",
    }
    assert payload["job_predictor"] == 11
    assert payload["job_h5ad_dataset"] == 23
    assert payload["job_script"] == 2
    assert payload["job_name"] == "demo_annotate&plot"
    args = argparse.Namespace(
        input_h5ad="demo.h5ad",
        base_url="https://example.org/",
        username_env="USER_ENV",
        password_env="PASS_ENV",
        dataset_name="demo",
        organism_id=7,
        public_flag=0,
        predictor_id=11,
    )
    dry_run = module.dry_run_payload(args)
    assert dry_run["counts_as_completed_metric"] is False
    assert dry_run["publication"]["pmid"] == "41554477"
    assert dry_run["readiness_gates"]["metric_output_path"].endswith(
        "scplantannotate_final_metrics.json"
    )
    assert "authorized_submit_and_wait" in dry_run["reproducible_commands"]
    assert "author_or_web_export_to_metric" in dry_run["reproducible_commands"]
    assert "excluded by benchmark-gap" in dry_run["metric_acceptance_rule"]
    assert "job_output_query" in dry_run["request_templates"]
    assert any("Poll" in item for item in dry_run["post_submit_automation"])


def test_scplantannotate_benchmark_package_selects_labelled_species_subset() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_scplantannotate_benchmark_package.py"
    spec = importlib.util.spec_from_file_location("write_scplantannotate_benchmark_package", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    import pandas as pd

    obs = pd.DataFrame(
        {
            "species": [
                "Arabidopsis_thaliana",
                "Arabidopsis thaliana",
                "Arabidopsis thaliana",
                "Oryza sativa",
                "Arabidopsis thaliana",
                "Arabidopsis_thaliana",
            ],
            "cell_type": ["cortex", "epidermis", "unannotated", "cortex", "root_hair", "Unknow"],
            "cell_type_coarse": ["ground", "dermal", "unknown", "ground", "dermal", "unknown"],
            "sample_id": ["s1", "s1", "s2", "s3", "s4", "s5"],
            "tissue": ["root", "root", "root", "root", "root", "root"],
        },
        index=["cell1", "cell2", "cell3", "cell4", "cell5", "cell6"],
    )

    eligible = module.eligible_obs(
        obs,
        species="Arabidopsis thaliana",
        label_key="cell_type",
        species_key="species",
    )
    positions = module.stratified_positions(
        eligible,
        label_key="cell_type",
        max_cells=2,
        seed=7,
    )
    truth = module.truth_frame(
        eligible.iloc[positions],
        label_key="cell_type",
        coarse_label_key="cell_type_coarse",
        cell_id_key="",
    )

    assert list(eligible.index) == ["cell1", "cell2", "cell5"]
    assert len(positions) == 2
    assert set(truth.columns) >= {"cell_id", "cell_type", "cell_type_coarse", "species", "tissue"}
    assert set(truth["cell_type"]).issubset({"cortex", "epidermis", "root_hair"})


def test_scplantannotate_prediction_export_writes_metric_payload(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "run_scplantannotate_authenticated_benchmark.py"
    spec = importlib.util.spec_from_file_location("run_scplantannotate_authenticated_metrics", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    prediction_csv = tmp_path / "predictions.csv"
    truth_csv = tmp_path / "truth.csv"
    prediction_csv.write_text(
        "cell_id,predicted_cell_type\n"
        "cell1,root_hair\n"
        "cell2,cortex\n"
        "cell3,cortex\n"
        "cell4,epidermis\n",
        encoding="utf-8",
    )
    truth_csv.write_text(
        "cell_id,cell_type\n"
        "cell1,root_hair\n"
        "cell2,cortex\n"
        "cell3,epidermis\n"
        "cell4,epidermis\n",
        encoding="utf-8",
    )

    metrics = module.prediction_metrics_from_csv(
        prediction_csv=prediction_csv,
        truth_csv=truth_csv,
    )

    assert metrics["method"] == "scplantannotate_authenticated_or_exported"
    assert metrics["status"] == "metrics_ready"
    assert metrics["test_cells"] == 4
    assert metrics["accuracy"] == 0.75
    assert metrics["macro_f1"] > 0


def test_saussurea_public_data_discovery_classifies_primary_single_cell_hits() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_public_data_discovery.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_public_data_discovery", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    summary = {
        "result": {
            "uids": ["1", "2"],
            "1": {
                "uid": "1",
                "title": "Saussurea involucrata single-cell root atlas",
                "accession": "PRJNA000001",
                "description": "10x scRNA-seq",
            },
            "2": {
                "uid": "2",
                "title": "Saussurea involucrata genome",
                "accession": "PRJNA000002",
                "description": "PacBio assembly",
            },
        }
    }
    hits = module.parse_hits("bioproject", "query", summary)

    assert hits[0].single_cell_terms is True
    assert hits[0].saussurea_involucrata_terms is True
    assert hits[1].single_cell_terms is False


def test_saussurea_public_data_discovery_keeps_chinese_query_terms() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_public_data_discovery.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_public_data_discovery_terms", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    joined_queries = "\n".join(module.QUERIES)

    assert "天山雪莲" in joined_queries
    assert "雪莲" in joined_queries
    assert "单细胞" in joined_queries
    assert "单核" in joined_queries
    assert module.SINGLE_CELL_RE.search("天山雪莲单细胞转录组") is not None
    assert module.SAUSSUREA_INVOLUCRATA_RE.search("snow lotus") is not None


def test_saussurea_public_data_discovery_marks_noisy_chinese_queries() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_public_data_discovery.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_public_data_discovery_quality", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    quality = module.query_quality('"天山雪莲" AND (单细胞 OR 单核)', 7288371)

    assert quality["reliability"] == "low_confidence_ncbi_tokenization_noise"
    assert quality["usable_for_primary_absence"] is False


def test_saussurea_public_data_discovery_tracks_nonpublic_literature_report() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_public_data_discovery.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_public_data_discovery_lit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    report = module.MANUAL_LITERATURE_REPORTS[0]

    assert report["species"] == "Saussurea involucrata"
    assert report["doi"] == "10.1002/adhm.202504623"
    assert report["public_matrix_found"] is False
    assert "data-request target" in report["use_in_project"]


def test_saussurea_data_request_package_writes_request_targets(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_data_request_package.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_data_request_package", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    package_dir = tmp_path / "outputs" / "publication_package"
    package_dir.mkdir(parents=True)
    (package_dir / "saussurea_public_data_discovery.json").write_text(
        json.dumps(
            {
                "summary": {"public_downloadable_saussurea_single_cell_matrix_found": False},
                "manual_literature_reports": [
                    {
                        "id": "saussurea_report",
                        "title": "Saussurea involucrata spheroids",
                        "species": "Saussurea involucrata",
                        "evidence_type": "reported single-cell transcriptomics",
                        "doi": "10.1002/adhm.202504623",
                        "pmid": "41668397",
                        "source_url": "https://advanced.onlinelibrary.wiley.com/doi/10.1002/adhm.202504623",
                        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/41668397/",
                        "data_availability": "request only",
                        "use_in_project": "data-request target",
                        "public_matrix_found": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "saussurea_supporting_evidence.json").write_text("[]", encoding="utf-8")
    (package_dir / "saussurea_h5ad_contract.json").write_text(
        json.dumps({"summary": {"contract_ready": False}}),
        encoding="utf-8",
    )

    payload = module.build_payload(tmp_path)
    output_md = package_dir / "saussurea_data_request_package.md"
    output_json = package_dir / "saussurea_data_request_package.json"
    output_email = package_dir / "saussurea_data_request_email.txt"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    module.write_email(payload, output_email)

    assert payload["summary"]["request_candidate_count"] == 1
    assert payload["summary"]["package_ready"] is True
    assert "cell_type" in payload["required_obs_fields"]
    assert "model-training/benchmarking permission" in output_md.read_text(encoding="utf-8")
    assert "Request for Saussurea involucrata single-cell transcriptomics data" in output_email.read_text(
        encoding="utf-8"
    )
    assert "10.1002/adhm.202504623" in output_json.read_text(encoding="utf-8")


def test_saussurea_public_data_discovery_retries_transient_ncbi_errors(monkeypatch) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_public_data_discovery.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_public_data_discovery_retry", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    calls: list[int] = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            raise module.urllib.error.URLError("connection reset")
        return FakeResponse()

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)

    payload = module.ncbi_get("esearch.fcgi", {"db": "sra", "term": "Saussurea"}, attempts=2)

    assert payload == {"ok": True}
    assert calls == [30, 30]


def test_saussurea_public_data_discovery_recovers_failed_query_round(monkeypatch) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_public_data_discovery.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_public_data_discovery_recovery", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    calls = {"esearch": 0}

    def fake_esearch(db, query, retmax):
        calls["esearch"] += 1
        if calls["esearch"] == 1:
            raise RuntimeError("transient NCBI reset")
        return {"esearchresult": {"idlist": ["1"], "count": "1"}}

    def fake_esummary(db, ids):
        return {
            "result": {
                "uids": ["1"],
                "1": {
                    "uid": "1",
                    "title": "Saussurea involucrata transcriptome",
                    "accession": "SRR000001",
                },
            }
        }

    monkeypatch.setattr(module, "DATABASES", ["sra"])
    monkeypatch.setattr(module, "QUERIES", ["Saussurea"])
    monkeypatch.setattr(module, "esearch", fake_esearch)
    monkeypatch.setattr(module, "esummary", fake_esummary)
    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)

    payload = module.build_discovery(retmax=1, recovery_rounds=1)

    assert payload["summary"]["error_count"] == 0
    assert payload["summary"]["unique_hit_count"] == 1
    assert calls["esearch"] == 2


def test_saussurea_public_data_discovery_parses_sra_xml_fields() -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_saussurea_public_data_discovery.py"
    spec = importlib.util.spec_from_file_location("write_saussurea_public_data_discovery_xml", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    record = {
        "uid": "123",
        "runs": '<Run acc="SRR000001" total_spots="1"/>',
        "expxml": "<Title>Saussurea involucrata 10x single-cell root atlas</Title>",
    }

    assert module.record_title(record) == "Saussurea involucrata 10x single-cell root atlas"
    assert module.record_accession(record) == "SRR000001"
    assert "Saussurea involucrata" in module.record_text(record)


def load_saussurea_contract_module():
    module_path = Path(__file__).parents[1] / "scripts" / "validate_saussurea_h5ad_contract.py"
    spec = importlib.util.spec_from_file_location("validate_saussurea_h5ad_contract", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_saussurea_h5ad_contract_reports_missing_file(tmp_path: Path) -> None:
    module = load_saussurea_contract_module()
    args = type(
        "Args",
        (),
        {
            "min_cells": 5,
            "min_genes": 4,
            "min_labelled_cells": 5,
            "min_fine_cell_types": 2,
            "min_samples": 2,
            "min_tissues": 1,
            "min_batches": 1,
            "top_journal_min_cells": 10,
            "top_journal_min_samples": 2,
            "top_journal_min_tissues": 1,
            "top_journal_min_cell_types": 2,
        },
    )()

    payload = module.inspect_h5ad(tmp_path / "missing.h5ad", args)

    assert payload["summary"]["exists"] is False
    assert payload["summary"]["contract_ready"] is False
    assert "Missing required file" in payload["errors"][0]


def test_saussurea_h5ad_contract_accepts_valid_minimal_h5ad(tmp_path: Path) -> None:
    module = load_saussurea_contract_module()
    path = tmp_path / "saussurea.h5ad"
    values = {
        "cell_type": ["cortex", "cortex", "epidermis", "epidermis", "xylem", "xylem"],
        "cell_type_coarse": ["root", "root", "root", "root", "vascular", "vascular"],
        "sample_id": ["s1", "s1", "s2", "s2", "s2", "s2"],
        "species": ["Saussurea involucrata"] * 6,
        "tissue": ["root"] * 6,
        "batch": ["b1", "b1", "b1", "b1", "b2", "b2"],
        "cell_id": [f"cell_{index}" for index in range(6)],
    }
    with h5py.File(path, "w") as handle:
        handle.create_dataset("X", data=np.ones((6, 4), dtype=np.float32))
        obs = handle.create_group("obs")
        string_dtype = h5py.string_dtype(encoding="utf-8")
        for key, column in values.items():
            obs.create_dataset(key, data=np.asarray(column, dtype=object), dtype=string_dtype)
    args = type(
        "Args",
        (),
        {
            "min_cells": 5,
            "min_genes": 4,
            "min_labelled_cells": 5,
            "min_fine_cell_types": 3,
            "min_samples": 2,
            "min_tissues": 1,
            "min_batches": 2,
            "top_journal_min_cells": 5,
            "top_journal_min_samples": 2,
            "top_journal_min_tissues": 1,
            "top_journal_min_cell_types": 3,
        },
    )()

    payload = module.inspect_h5ad(path, args)

    assert payload["summary"]["contract_ready"] is True
    assert payload["summary"]["top_journal_primary_data_ready"] is True
    assert payload["summary"]["fine_cell_type_count"] == 3
    assert payload["gates"]["species_is_saussurea_involucrata"] is True


def test_benchmark_gap_audit_requires_external_metric_payload(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_benchmark_gap_audit.py"
    spec = importlib.util.spec_from_file_location("write_benchmark_gap_audit_metrics", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    external_dir = tmp_path / "outputs" / "external_benchmarks"
    external_dir.mkdir(parents=True)
    (external_dir / "scplantannotate_authenticated_benchmark_plan.json").write_text(
        json.dumps({"status": "dry_run_credentials_required"}),
        encoding="utf-8",
    )
    (external_dir / "scplantllm_embedding_centroid_probe.json").write_text(
        json.dumps({"status": "completed", "metrics": {"macro_f1": 0.2}}),
        encoding="utf-8",
    )

    assert module.external_metric_files(tmp_path, "scplantannotate") == []
    assert [path.name for path in module.external_metric_files(tmp_path, "scplantllm")] == [
        "scplantllm_embedding_centroid_probe.json"
    ]

    (external_dir / "scplantannotate_final_metrics.json").write_text(
        json.dumps({"status": "completed", "metrics": {"macro_f1": 0.3}}),
        encoding="utf-8",
    )

    assert [path.name for path in module.external_metric_files(tmp_path, "scplantannotate")] == [
        "scplantannotate_final_metrics.json"
    ]


def load_scplantllm_probe_module():
    module_path = Path(__file__).parents[1] / "scripts" / "run_scplantllm_embedding_centroid_probe.py"
    spec = importlib.util.spec_from_file_location("run_scplantllm_embedding_centroid_probe", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_scplantllm_probe_converts_flashmha_state_dict() -> None:
    module = load_scplantllm_probe_module()
    raw = {
        "module.transformer_encoder.layers.0.self_attn.Wqkv.weight": torch.zeros(6, 2),
        "module.transformer_encoder.layers.0.self_attn.Wqkv.bias": torch.zeros(6),
        "grad_reverse_discriminator.out_layer.weight": torch.zeros(3, 2),
    }

    converted, meta = module.convert_flashmha_state_dict(raw)

    assert "transformer_encoder.layers.0.self_attn.in_proj_weight" in converted
    assert "transformer_encoder.layers.0.self_attn.in_proj_bias" in converted
    assert "grad_reverse_discriminator.out_layer.weight" not in converted
    assert meta.converted_wqkv_weight_count == 1
    assert meta.converted_wqkv_bias_count == 1
    assert meta.skipped_key_count == 1


def test_scplantllm_probe_prepare_batch_adds_cls_and_masks_padding() -> None:
    module = load_scplantllm_probe_module()
    shape = module.ModelShape(
        ntoken=10,
        d_model=4,
        nhead=2,
        d_hid=8,
        nlayers=1,
        nlayers_cls=1,
        n_cls=3,
        n_input_bins=5,
        pad_token_id=0,
        value_pad_index=3,
        cls_token_id=9,
    )
    gids = np.asarray([[1, 2, 0]], dtype=np.int64)
    values = np.asarray([[4, -2, -2]], dtype=np.int64)

    src, prepared_values, mask = module.prepare_batch(
        gids,
        values,
        shape=shape,
        device=torch.device("cpu"),
        cls_value=0,
    )

    assert src.tolist() == [[9, 1, 2, 0]]
    assert prepared_values.tolist() == [[0, 4, 3, 3]]
    assert mask.tolist() == [[False, False, True, True]]


def test_scplantllm_probe_nearest_centroid_predictions() -> None:
    module = load_scplantllm_probe_module()
    train_embeddings = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    train_labels = np.asarray(["root", "leaf"])
    test_embeddings = np.asarray([[0.9, 0.1], [0.1, 0.9]], dtype=np.float32)

    predictions, centroid_counts = module.nearest_centroid_predictions(
        train_embeddings,
        train_labels,
        test_embeddings,
    )

    assert predictions.tolist() == ["root", "leaf"]
    assert centroid_counts == {"leaf": 1, "root": 1}


def test_model_data_card_summarizes_runs_and_gaps(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_model_data_card.py"
    spec = importlib.util.spec_from_file_location("write_model_data_card", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    status = {
        "project_dir": "/root/snowlotus-cellfm",
        "publication_gates": {"snow_lotus_scRNA_present": False},
        "runs": [
            {
                "path": "outputs/foundation_5090_pretrain",
                "has_checkpoint": True,
                "checkpoint_bytes": 1024,
                "epochs_recorded": 2,
                "latest_epoch": {"epoch": 2, "fine_macro_f1": 0.8, "eval_loss": 1.2},
                "test_metrics": {},
            }
        ],
        "corpora": [{"path": "data/plant_foundation_corpus_public_mlm.h5ad", "exists": True, "bytes": 2048}],
        "public_data_targets": [
            {
                "dataset_id": "cotton_glandular_terpenoid_atlas",
                "priority": "B",
                "status": "download_candidate",
                "stage": "manifest_ready",
                "manifest": {"rows": 1},
                "raw_files": {"file_count": 1},
                "npz_files": {"file_count": 1},
            }
        ],
        "pending_corpus_additions": {
            "pending_manifests": [
                {
                    "manifest": "data/corpus_manifest.gse243419.tsv",
                    "dataset_ids": "cotton_glandular_terpenoid_atlas",
                    "rows_missing_from_public_mlm_manifest": 1,
                }
            ]
        },
    }
    status_path = tmp_path / "status_summary.json"
    status_path.write_text(json.dumps(status), encoding="utf-8")
    output_md = tmp_path / "model_data_card.md"
    output_json = tmp_path / "model_data_card.json"

    card = module.build_card(status)
    module.write_markdown(card, output_md)
    module.write_json(card, output_json)

    text = output_md.read_text(encoding="utf-8")
    assert "SnowLotus-CellFM Model and Data Card" in text
    assert "outputs/foundation_5090_pretrain" in text
    assert "data/saussurea_involucrata.h5ad" in text
    assert "cotton_glandular_terpenoid_atlas" in output_json.read_text(encoding="utf-8")


def test_late_refresh_config_uses_memory_safe_microbatch() -> None:
    config_path = Path(__file__).parents[1] / "configs" / "foundation_5090_mlm_public_late_refresh.yaml"
    safe_config_path = (
        Path(__file__).parents[1] / "configs" / "foundation_5090_mlm_public_late_refresh_safe.yaml"
    )
    post_gse_config_path = (
        Path(__file__).parents[1]
        / "configs"
        / "foundation_5090_mlm_public_post_gse226097_refresh_safe.yaml"
    )
    config = ExperimentConfig.load(config_path)
    safe_config = ExperimentConfig.load(safe_config_path)
    post_gse_config = ExperimentConfig.load(post_gse_config_path)
    queue_script = (
        Path(__file__).parents[1] / "scripts" / "queue_late_public_mlm_refresh.sh"
    ).read_text(encoding="utf-8")
    status_script = (
        Path(__file__).parents[1] / "scripts" / "write_status_summary.py"
    ).read_text(encoding="utf-8")
    health_script = (
        Path(__file__).parents[1] / "scripts" / "write_training_health_audit.py"
    ).read_text(encoding="utf-8")
    report_module = (Path(__file__).parents[1] / "src" / "snowcell" / "report.py").read_text(
        encoding="utf-8"
    )

    assert config.train.batch_size <= 6
    assert config.train.eval_batch_size <= 6
    assert config.train.gradient_accumulation_steps >= 24
    assert safe_config.data.max_genes <= 1024
    assert safe_config.train.batch_size <= 4
    assert safe_config.train.eval_batch_size <= 4
    assert safe_config.train.gradient_accumulation_steps >= 24
    assert safe_config.train.max_train_batches_per_epoch == 12000
    assert safe_config.train.max_eval_batches == 1200
    assert safe_config.train.heartbeat_steps == 100
    assert safe_config.train.latest_checkpoint_every_updates == 50
    assert safe_config.train.num_workers <= 2
    assert post_gse_config.data.max_genes <= 1024
    assert post_gse_config.train.batch_size <= 4
    assert post_gse_config.train.eval_batch_size <= 4
    assert post_gse_config.train.gradient_accumulation_steps >= 24
    assert (
        post_gse_config.train.init_checkpoint
        == "outputs/foundation_5090_mlm_public_expansion_continuation/best.pt"
    )
    assert (
        post_gse_config.output.directory
        == "outputs/foundation_5090_mlm_public_post_gse226097_refresh_safe"
    )
    assert "needs_late_training()" in queue_script
    assert "transfer_queues_pending()" in queue_script
    assert "queue_reviewed_geo_downloads.sh" in queue_script
    assert "queue_geo_promotion_downloads.sh" in queue_script
    assert "unsupported_single_cell_matrix.json" in queue_script
    assert "transfer queues still pending; delaying late public refresh" in queue_script
    assert "late refresh checkpoint missing or older" in queue_script
    assert "late_resume_config" in queue_script
    assert "write_late_resume_config()" in queue_script
    assert "resume_checkpoint" in queue_script
    assert "init_checkpoint" in queue_script
    assert "[ \"$late_output_dir/latest.pt\" -nt \"$mlm_corpus\" ]" in queue_script
    assert "config_to_run" in queue_script
    assert "late refresh tmux session already exists without matched training process" in queue_script
    assert "snowcell_mlm_public_post_gse226097_refresh_safe" in queue_script
    assert "foundation_5090_mlm_public_post_gse226097_refresh_safe.yaml" in queue_script
    assert "foundation_5090_mlm_public_post_gse226097_refresh_safe.resume.yaml" in queue_script
    assert "snowcell_mlm_public_expansion_continuation" in queue_script
    assert "configs/generated/foundation_5090_mlm_public_expansion_continuation.yaml" in queue_script
    assert ".venv/bin/snowcell train --config" in queue_script
    assert "observed training tmux session without matched train process" in queue_script
    assert "outputs/foundation_5090_mlm_public_post_gse226097_refresh_safe" in status_script
    assert "foundation_5090_mlm_public_post_gse226097_refresh_safe" in health_script
    assert "outputs/foundation_5090_mlm_public_post_gse226097_refresh_safe" in report_module


def test_public_safe_init_config_uses_completed_safe_mlm_checkpoint() -> None:
    config_path = Path(__file__).parents[1] / "configs" / "foundation_5090_public_safe_init.yaml"
    config = ExperimentConfig.load(config_path)
    status_script = (Path(__file__).parents[1] / "scripts" / "write_status_summary.py").read_text(
        encoding="utf-8"
    )
    health_script = (
        Path(__file__).parents[1] / "scripts" / "write_training_health_audit.py"
    ).read_text(encoding="utf-8")
    report_module = (Path(__file__).parents[1] / "src" / "snowcell" / "report.py").read_text(
        encoding="utf-8"
    )

    assert config.train.stage == "hybrid"
    assert config.train.init_checkpoint == "outputs/foundation_5090_mlm_public_late_refresh_safe/best.pt"
    assert config.output.directory == "outputs/foundation_5090_public_safe_init"
    assert config.architecture.d_model == 512
    assert config.architecture.n_layers == 10
    assert config.data.path == "data/plant_foundation_corpus.h5ad"
    assert "outputs/foundation_5090_public_safe_init" in status_script
    assert "foundation_5090_public_safe_init" in health_script
    assert "outputs/foundation_5090_public_safe_init" in report_module


def test_public_safe_init_start_script_resumes_in_exact_tmux_session() -> None:
    script = (
        Path(__file__).parents[1] / "scripts" / "start_public_safe_init_training.sh"
    ).read_text(encoding="utf-8")
    package_script = (
        Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh"
    ).read_text(encoding="utf-8")

    assert "foundation_5090_public_safe_init.yaml" in script
    assert "foundation_5090_public_safe_init.resume.yaml" in script
    assert "resume_checkpoint" in script
    assert "init_checkpoint" in script
    assert "tmux has-session -t \"=$session\"" in script
    assert "tmux new-session -d -s \"$session\"" in script
    assert "generate_publication_package.sh" in script
    assert "start_public_safe_init_training.sh" in package_script


def test_public_safe_init_annotation_bundle_script_uses_best_checkpoint() -> None:
    script = (
        Path(__file__).parents[1] / "scripts" / "create_public_safe_init_annotation_bundle.sh"
    ).read_text(encoding="utf-8")
    package_script = (
        Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh"
    ).read_text(encoding="utf-8")
    dossier_script = (
        Path(__file__).parents[1] / "scripts" / "write_submission_dossier.py"
    ).read_text(encoding="utf-8")

    assert "outputs/foundation_5090_public_safe_init/best.pt" in script
    assert "scplantllm_srp169576_public_safe_init" in script
    assert "snowcell annotate-bundle" in script
    assert "write_annotation_bundle_index.py" in script
    assert "create_public_safe_init_annotation_bundle.sh" in package_script
    assert "bash scripts/create_public_safe_init_annotation_bundle.sh" in dossier_script
    assert "outputs/foundation_5090_public_sprint/best.pt" not in dossier_script


def test_public_mlm_continuation_start_script_uses_isolated_output() -> None:
    script = (
        Path(__file__).parents[1] / "scripts" / "start_public_mlm_continuation_training.sh"
    ).read_text(encoding="utf-8")
    watch_script = (
        Path(__file__).parents[1] / "scripts" / "watch_public_mlm_continuation.sh"
    ).read_text(encoding="utf-8")
    watchdog_script = (
        Path(__file__).parents[1] / "scripts" / "start_public_mlm_continuation_watchdog.sh"
    ).read_text(encoding="utf-8")
    package_watchdog_script = (
        Path(__file__).parents[1]
        / "scripts"
        / "start_public_mlm_continuation_package_watchdog.sh"
    ).read_text(encoding="utf-8")
    config = (
        Path(__file__).parents[1]
        / "configs"
        / "generated"
        / "foundation_5090_mlm_public_expansion_continuation.yaml"
    ).read_text(encoding="utf-8")
    package_script = (
        Path(__file__).parents[1] / "scripts" / "generate_publication_package.sh"
    ).read_text(encoding="utf-8")
    checksum_script = (
        Path(__file__).parents[1] / "scripts" / "write_artifact_checksums.py"
    ).read_text(encoding="utf-8")
    dossier_script = (
        Path(__file__).parents[1] / "scripts" / "write_submission_dossier.py"
    ).read_text(encoding="utf-8")
    status_script = (Path(__file__).parents[1] / "scripts" / "write_status_summary.py").read_text(
        encoding="utf-8"
    )
    health_script = (
        Path(__file__).parents[1] / "scripts" / "write_training_health_audit.py"
    ).read_text(encoding="utf-8")
    report_module = (Path(__file__).parents[1] / "src" / "snowcell" / "report.py").read_text(
        encoding="utf-8"
    )
    curve_script = (
        Path(__file__).parents[1] / "scripts" / "write_training_curve_summary.py"
    ).read_text(encoding="utf-8")

    assert "snowcell_mlm_public_expansion_continuation" in script
    assert "foundation_5090_mlm_public_expansion_continuation.yaml" in script
    assert "foundation_5090_mlm_public_expansion_continuation.resume.yaml" in script
    assert "resume_checkpoint" in script
    assert "init_checkpoint" in script
    assert "write_resume_config" in script
    assert "completed_epochs" in script
    assert "SNOWCELL_MLM_CONTINUATION_FINALIZED_MARKER" in script
    assert "finalized_after_training.stamp" in script
    assert "finalization_needed" in script
    assert "finalize_training_outputs" in script
    assert "bash scripts/run_strict_benchmark_audits.sh || true" in script
    assert "touch '$final_marker'" in script
    assert "outputs/foundation_5090_mlm_public_expansion/epoch_0010.pt" in config
    assert "outputs/foundation_5090_mlm_public_expansion_continuation" in config
    assert "latest_checkpoint_every_updates" in config
    assert "start_public_mlm_continuation_training.sh" in package_script
    assert "watch_public_mlm_continuation.sh" in package_script
    assert "start_public_mlm_continuation_watchdog.sh" in package_script
    assert "start_public_mlm_continuation_package_watchdog.sh" in package_script
    assert "start_public_mlm_continuation_watchdog.sh" in dossier_script
    assert "start_public_mlm_continuation_package_watchdog.sh" in dossier_script
    assert "start_public_mlm_continuation_training.sh" in watch_script
    assert "latest_progress" in watch_script
    assert "snowcell_mlm_public_expansion_continuation_watchdog" in watchdog_script
    assert "watch_public_mlm_continuation.sh" in watchdog_script
    assert "snowcell_publication_package_watchdog_continuation" in package_watchdog_script
    assert "SNOWCELL_PACKAGE_REFRESH_RUN_ID" in package_watchdog_script
    assert "foundation_5090_mlm_public_expansion_continuation" in package_watchdog_script
    assert "configs/generated/*.yaml" in checksum_script
    assert "outputs/foundation_5090_mlm_public_expansion_continuation" in status_script
    assert "foundation_5090_mlm_public_expansion_continuation" in health_script
    assert "outputs/foundation_5090_mlm_public_expansion_continuation" in report_module
    assert "progress_latest.json" in curve_script


def test_training_health_audit_marks_oom_incomplete_run(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_training_health_audit.py"
    spec = importlib.util.spec_from_file_location("write_training_health_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    run_dir = tmp_path / "outputs" / "foundation_5090_mlm_public_late_refresh"
    log_dir = tmp_path / "logs"
    run_dir.mkdir(parents=True)
    log_dir.mkdir()
    (run_dir / "config.resolved.json").write_text("{}", encoding="utf-8")
    (log_dir / "mlm_public_late_refresh_20260724_000532.log").write_text(
        "Device: cuda\nmemory allocation failed with OOM on device 0\n",
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "training_health_audit.md"
    output_json = tmp_path / "outputs" / "publication_package" / "training_health_audit.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    late = next(
        run
        for run in payload["runs"]
        if run["run_id"] == "foundation_5090_mlm_public_late_refresh"
    )

    assert late["status"] == "oom_incomplete"
    assert payload["summary"]["oom_issue_count"] == 1
    assert "memory-safe late refresh config" in output_md.read_text(encoding="utf-8")
    assert "oom_incomplete" in output_json.read_text(encoding="utf-8")


def test_training_health_audit_marks_running_no_epoch_run(tmp_path: Path, monkeypatch) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_training_health_audit.py"
    spec = importlib.util.spec_from_file_location("write_training_health_audit_running", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    run_dir = tmp_path / "outputs" / "foundation_5090_mlm_public_late_refresh_safe"
    log_dir = tmp_path / "logs"
    run_dir.mkdir(parents=True)
    log_dir.mkdir()
    (run_dir / "config.resolved.json").write_text("{}", encoding="utf-8")
    (log_dir / "mlm_public_late_refresh_safe_manual.log").write_text(
        "Device: cuda\n",
        encoding="utf-8",
    )

    def fake_run_command(command, cwd, timeout=10):
        if command[:3] == ["tmux", "has-session", "-t"]:
            return {
                "command": command,
                "returncode": 0 if command[-1] == "=snowcell_mlm_public_late_refresh_safe" else 1,
                "stdout": "",
                "stderr": "",
            }
        if command[:2] == ["pgrep", "-af"] and "late_refresh_safe" in command[-1]:
            return {
                "command": command,
                "returncode": 0,
                "stdout": (
                    "123 .venv/bin/snowcell train --config "
                    "configs/foundation_5090_mlm_public_late_refresh_safe.yaml --device cuda"
                ),
                "stderr": "",
            }
        return {"command": command, "returncode": 1, "stdout": "", "stderr": ""}

    monkeypatch.setattr(module, "run_command", fake_run_command)
    payload = module.build_audit(tmp_path)
    safe = next(
        run
        for run in payload["runs"]
        if run["run_id"] == "foundation_5090_mlm_public_late_refresh_safe"
    )

    assert safe["status"] == "running_no_epoch_yet"
    assert safe["runtime"]["tmux_active"] is True
    assert safe["runtime"]["process_active"] is True
    assert payload["summary"]["running_runs"] >= 1


def test_training_health_audit_detects_generated_resume_process_token(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_training_health_audit.py"
    spec = importlib.util.spec_from_file_location("write_training_health_audit_resume_token", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    def fake_run_command(command, cwd, timeout=10):
        if command[:3] == ["tmux", "has-session", "-t"]:
            return {"command": command, "returncode": 0, "stdout": "", "stderr": ""}
        if command[:2] == ["pgrep", "-af"] and command[-1].endswith(".resume.yaml"):
            return {
                "command": command,
                "returncode": 0,
                "stdout": (
                    "321 .venv/bin/snowcell train --config "
                    "configs/generated/foundation_5090_public_safe_init.resume.yaml --device cuda"
                ),
                "stderr": "",
            }
        return {"command": command, "returncode": 1, "stdout": "", "stderr": ""}

    monkeypatch.setattr(module, "run_command", fake_run_command)
    runtime = module.runtime_summary(
        tmp_path,
        {
            "session": "snowcell_public_safe_init",
            "process_token": "configs/foundation_5090_public_safe_init.yaml",
            "process_tokens": [
                "configs/foundation_5090_public_safe_init.yaml",
                "configs/generated/foundation_5090_public_safe_init.resume.yaml",
            ],
        },
    )

    assert runtime["tmux_active"] is True
    assert runtime["process_active"] is True
    assert runtime["process_probe"]["returncode"] == 0
    assert "foundation_5090_public_safe_init.resume.yaml" in runtime["process_lines"][0]


def test_training_health_audit_counts_running_latest_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_training_health_audit.py"
    spec = importlib.util.spec_from_file_location(
        "write_training_health_audit_running_latest",
        module_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    run_dir = tmp_path / "outputs" / "foundation_5090_mlm_public_late_refresh_safe"
    log_dir = tmp_path / "logs"
    run_dir.mkdir(parents=True)
    log_dir.mkdir()
    (run_dir / "config.resolved.json").write_text("{}", encoding="utf-8")
    (run_dir / "latest.pt").write_bytes(b"checkpoint")
    (log_dir / "mlm_public_late_refresh_safe_manual.log").write_text(
        "Device: cuda\n",
        encoding="utf-8",
    )

    def fake_run_command(command, cwd, timeout=10):
        if command[:3] == ["tmux", "has-session", "-t"]:
            return {
                "command": command,
                "returncode": 0 if command[-1] == "=snowcell_mlm_public_late_refresh_safe" else 1,
                "stdout": "",
                "stderr": "",
            }
        if command[:2] == ["pgrep", "-af"] and "late_refresh_safe" in command[-1]:
            return {
                "command": command,
                "returncode": 0,
                "stdout": (
                    "123 .venv/bin/snowcell train --config "
                    "configs/foundation_5090_mlm_public_late_refresh_safe.yaml --device cuda"
                ),
                "stderr": "",
            }
        return {"command": command, "returncode": 1, "stdout": "", "stderr": ""}

    monkeypatch.setattr(module, "run_command", fake_run_command)
    payload = module.build_audit(tmp_path)
    safe = next(
        run
        for run in payload["runs"]
        if run["run_id"] == "foundation_5090_mlm_public_late_refresh_safe"
    )

    assert safe["status"] == "running_with_checkpoint"
    assert safe["checkpoint"]["kind"] == "latest"
    assert safe["latest_checkpoint"]["exists"] is True
    assert payload["summary"]["checkpoint_runs"] >= 1


def test_modality_compatibility_audit_routes_rna_and_snatac(tmp_path: Path) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_modality_compatibility_audit.py"
    spec = importlib.util.spec_from_file_location("write_modality_compatibility_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    data_dir = tmp_path / "data"
    discovery_dir = data_dir / "public_discovery"
    package_dir = tmp_path / "outputs" / "publication_package"
    discovery_dir.mkdir(parents=True)
    package_dir.mkdir(parents=True)
    public_manifest = data_dir / "public_dataset_manifest.tsv"
    public_manifest.write_text(
        "dataset_id\tspecies\ttissue_or_scope\tdata_type\tpriority\taccession_or_doi\t"
        "source_url\twhy_use\tstatus\n"
        "brassicaceae_regulatory_multiome\tBrassicaceae\troot\tsnATAC/snRNA regulatory atlas\t"
        "B\tGSE332675\thttps://example.org\tregulatory grammar\tdiscovery_candidate\n"
        "arabidopsis_root_atlas\tArabidopsis thaliana\troot\tscRNA\tA\tGSE152766\t"
        "https://example.org\troot annotation\tdownload_candidate\n"
        "rice_soil_stress_root_atlas\tOryza sativa\troot\tscRNA/spatial/bulk\tA\tGSE251706\t"
        "https://example.org\tstress root atlas\tdownload_candidate\n"
        "unsupported_single_cell_report\tMarchantia polymorpha\tspore\tsingle-cell transcriptomics\t"
        "C\tGSE336751\thttps://example.org\tevolutionary outgroup\tdownload_candidate\n",
        encoding="utf-8",
    )
    (discovery_dir / "geo_supplementary_files_20260723_205817.tsv").write_text(
        "dataset_id\taccession\tfilename\tfile_type\tmatrix_like\n"
        "brassicaceae_regulatory_multiome\tGSE332675\tGSE332675_snATAC_root.h5ad\th5ad\tTrue\n",
        encoding="utf-8",
    )
    (discovery_dir / "geo_promotion_download_queue.tsv").write_text(
        "accession\tdataset_id\tspecies\ttissue\ttitle\tfile_type_counts\t"
        "downloader_script\twrapper_script\tqueue_session\tmanifest\tlog_path\tsource_url\n"
        "GSE196882\tgeo_gse196882_zea_mays_spatial_transcriptomics_maize_embryonic_leaves\t"
        "Zea mays\tleaf\tSpatial transcriptomics of maize embryonic leaves\t"
        "archive:2;mtx_archive:1\tdownload_geo_raw_tar_mtx_subset.sh\t"
        "scripts/generated_geo_promotion_downloads/download_gse196882.sh\t"
        "snowcell_geo_promotion_gse196882\tdata/corpus_manifest.gse196882.tsv\t"
        "logs/geo_promotion_gse196882.log\thttps://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE196882\n",
        encoding="utf-8",
    )
    status_summary = package_dir / "status_summary.json"
    status_summary.write_text(
        json.dumps(
            {
                "public_data_targets": [
                    {
                        "dataset_id": "arabidopsis_root_atlas",
                        "stage": "manifest_ready",
                        "manifest": {"rows": 2},
                        "npz_files": {"file_count": 2},
                    },
                    {
                        "dataset_id": "rice_soil_stress_root_atlas",
                        "stage": "manifest_ready",
                        "manifest": {"rows": 1},
                        "npz_files": {"file_count": 1},
                    },
                    {
                        "dataset_id": "unsupported_single_cell_report",
                        "stage": "unsupported_for_matrix_corpus",
                        "manifest": {"rows": 0},
                        "npz_files": {"file_count": 0},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path, status_summary, public_manifest)
    output_md = package_dir / "modality_compatibility_audit.md"
    output_json = package_dir / "modality_compatibility_audit.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)
    routes = {item["dataset_id"]: item["route"] for item in payload["datasets"]}

    assert routes["brassicaceae_regulatory_multiome"] == "regulatory_or_multimodal_holdout"
    assert routes["arabidopsis_root_atlas"] == "rna_expression_corpus"
    assert routes["rice_soil_stress_root_atlas"] == "rna_expression_corpus"
    assert routes["unsupported_single_cell_report"] == "unsupported_for_expression_corpus"
    assert routes["geo_gse196882_zea_mays_spatial_transcriptomics_maize_embryonic_leaves"] == (
        "spatial_expression_pending_download"
    )
    spatial_item = next(
        item
        for item in payload["datasets"]
        if item["dataset_id"] == "geo_gse196882_zea_mays_spatial_transcriptomics_maize_embryonic_leaves"
    )
    assert spatial_item["source_catalog"] == "geo_promotion_download_queue"
    assert spatial_item["annotation_training_role"] == "expression_pretraining_or_spatial_validation_only"
    assert "supervised cell-type annotation" in spatial_item["claim_guardrail"]
    unsupported_item = next(
        item for item in payload["datasets"] if item["dataset_id"] == "unsupported_single_cell_report"
    )
    assert unsupported_item["source_catalog"] == "public_dataset_manifest"
    assert unsupported_item["annotation_training_role"] == "unsupported_for_expression_corpus"
    assert payload["summary"]["holdout_count"] == 1
    assert payload["summary"]["spatial_expression_context_count"] == 1
    assert payload["summary"]["promotion_candidate_count"] == 1
    assert "brassicaceae_regulatory_multiome" in output_md.read_text(encoding="utf-8")
    assert "rna_expression_corpus" in output_json.read_text(encoding="utf-8")


def load_download_progress_audit_module():
    module_path = Path(__file__).parents[1] / "scripts" / "write_download_progress_audit.py"
    spec = importlib.util.spec_from_file_location("write_download_progress_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.tmux_sessions = lambda: set()
    return module


def test_download_progress_audit_marks_partial_download(tmp_path: Path) -> None:
    module = load_download_progress_audit_module()
    raw_dir = tmp_path / "data" / "public" / "GSE270140_raw_tar"
    raw_dir.mkdir(parents=True)
    (raw_dir / "GSE270140_RAW.tar").write_bytes(b"partial payload")
    (raw_dir / "GSE270140_RAW.tar.aria2").write_text("aria2 control", encoding="utf-8")
    status_path = tmp_path / "outputs" / "publication_package" / "status_summary.json"
    status_path.parent.mkdir(parents=True)
    status_path.write_text(
        json.dumps(
            {
                "public_data_targets": [
                    {
                        "dataset_id": "arabidopsis_secondary_root_dev_atlas",
                        "stage": "downloading_or_raw_ready",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path, status_path)
    target = next(
        item
        for item in payload["targets"]
        if item["dataset_id"] == "arabidopsis_secondary_root_dev_atlas"
    )
    output_md = tmp_path / "outputs" / "publication_package" / "download_progress_audit.md"
    output_json = tmp_path / "outputs" / "publication_package" / "download_progress_audit.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    assert target["download_status"] == "downloading_partial"
    assert target["partial_file_count"] == 1
    assert target["raw_files"]["largest_file"]["bytes"] == len(b"partial payload")
    assert target["status_summary_stage"] == "downloading_or_raw_ready"
    assert payload["summary"]["downloading_partial_count"] == 1
    assert "GSE270140_RAW.tar.aria2" in output_md.read_text(encoding="utf-8")
    assert "downloading_partial" in output_json.read_text(encoding="utf-8")


def test_download_progress_audit_marks_manifest_complete(tmp_path: Path) -> None:
    module = load_download_progress_audit_module()
    data_dir = tmp_path / "data"
    npz_dir = data_dir / "public" / "GSE243419_npz"
    npz_dir.mkdir(parents=True)
    (npz_dir / "GSE243419_mtx_extracted.npz").write_bytes(b"npz")
    (data_dir / "corpus_manifest.gse243419.tsv").write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/GSE243419_npz/GSE243419_mtx_extracted.npz\t"
        "cotton_glandular_terpenoid_atlas\tGossypium hirsutum\n",
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)
    target = next(
        item
        for item in payload["targets"]
        if item["dataset_id"] == "cotton_glandular_terpenoid_atlas"
    )

    assert target["download_status"] == "complete_manifest"
    assert target["manifest_rows"] == 1
    assert target["npz_files"]["file_count"] == 1
    assert payload["summary"]["complete_manifest_count"] == 1


def test_download_progress_audit_marks_unsupported_matrix_corpus(tmp_path: Path) -> None:
    module = load_download_progress_audit_module()
    raw_dir = tmp_path / "data" / "public" / "GSE336751_raw_tar"
    raw_dir.mkdir(parents=True)
    (raw_dir / "GSE336751_RAW.tar").write_bytes(b"raw")
    (raw_dir / "unsupported_single_cell_matrix.json").write_text(
        json.dumps(
            {
                "accession": "GSE336751",
                "status": "unsupported_for_single_cell_matrix_corpus",
                "reason": "No Matrix Market/10x matrix files were found.",
            }
        ),
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)
    target = next(
        item
        for item in payload["targets"]
        if item["dataset_id"] == "marchantia_spore_asymmetry_single_cell"
    )
    output_md = tmp_path / "outputs" / "publication_package" / "download_progress_audit.md"
    module.write_markdown(payload, output_md)

    assert target["download_status"] == "unsupported_for_matrix_corpus"
    assert target["raw_files"]["unsupported_report_count"] == 1
    assert payload["summary"]["unsupported_for_matrix_corpus_count"] == 1
    assert "unsupported_for_matrix_corpus" in output_md.read_text(encoding="utf-8")


def test_download_progress_audit_includes_dynamic_gse_manifests(tmp_path: Path) -> None:
    module = load_download_progress_audit_module()
    data_dir = tmp_path / "data"
    complete_npz_dir = data_dir / "public" / "GSE273722_npz"
    complete_raw_dir = data_dir / "public" / "GSE273722_raw_tar"
    unsupported_raw_dir = data_dir / "public" / "GSE255880_raw_tar"
    complete_npz_dir.mkdir(parents=True)
    complete_raw_dir.mkdir(parents=True)
    unsupported_raw_dir.mkdir(parents=True)
    (complete_raw_dir / "GSE273722_RAW.tar").write_bytes(b"raw")
    (complete_raw_dir / "GSE273722_RAW.tar.aria2").write_text(
        "residual control",
        encoding="utf-8",
    )
    (complete_npz_dir / "GSE273722_mtx_extracted.npz").write_bytes(b"npz")
    (data_dir / "corpus_manifest.gse273722.tsv").write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/GSE273722_npz/GSE273722_mtx_extracted.npz\t"
        "geo_gse273722_camellia_sinensis_roots\tCamellia sinensis\n",
        encoding="utf-8",
    )
    (data_dir / "corpus_manifest.gse255880.tsv").write_text(
        "path\tdataset_id\tspecies\n",
        encoding="utf-8",
    )
    (unsupported_raw_dir / "unsupported_single_cell_matrix.json").write_text(
        json.dumps(
            {
                "accession": "GSE255880",
                "status": "unsupported_for_single_cell_matrix_corpus",
            }
        ),
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)
    by_id = {item["dataset_id"]: item for item in payload["targets"]}
    complete = by_id["geo_gse273722_camellia_sinensis_roots"]
    unsupported = by_id["geo_gse255880"]
    output_md = tmp_path / "outputs" / "publication_package" / "download_progress_audit.md"
    module.write_markdown(payload, output_md)

    assert complete["source"] == "dynamic_gse_manifest"
    assert complete["download_status"] == "complete_manifest"
    assert complete["manifest_rows"] == 1
    assert complete["raw_files"]["file_count"] == 1
    assert complete["npz_files"]["file_count"] == 1
    assert complete["active_partial_file_count"] == 0
    assert complete["residual_partial_file_count"] == 1
    assert unsupported["download_status"] == "unsupported_for_matrix_corpus"
    assert unsupported["raw_files"]["unsupported_report_count"] == 1
    assert payload["summary"]["active_partial_file_count"] == 0
    assert payload["summary"]["residual_partial_file_count"] == 1
    assert "geo_gse273722_camellia_sinensis_roots" in output_md.read_text(
        encoding="utf-8"
    )


def test_download_progress_audit_includes_geo_promotion_queue_targets(
    tmp_path: Path,
) -> None:
    module = load_download_progress_audit_module()
    data_dir = tmp_path / "data"
    discovery_dir = data_dir / "public_discovery"
    raw_dir = data_dir / "public" / "GSE273033_raw_tar"
    discovery_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    (raw_dir / "GSE273033_RAW.tar").write_bytes(b"partial payload")
    (raw_dir / "GSE273033_RAW.tar.aria2").write_text(
        "aria2 control",
        encoding="utf-8",
    )
    (discovery_dir / "geo_promotion_download_queue.tsv").write_text(
        "accession\tdataset_id\tspecies\ttissue\ttitle\tfile_type_counts\t"
        "downloader_script\twrapper_script\tqueue_session\tmanifest\tlog_path\t"
        "source_url\n"
        "GSE273033\tgeo_gse273033_arabidopsis_leaf_drought\tArabidopsis thaliana\t"
        "leaf\tDrought leaf atlas\tmtx_archive:1\t"
        "download_geo_raw_tar_mtx_subset.sh\tscripts/generated/download_gse273033.sh\t"
        "snowcell_geo_promotion_gse273033\tdata/corpus_manifest.gse273033.tsv\t"
        "logs/geo_promotion_gse273033.log\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE273033\n"
        "GSE235494\tgeo_gse235494_arabidopsis_root_multiome\tArabidopsis thaliana\t"
        "root\tRoot multiome\tmtx_archive:1\t"
        "download_geo_raw_tar_mtx_subset.sh\tscripts/generated/download_gse235494.sh\t"
        "snowcell_geo_promotion_gse235494\tdata/corpus_manifest.gse235494.tsv\t"
        "logs/geo_promotion_gse235494.log\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE235494\n",
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)
    by_id = {item["dataset_id"]: item for item in payload["targets"]}
    running = by_id["geo_gse273033_arabidopsis_leaf_drought"]
    queued = by_id["geo_gse235494_arabidopsis_root_multiome"]
    output_md = tmp_path / "outputs" / "publication_package" / "download_progress_audit.md"
    module.write_markdown(payload, output_md)

    assert running["source"] == "geo_promotion_queue"
    assert running["download_status"] == "downloading_partial"
    assert running["partial_file_count"] == 1
    assert running["active_partial_file_count"] == 1
    assert running["residual_partial_file_count"] == 0
    assert running["queue_session"] == "snowcell_geo_promotion_gse273033"
    assert queued["download_status"] == "queued_pending_download"
    assert payload["summary"]["downloading_partial_count"] == 1
    assert payload["summary"]["status_counts"]["queued_pending_download"] == 1
    assert payload["summary"]["active_partial_file_count"] == 1
    assert payload["summary"]["residual_partial_file_count"] == 0
    assert "geo_gse273033_arabidopsis_leaf_drought" in output_md.read_text(
        encoding="utf-8"
    )


def test_download_progress_audit_tracks_geo_mtx_component_partials(
    tmp_path: Path,
) -> None:
    module = load_download_progress_audit_module()
    data_dir = tmp_path / "data"
    discovery_dir = data_dir / "public_discovery"
    component_dir = data_dir / "public" / "GSE201931_mtx_components"
    discovery_dir.mkdir(parents=True)
    component_dir.mkdir(parents=True)
    (component_dir / "GSE201931_matrix.mtx.gz").write_bytes(b"partial matrix")
    (component_dir / "GSE201931_matrix.mtx.gz.aria2").write_text(
        "aria2 control",
        encoding="utf-8",
    )
    (component_dir / "GSE201931_features.tsv.gz").write_bytes(b"features")
    (discovery_dir / "geo_promotion_download_queue.tsv").write_text(
        "accession\tdataset_id\tspecies\ttissue\ttitle\tfile_type_counts\t"
        "downloader_script\twrapper_script\tqueue_session\tmanifest\tlog_path\t"
        "source_url\n"
        "GSE201931\tgeo_gse201931_tomato_scrna\tSolanum lycopersicum\tleaf\t"
        "Tomato single-cell transcriptome\tmtx_component:3\t"
        "download_geo_mtx_component_subset.sh\tscripts/generated/download_gse201931.sh\t"
        "snowcell_geo_promotion_gse201931\tdata/corpus_manifest.gse201931.tsv\t"
        "logs/geo_promotion_gse201931.log\t"
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE201931\n",
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)
    target = next(
        item
        for item in payload["targets"]
        if item["dataset_id"] == "geo_gse201931_tomato_scrna"
    )
    output_md = tmp_path / "outputs" / "publication_package" / "download_progress_audit.md"
    module.write_markdown(payload, output_md)

    assert target["download_status"] == "downloading_partial"
    assert target["partial_file_count"] == 1
    assert target["active_partial_file_count"] == 1
    assert target["raw_files"]["file_count"] == 2
    assert target["raw_files"]["largest_file"]["bytes"] == len(b"partial matrix")
    assert "GSE201931_matrix.mtx.gz.aria2" in output_md.read_text(encoding="utf-8")


def test_download_progress_audit_tracks_unlisted_active_geo_promotion(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_download_progress_audit_module()
    raw_dir = tmp_path / "data" / "public" / "GSE201640_raw_tar"
    raw_dir.mkdir(parents=True)
    (raw_dir / "GSE201640_RAW.tar").write_bytes(b"partial payload")
    (raw_dir / "GSE201640_RAW.tar.aria2").write_text(
        "aria2 control",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "tmux_sessions",
        lambda: {"snowcell_geo_promotion_gse201640"},
    )

    payload = module.build_audit(tmp_path)
    target = next(
        item
        for item in payload["targets"]
        if item["dataset_id"] == "geo_gse201640_active_promotion"
    )
    output_md = tmp_path / "outputs" / "publication_package" / "download_progress_audit.md"
    module.write_markdown(payload, output_md)
    markdown = output_md.read_text(encoding="utf-8")

    assert target["source"] == "active_untracked_geo_promotion"
    assert target["download_status"] == "downloading_partial"
    assert target["partial_file_count"] == 1
    assert target["active_partial_file_count"] == 1
    assert target["residual_partial_file_count"] == 0
    assert target["queue_session"] == "snowcell_geo_promotion_gse201640"
    assert target["accession"] == "GSE201640"
    assert payload["summary"]["downloading_partial_count"] == 1
    assert payload["summary"]["active_partial_file_count"] == 1
    assert "geo_gse201640_active_promotion" in markdown
    assert "snowcell_geo_promotion_gse201640" in markdown
    assert "GSE201640_RAW.tar.aria2" in markdown


def test_geo_promotion_queue_health_audit_marks_waiting_for_reviewed_queue(
    tmp_path: Path, monkeypatch
) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_geo_promotion_queue_health_audit.py"
    spec = importlib.util.spec_from_file_location("write_geo_promotion_queue_health_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    generated_dir = tmp_path / "scripts" / "generated_geo_promotion_downloads"
    generated_dir.mkdir(parents=True)
    (tmp_path / "scripts" / "queue_reviewed_geo_downloads.sh").write_text(
        'jobs=(\n'
        '  "snowcell_gse325371|data/corpus_manifest.gse325371.tsv|bash reviewed.sh|logs/gse325371.log"\n'
        ')\n',
        encoding="utf-8",
    )
    (generated_dir / "queue_geo_promotion_downloads.sh").write_text(
        'jobs=(\n'
        '  "snowcell_geo_promotion_gse196882|data/corpus_manifest.gse196882.tsv|'
        'bash scripts/generated_geo_promotion_downloads/download_gse196882.sh|'
        'logs/geo_promotion_gse196882.log"\n'
        '  "snowcell_geo_promotion_gse303996|data/corpus_manifest.gse303996.tsv|'
        'bash scripts/generated_geo_promotion_downloads/download_gse303996.sh|'
        'logs/geo_promotion_gse303996.log"\n'
        '  "snowcell_geo_promotion_gse273033|data/corpus_manifest.gse273033.tsv|'
        'bash scripts/generated_geo_promotion_downloads/download_gse273033.sh|'
        'logs/geo_promotion_gse273033.log"\n'
        ')\n',
        encoding="utf-8",
    )
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "data" / "corpus_manifest.gse303996.tsv").write_text(
        "path\tdataset_id\tspecies\n"
        "data/public/GSE303996_npz/GSE303996_mtx_extracted.npz\t"
        "geo_gse303996_arabidopsis_root_regeneration\tArabidopsis thaliana\n",
        encoding="utf-8",
    )
    raw_dir = tmp_path / "data" / "public" / "GSE325371_raw_tar"
    residual_dir = tmp_path / "data" / "public" / "GSE303996_raw_tar"
    unsupported_dir = tmp_path / "data" / "public" / "GSE273033_raw_tar"
    raw_dir.mkdir(parents=True)
    residual_dir.mkdir(parents=True)
    unsupported_dir.mkdir(parents=True)
    (raw_dir / "GSE325371_RAW.tar.aria2").write_text("partial", encoding="utf-8")
    (residual_dir / "GSE303996_RAW.tar.aria2").write_text(
        "residual",
        encoding="utf-8",
    )
    (unsupported_dir / "unsupported_single_cell_matrix.json").write_text(
        json.dumps({"accession": "GSE273033", "reason": "no matrix payload"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "tmux_sessions",
        lambda: {
            "snowcell_geo_promotion_download_queue",
            "snowcell_geo_promotion_gse201640",
            "snowcell_geo_promotion_gse273033",
        },
    )
    untracked_dir = tmp_path / "data" / "public" / "GSE201640_raw_tar"
    untracked_dir.mkdir(parents=True)
    (untracked_dir / "GSE201640_RAW.tar").write_bytes(b"partial")
    (untracked_dir / "GSE201640_RAW.tar.aria2").write_text(
        "aria2 control",
        encoding="utf-8",
    )

    payload = module.build_audit(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "geo_promotion_queue_health_audit.md"
    output_json = tmp_path / "outputs" / "publication_package" / "geo_promotion_queue_health_audit.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    assert payload["summary"]["queue_supervisor_active"] is True
    assert payload["summary"]["reviewed_pending_count"] == 1
    assert payload["summary"]["waiting_for_reviewed_queue_count"] == 1
    assert payload["summary"]["active_partial_file_count"] == 1
    assert payload["summary"]["residual_partial_file_count"] == 1
    assert payload["summary"]["unmanaged_active_promotion_count"] == 1
    assert payload["summary"]["unmanaged_running_promotion_count"] == 1
    assert payload["summary"]["running_count"] == 1
    assert payload["jobs"][0]["status"] == "waiting_for_reviewed_queue"
    complete_job = next(item for item in payload["jobs"] if item["accession"] == "GSE303996")
    assert complete_job["status"] == "complete_manifest"
    assert complete_job["active_partial_file_count"] == 0
    assert complete_job["residual_partial_file_count"] == 1
    unsupported_job = next(item for item in payload["jobs"] if item["accession"] == "GSE273033")
    assert unsupported_job["status"] == "unsupported_expression_corpus"
    assert unsupported_job["active_session"] is True
    assert unsupported_job["unsupported_report_count"] == 1
    assert payload["summary"]["status_counts"]["unsupported_expression_corpus"] == 1
    assert payload["summary"]["tracked_running_count"] == 0
    assert "GSE325371" in payload["summary"]["reviewed_pending_accessions"]
    assert "snowcell_geo_promotion_gse201640" in output_md.read_text(encoding="utf-8")
    assert "waiting_for_reviewed_queue" in output_md.read_text(encoding="utf-8")
    assert "snowcell_geo_promotion_gse196882" in output_json.read_text(encoding="utf-8")


def test_geo_promotion_queue_health_audit_tracks_component_partials(
    tmp_path: Path, monkeypatch
) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_geo_promotion_queue_health_audit.py"
    spec = importlib.util.spec_from_file_location("write_geo_promotion_queue_health_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    generated_dir = tmp_path / "scripts" / "generated_geo_promotion_downloads"
    generated_dir.mkdir(parents=True)
    (tmp_path / "scripts" / "queue_reviewed_geo_downloads.sh").write_text(
        "jobs=()\n",
        encoding="utf-8",
    )
    (generated_dir / "queue_geo_promotion_downloads.sh").write_text(
        'jobs=(\n'
        '  "snowcell_geo_promotion_gse201931|data/corpus_manifest.gse201931.tsv|'
        'bash scripts/generated_geo_promotion_downloads/download_gse201931.sh|'
        'logs/geo_promotion_gse201931.log"\n'
        ')\n',
        encoding="utf-8",
    )
    component_dir = tmp_path / "data" / "public" / "GSE201931_mtx_components"
    component_dir.mkdir(parents=True)
    (component_dir / "GSE201931_matrix.mtx.gz").write_bytes(b"partial matrix")
    (component_dir / "GSE201931_matrix.mtx.gz.aria2").write_text(
        "aria2 control",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "tmux_sessions",
        lambda: {"snowcell_geo_promotion_download_queue", "snowcell_geo_promotion_gse201931"},
    )

    payload = module.build_audit(tmp_path)
    output_md = tmp_path / "outputs" / "publication_package" / "geo_promotion_queue_health_audit.md"
    module.write_markdown(payload, output_md)
    job = payload["jobs"][0]

    assert job["status"] == "running"
    assert job["active_partial_file_count"] == 1
    assert job["residual_partial_file_count"] == 0
    assert payload["summary"]["active_partial_file_count"] == 1
    assert "Active partial control files" in output_md.read_text(encoding="utf-8")


def test_transfer_queue_health_audit_classifies_running_and_unsupported_jobs(
    tmp_path: Path, monkeypatch
) -> None:
    module_path = Path(__file__).parents[1] / "scripts" / "write_transfer_queue_health_audit.py"
    spec = importlib.util.spec_from_file_location("write_transfer_queue_health_audit", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    scripts_dir = tmp_path / "scripts"
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "public" / "GSE308757_raw_tar"
    active_unsupported_dir = data_dir / "public" / "GSE325371_raw_tar"
    unsupported_dir = data_dir / "public" / "GSE336751_raw_tar"
    scripts_dir.mkdir(parents=True)
    data_dir.mkdir()
    raw_dir.mkdir(parents=True)
    active_unsupported_dir.mkdir(parents=True)
    unsupported_dir.mkdir(parents=True)
    (scripts_dir / "queue_reviewed_geo_downloads.sh").write_text(
        'jobs=(\n'
        '  "snowcell_gse226097|data/corpus_manifest.gse226097.tsv|bash done.sh|logs/done.log"\n'
        '  "snowcell_gse308757|data/corpus_manifest.gse308757.tsv|bash running.sh|logs/running.log"\n'
        '  "snowcell_gse325371|data/corpus_manifest.gse325371.tsv|bash active_unsupported.sh|logs/active_unsupported.log"\n'
        '  "snowcell_gse336751|data/corpus_manifest.gse336751.tsv|bash unsupported.sh|logs/unsupported.log"\n'
        ')\n',
        encoding="utf-8",
    )
    (data_dir / "corpus_manifest.gse226097.tsv").write_text(
        "path\tdataset_id\tspecies\nx\tarabidopsis_lifecycle_spatial_atlas\tArabidopsis thaliana\n",
        encoding="utf-8",
    )
    (data_dir / "corpus_manifest.gse308757.tsv").write_text(
        "path\tdataset_id\tspecies\n",
        encoding="utf-8",
    )
    partial_payload = raw_dir / "GSE308757_RAW.tar"
    partial_control = raw_dir / "GSE308757_RAW.tar.aria2"
    partial_payload.write_bytes(b"partial")
    partial_control.write_text("control", encoding="utf-8")
    os.utime(partial_payload, (1, 1))
    os.utime(partial_control, (1, 1))
    (data_dir / "corpus_manifest.gse325371.tsv").write_text(
        "path\tdataset_id\tspecies\n",
        encoding="utf-8",
    )
    (active_unsupported_dir / "GSE325371_RAW.tar").write_bytes(b"active partial")
    (active_unsupported_dir / "GSE325371_RAW.tar.aria2").write_text(
        "control",
        encoding="utf-8",
    )
    (active_unsupported_dir / "unsupported_single_cell_matrix.json").write_text(
        json.dumps({"dataset_id": "tomato_salt_idioblast_atlas"}),
        encoding="utf-8",
    )
    (data_dir / "corpus_manifest.gse336751.tsv").write_text(
        "path\tdataset_id\tspecies\n",
        encoding="utf-8",
    )
    (unsupported_dir / "unsupported_single_cell_matrix.json").write_text(
        json.dumps({"dataset_id": "marchantia_spore_asymmetry_single_cell"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "tmux_sessions",
        lambda: {"snowcell_gse308757", "snowcell_gse325371"},
    )

    payload = module.build_audit(tmp_path)
    by_accession = {item["accession"]: item for item in payload["jobs"]}
    output_md = tmp_path / "outputs" / "publication_package" / "transfer_queue_health_audit.md"
    output_json = tmp_path / "outputs" / "publication_package" / "transfer_queue_health_audit.json"
    module.write_markdown(payload, output_md)
    module.write_json(payload, output_json)

    assert by_accession["GSE226097"]["status"] == "complete_manifest"
    assert by_accession["GSE308757"]["status"] == "running_partial_download"
    assert by_accession["GSE308757"]["stale_partial"] is True
    assert by_accession["GSE308757"]["transfer_files"]["latest_transfer_age_seconds"] > 1800
    assert by_accession["GSE308757"]["transfer_files"]["payload_bytes_are_provisional"] is True
    assert by_accession["GSE325371"]["status"] == "running_partial_download"
    assert by_accession["GSE325371"]["unsupported_report_count"] == 1
    assert by_accession["GSE325371"]["active_session"] is True
    assert by_accession["GSE325371"]["transfer_files"]["payload_bytes_are_provisional"] is True
    assert by_accession["GSE336751"]["status"] == "unsupported_expression_corpus"
    assert by_accession["GSE336751"]["transfer_files"]["payload_bytes_are_provisional"] is False
    assert payload["summary"]["complete_manifest_count"] == 1
    assert payload["summary"]["running_count"] == 2
    assert payload["summary"]["stale_partial_count"] == 1
    assert payload["summary"]["provisional_payload_count"] == 2
    assert payload["summary"]["provisional_payload_bytes"] > 0
    assert payload["summary"]["unsupported_expression_corpus_count"] == 1
    assert "running_partial_download" in output_md.read_text(encoding="utf-8")
    assert "Stale partial downloads" in output_md.read_text(encoding="utf-8")
    assert "Provisional payload byte jobs" in output_md.read_text(encoding="utf-8")
    assert "unsupported_expression_corpus" in output_json.read_text(encoding="utf-8")
