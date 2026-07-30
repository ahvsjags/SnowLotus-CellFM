# Plant-CellFM v9 Ontology-Label Species-Holdout Benchmark

This benchmark reuses the frozen v9 runtime-smoke embeddings and evaluates leave-species-out nearest-centroid transfer after mapping observed fine labels into a conservative plant cell-state ontology. Unknown and unannotated labels are excluded from the ontology-actionable denominator. The frozen exact-label benchmark remains the controlling headline metric.

## Alignment

| Item | Value |
| --- | ---: |
| Prediction rows | 3964 |
| Obs rows | 7424 |
| Aligned rows | 3964 |
| Missing prediction cell IDs | 0 |
| Embedding rows | 3964 |
| Embedding dimension | 256 |

## Aggregate Metrics

| Metric | Frozen exact-label benchmark | Recomputed exact labels | Ontology-actionable labels |
| --- | ---: | ---: | ---: |
| Test cells | 3964 | 3964 | 2324 / 3964 actionable |
| Unknown/unannotated excluded | 0 | 0 | 1640 (41.37%) |
| Coverage | 55.90% | 55.90% | 74.44% |
| All-cell/actionable accuracy | 23.54% | 23.64% | 14.97% |
| Known-label accuracy | 42.10% | 42.28% | 20.12% |
| Known-label macro-F1 | 0.1918 | 0.1919 | 0.1395 |

## Per-Species Ontology Records

| Species | actionable n | excluded unknown | coverage | action accuracy | known accuracy | macro-F1 | status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Arabidopsis thaliana | 1447 | 919 | 66.90% | 9.54% | 14.26% | 0.1219 | ok |
| Brassica rapa | 137 | 119 | 88.32% | 34.31% | 38.84% | 0.1917 | ok |
| Catharanthus roseus | 243 | 13 | 93.83% | 7.00% | 7.46% | 0.0630 | ok |
| Eutrema salsugineum | 0 | 62 | - | - | - | - | insufficient_labels |
| Fragaria vesca | 241 | 15 | 75.10% | 23.65% | 31.49% | 0.0816 | ok |
| Gossypium bickii | 256 | 0 | 90.62% | 34.77% | 38.36% | 0.3063 | ok |
| Gossypium hirsutum | 0 | 256 | - | - | - | - | insufficient_labels |
| Triticum aestivum | 0 | 256 | - | - | - | - | insufficient_labels |

## Interpretation

The ontology-actionable benchmark is stricter than a simple coverage audit because it uses the model embeddings and a leave-species nearest-centroid protocol. It should be reported as an additional label-harmonized diagnostic, not as a replacement for the frozen exact-label species-holdout result.

Large unknown/unannotated exclusions indicate that public plant single-cell labels remain a major bottleneck. A higher-tier revision should freeze both exact-label and ontology-label species-holdout protocols before making stronger cross-species claims.
