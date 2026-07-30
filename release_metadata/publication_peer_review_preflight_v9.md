# Plant-CellFM v9 Peer-Review Preflight

Generated: 2026-07-30 Asia/Shanghai

This preflight is a strict reviewer-style audit of the frozen v9 submission package. It is meant to guide the current submission and the next revision cycle, not to inflate the claim beyond the evidence.

## Editorial Position

Current decision if submitted as a computational method/resource paper: **submission-ready with major-revision risk**.

Current best-fit venues:

| Venue tier | Fit | Rationale |
| --- | --- | --- |
| Plant-focused methods/resource journal | Strong | The paper has a plant-specific problem, public corpus, adapter system, reproducible package, running CUDA service and Arabidopsis root case. |
| Genomics/computational biology methods journal | Good | The framework is reproducible and benchmarked, but stronger third-party model comparisons would improve competitiveness. |
| Top general methods venue | Stretch | The idea is interesting, but strict leave-species performance, incomplete scPlantLLM/scPlantAnnotate numeric closure and lack of independent biological validation would trigger major review pressure. |

Practical submission advice: submit the current package as a **plant-general single-cell annotation framework and resource**, not as a universal high-accuracy zero-shot annotator for every plant species.

## Evidence Strengths

| Strength | Evidence | Why it matters |
| --- | --- | --- |
| General plant scope | `SUBMISSION_INDEX_v9.md`; `release_metadata/plant_cellfm_v9_model_card.md` | The current system is no longer Snow Lotus-only. It is framed as Plant-CellFM with Snow Lotus as one target-species entry point. |
| Audited public corpus | `release_metadata/v9_data_card.md`; benchmark manifest metadata | 56 manifest rows, 29 datasets, 20 normalized species labels and 21 raw species strings before alias canonicalization are recorded. |
| Frozen checkpoint and checksum | GitHub release asset; `release_metadata/plant_cellfm_v9_model_card.md` | The checkpoint is externally addressable and SHA256-pinned. |
| Cross-group benchmark | `release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json` | v9 is compared with the frozen v3 baseline on the same shared-gene benchmark. |
| Traditional external comparator | `release_metadata/external_benchmark_panel_v9.md` | Seurat label transfer is completed on the frozen v9 subset; this gives a recognisable non-Plant-CellFM baseline. |
| Biological case | `release_metadata/plant_biology_case_study_v9.md`; `release_metadata/arabidopsis_root_literature_anchor_v9.md`; `release_metadata/arabidopsis_root_case_figure_v9.md` | Arabidopsis root adapter resolution, 13 cell states, 260 marker-candidate rows and a four-panel figure-ready package show biological use beyond raw metrics. |
| Live service and recovery | `release_metadata/api_runtime_smoke_v9.md`; `release_metadata/watchdog_recovery_status_v9.md` | The model is deployable as a CUDA service with recorded smoke and watchdog recovery evidence. |

## Reviewer-Risk Matrix

| Reviewer concern | Severity | Current answer | Residual risk |
| --- | --- | --- | --- |
| Strict cross-species accuracy is modest | High | Report all-cell open-set accuracy, coverage and known-label conditional metrics separately; emphasize improvement over v3, not universal accuracy. | Reviewers may still request stronger species-held-out results or broader independent species. |
| scPlantLLM/scPlantAnnotate are not numerically closed | High | Keep them as input-ready or access-limited audits; do not claim superiority over unavailable tools. | Higher-tier journals may require at least one official third-party model run. |
| Arabidopsis root case is computational | Medium | Anchor labels to published Arabidopsis root atlas terminology and mark model markers as computational candidates. | Wet-lab validation is not present; independent data replication would strengthen the case. |
| Snow Lotus may look like unfinished scope | Medium | State Snow Lotus as target-species adapter route, not completed atlas. | If the title overemphasizes Snow Lotus, reviewers may expect a Snow Lotus single-cell matrix. |
| Historical 5090 and old v0.x files remain in repo | Low | Current submission index, README, model card and package use RTX 4090 and v9. | Reviewers browsing old files may be confused unless they start from `SUBMISSION_INDEX_v9.md`. |

## Quantitative Claim Boundary

Use these as the headline numbers:

| Protocol | v9 all-cell accuracy | Coverage | Known-label accuracy | Known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |

Safe interpretation: Plant-CellFM v9 shows reproducible gains over the frozen v3 baseline and provides a plant-general adapter framework under open-set cross-species evaluation. The species-holdout score should not be presented as high-accuracy universal annotation.

## Recommended Manuscript Spine

1. Plant single-cell annotation lacks a reproducible plant-specific foundation-model and adapter framework across heterogeneous species, tissues and gene identifiers.
2. Plant-CellFM v9 builds a frozen public-plant corpus, shared-gene backbone, hierarchical annotation head and dynamic all-plant adapter contract.
3. The model is benchmarked under leave-dataset, leave-sample and normalized leave-species protocols, with strict all-cell open-set metrics and known-label conditional metrics reported separately.
4. The external panel includes v3, centroid and Seurat baselines, while scPlantLLM/scPlantAnnotate are disclosed at their auditable execution boundary.
5. The Arabidopsis root case demonstrates species-adapter resolution, root identity annotation and marker-candidate mining in a biologically interpretable public-data scenario.
6. The release provides a GitHub branch, release checkpoint, SHA256 records, final Word manuscript, editor package, live CUDA service evidence and watchdog recovery record.

## Next Revision Work That Would Move The Paper Up

| Priority | Work item | Acceptance evidence |
| --- | --- | --- |
| P1 | Complete one official third-party foundation-model comparator run, preferably scPlantLLM if weights/checkout become available. | Frozen metric JSON, exact environment, input manifest, command log and comparison table. |
| P1 | Add an independent public species/tissue replication case outside the current Arabidopsis-heavy evidence. | Separate held-out dataset, marker table and literature-anchored interpretation. |
| P2 | Rebuild species-holdout with clearer label harmonization and class ontology mapping. | Label ontology table, before/after coverage analysis and per-species failure audit. |
| P2 | Convert the Arabidopsis root case into a figure-ready biological result. | Completed in `release_metadata/arabidopsis_root_case_figure_v9.md`; next improvement is independent replication beyond Arabidopsis. |
| P3 | Prepare an English manuscript and response-ready reviewer supplement. | English `.docx` or `.tex`, figure panels, supplement table index and reproducibility checklist. |

## Submission-Safe Summary

Plant-CellFM v9 is currently best described as a reproducible plant-general foundation-model and adapter framework for single-cell expression annotation. Its strongest evidence is the complete engineering chain: public corpus, frozen RTX 4090 checkpoint, strict cross-group benchmark, v3/centroid/Seurat comparisons, figure-ready Arabidopsis root biological case, GitHub release asset, editor package and live CUDA service. The main limitation for top-tier review is not the existence of the system but the remaining need for stronger independent external-model closure and broader biological replication.
