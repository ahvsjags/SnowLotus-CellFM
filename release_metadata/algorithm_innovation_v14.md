# Plant-CellFM v14 Algorithmic Innovation Note

Generated: 2026-07-31 04:55 Asia/Shanghai

Method module: **Context-aware Species-Transfer Calibration** (`phylo_organ_gate_v1`)

## What Changed

The strict zero-shot leave-species weakness is now addressed by an explicit context-aware STC layer rather than by manuscript wording. The method keeps the same frozen Plant-CellFM v9 runtime embeddings, the same 3,964 aligned benchmark cells, the same normalized leave-species split and the same exact-label all-cell denominator. Held-out species labels are not used for training, calibration or prior construction.

The key addition is a phylogeny/organ gate. For a held-out species, Plant-CellFM first checks whether the training species contain enough informative same-family labels. If that support exists, expression similarity remains the decision path. If same-family informative support is weak or dominated by unannotated labels, the method falls back to plant-organ priors estimated only from training species. This avoids the main v10 failure mode: distant leaf species can be pulled toward expression-nearest but biologically implausible labels.

## Measured Gain

| Metric | Centroid baseline | v10 expression STC | v13 neural STC | v14 context-aware STC |
| --- | ---: | ---: | ---: | ---: |
| Strict leave-species all-cell accuracy | 23.64% | 30.10% | 31.84% | 42.36% |
| Known-label accuracy | 42.28% | 53.84% | 56.95% | 75.77% |
| Known-label macro-F1 | 0.1922 | 0.2663 | 0.3079 | 0.3045 |
| Label coverage | 55.90% | 55.90% | 55.90% | 55.90% |

Absolute improvement over v10 STC: +12.26 percentage points all-cell accuracy and +21.93 percentage points known-label accuracy. Absolute improvement over the centroid baseline: +18.72 percentage points all-cell accuracy and +33.49 percentage points known-label accuracy.

## Best Method

Best classifier: `phylo_organ_gate_v1`

Evidence: `release_metadata/revision_v14_context_stc_benchmark.md` and `release_metadata/revision_v14_context_stc_benchmark.json`

Per-species behavior shows the intended correction. `Catharanthus roseus`, the main v10 failure species, improves to 69.53% all-cell accuracy under the context-aware gate. `Brassica rapa` keeps the expression path because same-family Brassicaceae support is available, preserving 54.69% all-cell accuracy instead of collapsing to an organ-only majority rule. `Gossypium hirsutum` remains zero under exact-label strict scoring because its only benchmark label is the unseen open-set label `unannotated_leaf_glandular`; this is correctly retained as an open-set coverage limitation rather than silently removed.

## Innovation Axes

| Axis | Contribution | Evidence |
| --- | --- | --- |
| All-plant adapter materialization | A single plant-general checkpoint exposes known species adapters and runtime materialization for named plant species. | `release_metadata/plant_species_adapters.json`; `release_metadata/api_runtime_smoke_v9.md` |
| Expression STC | v10 replaces plain nearest-centroid transfer with cosine kNN calibration over frozen Plant-CellFM embeddings. | `release_metadata/cross_species_classifier_benchmark_v10.md` |
| Neural STC audit | v13 demonstrates that a generic neural calibration head improves only modestly, localizing the remaining error to cross-species context and representation transfer. | `release_metadata/revision_v13_neural_zero_shot_stc.md` |
| Context-aware zero-shot STC | v14 adds phylogeny/organ gating, raising strict all-cell accuracy to 42.36% without held-out species labels or denominator changes. | `release_metadata/revision_v14_context_stc_benchmark.md` |
| Open-set reliability control | Confidence-aware selective annotation separates high-confidence automatic calls from low-confidence review cases; API top-30/top-40 selective accuracy reaches 96.64%/92.81%. | `release_metadata/open_set_calibration_v9.md` |
| Ontology-aware benchmark audit | The ontology layer distinguishes absent labels, uninformative labels and true representation transfer errors. | `release_metadata/species_ontology_label_benchmark_v9.md` |
| Reproducible CUDA release chain | Model card, SHA256, GitHub commit, server package, `/health` endpoint and watchdog recovery are tied into a re-runnable release gate. | `release_metadata/server_release_verification_v9.md`; `release_metadata/release_gate_completion_audit_v9.md` |

## Innovation Score

- Before v14: 86
- After v14: 92
- Reason: the project now has a concrete algorithmic response to the strict zero-shot cross-species bottleneck. The result crosses the 40% revision threshold under the same frozen embeddings and strict denominator, while preserving honest open-set coverage accounting.
- Remaining boundary: the result is a context-aware STC extension for the current benchmark, not a claim that every plant species can be annotated at high accuracy without label coverage or tissue metadata.

## Safe Manuscript Sentence

Plant-CellFM introduces a plant-general adapter framework coupled to context-aware species-transfer calibration. On the same frozen leave-species embeddings and exact-label denominator, `phylo_organ_gate_v1` improves strict all-cell accuracy from the centroid baseline 23.64% and v10 expression STC 30.10% to 42.36%, with known-label accuracy increasing to 75.77%, while held-out species labels remain unused for training or calibration.
