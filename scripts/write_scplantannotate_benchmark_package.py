from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MISSING_LABELS = {"", "unknown", "unknow", "unannotated", "na", "nan", "none"}
DEFAULT_OUTPUT_DIR = Path("outputs/external_benchmarks/scplantannotate_public_sprint_input")


def normalize_text(value: Any) -> str:
    return str(value).strip()


def normalize_species(value: Any) -> str:
    return normalize_text(value).replace("_", " ").lower()


def eligible_obs(
    obs: pd.DataFrame,
    *,
    species: str,
    label_key: str,
    species_key: str,
) -> pd.DataFrame:
    if label_key not in obs:
        raise KeyError(f"missing label column: {label_key}")
    if species_key not in obs:
        raise KeyError(f"missing species column: {species_key}")
    labels = obs[label_key].map(normalize_text)
    species_values = obs[species_key].map(normalize_species)
    mask = labels.str.lower().map(lambda value: value not in MISSING_LABELS)
    if species:
        mask &= species_values == normalize_species(species)
    return obs.loc[mask].copy()


def stratified_positions(
    obs: pd.DataFrame,
    *,
    label_key: str,
    max_cells: int,
    seed: int,
) -> list[int]:
    if max_cells <= 0 or len(obs) <= max_cells:
        return list(range(len(obs)))
    rng = np.random.default_rng(seed)
    label_to_positions: dict[str, list[int]] = {}
    for position, label in enumerate(obs[label_key].map(normalize_text)):
        label_to_positions.setdefault(label, []).append(position)
    for positions in label_to_positions.values():
        rng.shuffle(positions)
    selected: list[int] = []
    labels = sorted(label_to_positions)
    while len(selected) < max_cells and labels:
        next_labels: list[str] = []
        for label in labels:
            positions = label_to_positions[label]
            if positions and len(selected) < max_cells:
                selected.append(positions.pop())
            if positions:
                next_labels.append(label)
        labels = next_labels
    return sorted(selected)


