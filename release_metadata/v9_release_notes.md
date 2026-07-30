# Plant-CellFM v0.9.0: frozen general-plant candidate

This release freezes the v9 LoRA checkpoint for reproducible review and manuscript submission.

## Contents

- `SnowLotus-CellFM-v9-lora-4090-best.pt`: 309,776,935-byte checkpoint trained on an NVIDIA RTX 4090.
- Source code and reproducibility scripts in the repository branch `agent/remote-pipeline-20260728`.
- Public plant corpus manifest, benchmark subset, baseline comparison, training configuration and model card in the repository and server-side package.

## Frozen evidence

- 56 manifest rows, 29 datasets and 21 plant species.
- 13.78 million cells in the built v9 corpus.
- Leave-dataset-out: 44.90% all-cell accuracy at 80.17% coverage; 56.01% known-label conditional accuracy and macro-F1 0.3485.
- Leave-sample-out: 62.00% all-cell accuracy at 98.71% coverage; 62.81% known-label conditional accuracy and macro-F1 0.4902.
- Leave-species-out: 36.35% all-cell accuracy at 68.82% coverage; 52.82% known-label conditional accuracy and macro-F1 0.2897.
- The conditional metrics are retained for comparability with the earlier benchmark, while all-cell accuracy is the primary open-set metric for species holdout.
- Candidate embedding finite-value gate: passed.

## Integrity

SHA256:

`9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`

The checkpoint is distributed as a release asset rather than committed to Git history. The repository contains no tracked private keys, server passwords or access tokens.
