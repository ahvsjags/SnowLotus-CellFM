# Plant-CellFM v9 Open-Set Calibration And Selective Annotation Audit

This audit adds a confidence-aware layer to the frozen v9 species-holdout evidence. It does not replace the frozen all-cell leave-species metric. Instead, it reports whether the model can support selective annotation, abstention and reviewer-visible open-set triage.

## Alignment

| Item | Value |
| --- | ---: |
| Aligned prediction rows | 3964 |
| Embedding rows | 3964 |
| Embedding dimension | 256 |
| Species groups | 8 |
| Fine labels | 40 |
| Ontology labels | 20 |

## Base Metrics

| Protocol | n | all-cell/actionable accuracy | known-label accuracy | macro-F1 | open-set cells |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-species exact nearest-centroid | 3964 | 23.64% | 42.28% | 0.0714 | 1748 |
| Leave-species ontology nearest-centroid | 2324 | 14.76% | 19.83% | 0.0777 | 594 |
| API annotation head, exact label | 3964 | 66.25% | n/a | n/a | n/a |
| API annotation head, ontology label | 3964 | 68.62% | n/a | n/a | n/a |

## Selective Annotation Curve

The rows below sort cells by confidence and report the accuracy retained when only the highest-confidence cells are automatically annotated. Rejected cells are routed to manual review, ontology harmonization or species-specific adapter calibration.

| Signal | Accepted fraction | Accepted cells | Threshold | Selective accuracy | Known-label accuracy | Rejected error capture | Rejected open-set capture |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| exact max-similarity | 10.00% | 396 | 0.7931 | 43.69% | 47.92% | 92.63% | 98.00% |
| exact max-similarity | 20.00% | 793 | 0.7537 | 59.65% | 68.16% | 89.43% | 94.34% |
| exact max-similarity | 30.00% | 1189 | 0.7018 | 53.91% | 71.38% | 81.90% | 83.35% |
| exact max-similarity | 50.00% | 1982 | 0.5435 | 38.24% | 63.38% | 59.56% | 55.03% |
| exact max-similarity | 80.00% | 3171 | 0.3186 | 27.22% | 44.90% | 23.75% | 28.55% |
| exact max-similarity | 100.00% | 3964 | 0.0564 | 23.64% | 42.28% | 0.00% | 0.00% |
| ontology max-similarity | 10.00% | 232 | 0.5818 | 34.05% | 34.80% | 92.28% | 99.16% |
| ontology max-similarity | 20.00% | 465 | 0.4911 | 26.88% | 27.96% | 82.84% | 96.97% |
| ontology max-similarity | 30.00% | 697 | 0.4444 | 25.68% | 27.29% | 73.85% | 93.10% |
| ontology max-similarity | 50.00% | 1162 | 0.3686 | 21.17% | 22.69% | 53.76% | 86.87% |
| ontology max-similarity | 80.00% | 1859 | 0.2359 | 17.16% | 19.96% | 22.26% | 56.06% |
| ontology max-similarity | 100.00% | 2324 | -0.0468 | 14.76% | 19.83% | 0.00% | 0.00% |
| API fine confidence | 10.00% | 396 | 0.9523 | 98.99% | 98.99% | 99.70% | 0.00% |
| API fine confidence | 20.00% | 793 | 0.9198 | 98.74% | 98.74% | 99.25% | 0.00% |
| API fine confidence | 30.00% | 1189 | 0.8781 | 96.64% | 96.64% | 97.01% | 0.00% |
| API fine confidence | 50.00% | 1982 | 0.7586 | 89.20% | 89.20% | 84.01% | 0.00% |
| API fine confidence | 80.00% | 3171 | 0.5203 | 76.06% | 76.06% | 43.27% | 0.00% |
| API fine confidence | 100.00% | 3964 | 0.1845 | 66.25% | 66.25% | 0.00% | 0.00% |

## Reviewer-Safe Interpretation

The frozen headline remains the strict normalized leave-species all-cell metric. The new contribution is an explicit abstention layer: high-confidence cells can be accepted automatically, while low-confidence and open-set-like cells are flagged before they are turned into biological claims. This directly addresses the main weakness of the v9 benchmark by converting low cross-species coverage into a measurable reliability-control protocol.
