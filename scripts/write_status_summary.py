from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_DIRS = [
    "outputs/smoke",
    "outputs/foundation_5090_public_sprint",
    "outputs/foundation_5090_public_safe_init",
    "outputs/foundation_5090_pretrain",
    "outputs/foundation_5090_mlm_public_available_expansion",
    "outputs/foundation_5090_mlm_public_expansion",
    "outputs/foundation_5090_mlm_public_expansion_continuation",
    "outputs/foundation_5090_mlm_public_late_refresh",
    "outputs/foundation_5090_mlm_public_late_refresh_safe",
    "outputs/foundation_5090_mlm_public_post_gse226097_refresh_safe",
]

CORPUS_FILES = [
    "data/plant_foundation_corpus.h5ad",
    "data/plant_foundation_corpus_public_mlm_available.h5ad",
    "data/plant_foundation_corpus_public_mlm.h5ad",
]

MANIFEST_FILES = [
    "data/corpus_manifest.tsv",
    "data/corpus_manifest.gse268881.available.tsv",
    "data/corpus_manifest.scplantdb.tsv",
    "data/corpus_manifest_public_mlm_available.tsv",
    "data/corpus_manifest_public_mlm.tsv",
]

PUBLIC_DATA_TARGETS = [
    {
        "dataset_id": "scplantdb_global",
        "manifest": "data/corpus_manifest.scplantdb.tsv",
        "raw_glob": "data/public/scPlantDB_h5ad*/*",
        "npz_glob": "data/public/scPlantDB_npz/*.npz",
    },
    {
        "dataset_id": "brassicaceae_multi_species_root_atlas",
        "manifest": "data/corpus_manifest.gse268881.tsv",
        "available_manifest": "data/corpus_manifest.gse268881.available.tsv",
        "raw_glob": "data/public/GSE268881_10x/*",
        "npz_glob": "data/public/GSE268881_npz/*.npz",
    },
    {
        "dataset_id": "arabidopsis_root_atlas",
        "manifest": "data/corpus_manifest.gse152766.tsv",
        "raw_glob": "data/public/GSE152766_mtx_tar/*",
        "npz_glob": "data/public/GSE152766_npz/*.npz",
    },
    {
        "dataset_id": "rice_root_tip_atlas",
        "manifest": "data/corpus_manifest.gse146034.tsv",
        "raw_glob": "data/public/GSE146034_raw_tar/*",
        "npz_glob": "data/public/GSE146034_npz/*.npz",
    },
    {
        "dataset_id": "arabidopsis_lifecycle_spatial_atlas",
        "manifest": "data/corpus_manifest.gse226097.tsv",
        "raw_glob": "data/public/GSE226097_rds/*",
        "npz_glob": "data/public/GSE226097_npz/*.npz",
    },
    {
        "dataset_id": "cotton_glandular_terpenoid_atlas",
        "manifest": "data/corpus_manifest.gse243419.tsv",
        "raw_glob": "data/public/GSE243419_raw_tar/*",
        "npz_glob": "data/public/GSE243419_npz/*.npz",
    },
    {
        "dataset_id": "rice_soil_stress_root_atlas",
        "manifest": "data/corpus_manifest.gse251706.tsv",
        "raw_glob": "data/public/GSE251706_rds/*",
        "npz_glob": "data/public/GSE251706_npz/*.npz",
    },
    {
        "dataset_id": "wheat_soil_root_atlas",
        "manifest": "data/corpus_manifest.gse270342.tsv",
        "raw_glob": "data/public/GSE270342_h5/*",
        "npz_glob": "data/public/GSE270342_npz/*.npz",
    },
    {
        "dataset_id": "arabidopsis_secondary_root_dev_atlas",
        "manifest": "data/corpus_manifest.gse270140.tsv",
        "raw_glob": "data/public/GSE270140_raw_tar/*",
        "npz_glob": "data/public/GSE270140_npz/*.npz",
    },
    {
        "dataset_id": "maize_easy_multiome_seedling",
        "manifest": "data/corpus_manifest.gse338572.tsv",
        "raw_glob": "data/public/GSE338572_rds/*",
        "npz_glob": "data/public/GSE338572_npz/*.npz",
    },
    {
        "dataset_id": "rice_leaf_stress_snuc_atlas",
        "manifest": "data/corpus_manifest.gse313726.tsv",
        "raw_glob": "data/public/GSE313726_rds/*",
        "npz_glob": "data/public/GSE313726_npz/*.npz",
    },
    {
        "dataset_id": "brassicaceae_regulatory_multiome",
        "manifest": "data/corpus_manifest.gse332675.tsv",
        "raw_glob": "data/public/GSE332675_h5ad/*",
        "npz_glob": "data/public/GSE332675_npz/*.npz",
    },
    {
        "dataset_id": "stevia_leaf_secondary_metabolism_snuc",
        "manifest": "data/corpus_manifest.gse311951.tsv",
        "raw_glob": "data/public/GSE311951_raw_tar/*",
        "npz_glob": "data/public/GSE311951_npz/*.npz",
    },
    {
        "dataset_id": "arabidopsis_lateral_root_founder_atlas",
        "manifest": "data/corpus_manifest.gse302041.tsv",
        "raw_glob": "data/public/GSE302041_rds/*",
        "npz_glob": "data/public/GSE302041_npz/*.npz",
    },
    {
        "dataset_id": "tomato_mycorrhiza_snuc_atlas",
        "manifest": "data/corpus_manifest.gse314252.tsv",
        "raw_glob": "data/public/GSE314252_rds/*",
        "npz_glob": "data/public/GSE314252_npz/*.npz",
    },
    {
        "dataset_id": "arabidopsis_scrna_method_benchmark",
        "manifest": "data/corpus_manifest.gse300264.tsv",
        "raw_glob": "data/public/GSE300264_rds/*",
        "npz_glob": "data/public/GSE300264_npz/*.npz",
    },
    {
        "dataset_id": "marchantia_spore_asymmetry_single_cell",
        "manifest": "data/corpus_manifest.gse336751.tsv",
        "raw_glob": "data/public/GSE336751_raw_tar/*",
        "npz_glob": "data/public/GSE336751_npz/*.npz",
    },
]


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_paths(root: Path) -> list[Path]:
    paths = {root / path for path in MANIFEST_FILES}
    paths.update((root / "data").glob("corpus_manifest.gse*.tsv"))
    paths.update((root / "data").glob("corpus_manifest.scplantdb*.tsv"))
    return sorted(paths, key=lambda item: item.as_posix())


