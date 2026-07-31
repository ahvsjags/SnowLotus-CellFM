# Plant-CellFM v16 Nested Hierarchical Probe

Generated: 2026-08-01 02:38 Asia/Shanghai

## Protocol

Every outer held-out species uses a separately selected learned classifier. Candidate selection is nested inside the remaining source species, so no held-out label is used to select regularisation, organ-context scale or prior weight.

| Summary metric | Value |
| --- | ---: |
| All-cell accuracy | 0.3532 |
| Known-label accuracy | 0.6318 |
| Known-label macro-F1 | 0.2643 |
| Train-label coverage | 0.5590 |

| Held-out species | Selected nested configuration | Cells | Coverage | All-cell accuracy | Known-label accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| Arabidopsis thaliana | `hierarchical_lr_c3_o10_p015` | 2366 | 0.4328 | 0.3195 | 0.7383 |
| Brassica rapa | `hierarchical_lr_c01_o05_p015` | 256 | 0.9375 | 0.1758 | 0.1875 |
| Catharanthus roseus | `embedding_lr_c1` | 256 | 0.9414 | 0.0000 | 0.0000 |
| Eutrema salsugineum | `embedding_lr_c1` | 62 | 1.0000 | 0.9839 | 0.9839 |
| Fragaria vesca | `embedding_lr_c1` | 256 | 0.6289 | 0.5586 | 0.8882 |
| Gossypium bickii | `embedding_lr_c1` | 256 | 0.9062 | 0.5625 | 0.6207 |
| Gossypium hirsutum | `embedding_lr_c1` | 256 | 0.0000 | 0.0000 | 0.0000 |
| Triticum aestivum | `embedding_lr_c1` | 256 | 1.0000 | 0.9805 | 0.9805 |

## Claim boundary

This is a learned classifier-side ablation on frozen embeddings. It is a strict zero-shot result only because every configuration is selected within outer training species. It does not use target-species labels, target-cell support labels or the deployment annotation head.
