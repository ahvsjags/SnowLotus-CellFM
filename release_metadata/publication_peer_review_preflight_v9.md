# Plant-CellFM v9 Peer-Review Preflight

Generated: 2026-07-30 Asia/Shanghai

This preflight is a strict reviewer-style audit of the frozen v9 submission package. It is meant to guide the current submission and the next revision cycle, not to inflate the claim beyond the evidence.

## Editorial Position

Current decision if submitted as a computational method/resource paper: **submission-ready with major-revision risk**.

Current best-fit venues:

| Venue tier | Fit | Rationale |
| --- | --- | --- |
| Plant-focused methods/resource journal | Strong | The paper has a plant-specific problem, public corpus, adapter system, reproducible package, running CUDA service, open-set calibration and two public-data biology cases. |
| Genomics/computational biology methods journal | Good-to-strong | The framework is reproducible and benchmarked; third-party benchmark contracts and multi-species public-data evidence improve competitiveness, while official third-party numeric closure remains the next upgrade. |
| Top general methods venue | Stretch / presubmission-inquiry ready | The idea is interesting and now has open-set/selective annotation evidence, but strict raw leave-species performance, incomplete scPlantLLM/scPlantAnnotate numeric closure and lack of wet-lab validation would trigger major review pressure. |

Practical submission advice: submit the current package as a **plant-general single-cell annotation framework and resource**, not as a universal high-accuracy zero-shot annotator for every plant species.

## Evidence Strengths