def truth_frame(
    obs: pd.DataFrame,
    *,
    label_key: str,
    coarse_label_key: str,
    cell_id_key: str,
) -> pd.DataFrame:
    if cell_id_key and cell_id_key in obs:
        cell_ids = obs[cell_id_key].map(normalize_text).to_numpy()
    else:
        cell_ids = obs.index.astype(str).to_numpy()
    columns = {
        "cell_id": cell_ids,
        "cell_type": obs[label_key].map(normalize_text).to_numpy(),
    }
    optional = {
        "cell_type_coarse": coarse_label_key,
        "species": "species",
        "tissue": "tissue",
        "sample_id": "sample_id",
        "batch": "batch",
    }
    for output_column, source_column in optional.items():
        if source_column in obs:
            columns[output_column] = obs[source_column].map(normalize_text).to_numpy()
    return pd.DataFrame(columns)


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    commands = payload["commands"]
    lines = [
        "# scPlantAnnotate Benchmark Input Package",
        "",
        f"- Status: `{summary['status']}`",
        f"- Counts as completed metric: `{summary['counts_as_completed_metric']}`",
        f"- Input h5ad: `{summary['input_h5ad']}`",
        f"- Truth CSV: `{summary['truth_csv']}`",
        f"- Selected cells: `{summary['selected_cells']}`",
        f"- Class count: `{summary['class_count']}`",
        f"- Species: `{summary['species']}`",
        f"- Label key: `{summary['label_key']}`",
        "",
        "## Reproducible Commands",
        "",
        "Authorized web/API submission:",
        "",
        f"```bash\n{commands['authorized_submit_and_wait']}\n```",
        "",
        "Author or web-exported predictions to metrics:",
        "",
        f"```bash\n{commands['author_or_web_export_to_metric']}\n```",
        "",
        "## Label Distribution",
        "",
        "| Label | Cells |",
        "| --- | ---: |",
    ]
    for label, count in payload["label_counts"][:40]:
        lines.append(f"| `{label}` | {count} |")
    lines.extend(
        [
            "",
            "This package is an input/readiness artifact only. It is intentionally excluded "
            "from completed external metric counts until scPlantAnnotate predictions are "
            "exported and scored against the truth CSV.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def write_readme(payload: dict[str, Any], output: Path) -> Path:
    return write_markdown(payload, output)


def build_package(
    *,
    project_dir: Path,
    input_h5ad: Path,
    output_dir: Path,
    species: str,
    label_key: str,
    coarse_label_key: str,
    species_key: str,
    cell_id_key: str,
    max_cells: int,
    seed: int,
    dataset_name: str,
    organism_id: str,
    predictor_id: str,
) -> dict[str, Any]:
    try:
        import anndata as ad
    except ImportError as exc:  # pragma: no cover - exercised on servers with anndata installed
        raise SystemExit("anndata is required to write the scPlantAnnotate h5ad package") from exc

    root_input = input_h5ad if input_h5ad.is_absolute() else project_dir / input_h5ad
    root_output = output_dir if output_dir.is_absolute() else project_dir / output_dir
    root_output.mkdir(parents=True, exist_ok=True)

    adata = ad.read_h5ad(root_input)
    eligible = eligible_obs(
        adata.obs,
        species=species,
        label_key=label_key,
        species_key=species_key,
    )
    if eligible.empty:
        raise ValueError(f"no eligible labelled cells found in {root_input}")
    positions = stratified_positions(eligible, label_key=label_key, max_cells=max_cells, seed=seed)
    selected_obs_names = eligible.index[positions]
    subset = adata[selected_obs_names].copy()
    subset.obs["cell_id"] = subset.obs.index.astype(str)

    input_output = root_output / "scplantannotate_input.h5ad"
    truth_output = root_output / "truth_labels.csv"
    summary_output = root_output / "summary.json"
    readme_output = root_output / "README.md"
    subset.write_h5ad(input_output)
    truth = truth_frame(
        subset.obs,
        label_key=label_key,
        coarse_label_key=coarse_label_key,
        cell_id_key="cell_id",
    )
    truth.to_csv(truth_output, index=False)

    label_counts = Counter(truth["cell_type"].map(normalize_text))
    metrics_output = Path("outputs/external_benchmarks/scplantannotate_final_metrics.json")
    plan_output = Path("outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json")
    summary = {
        "status": "input_ready_waiting_for_authorized_scplantannotate_run",
        "counts_as_completed_metric": False,
        "input_h5ad": display_path(input_output, project_dir),
        "truth_csv": display_path(truth_output, project_dir),
        "selected_cells": int(subset.n_obs),
        "retained_genes": int(subset.n_vars),
        "class_count": len(label_counts),
        "species": species,
        "label_key": label_key,
        "coarse_label_key": coarse_label_key,
        "source_h5ad": str(root_input),
        "dataset_name": dataset_name,
        "organism_id": organism_id,
        "predictor_id": predictor_id,
    }
    commands = {
        "authorized_submit_and_wait": (
            "SCPLANTANNOTATE_USERNAME=<user> SCPLANTANNOTATE_PASSWORD=<password> "
            "python scripts/run_scplantannotate_authenticated_benchmark.py "
            f"--input-h5ad {summary['input_h5ad']} "
            f"--dataset-name {dataset_name} "
            f"--organism-id {organism_id} --predictor-id {predictor_id} "
            f"--execute --wait --output {plan_output.as_posix()}"
        ),
        "author_or_web_export_to_metric": (
            "python scripts/run_scplantannotate_authenticated_benchmark.py "
            "--prediction-csv <scplantannotate_predictions.csv> "
            f"--truth-csv {summary['truth_csv']} "
            f"--metrics-output {metrics_output.as_posix()} "
            f"--output {plan_output.as_posix()}"
        ),
    }
    payload = {
        "summary": summary,
        "label_counts": sorted(label_counts.items(), key=lambda item: (-item[1], item[0])),
        "commands": commands,
    }
    write_json(payload, summary_output)
    write_readme(payload, readme_output)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a scPlantAnnotate benchmark input package.")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--input-h5ad", default=Path("data/plant_foundation_corpus.h5ad"), type=Path)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    parser.add_argument("--species", default="Arabidopsis thaliana")
    parser.add_argument("--label-key", default="cell_type")
    parser.add_argument("--coarse-label-key", default="cell_type_coarse")
    parser.add_argument("--species-key", default="species")
    parser.add_argument("--cell-id-key", default="cell_id")
    parser.add_argument("--max-cells", default=5000, type=int)
    parser.add_argument("--seed", default=20260725, type=int)
    parser.add_argument("--dataset-name", default="snowcell_public_sprint_scplantannotate_probe")
    parser.add_argument("--organism-id", default="1")
    parser.add_argument("--predictor-id", default="1")
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()

    payload = build_package(
        project_dir=args.project_dir,
        input_h5ad=args.input_h5ad,
        output_dir=args.output_dir,
        species=args.species,
        label_key=args.label_key,
        coarse_label_key=args.coarse_label_key,
        species_key=args.species_key,
        cell_id_key=args.cell_id_key,
        max_cells=args.max_cells,
        seed=args.seed,
        dataset_name=args.dataset_name,
        organism_id=args.organism_id,
        predictor_id=args.predictor_id,
    )
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
