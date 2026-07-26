# SnowLotus-CellFM Top-Journal Readiness Matrix

Generated UTC: `2026-07-26T03:12:32.901969+00:00`

## Gate Matrix

| ID | Requirement | Status | Evidence / Missing item |
| --- | --- | --- | --- |
| ssh_5090 | Stable SSH alias can execute tasks on the RTX 5090 server | READY | `publication_gates.ssh_remote_execution=true` |
| base_training | GPU training artifacts and traceable histories exist | READY | `publication_gates.gpu_training_active_or_artifacts_present=true` |
| public_data | Public plant single-cell data are ingested into manifests/corpora | READY | `publication_gates.public_data_ingested=true` |
| data_integrity | Referenced matrix files pass integrity audit | READY | `publication_gates.referenced_matrices_readable=true` |
| strict_split | Strict split audits are reproducible | READY | `publication_gates.strict_split_audit_present=true` |
| baseline_metric | At least one reproducible baseline benchmark metric exists | READY | `publication_gates.baseline_benchmark_metric_present=true` |
| external_tools | External tool comparisons are present | PARTIAL | Metric benchmarks present for `scplantllm, seurat`; missing `scplantannotate`. |
| snow_lotus_scrna | Snow Lotus scRNA/snRNA data exist for fine-tuning and validation | MISSING | Still missing data/saussurea_involucrata.h5ad |

## Current Training Evidence

- `outputs/smoke`: checkpoint, epoch=3, fine_macro_f1=0.0476, coarse_macro_f1=0.1250
- `outputs/foundation_5090_public_sprint`: checkpoint, epoch=3, fine_macro_f1=0.2602, coarse_macro_f1=0.2285
- `outputs/foundation_5090_public_safe_init`: checkpoint, epoch=12, fine_macro_f1=0.7523, coarse_macro_f1=0.7526
- `outputs/foundation_5090_pretrain`: checkpoint, epoch=24, fine_macro_f1=0.7983, coarse_macro_f1=0.7955
- `outputs/foundation_5090_mlm_public_expansion`: checkpoint, epoch=12
- `outputs/foundation_5090_mlm_public_expansion_continuation`: checkpoint, epoch=20
- `outputs/foundation_5090_mlm_public_late_refresh`: checkpoint, epoch=10
- `outputs/foundation_5090_mlm_public_late_refresh_safe`: checkpoint, epoch=8

## Data Integrity Evidence

- Manifests audited: `70`
- Matrix files audited: `240`
- Missing files: `0`
- Unreadable files: `0`
- Total readable cells: `4544570`

## Benchmark Readiness Evidence

- Baseline metric artifacts: `2`
- Split audit artifacts: `6`
- Supervised-ready split audits: `2`
- Marker candidate artifact present: `True`
- External benchmark files: `4`
- External metric benchmark files: `3`
- External metric methods present: `scplantllm, seurat`
- External metric methods missing: `scplantannotate`

## Public Data Targets

| Dataset | Stage | Manifest rows | Raw files | NPZ files |
| --- | --- | ---: | ---: | ---: |
| scplantdb_global | manifest_ready | 52 | 104 | 0 |
| brassicaceae_multi_species_root_atlas | manifest_ready | 5 | 15 | 5 |
| arabidopsis_root_atlas | manifest_ready | 2 | 1 | 2 |
| rice_root_tip_atlas | manifest_ready | 1 | 2 | 1 |
| arabidopsis_lifecycle_spatial_atlas | manifest_ready | 1 | 1 | 1 |
| cotton_glandular_terpenoid_atlas | manifest_ready | 1 | 2 | 1 |
| rice_soil_stress_root_atlas | manifest_ready | 1 | 1 | 1 |
| wheat_soil_root_atlas | manifest_ready | 1 | 1 | 1 |
| arabidopsis_secondary_root_dev_atlas | manifest_ready | 1 | 4 | 1 |
| maize_easy_multiome_seedling | manifest_ready | 1 | 1 | 1 |
| rice_leaf_stress_snuc_atlas | manifest_ready | 1 | 1 | 1 |
| brassicaceae_regulatory_multiome | not_started_or_metadata_only | 0 | 0 | 0 |
| stevia_leaf_secondary_metabolism_snuc | manifest_ready | 1 | 2 | 1 |
| arabidopsis_lateral_root_founder_atlas | manifest_ready | 1 | 1 | 1 |
| tomato_mycorrhiza_snuc_atlas | manifest_ready | 1 | 1 | 1 |
| arabidopsis_scrna_method_benchmark | manifest_ready | 1 | 1 | 1 |
| marchantia_spore_asymmetry_single_cell | unsupported_for_matrix_corpus | 0 | 3 | 0 |

## Strict Benchmark Evidence

- `outputs/strict_benchmarks/leaveout_brassicaceae_dataset.split_audit.json`: split_audit, supervised_ready=False
- `outputs/strict_benchmarks/leaveout_brassicaceae_dataset_available.split_audit.json`: split_audit, supervised_ready=False
- `outputs/strict_benchmarks/leaveout_eutrema_species.split_audit.json`: split_audit, supervised_ready=False
- `outputs/strict_benchmarks/leaveout_srp169576_sample.centroid_baseline.json`: baseline, supervised_ready=None, fine_test_macro_f1=0.4873
- `outputs/strict_benchmarks/leaveout_srp169576_sample.split_audit.json`: split_audit, supervised_ready=True
- `outputs/strict_benchmarks/public_sprint.marker_candidates.json`: split_audit, supervised_ready=None
- `outputs/strict_benchmarks/public_sprint_group_random.centroid_baseline.json`: baseline, supervised_ready=None, fine_test_macro_f1=0.7125
- `outputs/strict_benchmarks/public_sprint_group_random.split_audit.json`: split_audit, supervised_ready=True

