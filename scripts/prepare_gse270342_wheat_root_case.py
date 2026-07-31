from __future__ import annotations

"""Prepare the GSE270342 wheat-root author object for a non-overlap diagnostic.

The published object is from the same study as a prior strict-transfer exploratory
subset. Exact cells present in that prior subset are excluded before any new frozen
model inference. The retained cells remain a same-study author-label re-audit, not
an independent external benchmark.
"""

import argparse
import hashlib
import json
from pathlib import Path

import anndata as ad
import pandas as pd
from scipy.io import mmread

from snowcell.artifacts import load_checkpoint, vocabs_from_checkpoint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_DIR = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse270342"
    / "seurat_export"
    / "GSE270342_seuratObj_for_publication"
)
DEFAULT_MAPPING = ROOT / "data" / "orthologs" / "gse270342_wheat_to_arabidopsis_author_orthogroups.tsv"
DEFAULT_CHECKPOINT = ROOT / "models" / "SnowLotus_CellFM_SRP169576_annotation_1024_best.pt"
DEFAULT_STRICT_PREDICTIONS = ROOT / "figure_data" / "v2_embeddings" / "v17_nested_strict_predictions.csv"
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "external_validation"
    / "gse270342"
    / "GSE270342_wheat_root_author_annotated_nonoverlap_diagnostic.h5ad"
)
DEFAULT_RECORD = ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_input_preparation_v1.json"
DEFAULT_MARKDOWN = ROOT / "release_metadata" / "gse270342_wheat_nonoverlap_input_preparation_v1.md"
HISTORICAL_PREFIX = "wheat_soil_root_atlas:GSM8339904_rep1_filtered_feature_bc_matrix:"
AUTHOR_REPLICATE_PREFIX = "CS1_"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def required_file(directory: Path, name: str) -> Path:
    path = directory / name
    if not path.is_file():
        raise FileNotFoundError(f"Missing required exported Seurat file: {path}")
    return path


def historical_rep1_barcodes(path: Path) -> set[str]:
    values = pd.read_csv(path, usecols=["cell_id"], dtype=str)["cell_id"].fillna("")
    selected = values.loc[values.str.startswith(HISTORICAL_PREFIX)]
    if selected.empty:
        raise ValueError(f"No historical wheat reference cells found with prefix {HISTORICAL_PREFIX!r}.")
    return {value.removeprefix(HISTORICAL_PREFIX) for value in selected}


