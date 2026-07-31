# Plant-CellFM v11 Few-Shot Target Adapter Benchmark

Generated: 2026-08-01 03:33 Asia/Shanghai

## Protocol Boundary

This revision benchmark does not replace the strict zero-shot leave-species STC result. It evaluates the target-species adapter setting: a small labeled support set from the held-out species is used to calibrate the adapter/classifier, and all support cells are excluded from the query evaluation.

## Summary

Zero-shot strict STC reference: `knn_cosine_k9` all-cell accuracy 30.10%, known-label accuracy 53.84%, coverage 55.90%.

| Mode | Support setting | Support weight | Query cells | Support cells | Accuracy mean | Accuracy min-max | Macro-F1 mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| budgeted_random | 8 cells/species | 3 | 3900.0 | 64.0 | 59.21% | 49.85%-67.15% | 0.2195 |
| budgeted_random | 16 cells/species | 3 | 3837.0 | 127.0 | 67.34% | 58.93%-71.18% | 0.2904 |
| budgeted_random | 32 cells/species | 3 | 3725.0 | 239.0 | 72.30% | 68.11%-73.77% | 0.3648 |
| budgeted_random | 64 cells/species | 3 | 3501.0 | 463.0 | 75.89% | 72.32%-78.09% | 0.4619 |
| stratified_per_label | 1 cell(s)/label | 1 | 3901.0 | 63.0 | 45.67% | 40.71%-49.76% | 0.3963 |
| stratified_per_label | 1 cell(s)/label | 3 | 3901.0 | 63.0 | 56.84% | 48.50%-66.27% | 0.4724 |
| stratified_per_label | 3 cell(s)/label | 3 | 3781.0 | 183.0 | 68.73% | 64.93%-72.04% | 0.5356 |
| stratified_per_label | 5 cell(s)/label | 1 | 3667.0 | 297.0 | 73.08% | 70.52%-75.51% | 0.5465 |

## Revision Claim

Under the target-species adapter protocol, the best frozen-embedding few-shot setting reaches 75.89% mean query all-cell accuracy. The most conservative fixed-budget setting tested, 8 labeled cells per target species, already exceeds the 40% revision target.

## Representative Per-Species Query Accuracy

Representative configuration: `budgeted_random`, support value `64`, support weight `3`, seed `0`.

| Species | Query cells | Support cells | Support labels | Query accuracy | Top residual errors |
| --- | ---: | ---: | ---: | ---: | --- |
| Arabidopsis thaliana | 2302 | 64 | 16 | 72.68% | Mesophyll -> Xylem (57); Root cortex -> Root cap (38); proximal meristem -> stem cell niche (37) |
| Brassica rapa | 192 | 64 | 6 | 73.44% | Unknow -> Mesophyll (12); Mesophyll -> Unknow (10); Bundle sheath -> Unknow (8) |
| Catharanthus roseus | 192 | 64 | 6 | 72.40% | Mesophyll -> Leaf epidermis (10); Leaf epidermis -> Mesophyll (9); Unknow -> Mesophyll (8) |
| Eutrema salsugineum | 47 | 15 | 1 | 100.00% |  |
| Fragaria vesca | 192 | 64 | 6 | 63.02% | Hydathodes -> Mesophyll (19); Mesophyll -> Hydathodes (18); Unknow -> Mesophyll (10) |
| Gossypium bickii | 192 | 64 | 5 | 72.92% | Procambium -> Mesophyll (7); Mesophyll -> Leaf epidermis (7); Xylem -> Mesophyll (6) |
| Gossypium hirsutum | 192 | 64 | 1 | 100.00% |  |
| Triticum aestivum | 192 | 64 | 1 | 100.00% |  |

## Safe Reporting Sentence

Plant-CellFM v11 keeps zero-shot strict leave-species STC as the conservative benchmark and adds a target-species adapter protocol: with only 8 randomly labeled support cells per held-out species, query all-cell accuracy exceeds 40%, and larger support budgets approach the deployable runtime-head range.
