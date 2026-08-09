# Plant-CellFM v9 External Benchmark Panel

This panel separates completed metrics from official-source benchmark contracts whose final numeric closure still depends on official weights, authenticated APIs or exported predictions.

- Rows: `8`
- Completed metric rows: `6`
- Completed formal comparisons: `5`
- Claim-safe position: Plant-CellFM v9 has a completed frozen v3 comparison and a classical sample-holdout baseline. Seurat label transfer is included as a completed traditional external baseline. scPlantLLM remains contract-ready until the official checkpoint/probe metric is present; scPlantAnnotate remains contract-ready until authenticated or exported official predictions are available.

| Comparator | Protocol | Status | Main accuracy | Macro-F1 | Evidence |
| --- | --- | --- | ---: | ---: | --- |
| Plant-CellFM v9 vs frozen v3 extended | Leave-dataset-out | completed | 0.4490 | 0.3485 | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` |
| Plant-CellFM v9 vs frozen v3 extended | Leave-sample-out | completed | 0.6200 | 0.4902 | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` |
| Plant-CellFM v9 vs frozen v3 extended | Leave-species-out, species labels normalized | completed | 0.2354 | 0.1918 | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` |
| Classical cosine centroid, group-random split | group_random | completed | 0.7583 | 0.7125 | `release_metadata/strict_benchmarks/public_sprint_group_random.centroid_baseline.json` |
| Classical cosine centroid, SRP169576 sample holdout | explicit_leaveout | completed | 0.7337 | 0.4873 | `release_metadata/strict_benchmarks/leaveout_srp169576_sample.centroid_baseline.json` |
| scPlantLLM frozen embedding nearest-centroid probe | public sprint train/test chunks | contract_ready_metric_pending | - | - | `release_metadata/scplantllm_input_readiness.json` |
| Seurat label transfer | exported train/test split | completed | 0.2207 | 0.0603 | `release_metadata/external_benchmarks/seurat_v9_subset.json` |
| scPlantAnnotate | frozen 5,000-cell/12-class official web/API contract | contract_ready_auth_limited | - | - | `release_metadata/scplantannotate_formal_benchmark_v1.json` |

## Interpretation

The strongest completed comparison remains the frozen v9 versus frozen v3 extended benchmark on the same shared-gene public-plant subset. The SRP169576 sample-holdout centroid baseline provides a transparent classical comparator, and the Seurat label-transfer run adds a completed traditional external baseline. scPlantAnnotate now has a hash-locked 5,000-cell/12-class input and truth contract; it remains excluded from completed metrics until the authenticated official prediction export is scored.
