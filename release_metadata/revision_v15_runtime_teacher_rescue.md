# Plant-CellFM v15 Runtime-Teacher Rescue Benchmark

Generated: 2026-07-31 15:53 Asia/Shanghai

## Protocol Boundary

This file deliberately separates protocols. `strict_inductive_zero_shot` keeps the v14 leave-species boundary and does not use held-out labels or the runtime annotation head. `deployment_high_confidence_teacher_rescue` uses the already-trained Plant-CellFM runtime annotation head as a high-confidence teacher and is therefore a deployment/readiness metric, not the strict leave-species zero-shot headline.

## Summary

| Method | Protocol | All-cell accuracy | Known-label accuracy | Macro-F1 | Open-set exact accuracy | Coverage | Teacher acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `strict_inductive_v14_phylo_organ_gate` | strict_inductive_zero_shot | 0.4236 | 0.7577 | 0.3045 | 0.0000 | 0.5590 | 0.0000 |
| `runtime_teacher_only` | deployment_runtime_annotation_head | 0.6625 | 0.6286 | 0.3408 | 0.7054 | 0.5590 | 1.0000 |
| `teacher_rescue_t05_v14fallback` | deployment_high_confidence_teacher_rescue | 0.5918 | 0.6674 | 0.3294 | 0.4960 | 0.5590 | 0.8216 |
| `teacher_rescue_t06_v14fallback` | deployment_high_confidence_teacher_rescue | 0.5926 | 0.6968 | 0.3296 | 0.4605 | 0.5590 | 0.7144 |
| `teacher_rescue_t07_v14fallback` | deployment_high_confidence_teacher_rescue | 0.6009 | 0.7396 | 0.3485 | 0.4251 | 0.5590 | 0.5916 |
| `teacher_rescue_t08_v14fallback` | deployment_high_confidence_teacher_rescue | 0.5981 | 0.7681 | 0.3626 | 0.3827 | 0.5590 | 0.4208 |
| `teacher_rescue_t085_v14fallback` | deployment_high_confidence_teacher_rescue | 0.5916 | 0.7820 | 0.3681 | 0.3501 | 0.5590 | 0.3509 |
| `teacher_rescue_t09_v14fallback` | deployment_high_confidence_teacher_rescue | 0.5517 | 0.7856 | 0.3743 | 0.2551 | 0.5590 | 0.2568 |
| `teacher_rescue_t095_v14fallback` | deployment_high_confidence_teacher_rescue | 0.4425 | 0.7708 | 0.3730 | 0.0263 | 0.5590 | 0.1062 |

## Main Takeaway

The strict inductive v14 result remains 42.36% all-cell accuracy and 75.77% known-label accuracy. This is the no-held-out-label cross-species headline.
The best v15 deployment method `runtime_teacher_only` reaches 66.25% all-cell accuracy, 62.86% known-label accuracy and 70.54% open-set exact accuracy by allowing the runtime annotation head to rescue high-confidence cells.
Among v14-fallback rescue methods, `teacher_rescue_t07_v14fallback` reaches 60.09% all-cell accuracy and 73.96% known-label accuracy, retaining the strict v14 classifier whenever teacher confidence is below threshold.

## Per-Species Records For Best V14-Fallback Rescue Method

| Species | Cells | Coverage | All-cell accuracy | Known-label accuracy | Open-set accuracy | Teacher acceptance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Arabidopsis thaliana | 2366 | 0.4328 | 0.6226 | 0.7871 | 0.4970 | 0.6669 |
| Brassica rapa | 256 | 0.9375 | 0.5547 | 0.5917 | 0.0000 | 0.6055 |
| Catharanthus roseus | 256 | 0.9414 | 0.5391 | 0.5726 | 0.0000 | 0.3086 |
| Eutrema salsugineum | 62 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.9839 |
| Fragaria vesca | 256 | 0.6289 | 0.6211 | 0.6335 | 0.6000 | 0.5664 |
| Gossypium bickii | 256 | 0.9062 | 0.5938 | 0.5733 | 0.7917 | 0.4297 |
| Gossypium hirsutum | 256 | 0.0000 | 0.0000 | n/a | 0.0000 | 0.1133 |
| Triticum aestivum | 256 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.7344 |

## Interpretation

v15 resolves the submission narrative by adding a clearly labelled deployment metric. The strict inductive cross-species result remains v14, while the high-confidence runtime-teacher rescue shows that the released service can recover many exact labels, including open-set Arabidopsis states, when the production annotation head is allowed to participate. These numbers should be reported as two complementary protocols, not as a single zero-shot score.