def build_anndata(export_dir: Path, historical_prediction_path: Path) -> tuple[ad.AnnData, dict[str, object]]:
    matrix_path = required_file(export_dir, "matrix_cells_by_genes.mtx")
    genes_path = required_file(export_dir, "genes.txt")
    cells_path = required_file(export_dir, "cells.txt")
    metadata_path = required_file(export_dir, "metadata.csv")
    with matrix_path.open("rb") as handle:
        matrix = mmread(handle).tocsr()
    genes = pd.read_csv(genes_path, header=None, names=["source_feature"], dtype=str)["source_feature"].fillna("")
    cells = pd.read_csv(cells_path, header=None, names=["cell_id"], dtype=str)["cell_id"].fillna("")
    metadata = pd.read_csv(metadata_path, dtype=str).fillna("")
    if matrix.shape != (len(cells), len(genes)):
        raise ValueError(f"Matrix shape {matrix.shape} does not match {len(cells)} cells and {len(genes)} genes.")
    if genes.duplicated().any() or not genes.astype(str).str.strip().all():
        raise ValueError("Source feature identifiers must be non-empty and unique.")
    if cells.duplicated().any() or not cells.astype(str).str.strip().all():
        raise ValueError("Author cell identifiers must be non-empty and unique.")
    if "cell_id" not in metadata or metadata["cell_id"].tolist() != cells.tolist():
        raise ValueError("Author metadata cell order must exactly match the exported expression matrix.")
    if "annotation" not in metadata or not metadata["annotation"].astype(str).str.strip().any():
        raise ValueError("The author object has no non-empty annotation column.")

    prior_barcodes = historical_rep1_barcodes(historical_prediction_path)
    exact_overlap = cells.map(
        lambda cell_id: cell_id.startswith(AUTHOR_REPLICATE_PREFIX)
        and cell_id.removeprefix(AUTHOR_REPLICATE_PREFIX) in prior_barcodes
    ).to_numpy(dtype=bool)
    keep = ~exact_overlap
    if not keep.any():
        raise ValueError("All author cells overlap the prior strict-transfer exploratory subset.")

    matrix = matrix[keep].tocsr()
    retained_cells = cells.loc[keep].reset_index(drop=True)
    retained_metadata = metadata.loc[keep].reset_index(drop=True)
    obs = pd.DataFrame(index=retained_cells.to_numpy())
    obs["cell_id"] = retained_cells.to_numpy()
    obs["expert_annotation_raw"] = retained_metadata["annotation"].astype(str).to_numpy()
    obs["source_orig_ident"] = retained_metadata.get("orig.ident", pd.Series("", index=retained_metadata.index)).astype(str).to_numpy()
    obs["source_seurat_cluster"] = retained_metadata.get("seurat_clusters", pd.Series("", index=retained_metadata.index)).astype(str).to_numpy()
    obs["source_doublet_finder"] = retained_metadata.get("DoubletFinder", pd.Series("", index=retained_metadata.index)).astype(str).to_numpy()
    obs["species"] = "Triticum aestivum"
    obs["tissue"] = "root apical meristem"
    # The frozen root checkpoint only has these conditioning values in vocabulary.
    obs["Organ"] = "Root"
    obs["Tissue"] = "Whole root"
    obs["dataset_id"] = "GSE270342_author_annotated_wheat_root_nonoverlap"
    obs["sample_id"] = retained_metadata.get("orig.ident", pd.Series("GSE270342", index=retained_metadata.index)).astype(str).to_numpy()
    var = pd.DataFrame(index=genes.to_numpy())
    var["source_feature"] = genes.to_numpy()
    var["gene_namespace"] = "IWGSC_v2.1_style_wheat_gene_id"
    return ad.AnnData(X=matrix, obs=obs, var=var), {
        "author_cells": int(len(cells)),
        "historical_strict_prediction_rows": int(len(prior_barcodes)),
        "exact_cs1_barcode_overlap_excluded": int(exact_overlap.sum()),
        "retained_nonoverlap_cells": int(keep.sum()),
        "author_cell_prefixes": cells.str.extract(r"^(CS[0-9]+)_", expand=False).fillna("unprefixed").value_counts().sort_index().to_dict(),
    }


def mapping_coverage(adata: ad.AnnData, mapping_path: Path, checkpoint_path: Path) -> dict[str, object]:
    mapping = pd.read_csv(mapping_path, sep="\t", dtype=str).fillna("")
    required = {"source_gene", "target_gene", "orthogroup_id", "mapping_evidence"}
    if not required.issubset(mapping.columns):
        raise ValueError(f"Mapping file missing required columns: {sorted(required - set(mapping.columns))}")
    first_target = mapping.drop_duplicates("source_gene", keep="first").set_index("source_gene")["target_gene"]
    checkpoint = load_checkpoint(checkpoint_path, map_location="cpu")
    gene_vocab, _, _, _, _ = vocabs_from_checkpoint(checkpoint)
    checkpoint_tokens = set(gene_vocab.tokens)
    genes = pd.Index(adata.var_names.astype(str))
    target = pd.Series(genes.to_numpy(), dtype=str).map(first_target)
    author_mapped = target.notna().to_numpy()
    checkpoint_compatible = target.isin(checkpoint_tokens).to_numpy()
    total_umi = float(adata.X.sum())
    author_mapped_umi = float(adata.X[:, author_mapped].sum())
    checkpoint_compatible_umi = float(adata.X[:, checkpoint_compatible].sum())
    return {
        "mapping_path": mapping_path.relative_to(ROOT).as_posix(),
        "mapping_sha256": sha256(mapping_path),
        "checkpoint_path": checkpoint_path.relative_to(ROOT).as_posix(),
        "checkpoint_sha256": sha256(checkpoint_path),
        "checkpoint_gene_vocab_size": int(len(gene_vocab.tokens)),
        "source_gene_count": int(len(genes)),
        "author_orthogroup_mapped_genes": int(author_mapped.sum()),
        "author_orthogroup_mapped_gene_fraction": float(author_mapped.mean()),
        "checkpoint_compatible_mapped_genes": int(checkpoint_compatible.sum()),
        "checkpoint_compatible_gene_fraction": float(checkpoint_compatible.mean()),
        "total_umi": total_umi,
        "author_orthogroup_mapped_umi_fraction": float(author_mapped_umi / total_umi),
        "checkpoint_compatible_umi_fraction": float(checkpoint_compatible_umi / total_umi),
    }


