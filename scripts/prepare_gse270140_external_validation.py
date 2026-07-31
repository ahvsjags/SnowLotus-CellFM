from __future__ import annotations

"""Prepare the author-labelled GSE270140 Seurat export for frozen-model inference.

The GEO archive supplies an RDS object.  This script consumes the lossless RNA-count
MatrixMarket export made from that object, canonicalizes TAIR gene IDs, and writes a
compact AnnData input.  It does not alter counts, labels, or cell order.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

import anndata as ad
import pandas as pd
from scipy.io import mmread


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_DIR = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse270140"
    / "seurat_export_v2"
    / "GSM8335426_JWE03_Seurat_object"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse270140"
    / "GSM8335426_JWE03_author_annotated_secondary_root.h5ad"
)
DEFAULT_RECORD = ROOT / "release_metadata" / "gse270140_external_input_preparation_v1.json"
TAIR_GENE_ID = re.compile(r"^(AT[0-9A-Z]G\d{5})")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_tair_gene_id(raw_gene: str) -> str:
    """Return the TAIR locus carried by a GEO feature name, when present."""

    value = str(raw_gene).strip()
    match = TAIR_GENE_ID.match(value.upper())
    return match.group(1) if match else value


def build_anndata(export_dir: Path) -> ad.AnnData:
    matrix_path = export_dir / "matrix_cells_by_genes.mtx"
    genes_path = export_dir / "genes.txt"
    cells_path = export_dir / "cells.txt"
    metadata_path = export_dir / "metadata.csv"
    required = (matrix_path, genes_path, cells_path, metadata_path)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Seurat export files: {', '.join(missing)}")

    # scipy's fast MatrixMarket reader mishandles some absolute Windows paths
    # containing non-ASCII characters; an already-open binary handle is portable.
    with matrix_path.open("rb") as matrix_handle:
        matrix = mmread(matrix_handle).tocsr()
    genes = pd.read_csv(genes_path, header=None, names=["source_feature"], dtype=str)["source_feature"].fillna("")
    cells = pd.read_csv(cells_path, header=None, names=["cell_id"], dtype=str)["cell_id"].fillna("")
    metadata = pd.read_csv(metadata_path, dtype=str).fillna("")
    if matrix.shape != (len(cells), len(genes)):
        raise ValueError(
            f"Matrix shape {matrix.shape} does not match {len(cells)} cells and {len(genes)} features."
        )
    if cells.duplicated().any():
        raise ValueError("Cell identifiers must be unique for external inference.")
    if "cell_id" not in metadata.columns:
        raise ValueError("The RDS metadata export is missing its cell_id column.")
    if metadata["cell_id"].tolist() != cells.tolist():
        raise ValueError("RDS metadata order does not match matrix barcode order.")
    if "annotation" not in metadata.columns or not metadata["annotation"].astype(str).str.strip().any():
        raise ValueError("The RDS metadata export has no non-empty author annotation column.")

    canonical_ids = genes.map(canonical_tair_gene_id)
    if canonical_ids.duplicated().any():
        duplicate_ids = canonical_ids[canonical_ids.duplicated(keep=False)].unique().tolist()[:8]
        raise ValueError(
            "Canonical TAIR IDs are not one-to-one; sparse count collapsing is required before inference: "
            f"{duplicate_ids}"
        )

    obs = pd.DataFrame(index=cells.to_numpy())
    obs["cell_id"] = cells.to_numpy()
    obs["expert_annotation_raw"] = metadata["annotation"].astype(str).to_numpy()
    obs["source_orig_ident"] = metadata.get("orig.ident", pd.Series("", index=metadata.index)).astype(str).to_numpy()
    obs["source_seurat_cluster"] = metadata.get("seurat_clusters", pd.Series("", index=metadata.index)).astype(str).to_numpy()
    obs["source_phase"] = metadata.get("Phase", pd.Series("", index=metadata.index)).astype(str).to_numpy()
    obs["species"] = "Arabidopsis thaliana"
    obs["tissue"] = "secondary root"
    # The published checkpoint has one learned covariate per field.  These preserve
    # its frozen in-vocabulary conditioning rather than silently using index zero.
    obs["Organ"] = "Root"
    obs["Tissue"] = "Whole root"
    obs["dataset_id"] = "GSE270140_GSM8335426_author_annotated"
    obs["sample_id"] = "GSM8335426"
    var = pd.DataFrame(index=canonical_ids.to_numpy())
    var["source_feature"] = genes.to_numpy()
    var["canonical_gene_id"] = canonical_ids.to_numpy()
    var["gene_namespace"] = "TAIR10_locus_or_source_feature"
    return ad.AnnData(X=matrix, obs=obs, var=var)


def make_record(export_dir: Path, output: Path, adata: ad.AnnData) -> dict[str, object]:
    source_files = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(export_dir.iterdir())
        if path.is_file() and path.name in {"matrix_cells_by_genes.mtx", "genes.txt", "cells.txt", "metadata.csv"}
    }
    return {
        "schema_version": "plant_cellfm_gse270140_external_input_v1",
        "source": {
            "series_accession": "GSE270140",
            "sample_accession": "GSM8335426",
            "geo_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE270140",
            "publication_doi": "10.1038/s41477-025-01938-6",
            "source_object": "GSM8335426_JWE03_Seurat_object.rds.gz",
            "assay": "RNA",
            "slot": "counts",
            "author_annotation_column": "annotation",
        },
        "input_files": source_files,
        "prepared_h5ad": output.relative_to(ROOT).as_posix(),
        "prepared_h5ad_sha256": sha256(output),
        "matrix": {
            "cells": int(adata.n_obs),
            "genes": int(adata.n_vars),
            "nonzero_counts": int(adata.X.nnz),
            "canonical_tair_gene_ids": int(adata.var_names.str.match(r"^AT[0-9A-Z]G\d{5}$").sum()),
        },
        "frozen_inference_covariates": {"Organ": "Root", "Tissue": "Whole root"},
        "evidence_boundary": (
            "This author-labelled secondary-root dataset is evaluated post hoc against the frozen published "
            "SRP169576 annotation checkpoint. GSE270140 exists in historical project corpus manifests, so this "
            "record is a provenance-aware external reference case rather than a claim of globally unseen training data."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare GSE270140 author-labelled secondary-root input.")
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    args = parser.parse_args()
    export_dir = args.export_dir.resolve()
    output = args.output.resolve()
    record_path = args.record.resolve()
    adata = build_anndata(export_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(output, compression="gzip")
    record = make_record(export_dir, output, adata)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record["matrix"], ensure_ascii=False))


if __name__ == "__main__":
    main()
