from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def clean(value: str) -> str:
    return " ".join((value or "").strip().split())


def canonical_species(value: str) -> str:
    value = clean(value).replace("_", " ")
    return " ".join(value.split())


def slug(value: str) -> str:
    chars = []
    for char in clean(value).lower():
        chars.append(char if char.isalnum() else "_")
    return "".join(chars).strip("_") or "unknown_plant"


def manifest_files(root: Path) -> list[Path]:
    paths = sorted((root / "data").glob("corpus_manifest*.tsv"))
    return [path for path in paths if path.is_file() and ".template." not in path.name]


def select_rows(root: Path) -> tuple[list[dict[str, str]], str]:
    preferred = root / "data" / "corpus_manifest_public_mlm_plus_latest.tsv"
    if not preferred.exists():
        preferred = root / "data" / "corpus_manifest_public_mlm.tsv"
    rows = read_tsv(preferred)
    if rows:
        return rows, preferred.relative_to(root).as_posix()

    merged: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for path in manifest_files(root):
        for row in read_tsv(path):
            key = (
                clean(row.get("path", "")),
                clean(row.get("dataset_id", "")),
                clean(row.get("species", "")),
                clean(row.get("tissue", "")),
            )
            if key[0] and key[1]:
                merged[key] = row
    return list(merged.values()), "union(corpus_manifest*.tsv)"


def species_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_species: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"species": "", "manifest_rows": 0, "datasets": set(), "tissues": set()}
    )
    for row in rows:
        raw_species = clean(row.get("species", "")) or "unspecified"
        species = canonical_species(raw_species)
        key = species.lower()
        item = by_species[key]
        item["species"] = species
        item["manifest_rows"] += 1
        dataset_id = clean(row.get("dataset_id", ""))
        tissue = clean(row.get("tissue", ""))
        if dataset_id:
            item["datasets"].add(dataset_id)
        if tissue:
            item["tissues"].add(tissue)
    output = []
    for item in by_species.values():
        output.append(
            {
                "species": item["species"],
                "datasets": len(item["datasets"]),
                "manifest_rows": item["manifest_rows"],
                "tissues": sorted(item["tissues"]),
            }
        )
    return sorted(output, key=lambda item: (-item["datasets"], -item["manifest_rows"], item["species"]))


def collect_catalog_species(root: Path, selected_species: list[dict[str, Any]]) -> list[str]:
    values = {item["species"] for item in selected_species}
    for row in read_tsv(root / "data" / "public_dataset_manifest.tsv"):
        value = canonical_species(row.get("species", ""))
        if not value or "mixed" in value.lower():
            continue
        values.update(canonical_species(part) for part in value.split(";") if part.strip())
    return sorted(values)


