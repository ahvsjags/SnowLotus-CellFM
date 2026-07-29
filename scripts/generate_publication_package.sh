#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export PATH="/root/miniconda3/envs/myconda/bin:$PATH"
source .venv/bin/activate 2>/dev/null || true

mkdir -p outputs/publication_package
mkdir -p outputs/publication_package/scripts
mkdir -p outputs/publication_package/scripts/generated_geo_promotion_downloads
mkdir -p outputs/publication_package/strict_benchmarks
mkdir -p outputs/publication_package/public_discovery
mkdir -p outputs/publication_package/benchmarks
mkdir -p outputs/publication_package/data_audits
mkdir -p outputs/publication_package/runtime_smoke

PYTHONPATH=src /root/miniconda3/envs/myconda/bin/python -m snowcell.cli report \
  --project-dir . \
  --output outputs/publication_package/publication_readiness_report.md || true

python scripts/write_pending_corpus_additions.py \
  --project-dir . \
  --output-md outputs/publication_package/pending_corpus_additions.md \
  --output-json outputs/publication_package/pending_corpus_additions.json || true

python scripts/write_public_mlm_plus_readiness.py \
  --project-dir . \
  --output-md outputs/publication_package/public_mlm_plus_readiness.md \
  --output-json outputs/publication_package/public_mlm_plus_readiness.json || true

python scripts/extract_scplantdb_catalog.py \
  --chunks-dir data/public/source_pages/scplantdb_chunks \
  --output-tsv data/public_discovery/scplantdb_dataset_catalog.tsv \
  --output-json data/public_discovery/scplantdb_dataset_catalog.json \
  --output-md data/public_discovery/scplantdb_acquisition_catalog.md || true

python scripts/write_public_discovery_gap_audit.py \
  --project-dir . \
  --output-md outputs/publication_package/public_discovery/public_discovery_gap_audit.md \
  --output-json outputs/publication_package/public_discovery/public_discovery_gap_audit.json || true

python scripts/write_geo_manifest_promotion_candidates.py \
  --project-dir . \
  --output-md data/public_discovery/geo_manifest_promotion_candidates.md \
  --output-json data/public_discovery/geo_manifest_promotion_candidates.json \
  --output-tsv data/public_discovery/geo_manifest_promotion_candidates.tsv || true

python scripts/write_geo_promotion_download_wrappers.py \
  --project-dir . \
  --promotion-tsv data/public_discovery/geo_manifest_promotion_candidates.tsv \
  --output-dir scripts/generated_geo_promotion_downloads \
  --queue-script scripts/generated_geo_promotion_downloads/queue_geo_promotion_downloads.sh \
  --start-script scripts/generated_geo_promotion_downloads/start_geo_promotion_queue.sh \
  --output-md data/public_discovery/geo_promotion_download_queue.md \
  --output-json data/public_discovery/geo_promotion_download_queue.json \
  --output-tsv data/public_discovery/geo_promotion_download_queue.tsv || true

python scripts/audit_data_integrity.py \
  --project-dir . \
  --output-md outputs/publication_package/data_integrity_audit.md \
  --output-json outputs/publication_package/data_integrity_audit.json \
  --output-tsv outputs/publication_package/data_integrity_audit.tsv || true

python scripts/write_corpus_provenance_audit.py \
  --project-dir . \
  --output-md outputs/publication_package/corpus_provenance_audit.md \
  --output-json outputs/publication_package/corpus_provenance_audit.json \
  --output-tsv outputs/publication_package/corpus_provenance_audit.tsv || true

python scripts/write_scplantdb_manifest_audit.py \
  --project-dir . \
  --manifest data/corpus_manifest.scplantdb.tsv \
  --output-md outputs/publication_package/scplantdb_manifest_audit.md \
  --output-json outputs/publication_package/scplantdb_manifest_audit.json \
  --output-tsv outputs/publication_package/scplantdb_manifest_audit.tsv || true

python scripts/write_scplantannotate_benchmark_package.py \
  --project-dir . \
  --input-h5ad "${SNOWCELL_SCPLANTANNOTATE_INPUT_H5AD:-data/plant_foundation_corpus_public_mlm_available.h5ad}" \
  --output-dir outputs/external_benchmarks/scplantannotate_public_sprint_input \
  --output-md outputs/publication_package/scplantannotate_benchmark_input_package.md \
  --output-json outputs/publication_package/scplantannotate_benchmark_input_package.json || true

python scripts/run_scplantannotate_authenticated_benchmark.py \
  --input-h5ad outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad \
  --truth-csv outputs/external_benchmarks/scplantannotate_public_sprint_input/truth_labels.csv \
  --dataset-name snowcell_public_sprint_scplantannotate_probe \
  --organism-id 1 \
  --predictor-id 1 \
  --output outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json || true

