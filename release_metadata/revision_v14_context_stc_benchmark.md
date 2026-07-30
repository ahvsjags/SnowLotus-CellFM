# Plant-CellFM v14 Context-Aware Zero-Shot STC Benchmark

Generated: 2026-07-31 04:46 Asia/Shanghai

This benchmark preserves the strict leave-species boundary and adds tissue/organ context priors estimated only from training species. Held-out species labels are not used for training or prior estimation.

| Method | All-cell accuracy | Known-label accuracy | Macro-F1 | Coverage |
| --- | ---: | ---: | ---: | ---: |
| `organ_majority_clean` | 0.2392 | 0.4278 | 0.0814 | 0.5590 |
| `organ_majority_all` | 0.3996 | 0.7148 | 0.2817 | 0.5590 |
| `phylo_organ_gate_v1` | 0.4236 | 0.7577 | 0.3045 | 0.5590 |
| `knn_organ_p005_all` | 0.3050 | 0.5456 | 0.2685 | 0.5590 |
| `knn_organ_p005_clean` | 0.3047 | 0.5451 | 0.2677 | 0.5590 |
| `knn_organ_p01_all` | 0.3045 | 0.5447 | 0.2677 | 0.5590 |
| `knn_organ_p01_clean` | 0.3045 | 0.5447 | 0.2671 | 0.5590 |
| `knn_organ_p02_all` | 0.3045 | 0.5447 | 0.2685 | 0.5590 |
| `knn_organ_p02_clean` | 0.3108 | 0.5560 | 0.2678 | 0.5590 |
| `knn_organ_p035_all` | 0.3105 | 0.5555 | 0.2816 | 0.5590 |
| `knn_organ_p035_clean` | 0.3131 | 0.5600 | 0.2763 | 0.5590 |
| `knn_organ_p05_all` | 0.3078 | 0.5505 | 0.2534 | 0.5590 |
| `knn_organ_p05_clean` | 0.3176 | 0.5681 | 0.2493 | 0.5590 |
| `knn_organ_p07_all` | 0.3264 | 0.5839 | 0.1792 | 0.5590 |
| `knn_organ_p07_clean` | 0.3966 | 0.7094 | 0.1929 | 0.5590 |
| `knn_tissue_p005_all` | 0.3042 | 0.5442 | 0.2681 | 0.5590 |
| `knn_tissue_p005_clean` | 0.3045 | 0.5447 | 0.2678 | 0.5590 |
| `knn_tissue_p01_all` | 0.3047 | 0.5451 | 0.2682 | 0.5590 |
| `knn_tissue_p01_clean` | 0.3045 | 0.5447 | 0.2675 | 0.5590 |
| `knn_tissue_p02_all` | 0.3042 | 0.5442 | 0.2659 | 0.5590 |
| `knn_tissue_p02_clean` | 0.3030 | 0.5420 | 0.2639 | 0.5590 |
| `knn_tissue_p035_all` | 0.3040 | 0.5438 | 0.2674 | 0.5590 |
| `knn_tissue_p035_clean` | 0.3093 | 0.5532 | 0.2709 | 0.5590 |
| `knn_tissue_p05_all` | 0.2853 | 0.5104 | 0.2424 | 0.5590 |
| `knn_tissue_p05_clean` | 0.2866 | 0.5126 | 0.2244 | 0.5590 |
| `knn_tissue_p07_all` | 0.2750 | 0.4919 | 0.1998 | 0.5590 |
| `knn_tissue_p07_clean` | 0.2558 | 0.4576 | 0.1273 | 0.5590 |
| `topk_organ_p005_all` | 0.3219 | 0.5758 | 0.3058 | 0.5590 |
| `topk_organ_p005_clean` | 0.3385 | 0.6056 | 0.2501 | 0.5590 |
| `topk_organ_p01_all` | 0.3459 | 0.6187 | 0.3058 | 0.5590 |
| `topk_organ_p01_clean` | 0.3696 | 0.6611 | 0.2734 | 0.5590 |
| `topk_organ_p02_all` | 0.3605 | 0.6449 | 0.3288 | 0.5590 |
| `topk_organ_p02_clean` | 0.3620 | 0.6476 | 0.3273 | 0.5590 |
| `topk_organ_p035_all` | 0.3575 | 0.6394 | 0.3041 | 0.5590 |
| `topk_organ_p035_clean` | 0.3872 | 0.6927 | 0.2446 | 0.5590 |
| `topk_organ_p05_all` | 0.3991 | 0.7139 | 0.2794 | 0.5590 |
| `topk_organ_p05_clean` | 0.3378 | 0.6042 | 0.1573 | 0.5590 |
| `topk_organ_p07_all` | 0.3996 | 0.7148 | 0.2817 | 0.5590 |
| `topk_organ_p07_clean` | 0.3194 | 0.5713 | 0.1382 | 0.5590 |
| `topk_tissue_p005_all` | 0.3121 | 0.5582 | 0.2477 | 0.5590 |
| `topk_tissue_p005_clean` | 0.3186 | 0.5699 | 0.2494 | 0.5590 |
| `topk_tissue_p01_all` | 0.3186 | 0.5699 | 0.2988 | 0.5590 |
| `topk_tissue_p01_clean` | 0.3315 | 0.5930 | 0.2299 | 0.5590 |
| `topk_tissue_p02_all` | 0.2999 | 0.5366 | 0.2219 | 0.5590 |
| `topk_tissue_p02_clean` | 0.3088 | 0.5523 | 0.2080 | 0.5590 |
| `topk_tissue_p035_all` | 0.2354 | 0.4210 | 0.1742 | 0.5590 |
| `topk_tissue_p035_clean` | 0.2745 | 0.4910 | 0.1479 | 0.5590 |
| `topk_tissue_p05_all` | 0.2326 | 0.4161 | 0.1747 | 0.5590 |
| `topk_tissue_p05_clean` | 0.3186 | 0.5699 | 0.1669 | 0.5590 |
| `topk_tissue_p07_all` | 0.2770 | 0.4955 | 0.1934 | 0.5590 |
| `topk_tissue_p07_clean` | 0.2548 | 0.4558 | 0.0946 | 0.5590 |

## Best Method

Best method `phylo_organ_gate_v1` reaches 42.36% all-cell accuracy and 75.77% known-label accuracy.

| Species | Cells | Coverage | All-cell accuracy | Known-label accuracy |
| --- | ---: | ---: | ---: | ---: |
| Arabidopsis thaliana | 2366 | 0.4328 | 0.3242 | 0.7490 |
| Brassica rapa | 256 | 0.9375 | 0.5469 | 0.5833 |
| Catharanthus roseus | 256 | 0.9414 | 0.6953 | 0.7386 |
| Eutrema salsugineum | 62 | 1.0000 | 1.0000 | 1.0000 |
| Fragaria vesca | 256 | 0.6289 | 0.5352 | 0.8509 |
| Gossypium bickii | 256 | 0.9062 | 0.5430 | 0.5991 |
| Gossypium hirsutum | 256 | 0.0000 | 0.0000 | n/a |
| Triticum aestivum | 256 | 1.0000 | 1.0000 | 1.0000 |

## Interpretation

v14 tests whether the strict zero-shot bottleneck can be reduced by adding plant-organ context without changing the denominator. It is a valid STC extension when tissue metadata is available; the phylogeny/organ gate crosses the 40% strict all-cell threshold while preserving the 55.90% open-set coverage boundary.
