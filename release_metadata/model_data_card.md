# SnowLotus-CellFM Model and Data Card

- Generated UTC: `2026-07-25T21:55:59.024733+00:00`
- Project directory: `.`
- Model family: Transformer-based expression foundation model with MLM-style pretraining and hierarchical labels.
- Intended use: Plant single-cell and single-nucleus foundation annotation, public cross-species pretraining, and Snow Lotus transfer once primary Saussurea data are available.

## Model Artifacts

| run | checkpoint | checkpoint_size | epochs_recorded | latest_epoch | fine_macro_f1 | coarse_macro_f1 | eval_loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| outputs/smoke | True | 499.2 KB | 3 | 3 | 0.0476 | 0.1250 | 3.9180 |
| outputs/foundation_5090_public_sprint | True | 38.3 MB | 3 | 3 | 0.2602 | 0.2285 | 5.8913 |
| outputs/foundation_5090_public_safe_init | True | 181.7 MB | 12 | 12 | 0.7523 | 0.7526 | 3.7105 |
| outputs/foundation_5090_pretrain | True | 541.7 MB | 24 | 24 | 0.7983 | 0.7955 | 5.1526 |
| outputs/foundation_5090_mlm_public_available_expansion | False | 0 B | 0 |  |  |  |  |
| outputs/foundation_5090_mlm_public_expansion | True | 559.7 MB | 12 | 12 |  |  | 15.2775 |
| outputs/foundation_5090_mlm_public_expansion_continuation | True | 883.5 MB | 20 | 20 |  |  | 8.0196 |
| outputs/foundation_5090_mlm_public_late_refresh | True | 628.5 MB | 10 | 10 |  |  | 13.8535 |
| outputs/foundation_5090_mlm_public_late_refresh_safe | True | 882.0 MB | 8 | 8 |  |  | 9.6529 |
| outputs/foundation_5090_mlm_public_post_gse226097_refresh_safe | False | 0 B | 0 |  |  |  |  |

## Corpus Artifacts

| path | exists | size |
| --- | --- | --- |
| data/plant_foundation_corpus.h5ad | True | 43.1 MB |
| data/plant_foundation_corpus_public_mlm_available.h5ad | True | 704.7 MB |
| data/plant_foundation_corpus_public_mlm.h5ad | True | 1.9 GB |

## Public Data Targets

| dataset_id | priority | status | stage | manifest_rows | raw_files | npz_files |
| --- | --- | --- | --- | --- | --- | --- |
| scplantdb_global | A | manual_index | manifest_ready | 52 | 104 | 0 |
| brassicaceae_multi_species_root_atlas | A | download_candidate | manifest_ready | 5 | 15 | 5 |
| arabidopsis_root_atlas | A | download_candidate | manifest_ready | 2 | 1 | 2 |
| rice_root_tip_atlas | B | download_candidate | manifest_ready | 1 | 2 | 1 |
| arabidopsis_lifecycle_spatial_atlas | A | download_candidate | manifest_ready | 1 | 1 | 1 |
| cotton_glandular_terpenoid_atlas | B | download_candidate | manifest_ready | 1 | 2 | 1 |
| rice_soil_stress_root_atlas | A | download_candidate | manifest_ready | 1 | 1 | 1 |
| wheat_soil_root_atlas | B | download_candidate | manifest_ready | 1 | 1 | 1 |
| arabidopsis_secondary_root_dev_atlas | B | download_candidate | manifest_ready | 1 | 4 | 1 |
| maize_easy_multiome_seedling | B | download_candidate | manifest_ready | 1 | 1 | 1 |
| rice_leaf_stress_snuc_atlas | A | download_candidate | manifest_ready | 1 | 1 | 1 |
| brassicaceae_regulatory_multiome | B | discovery_candidate | not_started_or_metadata_only | 0 | 0 | 0 |
| stevia_leaf_secondary_metabolism_snuc | A | download_candidate | manifest_ready | 1 | 2 | 1 |
| arabidopsis_lateral_root_founder_atlas | B | download_candidate | manifest_ready | 1 | 1 | 1 |
| tomato_mycorrhiza_snuc_atlas | B | download_candidate | manifest_ready | 1 | 1 | 1 |
| arabidopsis_scrna_method_benchmark | B | download_candidate | manifest_ready | 1 | 1 | 1 |
| marchantia_spore_asymmetry_single_cell | C | download_candidate | unsupported_for_matrix_corpus | 0 | 3 | 0 |

## Pending Corpus Additions

