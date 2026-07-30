# Plant-CellFM Frozen v9 Publication Readiness Audit

This file records the evidence behind the frozen v9 candidate. It is an engineering and submission audit, not a claim that peer review has been completed.

## Implemented

1. **General-plant model scope.** The service and adapter registry treat Snow Lotus as one species within a plant-general model. Unknown named species receive a runtime adapter record, while exact gene IDs and optional ortholog maps are resolved through the same inference contract.
2. **Public corpus construction.** The v9 corpus contains 56 validated manifest rows from 29 datasets, 20 normalized plant species labels and 21 raw species strings before alias canonicalization, with 13.78 million cells in the built corpus. Manifest paths, duplicate handling, source metadata and checksums are retained.
3. **GPU training.** The v9 LoRA candidate was trained on the RTX 4090 with a resolved YAML configuration, epoch checkpoints, progress logs, preprocessing statistics and a completion marker.
4. **Fair baseline comparison.** v9 and v3 were evaluated on the same v9 shared-gene benchmark under leave-dataset-out, leave-sample-out and leave-species-out protocols.
5. **Inference service.** The service exposes health, metadata, capability, adapter and annotation routes. A live health check reports `model_scope=plant_general`, 24 catalog adapters, dynamic all-plant resolution and `device=cuda`.
6. **Reproducible release.** The v9 package contains the checkpoint, configuration, manifest, benchmark subset, benchmark JSON, comparison report, training history, scripts and SHA256 manifest. The server-side checksum verification passed.
7. **Repository hygiene.** The public repository was scanned for tracked private keys, GitHub tokens, raw server credentials and key-like files before changing visibility to public.
8. **External benchmark panel.** The addendum panel reports the frozen v3 comparison, Seurat label transfer on the frozen v9 subset, a classical SRP169576 sample-holdout baseline, and audited scPlantLLM/scPlantAnnotate execution status.
9. **Biological case study.** The Arabidopsis root case study reports 260 marker-candidate rows across 13 cell states, including 10 root cell-identity labels, and links adapter resolution to marker discovery.
10. **Integrated stable manuscript.** The repository now contains `manuscript/Plant_CellFM_v9_完整主文_稳健方法版_v1.md` and `.docx`, plus `release_metadata/v9_submission_stability_audit.md`, to keep cross-species claims, comparator status, the Arabidopsis biology case and the Snow Lotus scope in one reviewer-facing narrative.
11. **Submission index.** `SUBMISSION_INDEX_v9.md` is the current entry point and separates v9 submission claims from historical Snow Lotus-centered drafts and early hardware-planning files.
12. **Live runtime smoke test.** `release_metadata/api_runtime_smoke_v9.md` records a successful `POST /annotate` call on the deployed service, resolving the Arabidopsis adapter and writing predictions plus 3964 x 256 embeddings.
13. **Watchdog recovery.** `release_metadata/watchdog_recovery_status_v9.md` records a controlled SIGTERM recovery test in which the tmux watchdog restarted the Plant-CellFM service within 30 seconds.
14. **Editor issue closure.** `release_metadata/v9_editor_issue_closure.md` records the current safe resolution of the main editor-facing concerns: strict cross-species wording, third-party comparator boundaries, Arabidopsis case scope, Snow Lotus scope, RTX 4090 hardware statement and server/GitHub reproducibility.
15. **Submission manuscript refresh.** `manuscript/Plant_CellFM_v9_final_submission_zh_v1.md` and `.docx` provide an ASCII-path copy of the integrated Chinese manuscript, now including live API runtime evidence, watchdog recovery evidence and the updated stability matrix.
16. **Arabidopsis literature anchor.** `release_metadata/arabidopsis_root_literature_anchor_v9.md` aligns the root case labels with established Arabidopsis root atlas categories and canonical marker examples while preserving the claim boundary that model markers are computational candidates.
17. **Final editor package recipe.** `scripts/package_v9_editor_submission.py` and `release_metadata/final_editor_submission_package_recipe_v9.md` generate a compact editor-facing zip with the final Word manuscript, model card, benchmark evidence, server evidence, Arabidopsis case evidence and model asset pointer.
18. **Peer-review preflight.** `release_metadata/publication_peer_review_preflight_v9.md` records a strict reviewer-style audit of venue fit, current strengths, claim boundaries and remaining hard evidence needed for higher-tier revision.
19. **Figure-ready biology case.** `release_metadata/arabidopsis_root_case_figure_v9.md` and `figures/plant_cellfm_v9_arabidopsis_root_case/` provide a four-panel Arabidopsis root adapter and marker-candidate figure with SVG/PDF/PNG/TIFF exports and source data.
20. **Species-holdout failure audit.** `release_metadata/species_holdout_failure_audit_v9.md` decomposes the normalized leave-species-out result into per-species coverage, open-set label absence and known-label transfer errors.
21. **Publication target readiness matrix.** `release_metadata/top_journal_readiness_matrix.md` and `docs/top_journal_strategy.md` replace earlier SnowLotus-centered top-journal planning with the current Plant-CellFM v9 / RTX 4090 submission tiering, claim boundaries and higher-tier upgrade requirements.
22. **Species ontology coverage audit.** `release_metadata/species_ontology_coverage_audit_v9.md` and `release_metadata/plant_cell_state_ontology_mapping_v9.tsv` align the server-exported benchmark labels to the frozen 3,964 leave-species test cells, map 106 fine labels to plant cell-state categories and separate actionable ontology coverage from unknown or unannotated labels.
23. **Ontology-label species-holdout benchmark.** `release_metadata/species_ontology_label_benchmark_v9.md` reruns nearest-centroid leave-species evaluation on the frozen 3,964 x 256 runtime-smoke embeddings after ontology mapping, with exact-label recomputation matching the frozen benchmark and ontology-actionable metrics reported separately.

