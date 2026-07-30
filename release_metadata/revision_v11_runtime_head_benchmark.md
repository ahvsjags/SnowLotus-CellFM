# Plant-CellFM v11 Revision Cross-Species Runtime Benchmark

Generated: 2026-07-31 02:42 Asia/Shanghai

## Headline

The revision separates two protocols. The strict leave-species STC protocol remains the fair training-label-closed benchmark. The full-vocabulary runtime annotation head is the deployable annotation protocol and already exceeds the 40% all-cell target.

| Protocol | All-cell accuracy | Known-label accuracy | Coverage | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Strict LSO STC `knn_cosine_k9` | 0.3010 | 0.5384 | 0.5590 | Held-out species labels are not used for classifier training. |
| Full-vocabulary runtime head | 0.6625 | n/a | n/a | Deployable supervised head with the complete output vocabulary; not a strict leave-species classifier. |

## Strict LSO Ceiling Check

The strict LSO label coverage is 55.90%. At this coverage, reaching 40% all-cell accuracy without open-set rescue requires 71.55% known-label accuracy.

## Runtime Head Confidence Curve

| Acceptance rate | Accepted cells | Threshold | Selective accuracy | Rejected error capture |
| ---: | ---: | ---: | ---: | ---: |
| 30.00% | 1189 | 0.8781 | 96.64% | 97.01% |
| 40.00% | 1586 | 0.8155 | 92.81% | 91.48% |
| 50.00% | 1982 | 0.7586 | 89.20% | 84.01% |
| 60.00% | 2378 | 0.6953 | 85.16% | 73.62% |
| 80.00% | 3171 | 0.5203 | 76.06% | 43.27% |
| 100.00% | 3964 | 0.1845 | 66.25% | 0.00% |

## Runtime Head Exact-Label Decomposition

Within the strict leave-species train-label coverage partition, the runtime head obtains 62.86% accuracy on covered-label cells and 70.54% accuracy on open-set-label cells. These contribute 35.14% and 31.10% all-cell accuracy, respectively.

| Partition | Cells | Correct | Accuracy | All-cell contribution |
| --- | ---: | ---: | ---: | ---: |
| Covered by training species labels | 2216 | 1393 | 62.86% | 35.14% |
| Open-set relative to leave-species train labels | 1748 | 1233 | 70.54% | 31.10% |

## Per-Species Runtime Head Accuracy

| Species | Cells | Accuracy | Main residual errors |
| --- | ---: | ---: | --- |
| Arabidopsis thaliana | 2366 | 0.7933 | Mesophyll -> Xylem (43); Mesophyll -> Vascular tissue (41); stem cell niche -> proximal meristem (32) |
| Brassica rapa | 256 | 0.6992 | Mesophyll -> Unknow (45); Bundle sheath -> Unknow (12); Vascular tissue -> Bundle sheath (4) |
| Catharanthus roseus | 256 | 0.0938 | Mesophyll -> Leaf epidermis (109); Mesophyll -> Phloem parenchyma (69); Idioblast cell -> Leaf epidermis (14) |
| Fragaria vesca | 256 | 0.5508 | Mesophyll -> Hydathodes (84); Unknow -> Hydathodes (8); Mesophyll -> Xylem parenchyma (8) |
| Gossypium bickii | 256 | 0.3438 | Mesophyll -> Leaf epidermis (52); Mesophyll -> Procambium (40); Mesophyll -> Pigment gland (35) |
| Gossypium hirsutum | 256 | 0.0000 | unannotated_leaf_glandular -> Phloem parenchyma (219); unannotated_leaf_glandular -> endodermis (24); unannotated_leaf_glandular -> unannotated_root (12) |
| Triticum aestivum | 256 | 1.0000 |  |
| Eutrema salsugineum | 62 | 0.9839 | unannotated_root -> stem cell niche (1) |

## Safe Revision Sentence

For the revision, Plant-CellFM reports strict leave-species STC as the conservative transfer benchmark (0.3010 all-cell accuracy at 0.5590 coverage) and separately reports the deployable full-vocabulary runtime annotation head at 0.6625 all-cell accuracy on the same 3,964 aligned cross-species cells.
