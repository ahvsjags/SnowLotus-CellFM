"""Materialize the strict 3,964-cell benchmark from public raw sources.

The strict benchmark is intentionally fail-closed.  A cell is included only
when it can be matched to a source matrix by dataset, sample and barcode.  No
prediction, embedding or label table can be used as an expression substitute.
The output manifest records the source file hash and the matching rule for
every source dataset.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "data" / "external_validation" / "v9_benchmark_subset_256_shared_genes.h5ad"
DEFAULT_META = ROOT / "release_metadata" / "species_ontology_obs_labels_with_ids_v9.tsv"
DEFAULT_PREDICTIONS = ROOT / "figure_data" / "v2_embeddings" / "predictions.csv"
DEFAULT_MAP = ROOT / "release_metadata" / "v9_strict_raw_source_map_v1.json"
DEFAULT_MANIFEST = ROOT / "release_metadata" / "v9_strict_raw_materialization_v1.json"
DEFAULT_MARKDOWN = ROOT / "release_metadata" / "v9_strict_raw_materialization_v1.md"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _normalise(value: str) -> str:
    value = str(value).strip()
    value = value.split("@@")[-1]
    value = value.split(":")[-1]
    value = value.split("_")[-1] if value.startswith(("CS1_", "CS2_", "CS3_")) else value
    return value.removesuffix("-1").removesuffix("_1").strip("_")


def _candidate_keys(value: str) -> list[str]:
    value = str(value).strip()
    keys = [value, _normalise(value)]
    if "@@" in value:
        keys.append(value.split("@@", 1)[1])
    if ":" in value:
        keys.append(value.rsplit(":", 1)[1])
    if "_" in value:
        keys.append(value.rsplit("_", 1)[-1])
    return list(dict.fromkeys(key for key in keys if key))


def _source_key_map(adata: ad.AnnData, row_indices: list[int] | None = None) -> dict[str, list[int]]:
    keys: dict[str, list[int]] = {}
    obs = adata.obs
    columns = ["cell_id", "barcode", "barcodes", "obs_name", "orig.ident", "Orig.ident"]
    indices = row_indices if row_indices is not None else list(range(adata.n_obs))
    for row_index in indices:
        obs_name = str(adata.obs_names[row_index])
        values = [obs_name]
        for column in columns:
            if column in obs:
                values.append(str(obs.iloc[row_index][column]))
        for value in values:
            for key in _candidate_keys(value):
                keys.setdefault(key, []).append(row_index)
    return keys


def _sample_rows(adata: ad.AnnData, sample_id: str) -> list[int]:
    """Return rows for a target sample without trusting a global barcode key."""

    sample_id = str(sample_id).strip()
    if not sample_id:
        return list(range(adata.n_obs))
    obs = adata.obs
    candidates: list[set[int]] = []
    for column in ["sample_id", "sample", "orig.ident", "Orig.ident", "Libraries"]:
        if column in obs:
            values = obs[column].astype(str).to_numpy()
            candidates.append(set(np.flatnonzero(values == sample_id).tolist()))
    name_matches = {
        index
        for index, value in enumerate(adata.obs_names.astype(str))
        if value.split("@@", 1)[0].strip("_") == sample_id
    }
    candidates.append(name_matches)
    nonempty = [rows for rows in candidates if rows]
    if nonempty:
        return sorted(nonempty[0])
    if adata.n_obs == 0:
        return []
    # A raw 10x file can omit sample metadata. If it contains only one
    # sample, its entire matrix is still an unambiguous source.
    return list(range(adata.n_obs))


def _open_source(path: Path, cache_dir: Path) -> tuple[ad.AnnData, Path]:
    if path.suffix.lower() == ".h5":
        with h5py.File(path, "r") as handle:
            matrix = handle["matrix"]
            shape = tuple(int(value) for value in matrix["shape"][()])
            counts = sparse.csc_matrix(
                (matrix["data"][()], matrix["indices"][()], matrix["indptr"][()]),
                shape=shape,
            ).T.tocsr()
            barcodes = [value.decode() if isinstance(value, bytes) else str(value) for value in matrix["barcodes"][()]]
            feature_group = matrix["features"]
            feature_key = "name" if "name" in feature_group else "gene_names"
            genes = [value.decode() if isinstance(value, bytes) else str(value) for value in feature_group[feature_key][()]]
        return ad.AnnData(X=counts, obs=pd.DataFrame(index=barcodes), var=pd.DataFrame(index=pd.Index(genes, dtype=str))), path
    if path.suffix != ".gz":
        return ad.read_h5ad(path, backed="r"), path
    cache_dir.mkdir(parents=True, exist_ok=True)
    output = cache_dir / path.name.removesuffix(".gz")
    if not output.exists() or output.stat().st_size == 0:
        with gzip.open(path, "rb") as source, output.open("wb") as target:
            shutil.copyfileobj(source, target, length=1 << 20)
    return ad.read_h5ad(output, backed="r"), output


def _load_source_map(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "sources" in payload:
        payload = payload["sources"]
    if not isinstance(payload, dict):
        raise ValueError("source map must be an object keyed by dataset_id")
    return payload


def _close_source(source: ad.AnnData) -> None:
    backing = getattr(source, "file", None)
    if backing is not None:
        backing.close()


def _materialize(args: argparse.Namespace) -> dict[str, Any]:
    metadata = pd.read_csv(args.metadata, sep="\t")
    predictions = pd.read_csv(args.predictions)
    target_ids = set(predictions["cell_id"].astype(str))
    target = metadata[metadata["cell_id"].astype(str).isin(target_ids)].copy()
    if len(target) != len(target_ids):
        raise RuntimeError(f"strict target mismatch: metadata={len(target)} predictions={len(target_ids)}")
    source_map = _load_source_map(args.source_map)
    dataset_counts = target.groupby("dataset_id").size().to_dict()
    chunks: list[ad.AnnData] = []
    source_records: list[dict[str, Any]] = []
    unmatched: list[dict[str, str]] = []
    ambiguous: list[dict[str, Any]] = []
    # Preflight source availability before opening large compressed H5AD files.
    # A single missing dataset makes the strict materialization invalid, so
    # there is no value in spending minutes decompressing the other sources.
    for dataset_id, group in target.groupby("dataset_id", sort=True):
        spec = source_map.get(dataset_id, {})
        source_path = _resolve(spec.get("path"))
        if source_path is None or not source_path.exists():
            source_records.append({"dataset_id": dataset_id, "status": "missing", "path": str(source_path)})
            unmatched.extend({"dataset_id": dataset_id, "cell_id": cell_id, "reason": "source_missing"} for cell_id in group.cell_id.astype(str))
    if unmatched:
        report = {"unmatched": unmatched, "ambiguous": ambiguous, "source_records": source_records, "stage": "source_preflight"}
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"raw source preflight failed: unmatched={len(unmatched)}; see {args.manifest}")
    source_records.clear()
    with tempfile.TemporaryDirectory(prefix="plantcellfm_v9_sources_") as cache:
        cache_dir = Path(cache)
        for dataset_id, group in target.groupby("dataset_id", sort=True):
            spec = source_map[dataset_id]
            source_path = _resolve(spec.get("path"))
            if source_path is None or not source_path.exists():
                source_records.append({"dataset_id": dataset_id, "status": "missing", "path": str(source_path)})
                unmatched.extend({"dataset_id": dataset_id, "cell_id": cell_id, "reason": "source_missing"} for cell_id in group.cell_id.astype(str))
                continue
            source, materialized_path = _open_source(source_path, cache_dir)
            target_samples = group["sample_id"].astype(str).dropna().unique().tolist() if "sample_id" in group else [""]
            sample_key_maps = {
                sample_id: _source_key_map(source, _sample_rows(source, sample_id))
                for sample_id in target_samples
            }
            group_by_id = group.copy()
            group_by_id["cell_id"] = group_by_id["cell_id"].astype(str)
            group_by_id = group_by_id.set_index("cell_id")
            selected: list[int] = []
            for cell_id in group.cell_id.astype(str):
                sample_id = str(group_by_id.loc[cell_id, "sample_id"]) if "sample_id" in group_by_id else ""
                key_map = sample_key_maps.get(sample_id, _source_key_map(source))
                candidates = set()
                for key in _candidate_keys(cell_id):
                    candidates.update(key_map.get(key, []))
                if len(candidates) != 1:
                    record = {"dataset_id": dataset_id, "cell_id": cell_id, "reason": "unmatched" if not candidates else "ambiguous", "candidate_rows": sorted(candidates)[:10]}
                    (unmatched if not candidates else ambiguous).append(record)
                    continue
                selected.append(next(iter(candidates)))
            if len(selected) != len(group):
                source_records.append({
                    "dataset_id": dataset_id,
                    "status": "incomplete",
                    "path": str(source_path),
                    "source_materialized_path": str(materialized_path),
                    "source_sha256": _sha256(materialized_path),
                    "requested_cells": int(len(group)),
                    "matched_cells": int(len(selected)),
                })
                _close_source(source)
                continue
            part = source[selected].to_memory()
            part.obs_names = group.cell_id.astype(str).tolist()
            for column in ["cell_id", "species", "dataset_id", "sample_id", "tissue", "cell_type", "cell_type_coarse"]:
                if column in group:
                    if column == "cell_id":
                        part.obs[column] = part.obs_names.astype(str)
                    else:
                        part.obs[column] = group_by_id.loc[part.obs_names, column].astype(str).to_numpy()
            part.obs["strict_source_obs_name"] = source.obs_names[selected].astype(str).to_numpy()
            part.var_names_make_unique()
            chunks.append(part)
            source_records.append({
                "dataset_id": dataset_id,
                "status": "matched",
                "path": str(source_path),
                "source_materialized_path": str(materialized_path),
                "source_sha256": _sha256(materialized_path),
                "requested_cells": int(len(group)),
                "matched_cells": int(len(selected)),
                "matching_rule": "dataset-scoped candidate keys: cell_id, sample/barcode, normalized barcode",
            })
            _close_source(source)
    if unmatched or ambiguous or len(pd.concat(chunks).obs if chunks else []) != len(target):
        report = {"unmatched": unmatched, "ambiguous": ambiguous, "source_records": source_records}
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"raw materialization failed: unmatched={len(unmatched)} ambiguous={len(ambiguous)}; see {args.manifest}")

    merged = ad.concat(chunks, join="outer", merge="first", uns_merge="first", index_unique=None)
    merged = merged[target["cell_id"].astype(str).tolist(), :].copy()
    merged.uns["plantcellfm_strict_input"] = {
        "schema_version": "v9_strict_raw_materialization_v1",
        "n_cells": int(merged.n_obs),
        "n_genes": int(merged.n_vars),
        "source_records": source_records,
        "truth_is_metadata_only": True,
        "expression_is_from_public_raw_source": True,
    }
    args.target.parent.mkdir(parents=True, exist_ok=True)
    merged.write_h5ad(args.target, compression="gzip")
    input_hash = _sha256(args.target)
    payload = {
        "schema_version": "v9_strict_raw_materialization_v1",
        "status": "complete",
        "target": str(args.target),
        "target_sha256": input_hash,
        "n_cells": int(merged.n_obs),
        "n_genes": int(merged.n_vars),
        "source_records": source_records,
        "matching": "dataset-scoped exact/normalized source cell identity; fail-closed on missing or ambiguous matches",
        "raw_expression_provenance": "public source matrices; no prediction or embedding values used",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Strict v9 raw input materialization", "", f"Status: **{payload['status']}**", "", f"Cells: **{payload['n_cells']:,}**", f"Genes: **{payload['n_genes']:,}**", f"Input SHA256: `{input_hash}`", "", "| Dataset | Status | Requested | Matched | Source SHA256 |", "| --- | --- | ---: | ---: | --- |"]
    lines.extend(f"| {row['dataset_id']} | {row['status']} | {row.get('requested_cells', '-')} | {row.get('matched_cells', '-')} | `{row.get('source_sha256', '-')}` |" for row in source_records)
    lines.extend(["", "The expression matrix is read from the recorded public source files. Matching is dataset-scoped and fail-closed; the script cannot create a valid output from locked predictions or embeddings."])
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    for name in ["source_map", "metadata", "predictions", "target", "manifest", "markdown"]:
        value = getattr(args, name)
        if not value.is_absolute():
            setattr(args, name, ROOT / value)
    payload = _materialize(args)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
