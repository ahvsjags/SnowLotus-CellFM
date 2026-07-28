# SnowLotus-CellFM SRP169576 hybrid 4090 run card

## Run identity

- Host allocation: Matpool port `27317`, alias `matpool-px1-jcy`
- GPU: NVIDIA GeForce RTX 4090, 24 GB
- Environment: conda `myconda`, Python 3.11, PyTorch `2.6.0+cu124`
- Configuration: `configs/remote_srp169576_hybrid_4090.yaml`
- Server checkpoint: `/mnt/snowlotus_cellfm/outputs/remote_srp169576_hybrid_4090/best.pt`
- Server checkpoint SHA256: `da9e96db4ec276a6551e4feefc59a4fa6262e4cde62f36c3530378f5936c0adf`

## Data and training

- Dataset: scPlantDB SRP169576, 35,665 cells and 49,106 genes
- Labels: 13 fine cell types with group-disjoint `Orig.ident` split
- Architecture: 1,024 input genes, 256-dimensional hidden state, 4 Transformer layers, 8 attention heads, 768-dimensional feed-forward layer
- Training: supervised checkpoint initialization followed by 6 hybrid epochs combining hierarchical classification, masked gene modelling and value prediction
- Best validation epoch: 5; fine accuracy `0.81207`; fine macro-F1 `0.77929`

## Independent test

- Fine accuracy: `0.7771202022523558`
- Fine macro-F1: `0.7507624941531824`
- Fine weighted-F1: `0.7765414518634284`
- Coarse accuracy: `0.7774649505860721`
- Coarse macro-F1: `0.7492517913005974`

## Transparent fusion

- Evaluator: Transformer softmax plus expression-centroid cosine probability
- Alpha selected on validation: `0.35`
- Independent-test accuracy: `0.780625143645139`
- Independent-test macro-F1: `0.7551034174656124`
- Independent-test weighted-F1: `0.7801150228860219`
- Fusion is post-processing and does not modify the main checkpoint.
