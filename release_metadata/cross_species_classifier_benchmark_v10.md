# Plant-CellFM v10 Cross-Species Classifier Benchmark

This benchmark reuses the frozen v9 runtime-smoke embeddings and the same leave-species-out split. It tests whether classifier/metric calibration can improve exact-label species transfer without changing the held-out species labels or using held-out species for training.

## Summary

| Label key | Method | all-cell accuracy | known-label accuracy | macro-F1 | coverage | open-set cells |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| cell_type | centroid_cosine | 0.2364 | 0.4228 | 0.1922 | 0.5590 | 1748 |
| cell_type | knn_cosine_k1 | 0.2704 | 0.4838 | 0.2079 | 0.5590 | 1748 |
| cell_type | knn_cosine_k3 | 0.2944 | 0.5266 | 0.2407 | 0.5590 | 1748 |
| cell_type | knn_cosine_k5 | 0.2979 | 0.5329 | 0.2571 | 0.5590 | 1748 |
| cell_type | knn_cosine_k7 | 0.2969 | 0.5311 | 0.2516 | 0.5590 | 1748 |
| cell_type | knn_cosine_k9 | 0.3010 | 0.5384 | 0.2663 | 0.5590 | 1748 |
| cell_type | knn_cosine_k11 | 0.2972 | 0.5316 | 0.2538 | 0.5590 | 1748 |
| cell_type | knn_cosine_k15 | 0.2957 | 0.5289 | 0.2456 | 0.5590 | 1748 |
| cell_type | knn_cosine_k21 | 0.2921 | 0.5226 | 0.2363 | 0.5590 | 1748 |
| cell_type | knn_cosine_k31 | 0.2883 | 0.5158 | 0.2210 | 0.5590 | 1748 |
| cell_type | knn_cosine_uniform_k5 | 0.2977 | 0.5325 | 0.2515 | 0.5590 | 1748 |
| cell_type | knn_cosine_uniform_k9 | 0.2931 | 0.5244 | 0.2554 | 0.5590 | 1748 |
| cell_type | knn_cosine_uniform_k15 | 0.2830 | 0.5063 | 0.2092 | 0.5590 | 1748 |
| cell_type_coarse | centroid_cosine | 0.2364 | 0.4228 | 0.1922 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k1 | 0.2704 | 0.4838 | 0.2079 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k3 | 0.2944 | 0.5266 | 0.2407 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k5 | 0.2979 | 0.5329 | 0.2571 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k7 | 0.2969 | 0.5311 | 0.2516 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k9 | 0.3010 | 0.5384 | 0.2663 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k11 | 0.2972 | 0.5316 | 0.2538 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k15 | 0.2957 | 0.5289 | 0.2456 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k21 | 0.2921 | 0.5226 | 0.2363 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_k31 | 0.2883 | 0.5158 | 0.2210 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_uniform_k5 | 0.2977 | 0.5325 | 0.2515 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_uniform_k9 | 0.2931 | 0.5244 | 0.2554 | 0.5590 | 1748 |
| cell_type_coarse | knn_cosine_uniform_k15 | 0.2830 | 0.5063 | 0.2092 | 0.5590 | 1748 |

## Interpretation

An all-cell improvement here is a real held-out-species improvement for the frozen embedding plus classifier layer. The maximum exact-label all-cell accuracy remains limited by labels absent from the training species folds, so coverage is reported beside every score.