python scripts/write_status_summary.py \
  --project-dir . \
  --output outputs/publication_package/status_summary.json || true

python scripts/write_download_progress_audit.py \
  --project-dir . \
  --status-summary outputs/publication_package/status_summary.json \
  --output-md outputs/publication_package/download_progress_audit.md \
  --output-json outputs/publication_package/download_progress_audit.json || true

python scripts/write_transfer_queue_health_audit.py \
  --project-dir . \
  --output-md outputs/publication_package/transfer_queue_health_audit.md \
  --output-json outputs/publication_package/transfer_queue_health_audit.json || true

python scripts/write_geo_promotion_queue_health_audit.py \
  --project-dir . \
  --output-md outputs/publication_package/geo_promotion_queue_health_audit.md \
  --output-json outputs/publication_package/geo_promotion_queue_health_audit.json || true

python scripts/write_training_health_audit.py \
  --project-dir . \
  --output-md outputs/publication_package/training_health_audit.md \
  --output-json outputs/publication_package/training_health_audit.json || true

python scripts/write_training_curve_summary.py \
  --project-dir . \
  --output-md outputs/publication_package/training_curve_summary.md \
  --output-json outputs/publication_package/training_curve_summary.json \
  --output-tsv outputs/publication_package/training_curve_summary.tsv \
  --output-png outputs/publication_package/training_curve_summary.png || true

python scripts/write_modality_compatibility_audit.py \
  --project-dir . \
  --status-summary outputs/publication_package/status_summary.json \
  --public-manifest data/public_dataset_manifest.tsv \
  --output-md outputs/publication_package/modality_compatibility_audit.md \
  --output-json outputs/publication_package/modality_compatibility_audit.json || true

python scripts/write_benchmark_gap_audit.py \
  --status-summary outputs/publication_package/status_summary.json \
  --project-dir . \
  --output-md outputs/publication_package/benchmark_gap_audit.md \
  --output-json outputs/publication_package/benchmark_gap_audit.json || true

python scripts/write_external_tool_environment.py \
  --project-dir . \
  --output-md outputs/publication_package/external_tool_environment.md \
  --output-json outputs/publication_package/external_tool_environment.json || true

python scripts/write_scplantllm_input_readiness.py \
  --project-dir . \
  --input-dir outputs/external_benchmarks/scplantllm_public_sprint_input \
  --output-md outputs/publication_package/scplantllm_input_readiness.md \
  --output-json outputs/publication_package/scplantllm_input_readiness.json || true

python scripts/write_scplantannotate_access_audit.py \
  --timeout 5 \
  --max-bytes 500000 \
  --max-assets 8 \
  --max-endpoints 6 \
  --output-md outputs/publication_package/scplantannotate_access_audit.md \
  --output-json outputs/publication_package/scplantannotate_access_audit.json || true

python scripts/write_top_journal_readiness_matrix.py \
  --status-summary outputs/publication_package/status_summary.json \
  --output outputs/publication_package/top_journal_readiness_matrix.md \
  --output-json outputs/publication_package/top_journal_readiness_matrix.json || true

python scripts/write_submission_action_plan.py \
  --project-dir . \
  --output-md outputs/publication_package/submission_action_plan.md \
  --output-json outputs/publication_package/submission_action_plan.json \
  --output-tsv outputs/publication_package/submission_action_plan.tsv || true

python scripts/write_data_availability_package.py \
  --status-summary outputs/publication_package/status_summary.json \
  --public-manifest data/public_dataset_manifest.tsv \
  --output outputs/publication_package/data_availability_and_fair.md || true

python scripts/write_model_data_card.py \
  --status-summary outputs/publication_package/status_summary.json \
  --output-md outputs/publication_package/model_data_card.md \
  --output-json outputs/publication_package/model_data_card.json || true

python scripts/write_model_release_manifest.py \
  --project-dir . \
  --output-md outputs/publication_package/model_release_manifest.md \
  --output-json outputs/publication_package/model_release_manifest.json || true

python scripts/write_annotation_bundle_index.py \
  --project-dir . \
  --output-md outputs/publication_package/annotation_bundle_index.md \
  --output-json outputs/publication_package/annotation_bundle_index.json || true

python scripts/write_saussurea_supporting_evidence.py \
  --project-dir . \
  --output-md outputs/publication_package/saussurea_supporting_evidence.md \
  --output-json outputs/publication_package/saussurea_supporting_evidence.json || true

