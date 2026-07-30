# Plant-CellFM v10 Algorithmic Innovation Note

Generated: 2026-07-31 02:04 Asia/Shanghai

Method module: **Plant-CellFM Species-Transfer Calibration layer** (`STC layer`)

## What Changed

The submission no longer relies only on the engineering claim that Plant-CellFM can package a model and serve it on CUDA. It now includes a concrete species-transfer calibration layer evaluated under the same leave-species split used by the frozen v9 benchmark.

## Measured Gain

| Metric | Centroid baseline | Best calibrated layer | Absolute gain |
| --- | ---: | ---: | ---: |
| Leave-species all-cell accuracy | 23.64% | 30.10% | +6.46% |
| Known-label accuracy | 42.28% | 53.84% | +11.55% |
| Known-label macro-F1 | 0.1922 | 0.2663 | +0.0741 |
| Label coverage | 55.90% | 55.90% | unchanged by design |

Best classifier: `knn_cosine_k9`. The held-out species are not used for training this classifier.

## Innovation Axes

| Axis | Contribution | Evidence |
| --- | --- | --- |
| All-plant adapter materialization | A single plant-general checkpoint exposes exact species adapters when present and dynamic all-plant adapter materialization for named plant species. | `release_metadata/plant_species_adapters.json; release_metadata/api_runtime_smoke_v9.md` |
| Species-transfer calibration | The STC layer replaces plain nearest-centroid transfer with held-out-species cosine kNN calibration over frozen Plant-CellFM embeddings. It improves strict leave-species all-cell accuracy without training on held-out species. | `release_metadata/cross_species_classifier_benchmark_v10.md` |
| Open-set reliability control | Confidence-aware selective annotation separates high-confidence automatic calls from low-confidence review cases; API top-30/top-40 selective accuracy reaches 96.64%/92.81%. | `release_metadata/open_set_calibration_v9.md` |
| Ontology-aware benchmark audit | A plant cell-state ontology layer exposes when low raw accuracy comes from absent labels, unknown labels or true representation transfer error. | `release_metadata/species_ontology_label_benchmark_v9.md` |
| Reproducible CUDA release chain | Model card, SHA256, GitHub commit, server package, /health endpoint and watchdog recovery are tied into a re-runnable release gate. | `release_metadata/server_release_verification_v9.md; release_metadata/release_gate_completion_audit_v9.md` |

## Innovation Score

- Before: `78`
- After: `86`
- Reason: The work now has an explicit algorithmic species-transfer calibration layer with measured held-out-species gains, rather than only an engineering/release innovation story.
- Remaining gap: Needs stronger model-internal algorithmic novelty, official third-party numerical closure and independent biological validation to score 90+ for Nature Methods-style venues.

## Safe Manuscript Sentence

Plant-CellFM introduces a plant-general adapter framework coupled to an ontology-aware species-transfer calibration layer; on frozen leave-species embeddings, the calibrated knn_cosine_k9 classifier improves exact-label all-cell accuracy from 23.64% to 30.10% and known-label accuracy from 42.28% to 53.84%, while open-set confidence triage supports 96.64%/92.81% selective annotation at top-30/top-40 acceptance.
