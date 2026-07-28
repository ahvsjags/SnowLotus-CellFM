# SnowLotus-CellFM Model Release Manifest

Generated UTC: `2026-07-28T16:21:54.719092+00:00`

## Summary

- Checkpoints: `7`
- Label-release candidates: `3`
- Embedding-release candidates: `4`
- Checkpoint load errors: `0`
- Total checkpoint bytes: `348383544`

## Checkpoints

| Run | Kind | Status | Epoch | Stage | Bytes | Gene vocab | Fine vocab | Coarse vocab | Eval loss | Macro-F1 | SHA256 |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| local_srp169576_annotation_finetune_1024_unbalanced_8e | best | label_release_candidate | 7 | supervised | 49036360 | 32992 | 13 | 13 | 1.2341 | 0.7196 | `5cad86d483d912f1` |
| remote_cra0029771_pretrain_4090 | best | embedding_release_candidate | 7 | pretrain | 40709000 | 25078 | 0 | 0 | 6.6617 |  | `43ee624492c59334` |
| remote_gse146034_full_pretrain_4090 | best | embedding_release_candidate | 8 | pretrain | 43223624 | 27337 | 0 | 0 | 6.8097 |  | `e0bfed95591959e7` |
| remote_gse146034_pretrain_4090 | best | embedding_release_candidate | 7 | pretrain | 40085960 | 24344 | 0 | 0 | 6.8857 |  | `69bb458c42f5edd9` |
| remote_joint_scplantdb_pretrain_4090 | best | embedding_release_candidate | 8 | pretrain | 77255496 | 60004 | 0 | 0 | 7.1933 |  | `7300ba74d41e664c` |
| remote_srp169576_hybrid_4090 | best | label_release_candidate | 5 | hybrid | 49036552 | 32992 | 13 | 13 | 4.4479 | 0.7793 | `da9e96db4ec276a6` |
| remote_srp169576_joint_init_hybrid_4090 | best | label_release_candidate | 6 | hybrid | 49036552 | 32992 | 13 | 13 | 3.8749 | 0.8241 | `3d2ba3d4c15d2914` |
