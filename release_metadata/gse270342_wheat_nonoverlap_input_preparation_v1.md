# GSE270342 Wheat Root Non-overlap Diagnostic Input

- Author object: `GSE270342_seuratObj_for_publication.rds.gz` from `GSE270342`.
- Retained matrix: 7164 cells x 78115 IWGSC v2.1-style wheat features.
- Exact prior strict-transfer cells excluded: 224.
- Checkpoint-compatible feature coverage: 53.75% genes and 76.33% UMI counts.

## Evidence Boundary

- Exact barcodes from the previously recorded `GSM8339904_rep1` strict-transfer subset are removed before frozen inference.
- The remaining cells still originate from the same public study, so this is a provenance-aware author-label re-audit rather than an independent external benchmark.
- Any accuracy calculation must use a predeclared coarse author-to-model mapping and must not replace the nested leave-species primary result.
- Orthology is represented as author-published many-to-many orthogroups; the inference loader applies a deterministic first-target collapse and records the resulting coverage.
