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

The repository now includes `release_metadata/external_benchmark_panel_v9.md`, which separates completed metrics from input-ready or access-limited comparators.

| Comparator | Status | Main metric | Evidence |
| --- | --- | --- | --- |
| Frozen v3 extended baseline | completed | v9 improves all-cell accuracy by +0.2470, +0.2045 and +0.0441 under leave-dataset, leave-sample and normalized leave-species protocols | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` |
| Seurat label transfer | completed | fine accuracy 0.2207, fine macro-F1 0.0603 on the frozen v9 subset export | `release_metadata/external_benchmarks/seurat_v9_subset.json` |
| Classical cosine centroid, SRP169576 sample holdout | completed | fine accuracy 0.7337, fine macro-F1 0.4873 | `release_metadata/strict_benchmarks/leaveout_srp169576_sample.centroid_baseline.json` |
| scPlantLLM | input-ready, metric missing in current release tree | 20,000-cell compatible input, 24,392 retained genes, 1.0 gene-vocabulary overlap | `release_metadata/scplantllm_input_readiness.md` |
| scPlantAnnotate | web/API authentication required | official web server reachable but anonymous scriptable execution unavailable in the current audit | `release_metadata/scplantannotate_access_audit.md` |

The scPlantLLM official repository and paper describe a transformer plant single-cell foundation model with public code and checkpoints, but the current Matpool host could not complete a GitHub checkout/download because repeated GitHub TLS transfers terminated early. Therefore the frozen v9 package records scPlantLLM as input-ready rather than fabricating a metric. scPlantAnnotate is treated similarly: its official web route is reachable, but the current audit detected authenticated API endpoints and no anonymous batch execution path.

For the frozen v9 submission, the claim-safe comparison statement is:

> Plant-CellFM v9 improves over the frozen v3 extended baseline on an identical public-plant shared-gene benchmark under leave-dataset, leave-sample and normalized leave-species protocols. A completed Seurat label-transfer comparator on the frozen v9 subset shows substantially lower annotation performance under the same exported benchmark setting. scPlantLLM and scPlantAnnotate are included as audited third-party interfaces and should be upgraded to completed comparisons only when their official weights, authenticated API, CLI or author-provided export path can be executed reproducibly.
