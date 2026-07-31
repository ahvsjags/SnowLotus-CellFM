# Plant-CellFM / SnowLotus-CellFM

Plant-CellFM is the general-plant branch of SnowLotus-CellFM, a cross-species foundation model for plant single-cell and single-nucleus expression data. The model is not restricted to *Saussurea involucrata* (Snow Lotus): Snow Lotus is a target-species adapter and application scenario within a broader plant model.

## Current v5 Evidence-First Submission Package

The current reviewer-facing package is the evidence-first v5 release on [`agent/remote-pipeline-20260728`](https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728). It supersedes the v9 narrative below for manuscript, figure and benchmark claims, and keeps strict transfer, target-species adaptation, deployment and label-free external execution as separate evidence tiers.

- **Chinese manuscript**: [`Plant_CellFM_v5_顶刊证据主文.md`](manuscript/Plant_CellFM_v5_顶刊证据主文.md) and [`Word version`](manuscript/Plant_CellFM_v5_顶刊证据主文.docx).
- **Strict primary result**: nested leave-species v17 uses 3,964 aligned cells across 8 held-out species, retains every test cell, and reports 39.96% all-cell accuracy, 55.90% source-label coverage, 71.48% accuracy and 0.2817 macro-F1 on the covered-label subset.
- **Label-integrity companion**: v18 keeps 2,324 explicit-identity cells and audits 1,640 unknown/unannotated labels separately; it is a companion analysis, not a substitute headline.
- **Target-species adaptation**: 8, 16, 32 and 64 labelled support cells per species give 59.21%, 67.34%, 72.30% and 75.89% mean query all-cell accuracy across ten non-overlapping support/query draws.
- **Secondary-root adaptation case**: the frozen SRP169576 root checkpoint was LoRA-mode adapted on author-labelled GSE270140/GSM8335426 secondary-root cells. Its grouped 80/10/20 held-out test reports 83.97% fine accuracy and 84.47% macro-F1 across 2,352 cells; the published LFS checkpoint is byte-linked to its audit record in [`adapter asset metadata`](release_metadata/gse270140_secondary_root_adapter_model_asset_v1.json). This is explicitly one-sample supervised adaptation, not a zero-shot or independent external-validation result.
- **Figures and source data**: four main figures, six Extended Data figures, editable SVG/PDF, PNG previews, local 600-dpi TIFF submission copies and a TSV table for every quantitative panel live in [`figures/plant_cellfm_submission_v5`](figures/plant_cellfm_submission_v5).
- **Supplementary package**: 19 TSV tables plus an Excel workbook are in [`supplementary_tables/submission_v4`](supplementary_tables/submission_v4).
- **Claim and reproducibility record**: [`claim-level evidence ledger`](release_metadata/plant_cellfm_submission_evidence_ledger_v5.md), [`model card`](release_metadata/plant_cellfm_model_card_v4.json), [`v5 figure blueprint`](release_metadata/plant_cellfm_v5_figure_blueprint.md), [`v5 technical audit`](release_metadata/top_journal_figure_audit_v5.md), [`scPlantLLM execution audit`](release_metadata/scplantllm_official_execution_audit.md), [`root literature-concordance audit`](release_metadata/arabidopsis_root_literature_concordance_v4.md) and [`GSE152766 blind external-root audit`](release_metadata/gse152766_external_root_blind_inference_v4.md). The official scPlantLLM checkpoint now executes on CUDA with zero state-key mismatches and a 256/256 official-chunk frozen-encoder probe; it is explicitly not a matched v17 external ranking. The root case recovers 3/6 predefined canonical markers in matching top-20 programs, and a separate label-free GSE152766 root matrix gives a blind external execution in which 5/6 fixed canonical anchors peak in their corresponding predicted group. Neither result is wet-lab validation or external accuracy. Matched scPlantLLM/scPlantAnnotate predictions and independently annotated or experimental biological validation remain open evidence items.

Run the current package with:

```bash
python scripts/run_revision_v18_identity_curated_strict.py
python scripts/run_revision_v11_fewshot_adapter_benchmark.py
python scripts/build_v4_root_literature_concordance.py
python scripts/download_gse152766_external_root_case.py
python scripts/prepare_gse152766_external_root_case.py
python scripts/audit_gse152766_external_root_case.py
python scripts/render_v5_top_journal_figures.py
python scripts/render_v5_secondary_root_adapter_figure.py
python scripts/write_submission_v4_supplementary_tables.py
python scripts/audit_v5_submission_figure_suite.py
npm ci
npm run build:manuscript
```

## Historical v9 Checkpoint Release

The current publication candidate is the v9 LoRA checkpoint trained on an audited public plant corpus with an NVIDIA RTX 4090. The release is frozen for reproducibility; later v10 data-expansion jobs are not part of this candidate.

