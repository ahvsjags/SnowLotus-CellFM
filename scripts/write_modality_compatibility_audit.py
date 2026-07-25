from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path | None) -> Any:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def latest_file(path: Path, pattern: str) -> Path | None:
    files = sorted(path.glob(pattern), key=lambda item: item.as_posix())
    return files[-1] if files else None


def status_targets(status_summary: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(status_summary, dict):
        return {}
    targets = status_summary.get("public_data_targets")
    if not isinstance(targets, list):
        return {}
    return {
        str(target.get("dataset_id")): target
        for target in targets
        if isinstance(target, dict) and target.get("dataset_id")
    }


def file_rows_by_dataset(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row.get("dataset_id", ""), []).append(row)
    return grouped


def parse_counts(value: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for part in value.split(";"):
        if ":" not in part:
            continue
        key, raw_count = part.split(":", 1)
        key = key.strip()
        try:
            count = int(raw_count.strip())
        except ValueError:
            continue
        if key:
            counts[key] = count
    return counts


def lower_join(*values: str) -> str:
    return " ".join(value.lower() for value in values if value)


def infer_promotion_data_type(row: dict[str, str]) -> str:
    text = lower_join(row.get("title", ""), row.get("file_type_counts", ""))
    if "spatial" in text or "visium" in text or "merfish" in text:
        return "spatial transcriptomics GEO promotion"
    if "single-nuclei" in text or "single nuclei" in text or "snrna" in text:
        return "snRNA GEO promotion"
    if "single-cell" in text or "single cell" in text or "scrna" in text:
        return "scRNA GEO promotion"
    if "multiomics" in text or "multi-omics" in text:
        return "single-cell multiomics GEO promotion"
    return "GEO matrix promotion candidate"


def promotion_queue_rows(root: Path) -> list[dict[str, str]]:
    queue_path = root / "data" / "public_discovery" / "geo_promotion_download_queue.tsv"
    rows: list[dict[str, str]] = []
    for row in read_tsv(queue_path):
        dataset_id = row.get("dataset_id", "")
        if not dataset_id:
            continue
        rows.append(
            {
                "dataset_id": dataset_id,
                "species": row.get("species", ""),
                "tissue_or_scope": row.get("tissue", ""),
                "data_type": infer_promotion_data_type(row),
                "priority": "promotion",
                "accession_or_doi": row.get("accession", ""),
                "source_url": row.get("source_url", ""),
                "why_use": row.get("title", ""),
                "status": "promotion_download_queue",
                "_source_catalog": "geo_promotion_download_queue",
                "_wrapper_script": row.get("wrapper_script", ""),
                "_manifest_path": row.get("manifest", ""),
                "_geo_file_type_counts": row.get("file_type_counts", ""),
            }
        )
    return rows


def modality_flags(row: dict[str, str], files: list[dict[str, str]]) -> list[str]:
    text = lower_join(
        row.get("dataset_id", ""),
        row.get("species", ""),
        row.get("tissue_or_scope", ""),
        row.get("data_type", ""),
        row.get("why_use", ""),
        row.get("status", ""),
    )
    file_text = lower_join(
        *[
            " ".join(
                [
                    item.get("filename", ""),
                    item.get("file_type", ""),
                    str(item.get("matrix_like", "")),
                ]
            )
            for item in files
        ],
        row.get("_geo_file_type_counts", ""),
        row.get("_wrapper_script", ""),
    )
    flags: set[str] = set()
    if any(token in text or token in file_text for token in ["scrna", "single-cell", "single cell"]):
        flags.add("scRNA")
    if any(token in text or token in file_text for token in ["snrna", "single-nuclei", "single nuclei"]):
        flags.add("snRNA")
    if any(token in text or token in file_text for token in ["spatial", "visium", "merfish", "stereo-seq", "stereoseq", "slide-seq"]):
        flags.add("spatial")
    if any(token in text or token in file_text for token in ["atac", "snatac", "scatac"]):
        flags.add("ATAC")
    if "bulk" in text or "bulk" in file_text:
        flags.add("bulk")
    if any(token in text for token in ["genome", "wgs", "hi-c", "reference genome"]):
        flags.add("genome_context")
    if any(token in text or token in file_text for token in ["rna", "transcriptomics", "transcriptome", "mtx", "rds", "seurat"]):
        flags.add("rna_expression")
    return sorted(flags)


def classify_route(row: dict[str, str], files: list[dict[str, str]], status: dict[str, Any]) -> tuple[str, str]:
    text = lower_join(
        row.get("dataset_id", ""),
        row.get("species", ""),
        row.get("tissue_or_scope", ""),
        row.get("data_type", ""),
        row.get("why_use", ""),
        row.get("status", ""),
    )
    file_text = lower_join(
        *[
            " ".join(
                [
                    item.get("filename", ""),
                    item.get("file_type", ""),
                    str(item.get("matrix_like", "")),
                ]
            )
            for item in files
        ],
        row.get("_geo_file_type_counts", ""),
    )
    flags = set(modality_flags(row, files))
    manifest_rows = (status.get("manifest") or {}).get("rows", 0) or (
        status.get("available_manifest") or {}
    ).get("rows", 0)
    npz_count = (status.get("npz_files") or {}).get("file_count", 0)

    if "saussurea_involucrata_private" in text:
        return "primary_snow_lotus_required", "Core species data required for fine-tuning and validation."
    if "model_reference" in text or "reference" == row.get("status", ""):
        return "method_reference_only", "Reference or baseline tool; do not treat as expression corpus data."
    if "database" in text or "manual_index" in text:
        return "discovery_index_only", "Use as an accession discovery index, not as a directly ingested matrix."
    if "unsupported" in str(status.get("stage", "")).lower():
        return (
            "unsupported_for_expression_corpus",
            "Downloader or audit marked this target unsupported for expression-matrix corpus use.",
        )
    if "ATAC" in flags:
        if "rna" in text and ("rds" in file_text or "rna" in file_text):
            return "rna_subset_pending_multimodal_context", "RNA-compatible subset appears available; ATAC files should stay separate."
        return (
            "regulatory_or_multimodal_holdout",
            "Regulatory/ATAC-dominant files should not be mixed into RNA expression pretraining.",
        )
    if "spatial" in flags and not {"scRNA", "snRNA"} & flags:
        if manifest_rows or npz_count:
            return (
                "spatial_expression_corpus",
                "Spatial/spot-level expression matrix exists; use for expression pretraining or spatial marker validation, not supervised cell-type annotation unless deconvolved labels are verified.",
            )
        return (
            "spatial_expression_pending_download",
            "Spatial/spot-level expression candidate; download may support expression pretraining or spatial validation, but not supervised cell-type annotation labels by itself.",
        )
    if manifest_rows or npz_count:
        return "rna_expression_corpus", "Processed matrix manifest exists and passed downstream ingestion checks."
    if "bulk" in text or "genome" in text or "wgs" in text or "hi-c" in text or "transcriptome" in text:
        return "supporting_context_only", "Useful for vocabulary, ortholog, or biology context, not cell annotation training."
    if "scrna" in text or "snrna" in text or "single-cell" in text or "transcriptomics" in text:
        return "rna_expression_pending_download", "Expression-like single-cell target; queue or convert before corpus use."
    return "manual_review_required", "Modality is not specific enough for automatic RNA-corpus routing."


def annotation_training_role(route: str, flags: list[str]) -> str:
    flag_set = set(flags)
    if route == "primary_snow_lotus_required":
        return "required_primary_finetune_and_validation"
    if route in {"method_reference_only", "discovery_index_only"}:
        return "not_expression_training_data"
    if route in {"regulatory_or_multimodal_holdout", "supporting_context_only", "manual_review_required"}:
        return "holdout_until_rna_cell_matrix_verified"
    if route.startswith("spatial_expression") or ("spatial" in flag_set and not {"scRNA", "snRNA"} & flag_set):
        return "expression_pretraining_or_spatial_validation_only"
    if route == "rna_subset_pending_multimodal_context":
        return "rna_subset_training_only_after_layer_separation"
    if route == "unsupported_for_expression_corpus":
        return "unsupported_for_expression_corpus"
    if {"scRNA", "snRNA"} & flag_set:
        return "cell_annotation_training_eligible_after_label_audit"
    if route in {"rna_expression_corpus", "rna_expression_pending_download"}:
        return "expression_pretraining_only_until_cell_labels_verified"
    return "manual_review_required"


def claim_guardrail(route: str, role: str) -> str:
    if route.startswith("spatial_expression"):
        return "Do not claim supervised cell-type annotation from spot-level spatial data without deconvolution or verified cell labels."
    if role == "cell_annotation_training_eligible_after_label_audit":
        return "Cell-annotation claims require verified obs-level labels and held-out evaluation."
    if role == "expression_pretraining_only_until_cell_labels_verified":
        return "Use as unannotated expression pretraining until cell labels and label schema are audited."
    if role == "rna_subset_training_only_after_layer_separation":
        return "Separate RNA layers from ATAC/regulatory modalities before adding to the RNA corpus."
    if role == "unsupported_for_expression_corpus":
        return "Keep excluded from the corpus unless a later manual audit identifies a compatible expression matrix."
    if role == "holdout_until_rna_cell_matrix_verified":
        return "Keep out of the RNA expression corpus until matrix modality and observation units are verified."
    return "No additional claim guardrail beyond route rationale."


def build_audit(
    project_dir: str | Path,
    status_summary_path: str | Path | None = None,
    public_manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_dir)
    status_summary = read_json(Path(status_summary_path)) if status_summary_path else None
    public_manifest = Path(public_manifest_path) if public_manifest_path else root / "data" / "public_dataset_manifest.tsv"
    discovery_dir = root / "data" / "public_discovery"
    latest_file_index = latest_file(discovery_dir, "geo_supplementary_files_*.tsv")
    file_rows = read_tsv(latest_file_index) if latest_file_index else []
    files_by_dataset = file_rows_by_dataset(file_rows)
    targets = status_targets(status_summary)
    rows = []
    manifest_rows = [
        {**row, "_source_catalog": "public_dataset_manifest"}
        for row in read_tsv(public_manifest)
    ]
    dataset_ids = {row.get("dataset_id", "") for row in manifest_rows}
    candidate_rows = [
        row for row in promotion_queue_rows(root) if row.get("dataset_id") not in dataset_ids
    ]
    for row in [*manifest_rows, *candidate_rows]:
        dataset_id = row.get("dataset_id", "")
        files = files_by_dataset.get(dataset_id, [])
        target = targets.get(dataset_id, {})
        route, rationale = classify_route(row, files, target)
        flags = modality_flags(row, files)
        role = annotation_training_role(route, flags)
        file_type_counts = Counter(item.get("file_type", "") for item in files if item.get("file_type"))
        if not file_type_counts and row.get("_geo_file_type_counts"):
            file_type_counts.update(parse_counts(row.get("_geo_file_type_counts", "")))
        rows.append(
            {
                "dataset_id": dataset_id,
                "species": row.get("species", ""),
                "data_type": row.get("data_type", ""),
                "priority": row.get("priority", ""),
                "manifest_status": row.get("status", ""),
                "source_catalog": row.get("_source_catalog", "public_manifest"),
                "accession_or_doi": row.get("accession_or_doi", ""),
                "status_summary_stage": target.get("stage"),
                "route": route,
                "rationale": rationale,
                "modality_flags": flags,
                "annotation_training_role": role,
                "claim_guardrail": claim_guardrail(route, role),
                "geo_file_count": len(files),
                "geo_file_type_counts": dict(sorted(file_type_counts.items())),
                "example_files": [item.get("filename", "") for item in files[:6]],
            }
        )
    route_counts = Counter(item["route"] for item in rows)
    role_counts = Counter(item["annotation_training_role"] for item in rows)
    return {
        "project_dir": str(root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "public_manifest": public_manifest.as_posix(),
        "latest_geo_file_index": latest_file_index.as_posix() if latest_file_index else None,
        "summary": {
            "dataset_count": len(rows),
            "route_counts": dict(sorted(route_counts.items())),
            "annotation_training_role_counts": dict(sorted(role_counts.items())),
            "rna_ready_or_pending_count": sum(
                1
                for item in rows
                if item["route"] in {
                    "rna_expression_corpus",
                    "rna_expression_pending_download",
                    "rna_subset_pending_multimodal_context",
                "primary_snow_lotus_required",
                }
            ),
            "holdout_count": route_counts.get("regulatory_or_multimodal_holdout", 0),
            "spatial_expression_context_count": route_counts.get("spatial_expression_corpus", 0)
            + route_counts.get("spatial_expression_pending_download", 0),
            "promotion_candidate_count": len(candidate_rows),
        },
        "datasets": rows,
    }


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join("---" for _ in rows[0]) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines)


def write_markdown(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SnowLotus-CellFM Modality Compatibility Audit",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Latest GEO file index: `{payload.get('latest_geo_file_index') or 'not available'}`",
        "",
        "## Summary",
        "",
        markdown_table(
            [
                ["Route", "Datasets"],
                *[[route, str(count)] for route, count in payload["summary"]["route_counts"].items()],
            ]
        ),
        "",
        markdown_table(
            [
                ["Annotation role", "Datasets"],
                *[
                    [role, str(count)]
                    for role, count in payload["summary"]["annotation_training_role_counts"].items()
                ],
            ]
        ),
        "",
        "## Dataset Routes",
        "",
    ]
    rows = [["Dataset", "Source", "Data type", "Manifest status", "Stage", "Route", "Annotation role", "GEO file types"]]
    for item in payload["datasets"]:
        rows.append(
            [
                item["dataset_id"],
                item["source_catalog"],
                item["data_type"],
                item["manifest_status"],
                str(item.get("status_summary_stage") or "-"),
                item["route"],
                item["annotation_training_role"],
                ";".join(f"{key}:{value}" for key, value in item["geo_file_type_counts"].items()) or "-",
            ]
        )
    lines.extend(
        [
            markdown_table(rows),
            "",
            "## Holdouts and Rationale",
            "",
        ]
    )
    holdouts = [
        item
        for item in payload["datasets"]
        if item["route"]
        in {
            "regulatory_or_multimodal_holdout",
            "manual_review_required",
            "spatial_expression_pending_download",
            "spatial_expression_corpus",
            "unsupported_for_expression_corpus",
        }
    ]
    if not holdouts:
        lines.append("No modality holdouts were detected.")
    else:
        for item in holdouts:
            lines.append(f"- `{item['dataset_id']}`: {item['rationale']} Guardrail: {item['claim_guardrail']}")
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def write_json(payload: dict[str, Any], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write modality compatibility audit for SnowCell public data")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--status-summary", default=None)
    parser.add_argument("--public-manifest", default=None)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    payload = build_audit(args.project_dir, args.status_summary, args.public_manifest)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
