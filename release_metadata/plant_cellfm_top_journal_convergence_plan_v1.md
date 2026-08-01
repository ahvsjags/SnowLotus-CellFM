# Plant-CellFM Top-Journal Convergence Plan

## Objective

Build a submission package that can be reviewed as a rigorous plant single-cell methods paper: a reader should be able to identify the methodological contribution in the first figure, trace every headline number to a locked protocol and source table, distinguish transfer from target-labelled adaptation, and reproduce the released computational evidence without reconstructing hidden decisions.

This document is an internal delivery gate. It does not assert editorial acceptance or turn a technical audit into a journal-quality score.

## Central Paper Claim

Plant-CellFM is a protocol-aware framework for plant single-cell annotation that unifies explicit gene and orthology contracts, open-set cross-species evaluation, target-context adaptation and annotation outputs under one auditable release record.

The paper must not claim universal high-accuracy annotation, a completed Snow Lotus atlas, third-party superiority, independent external accuracy, or experimental validation unless new evidence is added.

## Main-Figure Storyline

| Figure | Reader question | Evidence delivered | Required visual form | Current gate |
| --- | --- | --- | --- | --- |
| Fig. 1 | What is the method and what enters it? | Frozen corpus, strict panel, gene and orthology contract, 24 registered adapters and output record. | Schematic-led composite with data anchors. | Complete |
| Fig. 2 | Does cross-species transfer survive the open set? | Nested 8-species, 3,964-cell protocol with all-cell, coverage and conditional denominators. | Quantitative grid with denominator decomposition. | Complete |
| Fig. 3 | What changes when target labels become available? | Ten-draw support/query-separated dose response from 8 to 64 cells. | Response curve plus per-species heterogeneity. | Complete |
| Fig. 4 | Is a blind biological output inspectable? | 6,566-cell label-free root inference and prespecified marker anchors. | Embedding plus marker-led evidence plate. | Complete, plausibility only |
| Fig. 5 | What does a genuinely unseen crop atlas reveal before and after adaptation? | Species-absent GSE297576 frozen screen, 10-species orthology contract, predeclared comparable denominator, four-library split, sealed OUGHW test and adapter checksum. | Evidence-tier ladder, paired topology, matched recovery, all-state F1 and feature-transfer audit. | Complete; frozen screen and same-atlas adaptation separated |

## Extended Data and Supplementary Evidence

| Asset | Review risk resolved | Traceable assets | Current gate |
| --- | --- | --- | --- |
| ED1-ED6, Tables S1-S20 | Label integrity, nested selection, internal checkpoints, marker protocol and GSE270140 adaptation. | Versioned source tables and audit records. | Complete |
| ED7, Table S21 | Retains the negative source-adapter transfer result rather than selectively presenting only gains. | Declared k=9 source-only protocol. | Complete |
| ED8, Tables S22-S24 | Official scPlantLLM checkpoint under the same prepared GSE270342 object, mapping and locked test. | Clean checkpoint loading, partial- and full-adapter checksums and exact prediction replay. | Complete as matched full-backbone reference |
| Fig. 5, Tables S25-S27 | A source-pinned species-absent external screen and library-held-out Sorghum adaptation. | Atlas conversion, ontology, frozen prediction, orthology, split and adapter audits. | Complete; not an external ranking or a zero-shot recovery claim |
| Visual source bundle | Enables panel-level data review and editorial production. | SVG, PDF, PNG, 600-dpi TIFF and tidy TSV per panel. | Complete |

## Non-Negotiable Evidence Rules

1. Keep strict leave-species all-cell accuracy at 39.96% as the primary nested result; do not replace it with the 42.36% global context-sensitivity analysis.
2. Keep support-labelled, GSE270140 and GSE270342 results labelled as target-supervised adaptation; no such result may be described as zero-shot or independent external validation.
3. Keep the GSE152766 root analysis labelled as a marker-coherence case because it has no expert identity labels.
4. Describe scPlantLLM as an official matched frozen, partial-adaptation and full-backbone adaptation reference. The full run trains every backbone parameter and a new head, but remains a same-study adaptation reference rather than independent, strict or compute-matched rank.
5. Retain barcode-overlap exclusion, split locks, SHA256 links, selection criteria and replay records in the source package.
6. Keep the GSE297576 frozen result (14.56% accuracy, 0.1083 macro-F1 across 14,909 comparable cells) distinct from the target-species LoRA result (76.02% raw 27-state accuracy and 0.7535 macro-F1 on the sealed OUGHW library). The latter is supervised within an author-labelled atlas and is not a zero-shot recovery claim.

## Submission-Scale Completion Gates

| Gate | Evidence threshold | Status |
| --- | --- | --- |
| Narrative | One central claim, five connected main figures and scope boundaries visible in captions. | Complete in v7 source manuscript |
| Data integrity | Frozen profile distinct from test panel; target labels isolated in strict protocol; overlap exclusion audited. | Complete |
| Method reproducibility | Deterministic preparation, locked IDs, release checksums and executable figure/audit scripts. | Complete |
| Visual production | Editable vector exports, 600-dpi raster exports, panel source TSVs and technical audit with zero export failures. | Complete |
| Comparator integrity | Matched official scPlantLLM frozen, partial-adaptation and full-backbone reference, with replayed held-out predictions. | Complete at same-study full-backbone scope |
| Highest-tier evidence | Compute-budget-matched third-party benchmark, runnable scPlantAnnotate result, and independently labelled multi-species external cohort. | Open, required for a stronger revision rather than claimed complete |

## Execution Order

1. Freeze v7 manuscript, figure captions, source tables and evidence ledger to the same protocol names and values.
2. Run the v6/v7 figure audits, full-adapter replay audit and complete automated test suite from a clean checkout.
3. Publish the exact source revision and release manifest; attach only checksum-addressed model artifacts.
4. For the next evidence tier, add a shared-ontology multi-study external cohort and close compute-budget-matched third-party baselines before extending architectural claims.

## Delivery Definition

The current v7 package is a coherent, evidence-bounded computational methods submission: its visual suite, source-data chain, protocol ledger, official same-study reference, species-absent external screen and sealed-library adaptation case are ready for technical review. A stronger high-tier revision still requires the open comparator and independent external-validation gates above; those are explicitly retained rather than concealed by presentation.
