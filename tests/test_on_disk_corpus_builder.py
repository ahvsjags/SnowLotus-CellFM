from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy import sparse


def load_builder_module():
    module_path = Path(__file__).parents[1] / "scripts" / "build_public_mlm_corpus_on_disk.py"
    spec = importlib.util.spec_from_file_location("build_public_mlm_corpus_on_disk", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_manifest(path: Path, rows: list[tuple[str, str, str]]) -> None:
    path.write_text(
        "path\tdataset_id\tspecies\ttissue\tlayer\tlabel_key\tcoarse_label_key\tsample_key\n"
        + "".join(
            f"{data_path}\t{dataset_id}\t{species}\troot\t\tcell_type\tcell_type_coarse\tsample_id\n"
            for data_path, dataset_id, species in rows
        ),
        encoding="utf-8",
    )


def test_on_disk_builder_deduplicates_manifest_rows_and_writes_manifest(tmp_path: Path) -> None:
    module = load_builder_module()
    data_a = tmp_path / "a.npz"
    data_b = tmp_path / "b.npz"
    data_a.write_bytes(b"placeholder")
    data_b.write_bytes(b"placeholder")
    base_manifest = tmp_path / "base.tsv"
    extra_manifest = tmp_path / "extra.tsv"
    merged_manifest = tmp_path / "merged.tsv"

    write_manifest(
        base_manifest,
        [
            (data_a.as_posix(), "dataset_a", "Arabidopsis thaliana"),
            (data_b.as_posix(), "dataset_b", "Oryza sativa"),
        ],
    )
    write_manifest(
        extra_manifest,
        [
            (data_a.as_posix(), "dataset_a", "Arabidopsis thaliana"),
            (data_a.as_posix(), "dataset_a_new_id", "Arabidopsis thaliana"),
        ],
    )
    args = argparse.Namespace(
        base_manifest=str(base_manifest),
        extra_manifest=[str(extra_manifest)],
        extra_glob=[],
    )

    rows, stats = module.load_merged_rows(args)
    module.write_manifest(rows, merged_manifest)
    lines = merged_manifest.read_text(encoding="utf-8").splitlines()

    assert stats["raw_rows"] == 4
    assert stats["deduplicated_rows"] == 3
    assert stats["duplicate_rows_removed"] == 1
    assert stats["missing_files"] == 0
    assert len(lines) == 4
    assert "dataset_a_new_id" in lines[-1]


def test_on_disk_builder_collapses_duplicate_genes_in_csr_matrix() -> None:
    module = load_builder_module()
    X = sparse.csr_matrix(
        np.asarray(
            [
                [1.0, 2.0, 3.0],
                [0.0, 4.0, 5.0],
            ],
            dtype=np.float32,
        )
    )
    collapsed, genes = module.collapse_duplicate_genes(
        X,
        np.asarray(["gene_b", "gene_a", "gene_b"]),
    )

    assert genes.tolist() == ["gene_a", "gene_b"]
    np.testing.assert_allclose(
        collapsed.toarray(),
        np.asarray(
            [
                [2.0, 4.0],
                [4.0, 5.0],
            ],
            dtype=np.float32,
        ),
    )


def test_on_disk_builder_writes_dry_run_summary(tmp_path: Path) -> None:
    module = load_builder_module()
    manifest = tmp_path / "merged.tsv"
    output = tmp_path / "full.h5ad"
    summary = tmp_path / "summary.json"
    rows = [
        {
            "path": "data/a.npz",
            "dataset_id": "dataset_a",
            "species": "Arabidopsis thaliana",
            "tissue": "root",
        },
        {
            "path": "data/b.npz",
            "dataset_id": "dataset_b",
            "species": "Oryza sativa",
            "tissue": "leaf",
        },
    ]

    module.write_summary(
        rows=rows,
        manifest=manifest,
        output=output,
        summary_output=summary,
        build_stats={
            "raw_rows": 3,
            "deduplicated_rows": 2,
            "duplicate_rows_removed": 1,
            "missing_files": 0,
        },
        shard_stats=[],
        errors=[],
        dry_run=True,
    )
    payload = json.loads(summary.read_text(encoding="utf-8"))

    assert payload["manifest_rows"] == 2
    assert payload["dataset_count"] == 2
    assert payload["species_count"] == 2
    assert payload["build_stats"]["duplicate_rows_removed"] == 1
    assert payload["dry_run"] is True