Reviewer-facing entry point: `SUBMISSION_INDEX_v9.md`. That file lists the current manuscript, model card, benchmark panel and stable claim boundaries for the frozen v9 package.

- Corpus: 56 manifest rows, 29 datasets, 20 normalized plant species labels and 21 raw species strings before alias canonicalization.
- Training corpus: 13.78 million cells after corpus construction.
- Architecture: 256-dimensional model, 4 transformer layers, 8 attention heads, LoRA rank 8.
- Training: six epochs, hybrid masked-expression modelling and hierarchical annotation objectives, CUDA mixed precision.
- Checkpoint: `best.pt` in the GitHub release asset and on the Matpool host at `/root/snowlotus_cellfm_v9_lora_shared_4090/best.pt`.
- Service: Plant-CellFM inference service with embedding, annotation, ortholog-map transfer and runtime species-adapter resolution.

## Historical v9 Submission Scope

Exploratory post-v9 continuation logs are kept outside the editor-facing v9 package. The current submission uses the frozen v9 checkpoint, v9 benchmarks, open-set calibration, third-party benchmark contracts, server verification and two public-data biology cases. The multi-species scPlantDB case is included as a biology demonstration and marker-candidate resource, not as a replacement performance claim for a new checkpoint.

## Archived v9 Evaluation Snapshot

The release reports both an internal held-out test and stricter cross-group evaluations. The latter are the appropriate evidence for cross-species generalization.

| Evaluation | All-cell accuracy | Label coverage | Known-label conditional accuracy | Known-label conditional macro-F1 |
| --- | ---: | ---: | ---: | ---: |
| Internal held-out test | 0.8113 | n/a | n/a | 0.3833 |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 |
| STC v10 `knn_cosine_k9`, same frozen embeddings | 0.3010 | 0.5590 | 0.5384 | 0.2663 |
| STC v14 `phylo_organ_gate_v1`, same frozen embeddings | 0.4236 | 0.5590 | 0.7577 | 0.3045 |
| v15 runtime-teacher rescue t0.70 with v14 fallback | 0.6009 | 0.5590 | 0.7396 | 0.3485 |
| v15 full runtime annotation head, deployment protocol | 0.6625 | 0.5590 partition | 0.6286 | 0.3408 |

The known-label conditional columns evaluate only test cells whose reference labels occur in the training fold. The all-cell accuracy column counts cells with unseen labels as errors, which is the appropriate open-set view for species holdout. The species-holdout protocol canonicalizes species aliases such as `Arabidopsis_thaliana` and `Arabidopsis thaliana` before splitting, reducing the selected benchmark from 9 raw species labels to 8 normalized species groups. Against the frozen v3 extended baseline on the same shared-gene benchmark, v9 all-cell accuracy improved by 24.70, 20.45 and 4.41 percentage points for leave-dataset, leave-sample and normalized leave-species evaluation, respectively. All benchmark JSON, model checksums, training history and the 256-cell benchmark subset are included in the release package.

The species-holdout failure audit is paired with a conservative label-ontology coverage audit. The ontology audit aligns the server-exported benchmark `obs` labels to the frozen 3,964 leave-species test cells, reconstructs exact-label coverage within 30 cells of the frozen JSON, maps 106 observed fine labels to plant cell-state categories, and reports 45.26% actionable ontology coverage after excluding 1,384 unknown or unannotated cells. This does not revise the frozen accuracy; it explains which errors come from open-set labels, uninformative annotations and fixable ontology harmonization.

The next diagnostic layer is an ontology-label leave-species benchmark using the frozen 3,964 x 256 runtime-smoke embeddings. Exact-label recomputation matches the frozen species benchmark closely, while the ontology-actionable protocol reports 2,324 actionable cells, 74.44% ontology-label coverage, 14.97% actionable all-cell accuracy and 20.12% known-label accuracy after excluding 1,640 unknown or unannotated cells. This result is intentionally reported as a stricter label-harmonized diagnostic, not as a replacement for the frozen exact-label species-holdout headline.

The v10 Species-Transfer Calibration (STC) layer adds a real classifier-side improvement under the same frozen runtime-smoke embeddings and the same leave-species split. Without using held-out species labels for training, the best `knn_cosine_k9` calibrated layer improves strict exact-label all-cell accuracy from the centroid baseline 23.64% to 30.10%, known-label accuracy from 42.28% to 53.84%, and known-label macro-F1 from 0.1922 to 0.2663. Coverage remains 55.90%, so this is reported as measured classifier calibration rather than a denominator change or a universal high-accuracy claim.

