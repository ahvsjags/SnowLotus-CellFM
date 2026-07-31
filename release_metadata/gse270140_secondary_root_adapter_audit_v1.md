# GSE270140 Secondary-Root Adapter Audit

## Claim Boundary

- This is a labelled within-dataset adaptation, not a zero-shot or leave-species result.
- The GSE270140 sample is split by unique cell barcode (80% train, 10% validation, 20% held-out test). Because it is one sample, it does not establish sample-level replication.
- The frozen base head has no secondary-root labels. The same pre-registered three-state semantic map is therefore used for the matched before/after recovery audit.

## Frozen Protocol

- Base checkpoint SHA256: `e16564fa0a1aa74dd19ca007d9aedbe89a12fc7d1051b761c15d39705a3386fc`
- Released adapter checkpoint SHA256: `1a306c4a5e21630a75a5a63d2867e86712b2da78eea3805eb5dc00b957134fd7` (byte-identical to `outputs/gse270140_secondary_root_lora_adapter_4070/best.pt`).
- Tuning: `LoRA-mode`, rank `8`; validation selection at epoch `7` by macro-F1 `0.7888`.
- Actual execution hardware: `NVIDIA GeForce RTX 4070 Laptop GPU (CUDA)`.

## Held-out Adaptation Result

- Primary training-evaluator fine accuracy / macro-F1: **0.8397 / 0.8447** on `2352` held-out cells.
- Detailed full-precision recheck: `0.8418` accuracy and `0.8464` macro-F1.

## Matched Three-state Semantic Recovery

| Method | Held-out shared cells | Accuracy | Macro-F1 | Weighted F1 |
| --- | ---: | ---: | ---: | ---: |
| Frozen base checkpoint | 1885 | 0.0202 | 0.0603 | 0.0349 |
| Secondary-root LoRA-mode adapter | 1885 | 0.9093 | 0.9159 | 0.9205 |

- Absolute semantic accuracy gain: **0.8891**; macro-F1 gain: **0.8556**.

## Per-class Held-out Detail

| Author annotation | Test cells | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Mature phloem parenchyma | 645 | 0.8879 | 0.8109 | 0.8476 |
| Periderm | 436 | 0.8958 | 0.8280 | 0.8605 |
| Vascular cambium | 355 | 0.8829 | 0.8704 | 0.8766 |
| Conductive phloem parenchyma | 247 | 0.6831 | 0.7854 | 0.7307 |
| Maturing xylem parenchyma | 164 | 0.8957 | 0.8902 | 0.8930 |
| Young xylem parenchyma | 148 | 0.8289 | 0.8514 | 0.8400 |
| Mature xylem parenchyma | 123 | 0.8112 | 0.9431 | 0.8722 |
| Fiber | 111 | 0.7607 | 0.8018 | 0.7807 |
| Companion cell | 30 | 0.8788 | 0.9667 | 0.9206 |
| Vessel identity cell/expanding vessel | 30 | 0.6222 | 0.9333 | 0.7467 |
| Myrosin idioblasts | 24 | 0.8571 | 1.0000 | 0.9231 |
| Sieve element | 23 | 0.7241 | 0.9130 | 0.8077 |
| Late differentiating vessel | 9 | 1.0000 | 0.7778 | 0.8750 |
| Lateral root primordium/meristem | 7 | 0.7778 | 1.0000 | 0.8750 |