| manifest | dataset_ids | rows_missing_from_public_mlm_manifest |
| --- | --- | --- |
| data/corpus_manifest.gse157757.tsv | geo_gse157757_zea_mays_single_cell_sequencing_reveals_phloem | 1 |
| data/corpus_manifest.gse180121.tsv | geo_gse180121_liriodendron_chinense_single_cell_transcriptomics_unveils_xylem | 3 |
| data/corpus_manifest.gse182507.tsv | geo_gse182507_medicago_truncatula_single_cell_rna_sequencing_medicago | 1 |
| data/corpus_manifest.gse190649.tsv | geo_gse190649_populus_tremula_single_nuclei_transcriptomic_populus_tremula | 1 |
| data/corpus_manifest.gse201640.tsv | geo_gse201640_zea_mays_decoding_gene_regulatory_network_endosperm | 1 |
| data/corpus_manifest.gse201931.tsv | geo_gse201931_solanum_lycopersicum_high_throughput_single_cell_transcriptome | 2 |
| data/corpus_manifest.gse210881.tsv | geo_gse210881_medicago_truncatula_gene_expression_profile_at_single | 1 |
| data/corpus_manifest.gse220277.tsv | geo_gse220277_arabidopsis_drought_recovery_plants_triggers_a | 1 |
| data/corpus_manifest.gse222584.tsv | geo_gse222584_oryza_sativa_single_cell_sequencing_revealed_cell | 1 |
| data/corpus_manifest.gse226149.tsv | geo_gse226149_glycine_max_gene_expression_profile_at_single | 1 |
| data/corpus_manifest.gse226826.tsv | geo_gse226826_arabidopsis_thaliana_time_resolved_single_cell_spatial | 1 |
| data/corpus_manifest.gse234192.tsv | arabidopsis_callus_regeneration_scrna | 1 |
| data/corpus_manifest.gse235495.tsv | geo_gse235495_arabidopsis_thaliana_multiome_same_cell_revealed_impact | 1 |
| data/corpus_manifest.gse240098.tsv | geo_gse240098_medicago_truncatula_spatial_co_transcriptomics_reveals_discrete | 1 |
| data/corpus_manifest.gse240102.tsv | geo_gse240102_medicago_truncatula_spatial_co_transcriptomics_reveals_discrete | 1 |
| data/corpus_manifest.gse241573.tsv | geo_gse241573_arabidopsis_thaliana_synthetic_deconvolution_an_auxin_dependent | 1 |
| data/corpus_manifest.gse243174.tsv | geo_gse243174_glycine_max_single_cell_multiomic_profiling_soybean | 1 |
| data/corpus_manifest.gse261441.tsv | geo_gse261441_arabidopsis_thaliana_a_single_nuclei_transcriptome_census | 4 |
| data/corpus_manifest.gse267159.tsv | geo_gse267159_populus_trichocarpa_single_cell_spatial_multi_omics | 12 |
| data/corpus_manifest.gse269624.tsv | geo_gse269624_arabidopsis_thaliana_glutathione_accelerates_cell_cycle_cellular | 1 |
| data/corpus_manifest.gse273722.tsv | geo_gse273722_camellia_sinensis_transcriptional_landscape_camellia_sinensis_roots | 1 |
| data/corpus_manifest.gse273875.tsv | geo_gse273875_oryza_sativa_a_single_cell_multiomics_atlas | 1 |
| data/corpus_manifest.gse275409.tsv | geo_gse275409_zea_mays_genetic_architecture_cell_type_specific | 1 |
| data/corpus_manifest.gse283835.tsv | geo_gse283835_populus_tremula_single_nuclei_transcriptomic_bulk_rna | 1 |
| data/corpus_manifest.gse303996.tsv | geo_gse303996_arabidopsis_thaliana_histone_deacetylases_cell_cycle_regulators | 1 |
| data/corpus_manifest.gse308672.tsv | geo_gse308672_arabidopsis_thaliana_discrete_cell_specific_hypoxic_responses | 1 |
| data/corpus_manifest.gse308757.tsv | rice_node_reproductive_stage_atlas | 1 |
| data/corpus_manifest.scplantdb.tsv | scplantdb_CRA002977_1;scplantdb_CRA002977_2;scplantdb_CRA004476;scplantdb_CRA004848;scplantdb_CRA006988;scplantdb_CRA007122;scplantdb_CRA008788;scplantdb_CRA009614;scplantdb_DRP009643;scplantdb_ERP132245;scplantdb_SRP148288;scplantdb_SRP164771;scplantdb_SRP166333;scplantdb_SRP169576;scplantdb_SRP171040;scplantdb_SRP173393;scplantdb_SRP182008;scplantdb_SRP224648;scplantdb_SRP235541;scplantdb_SRP241596;scplantdb_SRP247828_1;scplantdb_SRP247828_2;scplantdb_SRP247828_3;scplantdb_SRP250946;scplantdb_SRP253497;scplantdb_SRP272727_23_26;scplantdb_SRP273996;scplantdb_SRP279055;scplantdb_SRP280069;scplantdb_SRP281914;scplantdb_SRP285040;scplantdb_SRP285817;scplantdb_SRP286275;scplantdb_SRP286427;scplantdb_SRP292306;scplantdb_SRP307169;scplantdb_SRP307440;scplantdb_SRP309176;scplantdb_SRP320285;scplantdb_SRP330542;scplantdb_SRP332285;scplantdb_SRP335180;scplantdb_SRP335448;scplantdb_SRP338044;scplantdb_SRP339472;scplantdb_SRP354482;scplantdb_SRP374045;scplantdb_SRP386976;scplantdb_SRP390780;scplantdb_SRP398011;scplantdb_SRP406470;scplantdb_SRP424189 | 52 |

## Known Limitations

- Real Snow Lotus scRNA/snRNA primary data are not yet present as data/saussurea_involucrata.h5ad.
- Current public foundation training uses heterogeneous public plant matrices with incomplete harmonized labels.
- Several newly reviewed GEO datasets are still downloading or pending conversion.
- External tool benchmarks and wet-lab validation are required before top-journal biological claims.
- The current model card is a living project artifact and should be frozen with final checksums before submission.

## Recommended Next Actions

- Let public MLM training finish, then allow late-refresh to rebuild the corpus with GSE243419.
- Continue reviewed GEO downloads and add converted manifests to the public MLM corpus.
- Add primary Saussurea involucrata scRNA/snRNA h5ad and run Snow Lotus fine-tuning.
- Run strict external benchmarks and produce marker/regulator validation tables.
- Deposit final raw and processed data with stable accessions and update Data Availability.
