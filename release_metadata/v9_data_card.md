# Plant-CellFM v9 Data Card

## Data Sources

The v9 corpus is assembled from public plant single-cell and single-nucleus matrices represented by auditable tab-separated manifests. Each retained row records a source path, dataset identifier, species, tissue, layer, label keys and sample key.

| Field | Frozen v9 value |
| --- | ---: |
| Manifest rows | 56 |
| Unique datasets | 29 |
| Normalized species labels | 20 |
| Raw species strings before alias canonicalization | 21 |
| Cells in built corpus | approximately 13.78 million |
| Source genes before filtering | approximately 1.53 million |
| Missing manifest files | 0 |

## Processing

Input matrices are converted into auditable shards, normalized with a per-cell total of 10,000, transformed with `log1p`, filtered by minimum genes/cells, and mapped to the shared checkpoint vocabulary. Dataset, species, tissue and sample identifiers are retained for group-aware evaluation.

## Splits and Evaluation

The release contains a shared-gene benchmark subset and group-aware protocols for leave-dataset-out, leave-sample-out and leave-species-out testing. The v3 baseline and v9 candidate use the same benchmark subset and are compared using accuracy, macro-F1 and coverage.

## Provenance

The full corpus and training artifacts remain on the server paths recorded in `README.paths.txt` inside the v9 release package. The package includes the v9 manifest, manifest audit, corpus summary, benchmark subset, benchmark JSON files, training configuration, history, preprocessing statistics and SHA256 manifest.

## Intended Use

The data card supports reproducible plant expression modelling and annotation-transfer experiments. It does not imply that the corpus represents every plant species or that the internal held-out accuracy is universal across all plants.
