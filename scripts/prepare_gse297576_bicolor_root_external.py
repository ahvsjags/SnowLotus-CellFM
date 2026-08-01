from __future__ import annotations

"""Convert the author-labelled GSE297576 Sorghum root Seurat atlas to h5ad.

This is a deterministic data-preparation step for a future frozen external
evaluation. It does not run Plant-CellFM, fit a label map or report accuracy.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import rdata
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "external_validation" / "gse297576" / "GSE297576_seurat_object.bicolor_root_atlas.RDS"
DEFAULT_OUTPUT = ROOT / "outputs" / "external_validation" / "gse297576_bicolor_root" / "GSE297576_bicolor_root_author_atlas.h5ad"
DEFAULT_RECORD = ROOT / "release_metadata" / "gse297576_bicolor_root_external_conversion_v1.json"
GEO_SOURCE = "https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE297576&format=file&file=GSE297576_seurat_object.bicolor_root_atlas.RDS"
JGI_REPOSITORY = "https://code.jgi.doe.gov/LBaumgart/plant-multidap-and-single-cell"
JGI_COMMIT = "8a7e6cccb12ea45c32f8e42c75b439106ca22ffb"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def attributes(value: Any) -> dict[str, Any]:
    if isinstance(value, SimpleNamespace):
        return vars(value)
    if isinstance(value, dict):
        return value
    raise TypeError(f"Expected an R S4 namespace or mapping, found {type(value)!r}.")


def coordinate_names(logmap: Any) -> np.ndarray:
    if not hasattr(logmap, "dims") or not hasattr(logmap, "coords"):
        raise TypeError("The Seurat LogMap lacks xarray coordinate metadata.")
    first_dimension = logmap.dims[0]
    names = np.asarray(logmap.coords[first_dimension].values, dtype=str)
    if names.ndim != 1 or not len(names) or len(pd.Index(names).unique()) != len(names):
        raise ValueError("Expected a non-empty unique Seurat LogMap coordinate vector.")
    return names


def sparse_counts(r_object: Any) -> tuple[sparse.csr_matrix, pd.DataFrame, np.ndarray]:
    root = attributes(r_object)
    metadata = root.get("meta.data")
    if not isinstance(metadata, pd.DataFrame):
        raise TypeError("The Seurat object is missing a pandas-converted meta.data table.")
    rna = attributes(attributes(root["assays"])["RNA"])
    layer = attributes(attributes(rna["layers"])["counts"])
    dimensions = tuple(int(value) for value in np.asarray(layer["Dim"]).tolist())
    row_index = np.asarray(layer["i"], dtype=np.int32)
    column_pointer = np.asarray(layer["p"], dtype=np.int64)
    values = np.asarray(layer["x"], dtype=np.float64)
    if len(dimensions) != 2 or len(row_index) != len(values) or len(column_pointer) != dimensions[1] + 1:
        raise ValueError("The Seurat dgCMatrix dimensions, row index and column pointer disagree.")
    if (values < 0).any() or not np.allclose(values, np.rint(values)):
        raise ValueError("The external RNA counts layer must contain non-negative integer UMI values.")
    genes_by_cells = sparse.csc_matrix((values.astype(np.int32), row_index, column_pointer), shape=dimensions)
    cell_names = coordinate_names(rna["cells"])
    gene_names = coordinate_names(rna["features"])
    if genes_by_cells.shape != (len(gene_names), len(cell_names)):
        raise ValueError("The RNA count matrix shape does not match the Seurat feature/cell LogMaps.")
    if "cellBC" not in metadata.columns or metadata["cellBC"].astype(str).tolist() != cell_names.tolist():
        raise ValueError("The Seurat metadata cellBC column does not match the RNA count-matrix order.")
    if "celltype" not in metadata.columns or metadata["celltype"].isna().any():
        raise ValueError("The author celltype field is absent or incomplete.")
    return genes_by_cells.T.tocsr(), metadata.copy(), gene_names


def convert(input_path: Path, output_path: Path, record_path: Path, *, overwrite: bool) -> dict[str, Any]:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to replace {output_path}; pass --overwrite after reviewing its provenance.")
    r_object = rdata.read_rds(input_path)
    counts, metadata, genes = sparse_counts(r_object)
    cell_names = metadata["cellBC"].astype(str).to_numpy()
    obs = metadata.copy()
    obs.index = pd.Index(cell_names, name="cell_id")
    # These values exactly match the frozen root checkpoint conditioning vocabulary.
    # They are source-independent experimental descriptors, never reference labels.
    obs["Organ"] = "Root"
    obs["Tissue"] = "Whole root"
    obs["species"] = "Sorghum bicolor"
    obs["dataset_id"] = "GSE297576_bicolor_root_author_atlas"
    obs["sample_id"] = obs["library"].astype(str).to_numpy()
    var = pd.DataFrame({"gene_id": genes}, index=pd.Index(genes, name="gene_id"))
    atlas = ad.AnnData(X=counts, obs=obs, var=var)
    atlas.obsm["X_umap_author"] = metadata[["UMAP_1", "UMAP_2"]].to_numpy(dtype=np.float32)
    atlas.uns["external_validation_contract"] = {
        "dataset": "GSE297576",
        "species": "Sorghum bicolor",
        "tissue": "root",
        "reference_label_key": "celltype",
        "counts_layer": "Seurat RNA/layers/counts",
        "role": "author-labelled external candidate; not a frozen-corpus training input",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ad.settings.allow_write_nullable_strings = True
    atlas.write_h5ad(output_path, compression="gzip", compression_opts=4)
    frozen_profile = json.loads((ROOT / "release_metadata" / "plant_cellfm_model_card_v4.json").read_text(encoding="utf-8"))["frozen_current_corpus"]
    payload = {
        "schema_version": "plant_cellfm_gse297576_bicolor_root_external_conversion_v1",
        "status": "CONVERTED_AUTHOR_LABELLED_EXTERNAL_CANDIDATE",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "dataset": "GSE297576",
            "species": "Sorghum bicolor",
            "tissue": "root",
            "geo_source": GEO_SOURCE,
            "jgi_repository": JGI_REPOSITORY,
            "jgi_commit": JGI_COMMIT,
            "seurat_rds": input_path.relative_to(ROOT).as_posix(),
            "seurat_rds_sha256": sha256(input_path),
        },
        "matrix": {
            "cells": int(atlas.n_obs),
            "genes": int(atlas.n_vars),
            "nonzero_counts": int(atlas.X.nnz),
            "cell_identifier": "author meta.data/cellBC, matched exactly to RNA matrix column order",
            "gene_identifier": "author RNA Assay5 feature coordinate",
            "count_source": "RNA/layers/counts raw UMI layer",
        },
        "frozen_inference_covariates": {
            "Organ": "Root",
            "Tissue": "Whole root",
            "source": "fixed root-tissue descriptors required by the frozen checkpoint vocabulary; not derived from author celltype labels",
        },
        "author_reference": {
            "label_key": "celltype",
            "label_count": int(atlas.obs["celltype"].nunique()),
            "label_counts": {str(label): int(count) for label, count in atlas.obs["celltype"].value_counts().items()},
        },
        "frozen_profile_disjointness": {
            "profile_source": frozen_profile["profile_source"],
            "profiled_species": frozen_profile["species_list"],
            "candidate_species_not_in_profiled_species": "Sorghum bicolor" not in frozen_profile["species_list"],
            "boundary": "Species absence from the frozen profiled corpus supports an external-species contract, but source-level dataset disjointness and a frozen inference protocol must still be audited before reporting an external metric.",
        },
        "output": {
            "h5ad": output_path.relative_to(ROOT).as_posix(),
            "h5ad_sha256": sha256(output_path),
        },
        "claim_boundary": "This conversion preserves author labels and raw UMI counts for a future frozen external evaluation. It does not yet establish model-input orthology coverage, label-ontology alignment, frozen inference, a comparator result or any accuracy metric.",
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    payload = convert(input_path, args.output.resolve(), args.record.resolve(), overwrite=args.overwrite)
    print(json.dumps({"status": payload["status"], "cells": payload["matrix"]["cells"], "genes": payload["matrix"]["genes"], "labels": payload["author_reference"]["label_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
