# SnowLotus-CellFM CRA002977_1 pretraining run card

## Run identity

- Host allocation: Matpool port `27317`, alias `matpool-px1-jcy`
- GPU: NVIDIA GeForce RTX 4090, 24 GB
- Environment: conda `myconda`, Python 3.11, PyTorch `2.6.0+cu124`
- Configuration: `configs/remote_cra0029771_pretrain_4090.yaml`
- Server checkpoint: `/mnt/snowlotus_cellfm/outputs/remote_cra0029771_pretrain_4090/best.pt`
- Server checkpoint SHA256: `43ee624492c59334c87bc7afaa6af40ae1cbebc8f7f5005aeb68218b07d28651`

## Data and training

- Dataset: scPlantDB CRA002977_1, 10,947 cells and 53,678 genes
- Metadata: 7 cell types, leaf tissue, one `Orig.ident` and one `Libraries` value
- Split group: 14 `Seurat_clusters`, used only to create separated expression-reconstruction partitions
- Architecture: 512 input genes, 256-dimensional hidden state, 4 Transformer layers, 8 attention heads, 768-dimensional feed-forward layer
- Training: 8 epochs of masked gene/value modelling; 10,048,516 trainable parameters

## Held-out reconstruction

- Best validation MLM loss: `6.661694961123996` at epoch 7
- Test MLM loss: `7.563981429390285`
- Test gene loss: `7.563796893410061`
- Test value loss: `0.0018452299991622567`
