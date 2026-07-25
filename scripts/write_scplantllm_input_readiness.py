from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import h5py
import pandas as pd


REQUIRED_H5_KEYS = ["count/data", "count/cell_names", "count/gene_names"]
REQUIRED_META_COLUMNS = ["cell", "orig.ident", "celltype"]
REFERENCE_META_FILES = [
    "reference_preprocess/batch_effect.meta",
    "reference_preprocess/batch_effect_vocab.meta.json",
    "reference_preprocess/cell_type.meta",
    "reference_preprocess/cell_type_vocab.meta.json",
]


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else root / path


def inspect_h5(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "required_keys_present": False}
    with h5py.File(path, "r") as handle:
        present = [key for key in REQUIRED_H5_KEYS if key in handle]
        shape = list(handle["count/data"].shape) if "count/data" in handle else None
    return {
        "path": str(path),
        "exists": True,
        "present_required_keys": present,
        "missing_required_keys": [key for key in REQUIRED_H5_KEYS if key not in present],
        "required_keys_present": len(present) == len(REQUIRED_H5_KEYS),
        "matrix_shape": shape,
    }


def inspect_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "required_columns_present": False}
    frame = pd.read_csv(path, nrows=5)
    columns = list(frame.columns)
    return {
        "path": str(path),
        "exists": True,
        "columns": columns,
        "missing_required_columns": [
            column for column in REQUIRED_META_COLUMNS if column not in columns
        ],
        "required_columns_present": all(column in columns for column in REQUIRED_META_COLUMNS),
    }


def collect_reference_outputs(input_dir: Path) -> dict[str, Any]:
    files = [input_dir / relative for relative in REFERENCE_META_FILES]
    chunks_dir = input_dir / "reference_preprocess" / "chunks"
    chunks = sorted(chunks_dir.glob("*_chunk_*.h5")) if chunks_dir.exists() else []
    return {
        "metadata_files": [
            {"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}
            for path in files
        ],
        "metadata_ready": all(path.exists() for path in files),
        "chunk_files": [
            {"path": str(path), "bytes": path.stat().st_size}
            for path in chunks
        ],
        "chunk_count": len(chunks),
        "chunks_ready": len(chunks) > 0,
    }


def build_audit(project_dir: str | Path, input_dir: str | Path) -> dict[str, Any]:
    root = Path(project_dir)
    input_path = Path(input_dir)
    if not input_path.is_absolute():
        input_path = root / input_path
    summary = read_json(input_path / "summary.json")
    h5_candidates = sorted(input_path.glob("*.h5"))
    meta_candidates = sorted(input_path.glob("*meta.csv"))
    h5_report = inspect_h5(
        resolve_path(root, summary["h5_path"])
        if summary and summary.get("h5_path")
        else (h5_candidates[0] if h5_candidates else input_path / "missing.h5")
    )
    meta_report = inspect_meta(
        resolve_path(root, summary["metadata_csv"])
        if summary and summary.get("metadata_csv")
        else (meta_candidates[0] if meta_candidates else input_path / "missing.meta.csv")
    )
    scplantllm_dir = root / "external" / "scPlantLLM"
    gene_vocab = scplantllm_dir / "gene_vocab.json"
    reference = collect_reference_outputs(input_path)
    input_ready = bool(h5_report.get("required_keys_present")) and bool(meta_report.get("required_columns_present"))
    if reference["chunks_ready"]:
        status = "reference_preprocess_ready"
    elif reference["metadata_ready"]:
        status = "input_and_reference_metadata_ready"
    elif input_ready:
        status = "input_ready"
    else:
        status = "missing_or_incomplete"
    return {
        "summary": {
            "status": status,
            "input_ready": input_ready,
            "reference_metadata_ready": reference["metadata_ready"],
            "reference_chunks_ready": reference["chunks_ready"],
            "selected_cells": summary.get("selected_cells") if summary else None,
            "retained_genes": summary.get("retained_genes") if summary else None,
            "gene_vocab_overlap_rate": (
                summary.get("scplantllm_gene_vocab", {}).get("overlap_rate")
                if summary
                else None
            ),
        },
        "input_dir": str(input_path),
        "export_summary": summary,
        "h5": h5_report,
        "metadata_csv": meta_report,
        "scplantllm_checkout": {
            "path": str(scplantllm_dir),
            "exists": scplantllm_dir.exists(),
            "gene_vocab_exists": gene_vocab.exists(),
            "gene_vocab_bytes": gene_vocab.stat().st_size if gene_vocab.exists() else 0,
        },
        "reference_outputs": reference,
    }


def write_json(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_markdown(payload: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# SnowLotus-CellFM scPlantLLM Input Readiness",
        "",
        f"- Status: `{summary['status']}`",
        f"- Input HDF5/meta ready: `{summary['input_ready']}`",
        f"- Reference metadata ready: `{summary['reference_metadata_ready']}`",
        f"- Reference preprocess chunks ready: `{summary['reference_chunks_ready']}`",
        f"- Selected cells: `{summary['selected_cells']}`",
        f"- Retained genes: `{summary['retained_genes']}`",
        f"- scPlantLLM gene-vocabulary overlap rate: `{summary['gene_vocab_overlap_rate']}`",
        "",
        "## Required Input Checks",
        "",
        f"- HDF5 path: `{payload['h5']['path']}`",
        f"- HDF5 required keys present: `{payload['h5'].get('required_keys_present')}`",
        f"- HDF5 matrix shape: `{payload['h5'].get('matrix_shape')}`",
        f"- Metadata CSV: `{payload['metadata_csv']['path']}`",
        f"- Metadata required columns present: `{payload['metadata_csv'].get('required_columns_present')}`",
        "",
        "## Reference Checkout",
        "",
        f"- scPlantLLM checkout exists: `{payload['scplantllm_checkout']['exists']}`",
        f"- scPlantLLM gene vocab exists: `{payload['scplantllm_checkout']['gene_vocab_exists']}`",
        "",
        "## Reference Outputs",
        "",
        "| File | Exists | Bytes |",
        "| --- | --- | --- |",
    ]
    for item in payload["reference_outputs"]["metadata_files"]:
        lines.append(f"| `{item['path']}` | `{item['exists']}` | `{item['bytes']}` |")
    lines.append("")
    lines.append(f"- Reference chunk count: `{payload['reference_outputs']['chunk_count']}`")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit scPlantLLM input readiness without marking benchmark completion")
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--input-dir", default="outputs/external_benchmarks/scplantllm_public_sprint_input", type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    payload = build_audit(args.project_dir, args.input_dir)
    write_markdown(payload, args.output_md)
    write_json(payload, args.output_json)
    print(args.output_md)
    print(args.output_json)


if __name__ == "__main__":
    main()