The v13/v14 revision experiments close the stricter zero-shot concern. A neural calibration sweep shows that classifier capacity alone raises the strict all-cell score only to 31.84%, so the remaining error is not solved by another generic head. The v14 context-aware STC extension then adds a phylogeny/organ gate estimated only from training species metadata: if same-family informative training support exists, expression similarity is used; otherwise the method falls back to plant-organ priors. Under the same frozen embeddings, same 3,964 aligned cells and same 55.90% label coverage, `phylo_organ_gate_v1` reaches 42.36% strict all-cell accuracy, 75.77% known-label accuracy and 0.3045 known-label macro-F1 without using held-out species labels for training, calibration or prior construction.

The v15 runtime-teacher rescue benchmark adds a separate deployment/readiness protocol rather than changing the strict zero-shot claim. The strict inductive headline remains the v14 42.36% result. When the already-trained Plant-CellFM runtime annotation head is allowed to participate as a high-confidence teacher, `teacher_rescue_t07_v14fallback` reaches 60.09% all-cell accuracy, 73.96% known-label accuracy, 0.3485 known-label macro-F1 and 42.51% open-set exact accuracy while falling back to v14 below the confidence threshold. The full runtime annotation head reaches 66.25% all-cell accuracy, 62.86% covered-label accuracy and 70.54% open-set-label accuracy. These v15 values are deployment metrics and are not reported as strict leave-species zero-shot scores.

The v11 target-species adapter benchmark remains useful as a separate small-label adaptation protocol. With the same frozen embeddings, a small labeled support set from each held-out species is used only for adapter/classifier calibration, and all support cells are excluded from query evaluation. The conservative fixed-budget setting of 8 labeled support cells per target species reaches 59.21% mean query all-cell accuracy across 10 seeds; 16, 32 and 64 support cells per species reach 67.34%, 72.30% and 75.89%, respectively. This is explicitly separate from zero-shot strict STC.

The open-set calibration layer converts the low raw species-holdout metric into a controlled-use protocol. The deployed API annotation head reaches 66.25% exact-label accuracy on all 3,964 runtime-smoke cells; within the strict leave-species train-label partition it obtains 62.86% accuracy on covered-label cells and 70.54% on open-set-label cells, contributing 35.14% and 31.10% all-cell accuracy. When only the top 30% and top 40% fine-confidence cells are accepted automatically, selective accuracy rises to 96.64% and 92.81%. Lower-confidence and open-set-like cells are explicitly routed to manual review, ontology harmonization or species-adapter calibration.

The extended methods panel also includes transparent non-Plant-CellFM comparators and biological case-study assets. Seurat anchor-based label transfer was run on the frozen v9 subset export with 2,940 train cells and 512 test cells, obtaining fine accuracy 0.2207 and macro-F1 0.0603. The classical cosine-centroid SRP169576 sample-holdout baseline reports fine accuracy 0.7337 and macro-F1 0.4873. The scPlantLLM and scPlantAnnotate entries are now represented by official-source benchmark contracts and a v11 closure audit: scPlantLLM has a 20,000-cell input package with 24,392 retained genes and 1.0 vocabulary overlap, with the official LFS weight download tracked by SHA256/OID; scPlantAnnotate has a 5,000-cell, 12-class authenticated-input package and access audit. The Arabidopsis root case study contains 260 marker-candidate rows across 13 cell states, and the multi-species scPlantDB case adds 31,503 cells across 4 species, 4 tissues and 96 marker-candidate records.

## Repositories and Release

- Repository: https://github.com/ahvsjags/SnowLotus-CellFM
- Current v5 reviewer branch: https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728
- Frozen v9 release: https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora
- Code branch used for the release: `agent/remote-pipeline-20260728`

The repository contains the source package, training configurations, public-data manifests, audit scripts, benchmark code, model card, manuscript materials and service watchdog. The large checkpoint is distributed as a GitHub Release asset rather than committed to Git history.

## Model Functions

- Cross-species expression embeddings from `.h5ad` or `.npz` input.
- Masked-expression feature extraction and annotation inference.
- Hierarchical fine/coarse cell-state prediction when a supervised head is available.
- Exact-gene transfer followed by an optional ortholog TSV for species with different gene identifiers.
- Known adapter registry plus runtime adapter materialization for any named plant species.
- Reproducible output bundles containing predictions, embeddings, metadata and adapter-selection records.

## Quick Start

```bash
python -m pip install -e ".[singlecell,dev]"
snowcell make-demo --output data/demo.npz
snowcell train --config configs/smoke.yaml
snowcell predict --checkpoint outputs/smoke/best.pt --data data/demo.npz --output outputs/smoke/predictions.csv
```

For the frozen model, download the v9 release asset and use the packaged configuration and scripts. The server-side API exposes `GET /health`, `GET /metadata`, `GET /capabilities`, `GET /adapters` and `POST /annotate`.

