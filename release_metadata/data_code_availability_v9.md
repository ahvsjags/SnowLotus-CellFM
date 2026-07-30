# Data And Code Availability

Generated: `2026-07-30 21:35 Asia/Shanghai`

## Code Availability

Code repository: https://github.com/ahvsjags/SnowLotus-CellFM

Submission branch: `agent/remote-pipeline-20260728`

Release tag: `v0.9.0-plant-general-lora`

The reviewer-facing entry point is `SUBMISSION_INDEX_v9.md`.

## Model Availability

Frozen checkpoint asset: https://github.com/ahvsjags/SnowLotus-CellFM/releases/download/v0.9.0-plant-general-lora/SnowLotus-CellFM-v9-lora-4090-best.pt

Checkpoint SHA256: `9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`

Model card: `release_metadata/plant_cellfm_v9_model_card.md`

## Data Availability

The release records public-source accessions, processed benchmark manifests and derived audit tables. Original public datasets remain available from their source repositories under their original access conditions.

Primary release evidence files:

- `release_metadata/v9_data_card.md`
- `release_metadata/corpus_provenance_audit.md`
- `release_metadata/data_integrity_audit.json`
- `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json`

Benchmark and case evidence:

- `release_metadata/species_holdout_failure_audit_v9.md`
- `release_metadata/species_ontology_coverage_audit_v9.md`
- `release_metadata/species_ontology_label_benchmark_v9.md`
- `release_metadata/plant_biology_case_study_v9.md`
- `release_metadata/arabidopsis_root_case_figure_v9.md`

## Server Reproducibility

Server root: `/mnt/snowlotus_cellfm`

Final editor zip: `/mnt/snowlotus_cellfm/outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.zip`

Verifier command:

```bash
/root/miniconda3/envs/myconda/bin/python scripts/verify_v9_server_release.py --output-json release_metadata/server_release_verification_v9.json --output-md release_metadata/server_release_verification_v9.md
```

Release gate command:

```bash
/root/miniconda3/envs/myconda/bin/python scripts/write_release_gate_completion_audit_v9.py
```

## Claim Boundary

- The release does not claim a completed Snow Lotus single-cell atlas.
- The release does not claim universal high-accuracy zero-shot annotation for every plant species.
- The release does not claim final official scPlantLLM or scPlantAnnotate numerical superiority without executable third-party benchmark closure.
