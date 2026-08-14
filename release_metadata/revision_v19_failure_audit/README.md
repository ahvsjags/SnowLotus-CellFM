# Revision v19 strict cross-species failure audit

This audit is diagnostic only. It does not alter the strict benchmark or use held-out labels.

- Test cells: 3964
- Coverage: 0.5590
- All-cell accuracy: 0.3996
- Covered-label accuracy: 0.7148
- Macro-F1: 0.2817

## Priority order

| Held-out species | n | coverage | all-cell | covered-label | open-set cells | covered errors | failure mode |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Arabidopsis thaliana | 2366 | 0.4328 | 0.3242 | 0.7490 | 1342 | 257.0 | coverage_bottleneck |
| Gossypium hirsutum | 256 | 0.0000 | 0.0000 | NA | 256 | NA | ontology_or_gene_overlap_gap |
| Brassica rapa | 256 | 0.9375 | 0.1758 | 0.1875 | 16 | 195.0 | covered_label_transfer_failure |
| Fragaria vesca | 256 | 0.6289 | 0.5352 | 0.8509 | 95 | 24.0 | coverage_bottleneck |
| Gossypium bickii | 256 | 0.9062 | 0.5430 | 0.5991 | 24 | 93.0 | moderate_transfer_failure |
| Catharanthus roseus | 256 | 0.9414 | 0.6953 | 0.7386 | 15 | 63.0 | moderate_transfer_failure |
| Eutrema salsugineum | 62 | 1.0000 | 1.0000 | 1.0000 | 0 | 0.0 | strong_or_mixed_transfer |
| Triticum aestivum | 256 | 1.0000 | 1.0000 | 1.0000 | 0 | 0.0 | strong_or_mixed_transfer |

## Interpretation

The first model-side priority is to recover source-only ontology/gene overlap for zero-coverage species and the second is to reduce covered-label transfer errors in large held-out cohorts. The 80% all-cell target requires both coverage and conditional accuracy to improve; changing the denominator is not an acceptable intervention.
