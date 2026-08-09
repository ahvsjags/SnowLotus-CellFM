# v9 strict raw-source resolution audit

Status: **partial_fail_closed**

The strict benchmark contains 3,964 cells across 29 dataset blocks. The raw-input release gate remains closed unless every target cell is matched to a public expression matrix by dataset, assay/sample and cell identity. The materializer cannot substitute locked predictions, embeddings or labels for missing expression values.

## Resolved source

The GSE302041 lateral-root founder block was extracted from the public Seurat RDS into `data/public/GSE302041_root_strict_triplet.h5ad` (32,833 source genes, 18,194 source cells, 256 selected cells). The generated H5AD SHA256 is `38bc9572b60442b59547ee739ec46580cae72757d87bb514960ddef4c6bfb2c3`.

## Remaining blocker

The downloaded GSE152766 spliced/unspliced raw-count RDS was checked assay by assay against the frozen root target IDs. The spliced assay matched 123/134 cells exactly, with 10 missing and 1 ambiguous; the unspliced assay matched 110/122 exactly, with 9 missing and 3 ambiguous. Thus 233 cells have a unique candidate, 23 are absent and 4 have multiple candidates. Because the remaining mapping is not unique, `arabidopsis_root_atlas` is deliberately left blank in `v9_strict_raw_source_map_v1.json` and `scripts/materialize_v9_strict_raw_input.py` stops at source preflight.

The current strict result therefore remains a locked-output replay, not a raw-H5AD end-to-end replay. This audit records the exact blocking evidence and prevents an unsupported raw-input claim.
