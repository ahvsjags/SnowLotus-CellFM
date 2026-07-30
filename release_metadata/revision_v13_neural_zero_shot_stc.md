# Plant-CellFM v13 Neural Zero-Shot STC Benchmark

Generated: 2026-07-31 04:35 Asia/Shanghai

This benchmark trains a fold-specific neural calibration head on frozen Plant-CellFM embeddings using only training-species labels. Held-out species labels are not used for training.

| Method | All-cell accuracy | Known-label accuracy | Macro-F1 | Coverage |
| --- | ---: | ---: | ---: | ---: |
| `linear_wp0_e80` | 0.2581 | 0.4616 | 0.1947 | 0.5590 |
| `linear_wp025_e80` | 0.2931 | 0.5244 | 0.2194 | 0.5590 |
| `linear_wp05_e80` | 0.2904 | 0.5194 | 0.2717 | 0.5590 |
| `linear_wp075_e80` | 0.2614 | 0.4675 | 0.2130 | 0.5590 |
| `linear_wp05_e40` | 0.2762 | 0.4941 | 0.2227 | 0.5590 |
| `linear_wp05_e120` | 0.3010 | 0.5384 | 0.2547 | 0.5590 |
| `linear_zscore_wp025_e80` | 0.3184 | 0.5695 | 0.3079 | 0.5590 |
| `linear_zscore_wp05_e80` | 0.2818 | 0.5041 | 0.3006 | 0.5590 |

## Best Method

Best method `linear_zscore_wp025_e80` reaches 31.84% all-cell accuracy and 56.95% known-label accuracy.

| Species | Cells | Coverage | All-cell accuracy | Known-label accuracy |
| --- | ---: | ---: | ---: | ---: |
| Arabidopsis thaliana | 2366 | 0.4328 | 0.2418 | 0.5586 |
| Brassica rapa | 256 | 0.9375 | 0.6016 | 0.6417 |
| Catharanthus roseus | 256 | 0.9414 | 0.0156 | 0.0166 |
| Eutrema salsugineum | 62 | 1.0000 | 0.9839 | 0.9839 |
| Fragaria vesca | 256 | 0.6289 | 0.4766 | 0.7578 |
| Gossypium bickii | 256 | 0.9062 | 0.3633 | 0.4009 |
| Gossypium hirsutum | 256 | 0.0000 | 0.0000 | n/a |
| Triticum aestivum | 256 | 1.0000 | 1.0000 | 1.0000 |

## Interpretation

Neural STC tests whether the 30.10% strict zero-shot bottleneck is a classifier-capacity problem. Neural heads alone do not approach 40%, which motivated the v14 context-aware STC layer. The subsequent `revision_v14_context_stc_benchmark` result reaches 42.36% all-cell accuracy under the same strict leave-species denominator.
