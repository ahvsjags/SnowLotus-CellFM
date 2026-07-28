# Remote Joint Pipeline Run Card

Run date: 2026-07-28

## Server

- SSH alias: `matpool-px1-jcy`
- Project: `/mnt/snowlotus_cellfm`
- Runtime: conda environment `myconda`
- GPU: NVIDIA GeForce RTX 4090, 24 GB

## Data assets

- Current scPlantDB joint corpus: `272732` cells and `209405` source genes.
- Joint training vocabulary: `60000` genes.
- GSE146034 archive: `206387200` bytes at
  `/mnt/snowlotus_cellfm/data/public/GSE146034_raw_tar/GSE146034_RAW.tar`.
- GSE146034 converted bundle: `12564` cells and `38501` genes in
  `data/public/GSE146034_npz/GSE146034_mtx_extracted.npz`.
- GSE manifest: `data/corpus_manifest.gse146034.tsv`.

## Checkpoints

- Joint pretraining: `outputs/remote_joint_scplantdb_pretrain_4090/best.pt`.
  SHA256: `7300ba74d41e664c240cc35b4ae1de2a8402923260ac485c3975969312fed117`.
- GSE146034 pretraining: `outputs/remote_gse146034_pretrain_4090/best.pt`.
  SHA256: `69bb458c42f5edd9abbd0db29e180b56a25d9c55b5b4a770a528097b62a9966e`.
- Final label model: `outputs/remote_srp169576_joint_init_hybrid_4090/best.pt`.
  SHA256: `3d2ba3d4c15d29140b04a24227d496fd92b58ef1fd730fe20127eeb66681d8fd`.

## Verification

- Final label model independent test fine accuracy: `0.727962`.
- Final label model independent test fine macro-F1: `0.725557`.
- GSE pretraining test MLM loss: `6.899002`.
- Inference service: `http://127.0.0.1:8000`.
- Service health and metadata checks passed.
- CRA002977_1 service smoke bundle: `10947` cells, `256`-dimensional embeddings.
- GSE146034 embedding bundle: `12564` cells, `256`-dimensional embeddings.

The server-side release manifest is `outputs/model_release_manifest.current.md`.
