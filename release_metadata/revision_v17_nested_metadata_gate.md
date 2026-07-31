# Plant-CellFM v17 Nested Metadata-Gated Transfer

Generated: 2026-08-01 02:41 Asia/Shanghai

Every configuration is selected inside each outer training fold by leaving source species out. Target cell labels never enter selector fitting, model fitting or calibration.

| Metric | Value |
| --- | ---: |
| All-cell accuracy | 0.3996 |
| Known-label accuracy | 0.7148 |
| Known-label macro-F1 | 0.2817 |
| Train-label coverage | 0.5590 |

| Held-out species | Nested selected method | Cells | Coverage | All-cell accuracy | Known-label accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| Arabidopsis thaliana | `organ_context_prior` | 2366 | 0.4328 | 0.3242 | 0.7490 |
| Brassica rapa | `organ_context_prior` | 256 | 0.9375 | 0.1758 | 0.1875 |
| Catharanthus roseus | `gate_leaf_support_64` | 256 | 0.9414 | 0.6953 | 0.7386 |
| Eutrema salsugineum | `gate_leaf_support_64` | 62 | 1.0000 | 1.0000 | 1.0000 |
| Fragaria vesca | `gate_leaf_support_64` | 256 | 0.6289 | 0.5352 | 0.8509 |
| Gossypium bickii | `gate_leaf_support_64` | 256 | 0.9062 | 0.5430 | 0.5991 |
| Gossypium hirsutum | `gate_leaf_support_64` | 256 | 0.0000 | 0.0000 | 0.0000 |
| Triticum aestivum | `gate_leaf_support_64` | 256 | 1.0000 | 1.0000 | 1.0000 |

## Claim boundary

This experiment replaces a globally selected rule with nested source-species selection. It remains strict zero-shot because target labels are excluded from training, gate selection and prior estimation.