| Strength | Evidence | Why it matters |
| --- | --- | --- |
| General plant scope | `SUBMISSION_INDEX_v9.md`; `release_metadata/plant_cellfm_v9_model_card.md` | The current system is no longer Snow Lotus-only. It is framed as Plant-CellFM with Snow Lotus as one target-species entry point. |
| Audited public corpus | `release_metadata/v9_data_card.md`; benchmark manifest metadata | 56 manifest rows, 29 datasets, 20 normalized species labels and 21 raw species strings before alias canonicalization are recorded. |
| Frozen checkpoint and checksum | GitHub release asset; `release_metadata/plant_cellfm_v9_model_card.md` | The checkpoint is externally addressable and SHA256-pinned. |
| Cross-group benchmark | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` | v9 is compared with the frozen v3 baseline on the same shared-gene benchmark. |
| Species-holdout diagnosis | `release_metadata/species_holdout_failure_audit_v9.md` | The strict leave-species score is decomposed into open-set label absence, known-label errors and per-species revision targets. |
| Species ontology audit | `release_metadata/species_ontology_coverage_audit_v9.md`; `release_metadata/species_ontology_label_benchmark_v9.md`; `release_metadata/plant_cell_state_ontology_mapping_v9.tsv` | The label-harmonization layer maps 106 fine labels, separates actionable ontology coverage from unknown/unannotated cells and adds an embedding-based ontology-label species benchmark. |
| Open-set calibration | `release_metadata/open_set_calibration_v9.md`; `release_metadata/api_confidence_calibration_curve_v9.tsv` | The API head reaches 96.64%/92.81% selective accuracy at top-30/top-40 confidence acceptance, giving a concrete auto-annotate/review workflow. |
| Traditional external comparator | `release_metadata/external_benchmark_panel_v9.md` | Seurat label transfer is completed on the frozen v9 subset; this gives a recognisable non-Plant-CellFM baseline. |
| Third-party benchmark contract | `release_metadata/third_party_benchmark_contract_v10.md` | scPlantLLM/scPlantAnnotate now have official-source input packages, runner commands, missing artifacts and metric-closure rules rather than vague missing-status notes. |
| Biological cases | `release_metadata/plant_biology_case_study_v9.md`; `release_metadata/arabidopsis_root_literature_anchor_v9.md`; `release_metadata/arabidopsis_root_case_figure_v9.md`; `release_metadata/multispecies_scplantdb_case_v10.md` | Arabidopsis root plus multi-species scPlantDB demonstrate adapter resolution, 260 Arabidopsis marker candidates, 31,503 multi-species cells and 96 additional marker-candidate records. |
| Live service and recovery | `release_metadata/api_runtime_smoke_v9.md`; `release_metadata/watchdog_recovery_status_v9.md` | The model is deployable as a CUDA service with recorded smoke and watchdog recovery evidence. |

## Reviewer-Risk Matrix

| Reviewer concern | Severity | Current answer | Residual risk |
| --- | --- | --- | --- |
| Strict cross-species accuracy is modest | High | Report all-cell open-set accuracy, coverage and known-label conditional metrics separately; include the failure audit, ontology audit, ontology-label benchmark and open-set calibration. | Reviewers may still request stronger species-held-out raw results or broader independent species. |
| scPlantLLM/scPlantAnnotate are not numerically closed | High | Use the third-party benchmark contract and do not claim superiority until official metrics are frozen. | Higher-tier journals may require at least one official third-party model run. |
| Biology cases are computational | Medium | Anchor labels to published taxonomy and mark model markers as computational candidates; use the multi-species scPlantDB case to avoid a single-Arabidopsis story. | Wet-lab validation is not present; independent data replication would strengthen the case. |
| Snow Lotus may look like unfinished scope | Medium | State Snow Lotus as target-species adapter route, not completed atlas. | If the title overemphasizes Snow Lotus, reviewers may expect a Snow Lotus single-cell matrix. |
| Historical 5090 and old v0.x files remain in repo | Low | Current submission index, README, model card and package use RTX 4090 and v9. | Reviewers browsing old files may be confused unless they start from `SUBMISSION_INDEX_v9.md`. |

## Quantitative Claim Boundary

Use these as the headline numbers:

| Protocol | v9 all-cell accuracy | Coverage | Known-label accuracy | Known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |

Ontology-label diagnostic on the frozen runtime embeddings: after excluding 1,640 unknown/unannotated cells, the actionable ontology-label leave-species benchmark covers 2,324 / 3,964 cells (coverage 0.7444), with actionable all-cell accuracy 0.1497, known-label accuracy 0.2012 and macro-F1 0.1395. This diagnostic is reported to expose label-hierarchy and transfer failure modes; it does not replace the exact-label headline benchmark above.

Open-set calibration on the deployed API head: exact-label accuracy over all 3,964 runtime-smoke cells is 0.6625, while accepting only the top 30% and top 40% fine-confidence cells gives 0.9664 and 0.9281 selective accuracy. These values support a practical high-confidence auto-annotation workflow, not a replacement for the strict all-cell leave-species headline.

Safe interpretation: Plant-CellFM v9 shows reproducible gains over the frozen v3 baseline and provides a plant-general adapter framework under open-set cross-species evaluation. The species-holdout score should not be presented as high-accuracy universal annotation.

## Recommended Manuscript Spine

1. Plant single-cell annotation lacks a reproducible plant-specific foundation-model and adapter framework across heterogeneous species, tissues and gene identifiers.
2. Plant-CellFM v9 builds a frozen public-plant corpus, shared-gene backbone, hierarchical annotation head and dynamic all-plant adapter contract.
3. The model is benchmarked under leave-dataset, leave-sample and normalized leave-species protocols, with strict all-cell open-set metrics, known-label conditional metrics and a per-species failure audit reported separately.
4. The label ontology audit maps observed fine labels into plant cell-state categories and keeps unknown/unannotated labels outside actionable coverage; the ontology-label benchmark then reruns leave-species nearest-centroid transfer on frozen embeddings.
5. The open-set calibration layer defines how high-confidence cells can be accepted automatically while low-confidence/open-set-like cells are routed to review or adapter calibration.
6. The external panel includes v3, centroid and Seurat baselines, while scPlantLLM/scPlantAnnotate are disclosed through official-source benchmark contracts.
7. The Arabidopsis root and multi-species scPlantDB cases demonstrate species-adapter resolution, root identity annotation, species/tissue organization and marker-candidate mining in biologically interpretable public-data scenarios.
8. The release provides a GitHub branch, release checkpoint, SHA256 records, final Word manuscript, editor package, live CUDA service evidence and watchdog recovery record.

## Next Revision Work That Would Move The Paper Up

| Priority | Work item | Acceptance evidence |
| --- | --- | --- |
| P1 | Complete one official third-party foundation-model comparator run, preferably scPlantLLM if weights/checkout become available. | Contract is ready; remaining evidence is frozen metric JSON, exact environment, input manifest, command log and comparison table. |
| P1 | Strengthen the independent public species/tissue replication case. | Multi-species scPlantDB case is complete; next improvement is literature marker anchoring, figure panel or independent validation. |
| P2 | Improve model-side species transfer under label ontology and open-set calibration. | Coverage audit, embedding-based ontology benchmark and open-set calibration are completed; next step is adapter calibration, ortholog-aware tokenization or independent replication. |
| P2 | Convert the biology cases into a broader figure suite. | Arabidopsis figure package is complete; next improvement is a multi-species figure panel. |
| P3 | Prepare an English manuscript and response-ready reviewer supplement. | English `.docx` or `.tex`, figure panels, supplement table index and reproducibility checklist. |

## Submission-Safe Summary

Plant-CellFM v9 is currently best described as a reproducible plant-general foundation-model and adapter framework for single-cell expression annotation. Its strongest evidence is the complete engineering chain: public corpus, frozen RTX 4090 checkpoint, strict cross-group benchmark, v3/centroid/Seurat comparisons, species-holdout failure audit, ontology coverage audit, ontology-label benchmark, open-set calibration/selective annotation audit, third-party benchmark contracts, figure-ready Arabidopsis root biological case, multi-species scPlantDB public-data case, GitHub release asset, editor package and live CUDA service. The main limitation for top-tier review is not the existence of the system but the remaining need for official external-model metric closure, model-side cross-species raw performance improvement and broader biological validation.
