# GSE297576 Sorghum Root Adapter Audit

## Claim Boundary

- The adapter is trained on two Sorghum libraries, selected on one distinct library and evaluated once on a fourth sealed library.
- This is target-species adaptation, not a zero-shot or independent external model comparison.
- The frozen-before/adapter-after recovery comparison uses the same sealed test cells and a predeclared broad root ontology.

## Locked Protocol

- Released checkpoint SHA256: `f6f3da3dbfb9eda48973c041fc07fa019b6f03229ae57f072afc054d8a52755f`.
- Selection: epoch `10` by validation macro-F1 `0.7864`; test labels were not used for selection.
- Sealed test library: `OUGHW`; `4150` cells, `27` author states.

## Held-out Result

- Fine accuracy / macro-F1: **0.7602 / 0.7535**; weighted F1: `0.7623`.
- Coarse accuracy / macro-F1: `0.8282 / 0.7935`.

## Matched Broad-identity Recovery

| Method | Evaluable sealed cells | Accuracy | Macro-F1 | Weighted F1 |
| --- | ---: | ---: | ---: | ---: |
| Frozen Plant-CellFM root head | 3549 | 0.1479 | 0.1218 | 0.1640 |
| Sorghum 27-state LoRA adapter | 3549 | 0.8498 | 0.8362 | 0.8640 |

- Absolute accuracy gain: **0.7019**; macro-F1 gain: **0.7144**.

## Per-class Sealed-test Detail

| Author state | Test cells | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| cortex | 614 | 0.8821 | 0.5847 | 0.7032 |
| procambium | 400 | 0.8849 | 0.6725 | 0.7642 |
| atrichoblast | 396 | 0.8228 | 0.8561 | 0.8391 |
| pericycle | 340 | 0.8338 | 0.8853 | 0.8588 |
| elongating-xylem | 247 | 0.8268 | 0.7733 | 0.7992 |
| lignified-xylem | 180 | 0.8602 | 0.8889 | 0.8743 |
| meristem | 180 | 0.7208 | 0.6167 | 0.6647 |
| cortical sclerenchyma | 178 | 0.5325 | 0.7360 | 0.6179 |
| LRC | 165 | 0.7027 | 0.6303 | 0.6645 |
| phloem | 136 | 0.8851 | 0.9632 | 0.9225 |
| dividing cells | 132 | 0.8333 | 0.8712 | 0.8519 |
| s-phase | 128 | 0.7661 | 0.7422 | 0.7540 |
| trichoblast | 125 | 0.8655 | 0.8240 | 0.8443 |
| crown root initials | 99 | 0.6768 | 0.6768 | 0.6768 |
| early-stele | 98 | 0.6281 | 0.7755 | 0.6941 |
| early-cortex | 97 | 0.6542 | 0.7216 | 0.6863 |
| exodermis | 86 | 0.7624 | 0.8953 | 0.8235 |
| mature-endodermis | 86 | 0.7157 | 0.8488 | 0.7766 |
| early-epidermis | 83 | 0.6238 | 0.7590 | 0.6848 |
| cortical aerenchyma | 80 | 0.6848 | 0.7875 | 0.7326 |
| senescent cortex | 60 | 0.3269 | 0.8500 | 0.4722 |
| phloem/SE | 55 | 0.7246 | 0.9091 | 0.8065 |
| elongating-endodermis | 50 | 0.6200 | 0.6200 | 0.6200 |
| mature-xylem | 46 | 0.7500 | 0.9783 | 0.8491 |
| lignified-endodermis | 36 | 0.7750 | 0.8611 | 0.8158 |
| columella | 32 | 0.6591 | 0.9062 | 0.7632 |
| sclerenchyma | 21 | 0.6667 | 0.9524 | 0.7843 |
