# GSE270342 Wheat Root LoRA Adaptation Audit

- Prepared barcode-non-overlap input: `7164` cells.
- Fixed split: `5014` train / `717` validation / `1433` locked test cells.
- Selected checkpoint epoch: `8` using validation fine macro-F1.
- Released checkpoint: `models/Plant_CellFM_GSE270342_wheat_root_lora_adapter_best.pt` (SHA256 `597b7e425b0355ddfa81e4f5c9c63e85987d6b72fe49a841736b200ea6c2c22e`).
- Locked 13-class fine test: accuracy `62.25%`, macro-F1 `0.6660`.
- Matched direct-root locked subset: frozen `25.93%` to adapted `56.22%` (30.29 percentage points).

## Evidence Boundary

- This is a single-study, author-label-supervised species-adaptation experiment on a barcode-non-overlap input, not zero-shot transfer or independent external validation.
- The frozen baseline and LoRA adapter are compared only on the same locked cells and a predeclared direct anatomical map.
- The 13-class primary test metric uses author labels and is not directly comparable to the frozen 13-state root checkpoint vocabulary.
- No test labels selected the checkpoint, mapping policy, epoch, or hyperparameters.
