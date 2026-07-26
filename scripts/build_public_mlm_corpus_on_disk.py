#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from snowcell.corpus import CorpusItem, _as_csr, _load_item  # noqa: E402


MANIFEST_COLUMNS = [
    "path",
    "dataset_id",
    "species",
    "tissue",
    "layer",
    "label_key",
    "coarse_label_key",
    "sample_key",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a public MLM corpus through per-dataset h5ad shards and "
            "anndata.experimental.concat_on_disk. This avoids loading the "
            "entire public corpus into memory."
        )
    )
    parser.add_argument("--base-manifest", default="data/corpus_manifest_public_mlm.tsv")
    parser.add_argument("--extra-manifest", action="append", default=[])
    parser.add_argument(
        "--extra-glob",
        action="append",
        default=[
            "data/corpus_manifest.gse*.tsv",
            "data/corpus_manifest.scplantdb*.tsv",
        ],
    )
    parser.add_argument(
        "--manifest-output",
        default="data/corpus_manifest_public_mlm_full_on_disk.tsv",
    )
    parser.add_argument(
        "--output",
        default="data/plant_foundation_corpus_public_mlm_full_on_disk.h5ad",
    )
    parser.add_argument(
        "--work-dir",
        default="outputs/on_disk_corpus/public_mlm_full",
    )
    parser.add_argument(
        "--summary-output",
        default="outputs/publication_package/public_mlm_full_on_disk_manifest_summary.json",
    )
    parser.add_argument("--max-loaded-elems", type=int, default=25_000_000)
    parser.add_argument("--reuse-shards", action="store_true")
    parser.add_argument("--keep-shards", action="store_true")
    parser.add_argument("--skip-errors", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the de-duplicated manifest and summary, but do not build h5ad output.",
    )
    return parser.parse_args()


def read_manifest_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"missing manifest: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"manifest has no header: {path}")
        missing = {"path", "dataset_id", "species"} - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
        rows = []
        for row in reader:
            normalized = {column: (row.get(column, "") or "") for column in MANIFEST_COLUMNS}
            normalized["manifest_source"] = path.as_posix()
            rows.append(normalized)
    return rows


def default_extra_manifests(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(PROJECT.glob(pattern))
    return sorted(
        {
            path
            for path in paths
            if path.is_file() and path.stat().st_size > 0 and not path.name.endswith(".available.tsv")
        }
    )


def load_merged_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], dict[str, int]]:
    base = Path(args.base_manifest)
    if not base.is_absolute():
        base = PROJECT / base

    if args.extra_manifest:
        extras = [Path(path) if Path(path).is_absolute() else PROJECT / path for path in args.extra_manifest]
    else:
        extras = default_extra_manifests(args.extra_glob)

    raw_rows: list[dict[str, str]] = []
    for manifest in [base, *extras]:
        raw_rows.extend(read_manifest_rows(manifest))

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    missing_files = 0
    for row in raw_rows:
        key = (row["path"], row["dataset_id"])
        if key in seen:
            continue
        seen.add(key)
        data_path = Path(row["path"])
        if not data_path.is_absolute():
            data_path = PROJECT / data_path
        if not data_path.exists():
            missing_files += 1
        deduped.append(row)

    stats = {
        "base_manifest_count": 1,
        "extra_manifest_count": len(extras),
        "raw_rows": len(raw_rows),
        "deduplicated_rows": len(deduped),
        "duplicate_rows_removed": len(raw_rows) - len(deduped),
        "missing_files": missing_files,
    }
    return deduped, stats


def write_manifest(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in MANIFEST_COLUMNS})


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return value[:80] or "dataset"