python scripts/validate_saussurea_h5ad_contract.py \
  --input data/saussurea_involucrata.h5ad \
  --output-md outputs/publication_package/saussurea_h5ad_contract.md \
  --output-json outputs/publication_package/saussurea_h5ad_contract.json || true

python scripts/write_saussurea_public_data_discovery.py \
  --output-md outputs/publication_package/saussurea_public_data_discovery.md \
  --output-json outputs/publication_package/saussurea_public_data_discovery.json || true

python scripts/write_saussurea_data_request_package.py \
  --project-dir . \
  --output-md outputs/publication_package/saussurea_data_request_package.md \
  --output-json outputs/publication_package/saussurea_data_request_package.json \
  --output-email outputs/publication_package/saussurea_data_request_email.txt || true

python scripts/write_environment_snapshot.py \
  --project-dir . \
  --output outputs/publication_package/environment_snapshot.md \
  --json-output outputs/publication_package/environment_snapshot.json || true

python scripts/write_submission_dossier.py \
  --project-dir . \
  --output-md outputs/publication_package/submission_dossier.md \
  --output-json outputs/publication_package/submission_dossier.json || true

cp -f data/public_dataset_manifest.tsv outputs/publication_package/ 2>/dev/null || true
cp -f data/corpus_manifest*.tsv outputs/publication_package/ 2>/dev/null || true
cp -f data/public_discovery/*.tsv outputs/publication_package/public_discovery/ 2>/dev/null || true
cp -f data/public_discovery/*.json outputs/publication_package/public_discovery/ 2>/dev/null || true
cp -f data/public_discovery/*.md outputs/publication_package/public_discovery/ 2>/dev/null || true
cp -f data/public_discovery/*.txt outputs/publication_package/public_discovery/ 2>/dev/null || true
cp -f README.md outputs/publication_package/ 2>/dev/null || true
cp -f docs/top_journal_strategy.md outputs/publication_package/ 2>/dev/null || true
cp -f docs/saussurea_evidence_plan.md outputs/publication_package/ 2>/dev/null || true
cp -f docs/external_benchmark_blockers.md outputs/publication_package/ 2>/dev/null || true
cp -f configs/*.yaml outputs/publication_package/ 2>/dev/null || true
cp -f scripts/collect_public_data.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse268881_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/convert_gse268881_available.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/geo_10x_to_npz.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/geo_mtx_tar_to_npz.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/geo_page_download_urls.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/export_seurat_rds_to_mtx.R outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/export_seurat_rds_expression_slot_to_mtx.R outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/inspect_seurat_slots_without_signac.R outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/build_npz_from_seurat_export.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_npz_corpus_manifest.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_rds_unsupported_manifest_from_inspection.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/run_gse226826_without_signac_recovery.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/build_public_mlm_corpus.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/build_public_mlm_plus_corpus.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/build_available_public_mlm_corpus.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_public_mlm_v0_4_config.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/queue_public_mlm_expansion.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/queue_late_public_mlm_refresh.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_late_public_refresh_queue.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/watch_public_mlm_v0_4_after_v0_3.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_public_mlm_v0_4_after_v0_3_watchdog.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/watch_safe_mlm_refresh.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/watch_publication_package_refresh.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_publication_package_watchdog.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/queue_reviewed_geo_downloads.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_public_queues.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_reviewed_geo_queue.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/restart_geo_promotion_worker.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_public_mlm_training.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_public_mlm_continuation_training.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/watch_public_mlm_continuation.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_public_mlm_continuation_watchdog.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_public_mlm_continuation_package_watchdog.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/push_github_release.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_public_safe_init_training.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/ensure_public_data_jobs.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/discover_ncbi_public_datasets.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/discover_public_ncbi_data.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_public_discovery_refresh.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/review_geo_supplementary_candidates.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/review_geo_supplementary_candidates.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_geo_manifest_promotion_candidates.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_geo_promotion_download_wrappers.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/generated_geo_promotion_downloads/*.sh outputs/publication_package/scripts/generated_geo_promotion_downloads/ 2>/dev/null || true
cp -f scripts/monitor_snowcell_server.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_training_curve_summary.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_submission_action_plan.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/create_leaveout_config.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/audit_leaveout_splits.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/run_strict_benchmark_audits.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/tenx_h5_to_npz.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse270342_wheat_h5_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/fetch_geo_supplementary_filelist.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_geo_h5_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_geo_raw_tar_h5_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_geo_raw_tar_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_geo_mtx_tar_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_geo_mtx_component_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_geo_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_geo_page_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse152766_arabidopsis_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse146034_rice_root_tip_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse243419_cotton_glandular_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse226097_arabidopsis_lifecycle_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_gse226097_lifecycle_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/watch_gse226097_lifecycle_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_gse226097_lifecycle_watchdog.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/extract_scplantdb_catalog.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/probe_scplantdb_h5ad_sizes.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_scplantdb_h5ad_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/queue_scplantdb_budgeted_h5ad_download.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_scplantdb_budgeted_h5ad_queue.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_scplantdb_manifest_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse251706_rice_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse270140_arabidopsis_secondary_root_h5_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse270342_wheat_h5_generic.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse338572_maize_easy_multiome_rna_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse313726_rice_leaf_stress_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse302041_arabidopsis_lateral_root_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse314252_tomato_mycorrhiza_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse308757_rice_node_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse325371_tomato_salt_idioblast_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse234192_plant_callus_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse149217_tomato_rice_root_tip_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse300264_arabidopsis_method_rds_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse311951_stevia_leaf_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/download_gse336751_marchantia_spore_mtx_subset.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/queue_gse336751_marchantia_spore_when_idle.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_status_summary.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_top_journal_readiness_matrix.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_data_availability_package.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_artifact_checksums.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_environment_snapshot.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/validate_experiment_configs.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_pending_corpus_additions.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_public_mlm_plus_readiness.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_model_data_card.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_model_release_manifest.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_annotation_bundle_index.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/create_public_safe_init_annotation_bundle.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/evaluate_checkpoint_detailed.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/run_post_training_release_artifacts.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_submission_dossier.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/audit_data_integrity.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_corpus_provenance_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/collect_saussurea_supporting_metadata.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_saussurea_metadata_collection.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_saussurea_supporting_evidence.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/validate_saussurea_h5ad_contract.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_saussurea_public_data_discovery.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_saussurea_data_request_package.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_benchmark_gap_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/compare_all_plant_checkpoint_benchmarks.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_external_tool_environment.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_download_progress_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_public_discovery_gap_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_transfer_queue_health_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_geo_promotion_queue_health_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_training_health_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_modality_compatibility_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/export_seurat_benchmark_split.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/run_seurat_label_transfer_benchmark.R outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/start_seurat_public_sprint_benchmark.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/export_scplantllm_input.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_scplantllm_input_readiness.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/prepare_scplantllm_public_sprint_input.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/run_scplantllm_preprocess_probe.sh outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/run_scplantllm_embedding_centroid_probe.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_scplantannotate_access_audit.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/write_scplantannotate_benchmark_package.py outputs/publication_package/scripts/ 2>/dev/null || true
cp -f scripts/run_scplantannotate_authenticated_benchmark.py outputs/publication_package/scripts/ 2>/dev/null || true

find outputs -maxdepth 2 -type f \( -name 'test_metrics.json' -o -name 'history.json' -o -name 'config.resolved.json' \) \
  -print > outputs/publication_package/run_artifact_index.txt || true
find outputs/strict_benchmarks -maxdepth 1 -type f \( -name '*.json' -o -name '*.yaml' \) \
  -print > outputs/publication_package/strict_benchmark_index.txt 2>/dev/null || true
find outputs/detailed_evaluations -maxdepth 2 -type f \( -name '*.json' -o -name '*.md' -o -name '*.tsv' \) \
  -print > outputs/publication_package/detailed_evaluation_index.txt 2>/dev/null || true
cp -f outputs/strict_benchmarks/*.json outputs/publication_package/strict_benchmarks/ 2>/dev/null || true
cp -f outputs/strict_benchmarks/*.tsv outputs/publication_package/strict_benchmarks/ 2>/dev/null || true
cp -f configs/generated/*.yaml outputs/publication_package/strict_benchmarks/ 2>/dev/null || true
cp -f outputs/benchmarks/*.json outputs/publication_package/benchmarks/ 2>/dev/null || true
find outputs/benchmarks -maxdepth 1 -type f -name '*.json' \
  -print > outputs/publication_package/benchmark_index.txt 2>/dev/null || true
cp -f outputs/data_audits/gse268881_integrity.* outputs/publication_package/data_audits/ 2>/dev/null || true
cp -f outputs/data_audits/gse268881_refresh_complete.marker outputs/publication_package/data_audits/ 2>/dev/null || true
cp -f outputs/api_smoke_annotation_drp/annotation_metadata.json outputs/api_smoke_annotation_drp/adapter_selection.json outputs/api_smoke_annotation_drp/predictions.csv outputs/publication_package/runtime_smoke/ 2>/dev/null || true

if [ "${SNOWCELL_WRITE_ARTIFACT_CHECKSUMS:-1}" = "1" ]; then
  python scripts/write_artifact_checksums.py \
    --project-dir . \
    --output outputs/publication_package/artifact_checksums.tsv || true
fi

echo "Publication package: outputs/publication_package"