## External Benchmark Evidence

- `outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json`: scplantannotate_authenticated_or_exported, metric=False, test_cells=None
- `outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json`: scplantllm_frozen_embedding_nearest_centroid_probe, metric=True, test_cells=None
- `outputs/external_benchmarks/scplantllm_embedding_centroid_probe_128.json`: scplantllm_frozen_embedding_nearest_centroid_probe, metric=True, test_cells=None
- `outputs/external_benchmarks/seurat_public_sprint.json`: seurat_label_transfer, metric=True, test_cells=3637, fine_test_macro_f1=0.7395, coarse_test_macro_f1=0.7395

## Saussurea Supporting Transcriptome Evidence

- `saussurea_bulk_transcriptome`: status=download_candidate, accession=PRJNA169171 / SRR516284, runs=3, strategies=RNA-Seq, total_size_mb=1074.0, source_page=True
- `saussurea_genome_reference`: status=download_candidate, accession=PRJNA991078, runs=0, strategies=unknown, total_size_mb=0.0, source_page=True
- `saussurea_low_pressure`: status=download_candidate, accession=PRJNA1218246, runs=6, strategies=RNA-Seq, total_size_mb=12858.0, source_page=True
- `saussurea_low_temperature`: status=download_candidate, accession=PRJNA1033840, runs=9, strategies=RNA-Seq, total_size_mb=41107.0, source_page=True
- `saussurea_raw_sequence_reads`: status=discovery_candidate, accession=PRJNA387384, runs=0, strategies=unknown, total_size_mb=0.0, source_page=True
- `saussurea_medusa_wgs`: status=discovery_candidate, accession=PRJNA1278884, runs=14, strategies=RNA-Seq;WGS, total_size_mb=94669.0, source_page=True
- `saussurea_hypsipeta_leaf_rna`: status=discovery_candidate, accession=PRJNA1293189, runs=16, strategies=Hi-C;RNA-Seq;WGS, total_size_mb=316518.0, source_page=True
- `saussurea_lyrata_hic`: status=discovery_candidate, accession=PRJNA1355060, runs=3, strategies=Hi-C;RNA-Seq;WGS, total_size_mb=61530.0, source_page=True
- `saussurea_multicellular_spheroid_single_cell_report`: status=literature_request_candidate, accession=PMID:41668397 / DOI:10.1002/adhm.202504623, runs=0, strategies=unknown, total_size_mb=0.0, source_page=True
- `saussurea_discovered_prjna1121965`: status=discovered_runinfo_candidate, accession=PRJNA1121965, runs=66, strategies=RNA-Seq, total_size_mb=250565.0, source_page=True
- `saussurea_discovered_prjna1181600`: status=discovered_runinfo_candidate, accession=PRJNA1181600, runs=1, strategies=WGS, total_size_mb=761.0, source_page=True
- `saussurea_discovered_prjna1259734`: status=discovered_runinfo_candidate, accession=PRJNA1259734, runs=48, strategies=RNA-Seq, total_size_mb=728.0, source_page=True
- `saussurea_discovered_prjna383290`: status=discovered_runinfo_candidate, accession=PRJNA383290, runs=1, strategies=RNA-Seq, total_size_mb=8196.0, source_page=True
- `saussurea_discovered_prjna554516`: status=discovered_runinfo_candidate, accession=PRJNA554516, runs=1, strategies=RNA-Seq, total_size_mb=3492.0, source_page=True
- `saussurea_discovered_prjna635206`: status=discovered_runinfo_candidate, accession=PRJNA635206, runs=1, strategies=RNA-Seq, total_size_mb=3016.0, source_page=True
- `saussurea_discovered_prjna635243`: status=discovered_runinfo_candidate, accession=PRJNA635243, runs=1, strategies=RNA-Seq, total_size_mb=3193.0, source_page=True
- `saussurea_discovered_prjna690192`: status=discovered_runinfo_candidate, accession=PRJNA690192, runs=2, strategies=WGS, total_size_mb=1409.0, source_page=True
- `saussurea_discovered_prjna707512`: status=discovered_runinfo_candidate, accession=PRJNA707512, runs=1, strategies=RNA-Seq, total_size_mb=1459.0, source_page=True
- `saussurea_discovered_prjna721598`: status=discovered_runinfo_candidate, accession=PRJNA721598, runs=1, strategies=WGS, total_size_mb=1658.0, source_page=True
- `saussurea_discovered_prjna723196`: status=discovered_runinfo_candidate, accession=PRJNA723196, runs=5, strategies=RNA-Seq, total_size_mb=21446.0, source_page=True
- `saussurea_discovered_prjna728186`: status=discovered_runinfo_candidate, accession=PRJNA728186, runs=1, strategies=WGS, total_size_mb=589.0, source_page=True
- `saussurea_discovered_prjna782224`: status=discovered_runinfo_candidate, accession=PRJNA782224, runs=1, strategies=WGS, total_size_mb=1310.0, source_page=True
- `saussurea_discovered_prjna854342`: status=discovered_runinfo_candidate, accession=PRJNA854342, runs=1, strategies=WGS, total_size_mb=1492.0, source_page=True
- `saussurea_discovered_prjna860834`: status=discovered_runinfo_candidate, accession=PRJNA860834, runs=33, strategies=RNA-Seq, total_size_mb=187323.0, source_page=True

## Remaining Hard Gaps

- Add real `data/saussurea_involucrata.h5ad` with required cell, sample, tissue, species, batch, and label metadata.
- Finish pending public downloads/conversions and rebuild the public MLM corpus.
- Run comparable Seurat, scPlantLLM, and scPlantAnnotate benchmarks.
- Produce marker/regulator validation tables and independent biological validation evidence.