def markdown(record: dict[str, object]) -> str:
    source = record["source"]
    overlap = record["overlap_audit"]
    mapping = record["mapping_coverage"]
    matrix = record["matrix"]
    return "\n".join(
        [
            "# GSE270342 Wheat Root Non-overlap Diagnostic Input",
            "",
            f"- Author object: `{source['object_name']}` from `{source['series_accession']}`.",
            f"- Retained matrix: {matrix['cells']} cells x {matrix['genes']} IWGSC v2.1-style wheat features.",
            f"- Exact prior strict-transfer cells excluded: {overlap['exact_cs1_barcode_overlap_excluded']}.",
            f"- Checkpoint-compatible feature coverage: {mapping['checkpoint_compatible_gene_fraction']:.2%} genes and {mapping['checkpoint_compatible_umi_fraction']:.2%} UMI counts.",
            "",
            "## Evidence Boundary",
            "",
            "- Exact barcodes from the previously recorded `GSM8339904_rep1` strict-transfer subset are removed before frozen inference.",
            "- The remaining cells still originate from the same public study, so this is a provenance-aware author-label re-audit rather than an independent external benchmark.",
            "- Any accuracy calculation must use a predeclared coarse author-to-model mapping and must not replace the nested leave-species primary result.",
            "- Orthology is represented as author-published many-to-many orthogroups; the inference loader applies a deterministic first-target collapse and records the resulting coverage.",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--historical-strict-predictions", type=Path, default=DEFAULT_STRICT_PREDICTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    export_dir = args.export_dir.resolve()
    mapping_path = args.mapping.resolve()
    checkpoint_path = args.checkpoint.resolve()
    historical_path = args.historical_strict_predictions.resolve()
    output = args.output.resolve()
    record_path = args.record.resolve()
    markdown_path = args.markdown.resolve()
    for path in (mapping_path, checkpoint_path, historical_path):
        if not path.is_file():
            raise FileNotFoundError(f"Missing declared input: {path}")

    adata, overlap = build_anndata(export_dir, historical_path)
    mapping_stats = mapping_coverage(adata, mapping_path, checkpoint_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(output, compression="gzip")
    record: dict[str, object] = {
        "schema_version": "plant_cellfm_gse270342_wheat_root_nonoverlap_input_v1",
        "source": {
            "series_accession": "GSE270342",
            "geo_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE270342",
            "publication_doi": "10.1016/j.celrep.2025.115240",
            "object_name": "GSE270342_seuratObj_for_publication.rds.gz",
            "assay": "RNA",
            "slot": "counts",
            "author_annotation_column": "annotation",
        },
        "input_files": {
            name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for name in ("matrix_cells_by_genes.mtx", "genes.txt", "cells.txt", "metadata.csv")
            for path in [required_file(export_dir, name)]
        },
        "overlap_audit": {
            **overlap,
            "historical_prediction_path": historical_path.relative_to(ROOT).as_posix(),
            "historical_prediction_sha256": sha256(historical_path),
            "historical_prefix": HISTORICAL_PREFIX,
            "author_replicate_prefix_compared": AUTHOR_REPLICATE_PREFIX,
        },
        "mapping_coverage": mapping_stats,
        "prepared_h5ad": output.relative_to(ROOT).as_posix(),
        "prepared_h5ad_sha256": sha256(output),
        "matrix": {"cells": int(adata.n_obs), "genes": int(adata.n_vars), "nonzero_counts": int(adata.X.nnz)},
        "frozen_inference_covariates": {"Organ": "Root", "Tissue": "Whole root"},
        "claim_boundary": (
            "The input excludes exact cell-barcode overlap with the recorded GSE270342 replicate-1 strict-transfer "
            "subset. It remains a same-study author-label re-audit, not an independent external benchmark. Any result "
            "is a frozen-model diagnostic subject to its declared many-to-many author orthogroup contract."
        ),
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown(record), encoding="utf-8")
    print(json.dumps({"matrix": record["matrix"], "overlap": overlap, "mapping": mapping_stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