def build_adapters(species: list[str], species_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_species = {item["species"]: item for item in species_rows}
    adapters = [
        {
            "adapter_id": "plant_universal",
            "species": "__unregistered_plant__",
            "aliases": ["unknown plant", "new plant species", "any plant"],
            "status": "universal_fallback",
            "transfer_mode": "exact_gene_ids_then_ortholog_map",
            "gene_id_namespace": "dataset_defined",
            "ortholog_map": None,
            "supervised_head": None,
            "tasks": ["embedding", "mlm", "annotation_transfer", "marker_candidates"],
            "evidence": "general backbone; provide a species gene map for best transfer",
        }
    ]
    for name in species:
        row = by_species.get(name, {})
        adapters.append(
            {
                "adapter_id": f"plant_{slug(name)}",
                "species": name,
                "aliases": [name],
                "status": "general_backbone_ready",
                "transfer_mode": "exact_gene_ids_then_ortholog_map",
                "gene_id_namespace": "dataset_defined",
                "ortholog_map": None,
                "supervised_head": None,
                "tasks": ["embedding", "mlm", "annotation_transfer", "marker_candidates"],
                "evidence": {
                    "manifest_rows": row.get("manifest_rows", 0),
                    "datasets": row.get("datasets", 0),
                },
            }
        )
    return adapters


def build_payload(root: Path) -> dict[str, Any]:
    rows, selected_manifest = select_rows(root)
    datasets = sorted({clean(row.get("dataset_id", "")) for row in rows if row.get("dataset_id")})
    species = species_summary(rows)
    catalog = read_tsv(root / "data" / "public_dataset_manifest.tsv")
    catalog_species = collect_catalog_species(root, species)
    adapters = build_adapters(catalog_species, species)
    return {
        "schema_version": "plant-general-release-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "SnowLotus-CellFM",
        "model_scope": "plant_general",
        "model_name": "Plant-CellFM (general plant foundation model)",
        "scope_statement": (
            "A cross-species plant single-cell and single-nucleus expression backbone. "
            "Snow Lotus is a target-species adapter and case study, not the boundary of the model."
        ),
        "species_policy": {
            "coverage": "all plant species represented by the audited public corpus",
            "transfer": "new species can be added through exact gene identifiers or an ortholog map",
            "snow_lotus_role": "Saussurea involucrata adapter, reference-genome alignment and downstream validation",
            "catalog_species_count": len(catalog_species),
        },
        "capabilities": [
            "masked-expression pretraining",
            "cross-species cell embedding",
            "hierarchical cell-state annotation",
            "marker-candidate discovery",
            "gene-vocabulary transfer with ortholog mapping",
            "species-specific adapter fine-tuning via LoRA or supervised learning for every registered plant species",
            "Snow Lotus reference-genome and primary-data adapter as one member of the full species registry",
        ],
        "trained_assets": [
            {
                "role": "joint_plant_backbone",
                "path": "outputs/remote_joint_scplantdb_pretrain_4090/best.pt",
                "cells": 272732,
                "source_genes": 209405,
                "training_gene_vocabulary": 60000,
                "sha256": "7300ba74d41e664c240cc35b4ae1de2a8402923260ac485c3975969312fed117",
            },
            {
                "role": "full_rice_cross_species_pretraining",
                "path": "outputs/remote_gse146034_full_pretrain_4090/best.pt",
                "cells": 23532,
                "genes": 43311,
                "nonzero_entries": 63856201,
                "sha256": "e0bfed95591959e7120e5dec1ed5ce8b59721aae845cb9cbe7166991e0831329",
            },
            {
                "role": "operational_annotation_head",
                "path": "outputs/remote_srp169576_joint_init_hybrid_4090/best.pt",
                "independent_test_fine_accuracy": 0.7279620268770806,
                "independent_test_fine_macro_f1": 0.725556710508996,
                "sha256": "3d2ba3d4c15d29140b04a24227d496fd92b58ef1fd730fe20127eeb66681d8fd",
            },
        ],
        "corpus_snapshot": {
            "selected_manifest": selected_manifest,
            "manifest_rows": len(rows),
            "unique_datasets": len(datasets),
            "unique_species_in_selected_manifest": len(species),
            "species": species,
        },
        "data_catalog": {
            "public_dataset_manifest": "data/public_dataset_manifest.tsv",
            "registered_catalog_rows": len(catalog),
            "catalog_species_labels": catalog_species,
        },
        "species_adapters": adapters,
        "inference_contract": {
            "input": [".h5ad", ".npz"],
            "required_expression_axis": "cells x genes",
            "gene_id_order": "gene identifiers are matched to the checkpoint vocabulary; use data.ortholog_map for novel species during training or offline preprocessing",
            "outputs": ["cell annotations", "256-dimensional embeddings", "bundle metadata"],
            "service_routes": ["GET /health", "GET /metadata", "GET /capabilities", "GET /adapters", "POST /annotate"],
            "modes": {
                "embedding": "general plant backbone checkpoint",
                "annotation": "optional supervised annotation checkpoint",
            },
            "primary_checkpoint": "outputs/remote_joint_scplantdb_pretrain_4090/best.pt",
        },
        "reproducibility": {
            "gpu": "NVIDIA GeForce RTX 4090 24 GB",
            "runtime": "conda environment myconda",
            "remote_project": "/mnt/snowlotus_cellfm",
            "github": "https://github.com/ahvsjags/SnowLotus-CellFM",
            "branch": "agent/remote-pipeline-20260728",
        },
    }


def write_species_tsv(species: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["species", "datasets", "manifest_rows", "tissues"], delimiter="\t")
        writer.writeheader()
        for item in species:
            writer.writerow({**item, "tissues": ";".join(item["tissues"])})


def write_markdown(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    snapshot = payload["corpus_snapshot"]
    lines = [
        "# Plant-CellFM General Plant Model Card",
        "",
        f"- Generated UTC: `{payload['generated_at_utc']}`",
        f"- Model scope: **{payload['model_scope']}**",
        f"- Model name: `{payload['model_name']}`",
        "- Snow Lotus is an adapter and case study; the backbone is designed for cross-species plant expression data.",
        f"- Registered adapters: **{len(payload['species_adapters'])}**, including the universal fallback for newly added plant species.",
        "",
        "## Scope and Functions",
        "",
        payload["scope_statement"],
        "",
        *[f"- {item}" for item in payload["capabilities"]],
        "",
        "## Verified Backbone Assets",
        "",
        "| Role | Checkpoint | Evidence | SHA256 |",
        "| --- | --- | --- | --- |",
    ]
    for asset in payload["trained_assets"]:
        evidence = ", ".join(f"{key}={value}" for key, value in asset.items() if key not in {"role", "path", "sha256"})
        lines.append(f"| {asset['role']} | `{asset['path']}` | {evidence} | `{asset['sha256']}` |")
    lines.extend(
        [
            "",
            "## Corpus Coverage",
            "",
            f"- Selected manifest: `{snapshot['selected_manifest']}`",
            f"- Manifest rows: **{snapshot['manifest_rows']}**",
            f"- Unique datasets: **{snapshot['unique_datasets']}**",
            f"- Unique species in selected manifest: **{snapshot['unique_species_in_selected_manifest']}**",
            "",
            "| Species | Datasets | Manifest rows | Tissues |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for item in snapshot["species"]:
        lines.append(f"| {item['species']} | {item['datasets']} | {item['manifest_rows']} | {', '.join(item['tissues'])} |")
    lines.extend(
        [
            "",
            "## Cross-Species Transfer Contract",
            "",
            "1. Use exact gene identifiers when the new species shares the checkpoint vocabulary.",
            "2. For species-specific identifiers, provide a source-to-target ortholog map and retain mapping confidence.",
            "3. Run the general backbone for embeddings and MLM features, then attach a task- or species-specific head when labels are available.",
            "4. The Snow Lotus branch adds reference-genome, gene-catalog and future primary single-cell adaptation assets without narrowing the general model.",
            "The runtime uses the joint scPlantDB checkpoint as the primary general-plant backbone. The supervised checkpoint is an optional annotation head, not the definition of the plant scope.",
            "",
            "## Reproducibility",
            "",
            f"- GPU: `{payload['reproducibility']['gpu']}`",
            f"- Remote project: `{payload['reproducibility']['remote_project']}`",
            f"- GitHub: {payload['reproducibility']['github']}/tree/{payload['reproducibility']['branch']}",
            "- Service routes: `/health`, `/metadata`, `/capabilities`, `/annotate`.",
            "",
            "This card defines the current plant-general release boundary. Coverage grows by promoting new public plant matrices into the manifest and rerunning the same audit and training pipeline.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the current plant-general model card and species coverage summary")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json-output", default="release_metadata/plant_general_model_card.json")
    parser.add_argument("--markdown-output", default="release_metadata/plant_general_model_card.md")
    parser.add_argument("--species-output", default="release_metadata/plant_general_corpus_species.tsv")
    parser.add_argument("--adapters-output", default="release_metadata/plant_species_adapters.json")
    args = parser.parse_args()
    root = Path(args.project_dir).resolve()
    payload = build_payload(root)
    Path(args.json_output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, Path(args.markdown_output))
    write_species_tsv(payload["corpus_snapshot"]["species"], Path(args.species_output))
    Path(args.adapters_output).write_text(
        json.dumps(
            {
                "schema_version": "plant-species-adapters-v1",
                "model_scope": payload["model_scope"],
                "fallback_adapter": "plant_universal",
                "adapters": payload["species_adapters"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(args.json_output)
    print(args.markdown_output)
    print(args.species_output)
    print(args.adapters_output)


if __name__ == "__main__":
    main()