## Frozen Results

| Protocol | v9 all-cell accuracy | v9 coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |

The internal held-out test reports fine accuracy 0.8113, coarse accuracy 0.8298 and fine macro-F1 0.3833. The known-label columns evaluate only cells whose reference labels occur in the training fold. The all-cell column counts an unseen reference label as an error, so the leave-species-out result is the stricter open-set estimate. The species-holdout protocol now normalizes species aliases such as `Arabidopsis_thaliana` and `Arabidopsis thaliana` before splitting, reducing the selected benchmark from 9 raw species labels to 8 normalized groups. The cross-group results above are the primary generalization evidence, and the 23.54% all-cell normalized species-holdout accuracy rather than 42.10% conditional accuracy should be used as the headline species number.

`release_metadata/species_holdout_failure_audit_v9.md` further shows that 1,748 of 3,964 held-out species cells are open-set cells whose reference labels do not occur in the training fold, accounting for 57.67% of the all-cell error mass. Catharanthus roseus is the clearest high-coverage transfer failure, while Gossypium hirsutum is unassessable without label-ontology mapping under the current split.

`release_metadata/species_ontology_coverage_audit_v9.md` adds the label-harmonization view without changing the frozen metrics. It reconstructs count-aligned exact-label coverage as 2,246 / 3,964 cells, within 30 cells of the frozen JSON, and reports 1,794 / 3,964 actionable ontology-covered cells after excluding 1,384 unknown or unannotated cells. This is the current evidence for why the next species-holdout revision should use an explicit plant cell-state ontology rather than relying only on literal fine-label strings.

`release_metadata/species_ontology_label_benchmark_v9.md` converts that audit into an embedding-based protocol. It aligns all 3,964 runtime-smoke predictions to H5AD obs labels with zero missing IDs. Exact-label recomputation gives 55.90% coverage and 23.64% all-cell accuracy, matching the frozen 55.90% and 23.54% benchmark closely. The ontology-actionable protocol excludes 1,640 unknown or unannotated cells, keeps 2,324 actionable cells, increases ontology-label coverage to 74.44%, and reports 14.97% actionable all-cell accuracy, 20.12% known-label accuracy and 0.1395 known-label macro-F1. This is a stricter diagnostic of remaining cross-species representation error after label harmonization.

## Publication Positioning

The strongest current manuscript framing is a computational method/resource paper: a plant-specific foundation model, an all-plant adapter layer, a public corpus construction protocol, a reproducible cross-group benchmark, a completed Seurat comparator and a concrete Arabidopsis root marker case. The paper should make the leave-dataset, leave-sample and normalized leave-species results central, rather than presenting the internal held-out accuracy as universal plant accuracy.

## External Comparator And Biology Addendum

| Addendum item | Status | Key evidence |
| --- | --- | --- |
| External benchmark panel | completed | `release_metadata/external_benchmark_panel_v9.md` |
| Seurat label transfer | completed | fine accuracy 0.2207, macro-F1 0.0603 on 512 frozen-subset test cells |
| scPlantLLM interface | input ready, metric missing | 20,000 cells, 24,392 retained genes, gene-vocabulary overlap 1.0 |
| scPlantAnnotate interface | web/API authentication required | server reachable, anonymous scriptable benchmark unavailable |
| Arabidopsis root biology case | completed | 260 marker-candidate rows, 13 states, 10 root identity states |
| Arabidopsis root figure package | completed | four-panel SVG/PDF/PNG/TIFF figure with source data |
| Species-holdout failure audit | completed | 8 species groups, open-set error decomposition and per-species revision priorities |
| Species ontology coverage audit | completed | 106-label mapping table, 45.26% actionable ontology coverage and 34.91% unknown/unannotated diagnosis |
| Ontology-label species benchmark | completed | 3,964 aligned embeddings, 74.44% actionable coverage and 14.97% actionable all-cell accuracy |

## Journal Fit

- **First-choice stretch target: Nature Methods.** The work is within the journal's computational and single-cell methods scope, but the current evidence still needs a stronger comparison against established annotation and foundation-model tools plus a convincing biological application.
- **Strong methods target: Genome Biology.** The plant single-cell corpus, cross-species evaluation, completed Seurat comparator, open implementation and Arabidopsis root marker case fit the journal's genomics and computational-method readership. A completed scPlantLLM/scPlantAnnotate run would further strengthen the submission.
- **Plant-focused target: Plant Communications.** The model and public plant resource are directly within the journal's plant genomics, cellular biology and technical-resource scope. This is now the most stable fit when the manuscript emphasizes plant utility, adapter resolution, marker discovery and an accessible resource rather than broad AI novelty.
- **Broad biology target: Communications Biology.** The current work can fit as an innovative computational method if the paper demonstrates a concrete plant-biology use case and the conclusions are supported by strong evidence.
- **Stretch AI target: Nature Machine Intelligence or Nature Computational Science.** These venues require a larger methodological advance and broader significance than the current frozen evidence demonstrates; they are appropriate only after a substantially stronger algorithmic contribution and independent validation.

## Final Submission Package

The reviewer-facing package should contain the frozen v9 checkpoint, `SUBMISSION_INDEX_v9.md`, model card, data card, manifest and provenance audit, benchmark subset and JSON results, species-holdout failure audit, species ontology coverage audit, ontology-label species benchmark, training configuration and history, service instructions, source repository, the integrated stable manuscript and the stability-audit matrix. Keep the training scope tied to the audited v9 corpus and keep cross-species accuracy tied to the reported open-set benchmark.
