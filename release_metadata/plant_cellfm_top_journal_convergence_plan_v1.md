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
| Fig. 5 | Can adaptation handle a difficult crop input contract? | Wheat barcode exclusion, author orthogroups, locked 13-class test and adapter checksum. | Provenance-led asymmetric composite. | Complete, same-study adaptation |

## Extended Data and Supplementary Evidence

| Asset | Review risk resolved | Traceable assets | Current gate |
| --- | --- | --- | --- |
| ED1-ED6, Tables S1-S20 | Label integrity, nested selection, internal checkpoints, marker protocol and GSE270140 adaptation. | Versioned source tables and audit records. | Complete |
| ED7, Table S21 | Retains the negative source-adapter transfer result rather than selectively presenting only gains. | Declared k=9 source-only protocol. | Complete |
| ED8, Tables S22-S23 | Official scPlantLLM checkpoint under the same prepared GSE270342 object, mapping and locked test. | Clean checkpoint loading, partial-adapter checksum and prediction replay. | Complete as matched partial reference |
| Visual source bundle | Enables panel-level data review and editorial production. | SVG, PDF, PNG, 600-dpi TIFF and tidy TSV per panel. | Complete |

## Non-Negotiable Evidence Rules

1. Keep strict leave-species all-cell accuracy at 39.96% as the primary nested result; do not replace it with the 42.36% global context-sensitivity analysis.
2. Keep support-labelled, GSE270140 and GSE270342 results labelled as target-supervised adaptation; no such result may be described as zero-shot or independent external validation.
3. Keep the GSE152766 root analysis labelled as a marker-coherence case because it has no expert identity labels.
4. Describe scPlantLLM as an official matched frozen and partial-adaptation reference. The first five blocks remain frozen, so it is not full-backbone fine-tuning or a compute-matched rank.
5. Retain barcode-overlap exclusion, split locks, SHA256 links, selection criteria and replay records in the source package.

## Submission-Scale Completion Gates

| Gate | Evidence threshold | Status |
| --- | --- | --- |
| Narrative | One central claim, five connected main figures and scope boundaries visible in captions. | Complete in v6 source manuscript |
| Data integrity | Frozen profile distinct from test panel; target labels isolated in strict protocol; overlap exclusion audited. | Complete |
| Method reproducibility | Deterministic preparation, locked IDs, release checksums and executable figure/audit scripts. | Complete |
| Visual production | Editable vector exports, 600-dpi raster exports, panel source TSVs and technical audit with zero export failures. | Complete |
| Comparator integrity | Matched official scPlantLLM frozen and partial-adaptation reference, with replayed held-out predictions. | Complete at partial-adaptation scope |
| Highest-tier evidence | Full-backbone or compute-budget-matched third-party benchmark, runnable scPlantAnnotate result, and independently labelled multi-species external cohort. | Open, required for a stronger revision rather than claimed complete |

## Execution Order

1. Freeze v6 manuscript, figure captions, source tables and evidence ledger to the same protocol names and values.
2. Run the figure suite audit, partial-adapter replay audit and complete automated test suite from a clean checkout.
3. Publish the exact source revision and release manifest; attach only checksum-addressed model artifacts.
4. For the next evidence tier, add a shared-ontology multi-study external cohort and close full-backbone or compute-budget-matched third-party baselines before extending architectural claims.

## Delivery Definition

The current v6 package is a coherent, evidence-bounded computational methods submission: its visual suite, source-data chain, protocol ledger, official third-party reference and adaptation cases are ready for technical review. A stronger high-tier revision requires the open comparator and independent external-validation gates above; those are explicitly retained rather than concealed by presentation.
