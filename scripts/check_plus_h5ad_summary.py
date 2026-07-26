from __future__ import annotations

import json

import anndata as ad


path = "data/plant_foundation_corpus_public_mlm_plus_latest.h5ad"
adata = ad.read_h5ad(path, backed="r")
obs = adata.obs
summary = {
    "path": path,
    "shape": [int(adata.n_obs), int(adata.n_vars)],
    "dataset_count": int(obs["dataset_id"].nunique()) if "dataset_id" in obs else None,
    "species_count": int(obs["species"].nunique()) if "species" in obs else None,
    "has_gse155304": bool(
        "dataset_id" in obs
        and (obs["dataset_id"].astype(str) == "geo_gse155304_arabidopsis_thaliana_single_cell_level_analysis_arabidopsis").any()
    ),
}
print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
adata.file.close()
