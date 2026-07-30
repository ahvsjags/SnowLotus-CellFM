# Plant-CellFM v9 API Runtime Smoke Test

Generated: 2026-07-30 17:04 Asia/Shanghai

## Purpose

This audit verifies that the deployed Plant-CellFM v9 service can do more than return a health check. It confirms that the live `/annotate` route accepts a server-side plant expression matrix, resolves a plant species adapter, runs the annotation checkpoint on CUDA and writes prediction, embedding and metadata artifacts.

## Request

```json
{
  "data_path": "/root/snowlotus_public_plants_v9/v9_benchmark_subset_256_shared_genes.h5ad",
  "output_dir": "/mnt/snowlotus_cellfm/outputs/runtime_smoke_v9_annotation_20260730_1659",
  "species": "Arabidopsis thaliana",
  "mode": "annotation",
  "batch_size": 64
}
```

## Result

| Field | Value |
| --- | --- |
| Route | `POST /annotate` |
| Status | `ok` |
| Device | `cuda` |
| Requested species | `Arabidopsis thaliana` |
| Resolved adapter | `plant_arabidopsis_thaliana` |
| Used fallback adapter | `false` |
| Checkpoint role | `annotation` |
| Cells annotated | `3964` |
| Embedding shape | `3964 x 256` |
| Predictions file lines | `3965`, including header |

## Output Files

| File | SHA256 |
| --- | --- |
| `/mnt/snowlotus_cellfm/outputs/runtime_smoke_v9_annotation_20260730_1659/adapter_selection.json` | `3bb69352537daf04b86e2835d4f66f05c14e1498bb59a07904aa642e9c3d014f` |
| `/mnt/snowlotus_cellfm/outputs/runtime_smoke_v9_annotation_20260730_1659/annotation_metadata.json` | `62d86701e35dd9153b2e69b8c760d6ef6298789509c14e5c51e6c82cf973b876` |
| `/mnt/snowlotus_cellfm/outputs/runtime_smoke_v9_annotation_20260730_1659/embeddings.npy` | `f1d7df09756da9322a45fb270aa110f92a457ff160e90c002ed5cf2a7c2dd013` |
| `/mnt/snowlotus_cellfm/outputs/runtime_smoke_v9_annotation_20260730_1659/predictions.csv` | `878b413e372cc07f6cb5d84d628528ed66c3438acd22d5bc99c0f61e16b057bb` |

## First Prediction Rows

```text
cell_id,cell_index,fine_label,fine_confidence,coarse_label,coarse_confidence
scplantdb_CRA002977_1:CRX125602@@_AAACCTGGTGCACTTA-1,0,Leaf pavement cell,0.954526,Leaf pavement cell,0.953002
scplantdb_CRA002977_1:CRX125602@@_AAAGATGTCGCCATAA-1,1,Xylem,0.513961,Xylem,0.491332
scplantdb_CRA002977_1:CRX125602@@_AACCATGCACCAACCG-1,2,Phloem parenchyma,0.791759,Phloem parenchyma,0.792273
```

## Interpretation

The live server passed an end-to-end annotation smoke test. This supports the claim that the frozen Plant-CellFM v9 package is callable as a deployed service with dynamic plant adapter resolution, annotation output, embedding output and auditable runtime artifacts.
