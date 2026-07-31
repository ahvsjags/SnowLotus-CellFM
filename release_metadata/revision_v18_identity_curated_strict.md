# Plant-CellFM v18 Identity-Curated Nested Strict Transfer

Generated: 2026-08-01 03:32 Asia/Shanghai

## Protocol

This is a companion benchmark, not a replacement for v17. Before any outer split, model fitting or inner candidate selection, labels beginning with `unknown`, `unknow` or `unannotated` are moved to an audit-only set. Target species labels remain inaccessible until final scoring.

| Label-integrity item | Value |
| --- | ---: |
| All public-label cells | 3,964 |
| Curated explicit-identity cells | 2,324 |
| Audit-only unknown/unannotated cells | 1,640 |
| Species retained | 5 / 8 |

| Metric on curated explicit identities | Value |
| --- | ---: |
| All-cell accuracy | 0.4079 |
| Known-label accuracy | 0.7054 |
| Known-label macro-F1 | 0.1497 |
| Train-label coverage | 0.5783 |

| Held-out species | Cells | Coverage | All-cell accuracy | Known-label accuracy | Nested selected decoder |
| --- | ---: | ---: | ---: | ---: | --- |
| Arabidopsis thaliana | 1447 | 0.4264 | 0.3103 | 0.7277 | `organ_context_prior` |
| Brassica rapa | 137 | 0.8832 | 0.3285 | 0.3719 | `organ_context_prior` |
| Catharanthus roseus | 243 | 0.9383 | 0.7325 | 0.7807 | `gate_leaf_support_64` |
| Fragaria vesca | 241 | 0.6058 | 0.5685 | 0.9384 | `gate_leaf_support_64` |
| Gossypium bickii | 256 | 0.9062 | 0.5430 | 0.5991 | `organ_context_prior` |

## Claim boundary

The v18 cohort contains only explicit reference identities and five species with at least one such identity. It does not establish universal species transfer, and it must be reported beside the full v17 all-public-label stress test rather than substituted for it.
