# SnowLotus-CellFM Model Release Manifest

Generated UTC: `2026-07-26T01:53:45.713814+00:00`

## Summary

- Checkpoints: `16`
- Label-release candidates: `5`
- Embedding-release candidates: `11`
- Checkpoint load errors: `0`
- Total checkpoint bytes: `20097414082`

## Checkpoints

| Run | Kind | Status | Epoch | Stage | Bytes | Gene vocab | Fine vocab | Coarse vocab | Eval loss | Macro-F1 | SHA256 |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| foundation_5090_mlm_public_expansion | best | embedding_release_candidate | 4 | pretrain | 586940238 | 215617 | 0 | 0 | 12.9964 |  | `3d0d832cc7f4b0c6` |
| foundation_5090_mlm_public_expansion_continuation | best | embedding_release_candidate | 7 | pretrain | 926433358 | 379504 | 0 | 0 | 7.1917 |  | `00c1b0a1049c4415` |
| foundation_5090_mlm_public_expansion_continuation | latest | embedding_release_candidate | 20 | pretrain | 2751940673 | 378714 | 0 | 0 |  |  | `b1a1b41c7d762019` |
| foundation_5090_mlm_public_expansion_continuation_v0_3 | latest | embedding_release_candidate | 1 | pretrain | 2756811073 | 379504 | 0 | 0 |  |  | `af1dc43eac9f7cc2` |
| foundation_5090_mlm_public_expansion_continuation_v0_3_seed47 | latest | embedding_release_candidate | 1 | pretrain | 2756811073 | 379504 | 0 | 0 |  |  | `c8cc27dedea0319d` |
| foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8 | latest | embedding_release_candidate | 1 | pretrain | 2756811073 | 379504 | 0 | 0 |  |  | `fa4fe29bb0682107` |
| foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm | best | embedding_release_candidate | 7 | pretrain | 926433358 | 379504 | 0 | 0 | 7.1917 |  | `00c1b0a1049c4415` |
| foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm | latest | embedding_release_candidate | 8 | pretrain | 2756812801 | 379504 | 0 | 0 |  |  | `bc5ad41551eb2473` |
| foundation_5090_mlm_public_late_refresh | best | embedding_release_candidate | 4 | pretrain | 658999758 | 250325 | 0 | 0 | 12.5043 |  | `e32284d4dc3fafd5` |
| foundation_5090_mlm_public_late_refresh_safe | best | embedding_release_candidate | 8 | pretrain | 924798222 | 378714 | 0 | 0 | 9.6529 |  | `87e235a3bc3f8317` |
| foundation_5090_mlm_public_late_refresh_safe | latest | embedding_release_candidate | 8 | pretrain | 924801344 | 378714 | 0 | 0 |  |  | `0fc5b787c30e6569` |
| foundation_5090_pretrain | best | label_release_candidate | 14 | hybrid | 568000678 | 22335 | 13 | 13 | 5.0190 | 0.8121 | `ebc95ca58ffede9c` |
| foundation_5090_public_safe_init | best | label_release_candidate | 10 | hybrid | 190528014 | 24396 | 13 | 13 | 3.5341 | 0.7700 | `fceb733334b959d8` |
| foundation_5090_public_safe_init | latest | label_release_candidate | 12 | hybrid | 570656469 | 24396 | 13 | 13 |  |  | `5d7d00d59b5520c7` |
| foundation_5090_public_sprint | best | label_release_candidate | 3 | hybrid | 40124751 | 24396 | 13 | 13 | 5.8913 | 0.2602 | `18314389d2b7ba84` |
| smoke | best | label_release_candidate | 1 | hybrid | 511199 | 164 | 6 | 4 | 4.0294 | 0.0476 | `a912aeb3ea09a17c` |