def file_summary(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def manifest_summary(path: Path) -> dict[str, Any]:
    summary = file_summary(path)
    if not path.exists():
        summary["rows"] = 0
        return summary
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    summary["rows"] = len(rows)
    summary["dataset_ids"] = sorted({row.get("dataset_id", "") for row in rows if row.get("dataset_id")})
    summary["species"] = sorted({row.get("species", "") for row in rows if row.get("species")})
    return summary


def glob_summary(root: Path, pattern: str) -> dict[str, Any]:
    paths = sorted(root.glob(pattern))
    files = [path for path in paths if path.is_file()]
    unsupported_reports = [
        path for path in files if path.name == "unsupported_single_cell_matrix.json"
    ]
    return {
        "pattern": pattern,
        "file_count": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "examples": [str(path) for path in files[:5]],
        "unsupported_report_count": len(unsupported_reports),
        "unsupported_reports": [str(path) for path in unsupported_reports],
    }


def public_data_target_summary(root: Path) -> list[dict[str, Any]]:
    items = []
    public_rows_by_id: dict[str, dict[str, str]] = {}
    manifest_path = root / "data" / "public_dataset_manifest.tsv"
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                public_rows_by_id[row.get("dataset_id", "")] = row
    for target in PUBLIC_DATA_TARGETS:
        manifest = manifest_summary(root / target["manifest"])
        available_manifest = (
            manifest_summary(root / target["available_manifest"])
            if "available_manifest" in target
            else None
        )
        raw = glob_summary(root, target["raw_glob"])
        npz = glob_summary(root, target["npz_glob"])
        rows = manifest["rows"] or (available_manifest or {}).get("rows", 0)
        if rows:
            stage = "manifest_ready"
        elif raw["unsupported_report_count"] or npz["unsupported_report_count"]:
            stage = "unsupported_for_matrix_corpus"
        elif npz["file_count"]:
            stage = "npz_ready_no_manifest"
        elif raw["file_count"]:
            stage = "downloading_or_raw_ready"
        else:
            stage = "not_started_or_metadata_only"
        items.append(
            {
                "dataset_id": target["dataset_id"],
                "priority": public_rows_by_id.get(target["dataset_id"], {}).get("priority"),
                "status": public_rows_by_id.get(target["dataset_id"], {}).get("status"),
                "manifest": manifest,
                "available_manifest": available_manifest,
                "raw_files": raw,
                "npz_files": npz,
                "stage": stage,
            }
        )
    return items


def sra_runinfo_summary(root: Path) -> list[dict[str, Any]]:
    items = []
    for path in sorted((root / "data" / "public" / "sra_runinfo").glob("*.runinfo.csv")):
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        items.append(
            {
                "path": str(path),
                "rows": len(rows),
                "runs": [row.get("Run", "") for row in rows[:10]],
                "scientific_names": sorted({row.get("ScientificName", "") for row in rows if row.get("ScientificName")}),
                "library_strategies": sorted({row.get("LibraryStrategy", "") for row in rows if row.get("LibraryStrategy")}),
                "library_sources": sorted({row.get("LibrarySource", "") for row in rows if row.get("LibrarySource")}),
                "total_size_mb": sum(float(row.get("size_MB") or 0) for row in rows),
            }
        )
    return items


def public_discovery_summary(root: Path) -> dict[str, Any]:
    discovery_dir = root / "data" / "public_discovery"
    ncbi_files = sorted(discovery_dir.glob("ncbi_discovery_*.tsv"))
    geo_review_files = sorted(discovery_dir.glob("geo_supplementary_review_*.tsv"))
    geo_file_index_files = sorted(discovery_dir.glob("geo_supplementary_files_*.tsv"))
    scplantdb_catalog = discovery_dir / "scplantdb_dataset_catalog.tsv"
    scplantdb_probe = discovery_dir / "scplantdb_h5ad_size_probe.tsv"
    scplantdb_selected = discovery_dir / "scplantdb_selected_h5ad_datasets.txt"
    public_discovery_gap = (
        root / "outputs" / "publication_package" / "public_discovery" / "public_discovery_gap_audit.json"
    )
    latest_geo_reviews: list[dict[str, str]] = []
    if geo_review_files:
        with geo_review_files[-1].open("r", encoding="utf-8", newline="") as handle:
            latest_geo_reviews = list(csv.DictReader(handle, delimiter="\t"))
    scplantdb_catalog_rows: list[dict[str, str]] = []
    if scplantdb_catalog.exists():
        with scplantdb_catalog.open("r", encoding="utf-8", newline="") as handle:
            scplantdb_catalog_rows = list(csv.DictReader(handle, delimiter="\t"))
    scplantdb_probe_rows: list[dict[str, str]] = []
    if scplantdb_probe.exists():
        with scplantdb_probe.open("r", encoding="utf-8", newline="") as handle:
            scplantdb_probe_rows = list(csv.DictReader(handle, delimiter="\t"))
    selected_ids = []
    if scplantdb_selected.exists():
        selected_ids = [
            line.strip()
            for line in scplantdb_selected.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    scplantdb_reachable = [
        row
        for row in scplantdb_probe_rows
        if row.get("ok", "").lower() == "true" and int(row.get("content_length") or 0) > 0
    ]
    scplantdb_probe_selected = [
        row for row in scplantdb_probe_rows if row.get("selected_for_download", "").lower() == "true"
    ]
    ready_reviews = [
        row
        for row in latest_geo_reviews
        if row.get("download_ready", "").lower() == "true"
    ]
    return {
        "ncbi_discovery_files": [str(path) for path in ncbi_files],
        "geo_review_files": [str(path) for path in geo_review_files],
        "geo_file_index_files": [str(path) for path in geo_file_index_files],
        "latest_geo_review": str(geo_review_files[-1]) if geo_review_files else None,
        "latest_geo_file_index": str(geo_file_index_files[-1]) if geo_file_index_files else None,
        "latest_geo_review_rows": len(latest_geo_reviews),
        "download_ready_rows": len(ready_reviews),
        "download_ready_accessions": [
            {
                "dataset_id": row.get("dataset_id"),
                "accession": row.get("accession"),
                "matrix_file_count": int(row.get("matrix_file_count") or 0),
                "recommended_action": row.get("recommended_action"),
            }
            for row in ready_reviews[:20]
        ],
        "scplantdb_catalog": {
            "path": str(scplantdb_catalog),
            "exists": scplantdb_catalog.exists(),
            "rows": len(scplantdb_catalog_rows),
            "species": sorted(
                {row.get("species", "") for row in scplantdb_catalog_rows if row.get("species")}
            ),
        },
        "scplantdb_h5ad_probe": {
            "path": str(scplantdb_probe),
            "exists": scplantdb_probe.exists(),
            "rows": len(scplantdb_probe_rows),
            "reachable_rows": len(scplantdb_reachable),
            "selected_rows": len(scplantdb_probe_selected),
            "selected_dataset_ids": selected_ids
            or [row.get("dataset", "") for row in scplantdb_probe_selected if row.get("dataset")],
            "smallest_reachable": [
                {
                    "dataset": row.get("dataset"),
                    "species": row.get("species"),
                    "size_mb": float(row.get("size_mb") or 0),
                }
                for row in sorted(
                    scplantdb_reachable,
                    key=lambda item: int(item.get("content_length") or 0),
                )[:10]
            ],
        },
        "gap_audit": {
            "path": str(public_discovery_gap),
            "exists": public_discovery_gap.exists(),
            "summary": (read_json(public_discovery_gap) or {}).get("summary")
            if public_discovery_gap.exists()
            else {},
        },
    }


def pending_corpus_summary(root: Path) -> dict[str, Any]:
    path = root / "outputs" / "publication_package" / "pending_corpus_additions.json"
    payload = read_json(path)
    if not isinstance(payload, list):
        return {
            "path": str(path),
            "exists": path.exists(),
            "pending_refresh_count": 0,
            "pending_manifests": [],
        }
    pending = [item for item in payload if item.get("pending_refresh")]
    return {
        "path": str(path),
        "exists": path.exists(),
        "pending_refresh_count": len(pending),
        "pending_manifests": [
            {
                "manifest": item.get("manifest"),
                "dataset_ids": item.get("dataset_ids"),
                "rows_missing_from_public_mlm_manifest": item.get(
                    "rows_missing_from_public_mlm_manifest"
                ),
            }
            for item in pending
        ],
    }


def data_integrity_summary(root: Path) -> dict[str, Any]:
    path = root / "outputs" / "publication_package" / "data_integrity_audit.json"
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {
            "path": str(path),
            "exists": path.exists(),
            "manifest_count": 0,
            "ready_manifests": 0,
            "issue_manifests": 0,
            "matrix_count": 0,
            "missing_files": 0,
            "unreadable_files": 0,
            "total_cells": 0,
            "issue_manifests_detail": [],
        }
    summary = payload.get("summary", {})
    issue_manifests = [
        {
            "manifest": item.get("manifest"),
            "status": item.get("status"),
            "missing_files": item.get("missing_files"),
            "unreadable_files": item.get("unreadable_files"),
            "missing_columns": item.get("missing_columns"),
        }
        for item in payload.get("manifests", [])
        if item.get("status") != "ready"
    ]
    return {
        "path": str(path),
        "exists": path.exists(),
        "manifest_count": summary.get("manifest_count", 0),
        "ready_manifests": summary.get("ready_manifests", 0),
        "issue_manifests": summary.get("issue_manifests", 0),
        "matrix_count": summary.get("matrix_count", 0),
        "missing_files": summary.get("missing_files", 0),
        "unreadable_files": summary.get("unreadable_files", 0),
        "total_cells": summary.get("total_cells", 0),
        "issue_manifests_detail": issue_manifests,
    }


def scplantdb_manifest_audit_summary(root: Path) -> dict[str, Any]:
    path = root / "outputs" / "publication_package" / "scplantdb_manifest_audit.json"
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {
            "path": str(path),
            "exists": path.exists(),
            "rows": 0,
            "ready_rows": 0,
            "issue_rows": 0,
            "missing_training_obs_key_rows": 0,
            "total_cells": 0,
            "species_count": 0,
            "species": [],
        }
    summary = payload.get("summary", {})
    return {
        "path": str(path),
        "exists": path.exists(),
        "rows": summary.get("rows", 0),
        "ready_rows": summary.get("ready_rows", 0),
        "issue_rows": summary.get("issue_rows", 0),
        "missing_training_obs_key_rows": summary.get("missing_training_obs_key_rows", 0),
        "total_cells": summary.get("total_cells", 0),
        "species_count": summary.get("species_count", 0),
        "species": summary.get("species", []),
    }


def run_summary(path: Path) -> dict[str, Any]:
    history = read_json(path / "history.json")
    test_metrics = read_json(path / "test_metrics.json")
    latest_progress = read_json(path / "progress_latest.json")
    epochs = (history or {}).get("epochs", [])
    latest_epoch = epochs[-1] if epochs else None
    best_checkpoint = path / "best.pt"
    latest_checkpoint = path / "latest.pt"
    selected_checkpoint = best_checkpoint if best_checkpoint.exists() else latest_checkpoint
    return {
        "path": str(path),
        "has_checkpoint": best_checkpoint.exists() or latest_checkpoint.exists(),
        "checkpoint_kind": "best" if best_checkpoint.exists() else "latest",
        "checkpoint_bytes": (
            selected_checkpoint.stat().st_size if selected_checkpoint.exists() else 0
        ),
        "best_checkpoint": {
            "path": str(best_checkpoint),
            "exists": best_checkpoint.exists(),
            "bytes": best_checkpoint.stat().st_size if best_checkpoint.exists() else 0,
        },
        "latest_checkpoint": {
            "path": str(latest_checkpoint),
            "exists": latest_checkpoint.exists(),
            "bytes": latest_checkpoint.stat().st_size if latest_checkpoint.exists() else 0,
        },
        "epochs_recorded": len(epochs),
        "latest_epoch": latest_epoch,
        "latest_progress": latest_progress,
        "test_metrics": test_metrics,
    }


def strict_benchmark_summary(root: Path) -> list[dict[str, Any]]:
    items = []
    for path in sorted((root / "outputs" / "strict_benchmarks").glob("*.json")):
        payload = read_json(path) or {}
        item = {
            "path": str(path),
            "bytes": path.stat().st_size,
            "kind": "baseline" if payload.get("method") else "split_audit",
            "supervised_benchmark_ready": payload.get("supervised_benchmark_ready"),
            "fine_test_macro_f1": payload.get("fine_test_macro_f1"),
            "coarse_test_macro_f1": payload.get("coarse_test_macro_f1"),
            "data_path": payload.get("data_path"),
            "leaveout_key": payload.get("leaveout_key"),
        }
        items.append(item)
    return items


EXTERNAL_NONMETRIC_NAME_TOKENS = [
    "access_audit",
    "readiness",
    "_input",
    "input_",
    "benchmark_plan",
    "_plan",
]
REQUIRED_EXTERNAL_METHODS = ["seurat", "scplantllm", "scplantannotate"]


def has_external_metric_payload(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if isinstance(payload.get("metrics"), dict) and payload["metrics"]:
        return True
    metric_keys = {
        "accuracy",
        "macro_f1",
        "micro_f1",
        "weighted_f1",
        "fine_test_macro_f1",
        "coarse_test_macro_f1",
    }
    return any(payload.get(key) is not None for key in metric_keys)


def external_method_tag(path: Path, payload: dict[str, Any]) -> str:
    combined = f"{path.name} {payload.get('method', '')}".lower()
    for method in REQUIRED_EXTERNAL_METHODS:
        if method in combined:
            return method
    return str(payload.get("method") or "unknown")


def is_external_metric_file(path: Path, payload: Any) -> bool:
    lowered = path.name.lower()
    if any(token in lowered for token in EXTERNAL_NONMETRIC_NAME_TOKENS):
        return False
    return has_external_metric_payload(payload)


def benchmark_readiness_summary(root: Path, items: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_items = [item for item in items if item.get("kind") == "baseline"]
    split_items = [item for item in items if item.get("kind") == "split_audit"]
    external_dir = root / "outputs" / "external_benchmarks"
    external_files = sorted(external_dir.glob("*.json")) if external_dir.exists() else []
    metric_method_tags = []
    metric_files = []
    for path in external_files:
        payload = read_json(path) or {}
        if is_external_metric_file(path, payload):
            metric_files.append(path)
            metric_method_tags.append(external_method_tag(path, payload))
    present_methods = sorted(set(metric_method_tags))
    missing_methods = [
        method for method in REQUIRED_EXTERNAL_METHODS if method not in present_methods
    ]
    return {
        "baseline_metric_count": sum(
            1
            for item in baseline_items
            if item.get("fine_test_macro_f1") is not None
            or item.get("coarse_test_macro_f1") is not None
        ),
        "split_audit_count": len(split_items),
        "supervised_split_audit_count": sum(
            1 for item in split_items if item.get("supervised_benchmark_ready")
        ),
        "marker_candidate_artifact_present": any(
            "marker_candidates" in item.get("path", "") for item in items
        ),
        "external_benchmark_files": [str(path) for path in external_files],
        "external_benchmark_count": len(external_files),
        "external_metric_files": [str(path) for path in metric_files],
        "external_metric_count": len(metric_files),
        "external_metric_methods": present_methods,
        "external_missing_methods": missing_methods,
        "external_required_methods": REQUIRED_EXTERNAL_METHODS,
    }


def external_benchmark_summary(root: Path) -> list[dict[str, Any]]:
    items = []
    external_dir = root / "outputs" / "external_benchmarks"
    for path in sorted(external_dir.glob("*.json")) if external_dir.exists() else []:
        payload = read_json(path) or {}
        has_metric = is_external_metric_file(path, payload)
        items.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "method": payload.get("method"),
                "method_tag": external_method_tag(path, payload),
                "has_metric": has_metric,
                "test_cells": payload.get("test_cells"),
                "fine_test_accuracy": payload.get("fine_test_accuracy"),
                "fine_test_macro_f1": payload.get("fine_test_macro_f1"),
                "coarse_test_accuracy": payload.get("coarse_test_accuracy"),
                "coarse_test_macro_f1": payload.get("coarse_test_macro_f1"),
                "input_dir": payload.get("input_dir"),
            }
        )
    return items


def build_summary(project_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    runs = [run_summary(root / run_dir) for run_dir in RUN_DIRS]
    manifests = [manifest_summary(path) for path in manifest_paths(root)]
    corpora = [file_summary(root / path) for path in CORPUS_FILES]
    public_manifest = manifest_summary(root / "data" / "public_dataset_manifest.tsv")
    integrity = data_integrity_summary(root)
    scplantdb_manifest_audit = scplantdb_manifest_audit_summary(root)
    strict_benchmarks = strict_benchmark_summary(root)
    benchmark_readiness = benchmark_readiness_summary(root, strict_benchmarks)
    external_benchmarks = external_benchmark_summary(root)
    return {
        "project_dir": str(root),
        "runs": runs,
        "corpora": corpora,
        "manifests": manifests,
        "public_dataset_manifest": public_manifest,
        "public_data_targets": public_data_target_summary(root),
        "public_discovery": public_discovery_summary(root),
        "pending_corpus_additions": pending_corpus_summary(root),
        "data_integrity": integrity,
        "scplantdb_manifest_audit": scplantdb_manifest_audit,
        "sra_runinfo": sra_runinfo_summary(root),
        "strict_benchmarks": strict_benchmarks,
        "benchmark_readiness": benchmark_readiness,
        "external_benchmarks": external_benchmarks,
        "publication_gates": {
            "ssh_remote_execution": True,
            "gpu_training_active_or_artifacts_present": any(run["has_checkpoint"] for run in runs),
            "public_data_ingested": any(item["rows"] > 0 for item in manifests),
            "data_integrity_audit_present": integrity["exists"],
            "referenced_matrices_readable": (
                integrity["exists"]
                and integrity["matrix_count"] > 0
                and integrity["missing_files"] == 0
                and integrity["unreadable_files"] == 0
            ),
            "strict_split_audit_present": any(item["kind"] == "split_audit" for item in strict_benchmarks),
            "baseline_benchmark_metric_present": benchmark_readiness["baseline_metric_count"] > 0,
            "external_tool_benchmarks_present": benchmark_readiness["external_metric_count"] > 0,
            "snow_lotus_scRNA_present": (root / "data" / "saussurea_involucrata.h5ad").exists(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Write SnowCell machine-readable status summary")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    summary = build_summary(args.project_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
