# SRP169576 1024-gene annotation run card

## Reproducibility

- Data: `data/public/scPlantDB_h5ad/SRP169576.h5ad`
- Config: `configs/local_srp169576_annotation_finetune_1024_unbalanced.yaml`
- Runner: `scripts/run_local_srp169576_annotation_finetune_1024_unbalanced.ps1`
- Checkpoint: `best.pt` (validation-best epoch 4)
- Checkpoint SHA256: `e16564fa0a1aa74dd19ca007d9aedbe89a12fc7d1051b761c15d39705a3386fc`
- Evaluated device: CUDA
- Held-out test cells: 17,404
- Labels: 13 fine/coarse classes

## Validation selection

The Transformer checkpoint reached validation fine accuracy `0.8020833` and fine macro-F1 `0.7618149` at epoch 4. A transparent probability fusion head was selected on validation with centroid weight `alpha=0.45`, model temperature `1.0`, and centroid temperature `0.05`.

## Held-out test results

| Method | Accuracy | Macro-F1 | Weighted-F1 |
| --- | ---: | ---: | ---: |
| Transformer | 0.7597104 | 0.7417440 | 0.7568558 |
| Cosine centroid | 0.7747070 | 0.7445827 | 0.7757967 |
| SnowLotus hybrid fusion | 0.7648242 | 0.7467307 | 0.7621742 |

## Artifacts

- Detailed Transformer evaluation: `detailed_test/detailed_metrics.json`
- Confusion matrices: `detailed_test/fine_confusion_matrix.tsv` and `detailed_test/coarse_confusion_matrix.tsv`
- Hybrid fusion summary: `hybrid_fusion.json`
- Hybrid per-cell predictions: `hybrid_fusion_test_predictions.tsv`

The hybrid output keeps the learned Transformer prediction and the expression-centroid prediction in the same row, making the final annotation auditable at cell level while retaining the model embedding and checkpoint as the primary learned representation.
