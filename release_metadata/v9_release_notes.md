# Plant-CellFM v0.9.0: frozen general-plant candidate

This release freezes the v9 LoRA checkpoint for reproducible review and manuscript submission.

## Contents

- `SnowLotus-CellFM-v9-lora-4090-best.pt`: 309,776,935-byte checkpoint trained on an NVIDIA RTX 4090.
- Source code and reproducibility scripts in the repository branch `agent/remote-pipeline-20260728`.
- Public plant corpus manifest, benchmark subset, baseline comparison, training configuration and model card in the repository and server-side package.

## Frozen evidence

- 56 manifest rows, 29 datasets and 21 plant species.
- 13.78 million cells in the built v9 corpus.
- Leave-dataset-out: accuracy 0.5601, macro-F1 0.3485.
- Leave-sample-out: accuracy 0.6281, macro-F1 0.4902.
- Leave-species-out: accuracy 0.5282, macro-F1 0.2897.
- Candidate embedding finite-value gate: passed.

## Integrity

SHA256:

`9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`

The checkpoint is distributed as a release asset rather than committed to Git history. The repository contains no tracked private keys, server passwords or access tokens.
