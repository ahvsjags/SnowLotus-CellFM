# Plant-CellFM v9 Final Handoff Summary

Generated: `2026-07-31 02:04 Asia/Shanghai`

## Position

Project: `Plant-CellFM / SnowLotus-CellFM`

Scope: plant-general single-cell and single-nucleus expression foundation model with all-plant adapter framework.

Formal hardware statement: `NVIDIA GeForce RTX 4090, 24 GB VRAM`.

Repository: https://github.com/ahvsjags/SnowLotus-CellFM

Branch: `agent/remote-pipeline-20260728`

Release tag: `v0.9.0-plant-general-lora`

## Server

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

## Read First

- `SUBMISSION_INDEX_v9.md`
- `manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx`
- `release_metadata/final_handoff_summary_v9.md`
- `release_metadata/plant_cellfm_v9_model_card.md`
- `release_metadata/release_gate_completion_audit_v9.md (generated on server/outputs)`
- `release_metadata/server_release_verification_v9.md (generated on server/outputs)`
- `release_metadata/species_ontology_label_benchmark_v9.md`
- `release_metadata/cross_species_classifier_benchmark_v10.md`
- `release_metadata/revision_v13_neural_zero_shot_stc.md`
- `release_metadata/revision_v14_context_stc_benchmark.md`
- `release_metadata/revision_v11_fewshot_adapter_benchmark.md`
- `release_metadata/revision_v11_runtime_head_benchmark.md`
- `release_metadata/revision_v11_third_party_closure.md`
- `release_metadata/algorithm_innovation_v14.md`
- `release_metadata/open_set_calibration_v9.md`
- `release_metadata/third_party_benchmark_contract_v10.md`
- `release_metadata/multispecies_scplantdb_case_v10.md`
- `release_metadata/submission_scorecard_v14.md`
- GITHUB_SYNC_RECOVERY.md inside the final zip

## Headline Metrics

| Metric | Value |
| --- | ---: |
| Leave-dataset-out v9 all-cell accuracy | 0.4490 |
| Leave-dataset-out v3 all-cell accuracy | 0.2021 |
| Leave-sample-out v9 all-cell accuracy | 0.6200 |
| Leave-sample-out v3 all-cell accuracy | 0.4155 |
| Normalized leave-species-out v9 all-cell accuracy | 0.2354 |
| Normalized leave-species-out v3 all-cell accuracy | 0.1912 |
| Normalized leave-species-out v9 coverage | 0.5590 |
| Normalized leave-species-out v9 known-label accuracy | 0.4210 |
| STC `knn_cosine_k9` leave-species all-cell accuracy | 0.3010 |
| STC centroid baseline leave-species all-cell accuracy | 0.2364 |
| STC leave-species known-label accuracy | 0.5384 |
| STC centroid baseline known-label accuracy | 0.4228 |
| STC leave-species macro-F1 | 0.2663 |
| STC centroid baseline macro-F1 | 0.1922 |
| v13 neural STC leave-species all-cell accuracy | 0.3184 |
| v14 context-aware STC leave-species all-cell accuracy | 0.4236 |
| v14 context-aware STC leave-species known-label accuracy | 0.7577 |
| v14 context-aware STC leave-species macro-F1 | 0.3045 |
| v11 few-shot adapter, 8 support cells/species mean query all-cell accuracy | 0.5921 |
| v11 few-shot adapter, 16 support cells/species mean query all-cell accuracy | 0.6734 |
| v11 full-vocabulary runtime-head all-cell accuracy | 0.6625 |
| v11 runtime-head covered-label accuracy | 0.6286 |
| v11 runtime-head open-set-label accuracy | 0.7054 |
| Ontology-label actionable coverage | 74.44% |
| Ontology-label actionable all-cell accuracy | 14.97% |
| Ontology-label known-label accuracy | 20.12% |
| Ontology-label macro-F1 | 0.1395 |
| API confidence top-30 selective accuracy | 96.64% |
| API confidence top-40 selective accuracy | 92.81% |

## Biology Case

Arabidopsis root adapter and marker-candidate case contains `260` marker-candidate rows, `13` cell states and `10` root-identity states.

Multi-species scPlantDB public-data biology case contains `31503` cells, `4` species, `4` tissues and `96` marker-candidate rows.

## Safe Claims

- Plant-CellFM v9 is a reproducible plant-general foundation-model and adapter framework for plant single-cell expression annotation.
- The current release is not Snow Lotus-only; Snow Lotus is a target-species adapter entry point under the same contract.
- The strict leave-species result should be interpreted as open-set cross-species transfer evidence, not universal high-accuracy annotation for every plant species.
- The v10 expression STC layer improves strict frozen leave-species all-cell accuracy from 23.64% to 30.10%; the v14 context-aware STC layer further improves the same strict denominator to 42.36% all-cell and 75.77% known-label accuracy without training on held-out species labels.
- The v11 few-shot target-adapter benchmark improves the practical new-species adaptation protocol above the 40% revision target: 8 random labeled support cells per target species reach 59.21% mean query all-cell accuracy.
- The v11 runtime-head benchmark reports the deployable full-vocabulary annotation protocol at 66.25% all-cell accuracy, with covered-label and open-set-label performance separated.
- The open-set calibration audit supports a high-confidence auto-annotation and low-confidence review workflow.
- The release includes completed v3, centroid and Seurat comparators; scPlantLLM/scPlantAnnotate are disclosed through official-source benchmark contracts unless official runs are added later.
- The Arabidopsis root and multi-species scPlantDB cases are public-data computational biology demonstrations with marker candidates, not wet-lab validation.

## Do Not Claim

- Do not claim a completed Snow Lotus single-cell atlas.
- Do not claim universal high-accuracy zero-shot annotation for every plant species.
- Do not present v11 few-shot adapter results as zero-shot leave-species results; they require labeled target-species support cells.
- Do not claim official scPlantLLM/scPlantAnnotate numerical superiority without executable third-party metrics.
- Do not cite early hardware planning notes as the formal hardware statement; use RTX 4090.
- Do not treat 90+ evidence-readiness as 90+ raw cross-species accuracy.

## Handoff Interpretation

Use this file as the short handoff layer. The authoritative proof remains the server verifier, release gate audit, model card, benchmark JSON files, final Word manuscript and final editor zip status JSON.

