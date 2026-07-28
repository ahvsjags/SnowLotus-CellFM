# Plant-CellFM General Plant Model Card

- Generated UTC: `2026-07-28T18:26:15.589701+00:00`
- Model scope: **plant_general**
- Model name: `Plant-CellFM (SnowLotus-CellFM general-plant release)`
- Snow Lotus is an adapter and case study; the backbone is designed for cross-species plant expression data.
- Registered adapters: **20**, including the universal fallback for newly added plant species.

## Scope and Functions

A cross-species plant single-cell and single-nucleus expression backbone. Snow Lotus is a target-species adapter and case study, not the boundary of the model.

- masked-expression pretraining
- cross-species cell embedding
- hierarchical cell-state annotation
- marker-candidate discovery
- gene-vocabulary transfer with ortholog mapping
- species-specific adapter fine-tuning via LoRA or supervised learning for every registered plant species
- Snow Lotus reference-genome and primary-data adapter as one member of the full species registry

## Verified Backbone Assets

| Role | Checkpoint | Evidence | SHA256 |
| --- | --- | --- | --- |
| joint_plant_backbone | `outputs/remote_joint_scplantdb_pretrain_4090/best.pt` | cells=272732, source_genes=209405, training_gene_vocabulary=60000 | `7300ba74d41e664c240cc35b4ae1de2a8402923260ac485c3975969312fed117` |
| full_rice_cross_species_pretraining | `outputs/remote_gse146034_full_pretrain_4090/best.pt` | cells=23532, genes=43311, nonzero_entries=63856201 | `e0bfed95591959e7120e5dec1ed5ce8b59721aae845cb9cbe7166991e0831329` |
| operational_annotation_head | `outputs/remote_srp169576_joint_init_hybrid_4090/best.pt` | independent_test_fine_accuracy=0.7279620268770806, independent_test_fine_macro_f1=0.725556710508996 | `3d2ba3d4c15d29140b04a24227d496fd92b58ef1fd730fe20127eeb66681d8fd` |

## Corpus Coverage

- Selected manifest: `data/corpus_manifest_public_mlm_plus_latest.tsv`
- Manifest rows: **30**
- Unique datasets: **25**
- Unique species in selected manifest: **11**

| Species | Datasets | Manifest rows | Tissues |
| --- | ---: | ---: | --- |
| Arabidopsis thaliana | 17 | 18 | multi_organ, root, secondary_root |
| Oryza sativa | 3 | 3 | leaf, root, root_tip |
| Camelina sativa | 1 | 1 | root |
| Eutrema salsugineum | 1 | 1 | root |
| Gossypium hirsutum | 1 | 1 | leaf_glandular_cells |
| Schrenkiella parvula | 1 | 1 | root |
| Sisymbrium irio | 1 | 1 | root |
| Solanum lycopersicum | 1 | 1 | root |
| Stevia rebaudiana | 1 | 1 | leaf |
| Triticum aestivum | 1 | 1 | root |
| Zea mays | 1 | 1 | seedling |

## Cross-Species Transfer Contract

1. Use exact gene identifiers when the new species shares the checkpoint vocabulary.
2. For species-specific identifiers, provide a source-to-target ortholog map and retain mapping confidence.
3. Run the general backbone for embeddings and MLM features, then attach a task- or species-specific head when labels are available.
4. The Snow Lotus branch adds reference-genome, gene-catalog and future primary single-cell adaptation assets without narrowing the general model.

## Reproducibility

- GPU: `NVIDIA GeForce RTX 4090 24 GB`
- Remote project: `/mnt/snowlotus_cellfm`
- GitHub: https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728
- Service routes: `/health`, `/metadata`, `/capabilities`, `/annotate`.

This card defines the current plant-general release boundary. Coverage grows by promoting new public plant matrices into the manifest and rerunning the same audit and training pipeline.
