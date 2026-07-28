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
- Historical GSE146034 subset bundle: `12564` cells and `38501` genes in
  `data/public/GSE146034_npz/GSE146034_mtx_extracted.npz`.
- Full GSE146034 bundle: `23532` cells, `43311` genes, and `63856201` nonzero
  entries in `data/plant_foundation_corpus_gse146034_full.npz`.
- Full GSE manifest: `data/corpus_manifest.gse146034_full_samples.tsv`.
- Full GSE corpus SHA256:
  `8cbd6b4dfc28d5f634333e1781549feacb05bc2341c8e1b17307d7298b3a4bab`.

## Checkpoints

- Joint pretraining: `outputs/remote_joint_scplantdb_pretrain_4090/best.pt`.
  SHA256: `7300ba74d41e664c240cc35b4ae1de2a8402923260ac485c3975969312fed117`.
- GSE146034 pretraining: `outputs/remote_gse146034_pretrain_4090/best.pt`.
  SHA256: `69bb458c42f5edd9abbd0db29e180b56a25d9c55b5b4a770a528097b62a9966e`.
- Full GSE146034 pretraining: `outputs/remote_gse146034_full_pretrain_4090/best.pt`.
  SHA256: `e0bfed95591959e7120e5dec1ed5ce8b59721aae845cb9cbe7166991e0831329`.
- Final label model: `outputs/remote_srp169576_joint_init_hybrid_4090/best.pt`.
  SHA256: `3d2ba3d4c15d29140b04a24227d496fd92b58ef1fd730fe20127eeb66681d8fd`.

## Verification

- Final label model independent test fine accuracy: `0.727962`.
- Final label model independent test fine macro-F1: `0.725557`.
- Full GSE pretraining test MLM loss: `6.818127`.
- Inference service: `http://127.0.0.1:8000`.
- Service health and metadata checks passed.
- CRA002977_1 service smoke bundle: `10947` cells, `256`-dimensional embeddings.
- Full GSE146034 pretraining embedding bundle: `23532` cells, `256`-dimensional embeddings.
- Full GSE146034 final annotation bundle: `23532` cells, `256`-dimensional embeddings.

The server-side release manifest is `outputs/model_release_manifest.current.md`.
