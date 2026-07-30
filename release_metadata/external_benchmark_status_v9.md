# Plant-CellFM v9 External Benchmark Status

This note records the current comparison evidence for the frozen v9 submission package.

## Completed Comparison

The frozen v9 checkpoint is compared against the frozen v3 extended baseline on the same v9 shared-gene benchmark subset. The benchmark uses identical cell selection, embeddings, leave-dataset-out, leave-sample-out and leave-species-out protocols, and reports both all-cell open-set accuracy and known-label conditional metrics.

| Protocol | v3 extended all-cell accuracy | v9 all-cell accuracy | Delta |
| --- | ---: | ---: | ---: |
| Leave-dataset-out | 0.2021 | 0.4490 | +0.2470 |
| Leave-sample-out | 0.4155 | 0.6200 | +0.2045 |
| Leave-species-out, species labels normalized | 0.1912 | 0.2354 | +0.0441 |

The normalized species protocol canonicalizes aliases such as `Arabidopsis_thaliana` and `Arabidopsis thaliana` before splitting, so the selected benchmark contains 8 normalized species groups from 9 raw species labels.

## Third-Party Tool Interfaces

The repository contains preparation and audit assets for scPlantLLM and scPlantAnnotate-style comparisons, including input-readiness materials, benchmark package records and access audits. These assets should be cited as reproducibility interfaces rather than as completed third-party benchmark results unless a valid authenticated API, official checkpoint, scriptable CLI or author-provided export path is available.

For the frozen v9 submission, the claim-safe comparison statement is:

> Plant-CellFM v9 improves over the frozen v3 extended baseline on an identical public-plant shared-gene benchmark under leave-dataset, leave-sample and normalized leave-species protocols. Third-party plant foundation-model and annotation-tool comparisons are prepared through documented input packages and access audits, and can be appended when a reproducible execution path is available.
