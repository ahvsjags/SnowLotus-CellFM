# Plant-CellFM General Plant Model Card

- Generated UTC: `2026-07-29T09:04:15.639141+00:00`
- Model scope: **plant_general**
- Model name: `Plant-CellFM (general plant foundation model)`
- Snow Lotus is an adapter and case study; the backbone is designed for cross-species plant expression data.
- Known adapters: **21**; runtime dynamic adapters are materialized for any additional plant species.

## Scope and Functions

A cross-species plant single-cell and single-nucleus expression backbone. Snow Lotus is a target-species adapter and case study, not the boundary of the model.

- masked-expression pretraining
- cross-species cell embedding
- hierarchical cell-state annotation
- marker-candidate discovery
- gene-vocabulary transfer with ortholog mapping
- runtime dynamic adapter materialization for any plant species
- species-specific adapter fine-tuning via LoRA or supervised learning for every requested plant species
- Snow Lotus reference-genome and primary-data adapter as one member of the all-plant system

## Verified Backbone Assets

| Role | Checkpoint | Evidence | SHA256 |
| --- | --- | --- | --- |
| joint_plant_backbone | `outputs/remote_joint_scplantdb_pretrain_4090/best.pt` | cells=272732, source_genes=209405, training_gene_vocabulary=60000 | `7300ba74d41e664c240cc35b4ae1de2a8402923260ac485c3975969312fed117` |
| full_rice_cross_species_pretraining | `outputs/remote_gse146034_full_pretrain_4090/best.pt` | cells=23532, genes=43311, nonzero_entries=63856201 | `e0bfed95591959e7120e5dec1ed5ce8b59721aae845cb9cbe7166991e0831329` |
| operational_annotation_head | `outputs/remote_srp169576_joint_init_hybrid_4090/best.pt` | independent_test_fine_accuracy=0.7279620268770806, independent_test_fine_macro_f1=0.725556710508996 | `3d2ba3d4c15d29140b04a24227d496fd92b58ef1fd730fe20127eeb66681d8fd` |
| joint_plant_backbone_public_plants_v1 | `outputs/plant_general_foundation_public_plants_v1_4090/best.pt` | manifest_rows=24, datasets=19, species=13 | `c3bea25a80b05585cb5930c04420a0ef2bf77f5f3d7abc0db1d161192ee93f80` |
| all_plant_annotation_head_public_plants_v1_cell_split | `outputs/plant_general_annotation_public_plants_v1_cell_split_4090/best.pt` | test_fine_accuracy=0.3759765625, test_fine_macro_f1=0.29283734321768556, test_coarse_accuracy=0.38623046875, test_coarse_macro_f1=0.3007575543721608 | `97f5f0e5d0847a7dbb4759759414ce07135e78ca6ff60f3ac36942e577f18fcb` |

## Corpus Coverage

- Selected manifest: `union(corpus_manifest*.tsv)`
- Manifest rows: **26**
- Unique datasets: **21**
- Unique species in selected manifest: **13**

| Species | Datasets | Manifest rows | Tissues |
| --- | ---: | ---: | --- |
| Arabidopsis thaliana | 9 | 10 | Rosette leaf, True leaf, Vegetative shoot apex, Whole root, root, secondary_root |
| Oryza sativa | 3 | 3 | leaf, root, root_tip |
| Gossypium hirsutum | 1 | 3 | leaf_glandular_cells |
| 9311 | 1 | 1 | unknown_tissue |
| Brassica rapa | 1 | 1 | Rosette leaf |
| Catharanthus roseus | 1 | 1 | Leaf |
| Fragaria vesca | 1 | 1 | True leaf |
| Gossypium bickii | 1 | 1 | Cotyledon |
| Nip | 1 | 1 | unknown_tissue |
| Solanum lycopersicum | 1 | 1 | root |
| Stevia rebaudiana | 1 | 1 | leaf |
| Triticum aestivum | 1 | 1 | root |
| Zea mays | 1 | 1 | seedling |

## Verified Cross-Species Benchmark

- `public_plants_v1_cross_species`: `4864` sampled cells, `19` datasets, `14` species; evidence `outputs/benchmarks/public_plants_v1_cross_species.json`; checkpoint SHA256 `c3bea25a80b05585cb5930c04420a0ef2bf77f5f3d7abc0db1d161192ee93f80`.
  - `leave_dataset_out_fine`: n_evaluable=3146, accuracy=0.029561347743165926, macro_f1=0.009377133693602163, coverage=0.9228335584869676
  - `leave_dataset_out_coarse`: n_evaluable=3148, accuracy=0.027318932655654382, macro_f1=0.008793926289727458, coverage=0.9152438055908514
  - `leave_sample_out_fine`: n_evaluable=4497, accuracy=0.10851678897042473, macro_f1=0.05312626132848596, coverage=0.991857074423646
  - `leave_sample_out_coarse`: n_evaluable=4477, accuracy=0.11793611793611794, macro_f1=0.0643503783612768, coverage=0.9879622249391838
  - `leave_species_out_fine`: n_evaluable=2970, accuracy=0.0872053872053872, macro_f1=0.037071278344155835, coverage=0.8107681729675578
  - `leave_species_out_coarse`: n_evaluable=2972, accuracy=0.0851278600269179, macro_f1=0.03997958881271549, coverage=0.8019547563237495

## Cross-Species Transfer Contract

1. Use exact gene identifiers when the new species shares the checkpoint vocabulary.
2. For species-specific identifiers, provide a source-to-target ortholog map and retain mapping confidence.
3. Run the general backbone for embeddings and MLM features, then attach a task- or species-specific head when labels are available.
4. The Snow Lotus branch adds reference-genome, gene-catalog and future primary single-cell adaptation assets without narrowing the general model.
5. A request containing a new plant name creates a runtime adapter with its own adapter identifier while reusing the general backbone. The universal fallback is reserved for requests without a species name.
The runtime uses the joint scPlantDB checkpoint as the primary general-plant backbone. The supervised checkpoint is an optional annotation head, not the definition of the plant scope.

## Reproducibility

- GPU: `NVIDIA GeForce RTX 4090 24 GB`
- Remote project: `/mnt/snowlotus_cellfm`
- GitHub: https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728
- Service routes: `/health`, `/metadata`, `/capabilities`, `/annotate`.

This card defines the current plant-general release boundary. Coverage grows by promoting new public plant matrices into the manifest and rerunning the same audit and training pipeline.
