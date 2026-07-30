# Plant-CellFM Frozen v9 Publication Readiness Audit

This file records the evidence behind the frozen v9 candidate. It is an engineering and submission audit, not a claim that peer review has been completed.

## Implemented

1. **General-plant model scope.** The service and adapter registry treat Snow Lotus as one species within a plant-general model. Unknown named species receive a runtime adapter record, while exact gene IDs and optional ortholog maps are resolved through the same inference contract.
2. **Public corpus construction.** The v9 corpus contains 56 validated manifest rows from 29 datasets and 21 species, with 13.78 million cells in the built corpus. Manifest paths, duplicate handling, source metadata and checksums are retained.
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

## Frozen Results

| Protocol | v9 all-cell accuracy | v9 coverage | v9 known-label accuracy | v9 known-label macro-F1 | v3 all-cell accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Leave-dataset-out | 0.4490 | 0.8017 | 0.5601 | 0.3485 | 0.2021 |
| Leave-sample-out | 0.6200 | 0.9871 | 0.6281 | 0.4902 | 0.4155 |
| Leave-species-out, species labels normalized | 0.2354 | 0.5590 | 0.4210 | 0.1918 | 0.1912 |

The internal held-out test reports fine accuracy 0.8113, coarse accuracy 0.8298 and fine macro-F1 0.3833. The known-label columns evaluate only cells whose reference labels occur in the training fold. The all-cell column counts an unseen reference label as an error, so the leave-species-out result is the stricter open-set estimate. The species-holdout protocol now normalizes species aliases such as `Arabidopsis_thaliana` and `Arabidopsis thaliana` before splitting, reducing the selected benchmark from 9 raw species labels to 8 normalized groups. The cross-group results above are the primary generalization evidence, and the 23.54% all-cell normalized species-holdout accuracy rather than 42.10% conditional accuracy should be used as the headline species number.

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

## Journal Fit

- **First-choice stretch target: Nature Methods.** The work is within the journal's computational and single-cell methods scope, but the current evidence still needs a stronger comparison against established annotation and foundation-model tools plus a convincing biological application.
- **Strong methods target: Genome Biology.** The plant single-cell corpus, cross-species evaluation, completed Seurat comparator, open implementation and Arabidopsis root marker case fit the journal's genomics and computational-method readership. A completed scPlantLLM/scPlantAnnotate run would further strengthen the submission.
- **Plant-focused target: Plant Communications.** The model and public plant resource are directly within the journal's plant genomics, cellular biology and technical-resource scope. This is now the most stable fit when the manuscript emphasizes plant utility, adapter resolution, marker discovery and an accessible resource rather than broad AI novelty.
- **Broad biology target: Communications Biology.** The current work can fit as an innovative computational method if the paper demonstrates a concrete plant-biology use case and the conclusions are supported by strong evidence.
- **Stretch AI target: Nature Machine Intelligence or Nature Computational Science.** These venues require a larger methodological advance and broader significance than the current frozen evidence demonstrates; they are appropriate only after a substantially stronger algorithmic contribution and independent validation.

## Final Submission Package

The reviewer-facing package should contain the frozen v9 checkpoint, `SUBMISSION_INDEX_v9.md`, model card, data card, manifest and provenance audit, benchmark subset and JSON results, training configuration and history, service instructions, source repository, the integrated stable manuscript and the stability-audit matrix. Keep the training scope tied to the audited v9 corpus and keep cross-species accuracy tied to the reported open-set benchmark.