## Reproducibility Evidence

### Current v5 evidence assets

- `manuscript/Plant_CellFM_v5_顶刊证据主文.md`
- `manuscript/Plant_CellFM_v5_顶刊证据主文.docx`
- `release_metadata/plant_cellfm_model_card_v4.json`
- `release_metadata/revision_v17_nested_metadata_gate.json`
- `release_metadata/revision_v18_identity_curated_strict.json`
- `release_metadata/plant_cellfm_v5_figure_blueprint.md`
- `release_metadata/plant_cellfm_submission_evidence_ledger_v5.md`
- `release_metadata/top_journal_figure_audit_v5.md`
- `figures/plant_cellfm_submission_v5/`
- `supplementary_tables/submission_v4/`
- `scripts/render_v5_top_journal_figures.py`
- `scripts/write_submission_v4_supplementary_tables.py`
- `scripts/audit_v5_submission_figure_suite.py`

### Archived v9 evidence assets

- `SUBMISSION_INDEX_v9.md`
- `release_metadata/plant_cellfm_v9_model_card.md`
- `release_metadata/v9_data_card.md`
- `release_metadata/data_integrity_audit.md`
- `release_metadata/corpus_provenance_audit.md`
- `release_metadata/benchmark_gap_audit.md`
- `release_metadata/external_benchmark_status_v9.md`
- `release_metadata/external_benchmark_panel_v9.md`
- `release_metadata/plant_biology_case_study_v9.md`
- `release_metadata/arabidopsis_root_case_figure_v9.md`
- `release_metadata/species_holdout_failure_audit_v9.md`
- `release_metadata/species_ontology_coverage_audit_v9.md`
- `release_metadata/species_ontology_label_benchmark_v9.md`
- `release_metadata/cross_species_classifier_benchmark_v10.md`
- `release_metadata/revision_v13_neural_zero_shot_stc.md`
- `release_metadata/revision_v14_context_stc_benchmark.md`
- `release_metadata/revision_v15_runtime_teacher_rescue.md`
- `release_metadata/revision_v11_fewshot_adapter_benchmark.md`
- `release_metadata/revision_v11_runtime_head_benchmark.md`
- `release_metadata/revision_v11_third_party_closure.md`
- `release_metadata/algorithm_innovation_v10.md`
- `release_metadata/algorithm_innovation_v14.md`
- `release_metadata/open_set_calibration_v9.md`
- `release_metadata/third_party_benchmark_contract_v10.md`
- `release_metadata/multispecies_scplantdb_case_v10.md`
- `release_metadata/submission_scorecard_v11.md`
- `release_metadata/submission_scorecard_v14.md`
- `release_metadata/plant_cell_state_ontology_mapping_v9.tsv`
- `release_metadata/third_party_comparator_sources_v9.md`
- `release_metadata/v9_submission_stability_audit.md`
- `release_metadata/publication_peer_review_preflight_v9.md`
- `release_metadata/top_journal_readiness_matrix.md`
- `release_metadata/server_sustainability_status_v9.md`
- `release_metadata/watchdog_recovery_status_v9.md`
- `release_metadata/v9_editor_issue_closure.md`
- `release_metadata/final_editor_submission_package_recipe_v9.md`
- `release_metadata/api_runtime_smoke_v9.md`
- `manuscript/Plant_CellFM_v9_完整主文_稳健方法版_v1.md`
- `manuscript/Plant_CellFM_v9_final_submission_zh_v1.md`
- `manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx`
- `docs/publication_readiness_v9.md`
- `docs/top_journal_strategy.md`
- `scripts/package_v9_release.sh`
- `scripts/package_v9_editor_submission.py`
- `tests/`

The local regression suite passes with `PYTHONPATH=src pytest -q`. The release package also includes a SHA256 manifest that was verified on the server.

## Evidence Boundary

The v4 package supports the claim that Plant-CellFM is a reproducible, protocol-aware framework for cross-species plant single-cell annotation and target-species adaptation. The primary strict result is v17, not the historical v14 global-context sensitivity value: it reports 39.96% all-cell accuracy across all 3,964 held-out cells at 55.90% source-label coverage. v18 supplies a separate explicit-identity denominator rather than revising that strict headline. Few-shot adaptation and the runtime full-vocabulary head are distinct labelled protocols and must not be presented as zero-shot leave-species performance. The current package documents matched frozen v3-to-v9 checkpoint gains, but does not claim completed numerical superiority over scPlantLLM or scPlantAnnotate, universal performance across all plants, a Snow Lotus single-cell atlas, or wet-lab validation of marker candidates.

## Citation

SnowLotus-CellFM Consortium. *Plant-CellFM: a cross-species foundation model and adapter layer for plant single-cell expression annotation*. Frozen v9 release, 2026.