def make_unique(values: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for raw in values:
        value = raw or "missing"
        count = seen.get(value, 0)
        seen[value] = count + 1
        result.append(value if count == 0 else f"{value}__dup{count}")
    return result


def collapse_duplicate_genes(X: sparse.csr_matrix, genes: np.ndarray) -> tuple[sparse.csr_matrix, np.ndarray]:
    gene_text = np.asarray([str(gene) for gene in genes], dtype=object)
    unique = np.asarray(sorted(set(gene_text.tolist())), dtype=str)
    if len(unique) == len(gene_text):
        return X, unique

    gene_index = {gene: index for index, gene in enumerate(unique)}
    rows = np.arange(len(gene_text), dtype=np.int64)
    columns = np.asarray([gene_index[str(gene)] for gene in gene_text], dtype=np.int64)
    projector = sparse.csr_matrix(
        (np.ones(len(gene_text), dtype=np.float32), (rows, columns)),
        shape=(len(gene_text), len(unique)),
    )
    return (X @ projector).tocsr().astype(np.float32), unique


def row_to_item(row: dict[str, str]) -> CorpusItem:
    return CorpusItem(
        path=row["path"],
        dataset_id=row["dataset_id"],
        species=row["species"],
        tissue=row.get("tissue", "") or "unknown_tissue",
        layer=row.get("layer", "") or None,
        label_key=row.get("label_key", "") or "cell_type",
        coarse_label_key=row.get("coarse_label_key", "") or "cell_type_coarse",
        sample_key=row.get("sample_key", "") or "sample_id",
    )


def write_shard(row: dict[str, str], index: int, output: Path) -> dict[str, object]:
    import anndata as ad

    matrix = _load_item(row_to_item(row))
    X, genes = collapse_duplicate_genes(_as_csr(matrix.X), matrix.genes)
    obs = pd.DataFrame(
        {
            key: np.asarray([str(value) for value in values], dtype=object)
            for key, values in matrix.obs.items()
        }
    )
    if "cell_id" in obs:
        obs.index = make_unique(obs["cell_id"].astype(str).tolist())
    else:
        obs.index = [f"{row['dataset_id']}:cell_{i}" for i in range(matrix.n_cells)]
    obs.index = pd.Index(obs.index.astype(str), name=None)
    var = pd.DataFrame(index=pd.Index(genes.astype(str), name=None))
    adata = ad.AnnData(X=X, obs=obs, var=var)
    output.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(output, compression="gzip")
    return {
        "index": index,
        "dataset_id": row["dataset_id"],
        "path": row["path"],
        "shard": output.as_posix(),
        "cells": int(adata.n_obs),
        "genes": int(adata.n_vars),
        "nnz": int(X.nnz),
        "bytes": int(output.stat().st_size),
    }


def build_shards(
    rows: list[dict[str, str]],
    work_dir: Path,
    reuse: bool,
    skip_errors: bool,
) -> tuple[list[Path], list[dict[str, object]], list[dict[str, str]]]:
    shard_dir = work_dir / "shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    shard_paths: list[Path] = []
    shard_stats: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    for index, row in enumerate(rows, start=1):
        shard = shard_dir / f"{index:04d}_{safe_name(row['dataset_id'])}.h5ad"
        shard_paths.append(shard)
        if reuse and shard.exists() and shard.stat().st_size > 0:
            shard_stats.append(
                {
                    "index": index,
                    "dataset_id": row["dataset_id"],
                    "path": row["path"],
                    "shard": shard.as_posix(),
                    "reused": True,
                    "bytes": int(shard.stat().st_size),
                }
            )
            print(f"[{index}/{len(rows)}] reuse {shard}", flush=True)
            continue
        try:
            print(f"[{index}/{len(rows)}] build {row['dataset_id']} <- {row['path']}", flush=True)
            shard_stats.append(write_shard(row, index, shard))
        except Exception as exc:
            if not skip_errors:
                raise
            errors.append(
                {
                    "index": str(index),
                    "dataset_id": row["dataset_id"],
                    "path": row["path"],
                    "error": repr(exc),
                }
            )
            shard_paths.pop()
            print(f"[{index}/{len(rows)}] skip {row['dataset_id']}: {exc!r}", flush=True)
    return shard_paths, shard_stats, errors


def concat_shards(shards: list[Path], output: Path, max_loaded_elems: int) -> None:
    import anndata as ad

    if not shards:
        raise ValueError("no shards to concatenate")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = output.with_name(f".{output.name}.tmp.{os.getpid()}")
    if tmp_output.exists():
        tmp_output.unlink()
    ad.experimental.concat_on_disk(
        [path.as_posix() for path in shards],
        tmp_output.as_posix(),
        join="outer",
        merge="same",
        max_loaded_elems=max_loaded_elems,
    )
    tmp_output.replace(output)


def write_summary(
    rows: list[dict[str, str]],
    manifest: Path,
    output: Path,
    summary_output: Path,
    build_stats: dict[str, int],
    shard_stats: list[dict[str, object]],
    errors: list[dict[str, str]],
    dry_run: bool,
) -> None:
    datasets = Counter(row["dataset_id"] for row in rows if row.get("dataset_id"))
    species = Counter(row["species"] for row in rows if row.get("species"))
    payload: dict[str, object] = {
        "manifest": manifest.as_posix(),
        "corpus": output.as_posix(),
        "manifest_rows": len(rows),
        "dataset_count": len(datasets),
        "species_count": len(species),
        "top_datasets": datasets.most_common(20),
        "top_species": species.most_common(20),
        "build_stats": build_stats,
        "shards": shard_stats,
        "errors": errors,
        "dry_run": dry_run,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    if output.exists() and not dry_run:
        import anndata as ad

        adata = ad.read_h5ad(output, backed="r")
        try:
            payload.update(
                {
                    "corpus_bytes": int(output.stat().st_size),
                    "n_obs": int(adata.n_obs),
                    "n_vars": int(adata.n_vars),
                }
            )
        finally:
            adata.file.close()
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows, stats = load_merged_rows(args)

    manifest_output = Path(args.manifest_output)
    output = Path(args.output)
    work_dir = Path(args.work_dir)
    summary_output = Path(args.summary_output)
    if not manifest_output.is_absolute():
        manifest_output = PROJECT / manifest_output
    if not output.is_absolute():
        output = PROJECT / output
    if not work_dir.is_absolute():
        work_dir = PROJECT / work_dir
    if not summary_output.is_absolute():
        summary_output = PROJECT / summary_output

    write_manifest(rows, manifest_output)
    print(f"wrote manifest: {manifest_output} rows={len(rows)}", flush=True)

    shard_stats: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    if not args.dry_run:
        shards, shard_stats, errors = build_shards(
            rows=rows,
            work_dir=work_dir,
            reuse=args.reuse_shards,
            skip_errors=args.skip_errors,
        )
        concat_shards(shards, output, max_loaded_elems=args.max_loaded_elems)
        if not args.keep_shards:
            shutil.rmtree(work_dir / "shards", ignore_errors=True)

    write_summary(
        rows=rows,
        manifest=manifest_output,
        output=output,
        summary_output=summary_output,
        build_stats=stats,
        shard_stats=shard_stats,
        errors=errors,
        dry_run=args.dry_run,
    )
    print(summary_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
