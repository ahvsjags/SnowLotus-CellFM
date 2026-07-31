# Plant-CellFM: protocol-aware cross-species annotation and context adaptation for plant single-cell atlases

## Abstract

Plant single-cell and single-nucleus atlases are expanding across model plants, crops and non-model species, yet annotation transfer remains confounded by gene-identifier differences, open cell-state vocabularies and mixed evaluation protocols. We present Plant-CellFM, a plant expression modelling framework that treats annotation as an auditable evidence chain rather than a single classifier score. The frozen corpus profile contains 272,732 cells, 209,405 genes, five profiled species, nine public datasets, 31 samples and 34 raw labels; the separate strict evaluation panel contains 3,964 aligned cells from eight held-out species. Plant-CellFM combines a 256-dimensional four-layer encoder, an explicit gene-identifier and orthology contract, LoRA adaptation interfaces, hierarchical annotation outputs, ranked marker candidates and a runtime annotation head. In the primary nested leave-species protocol, target labels are excluded from fitting, rule selection and calibration. The result is 39.96% all-cell accuracy, 55.90% source-label coverage, 71.48% accuracy and 0.2817 macro-F1 on the covered-label subset. Labelled target-species adaptation gives a reproducible dose response from 59.21% to 75.89% mean query all-cell accuracy as support increases from 8 to 64 cells per species across ten disjoint support-query draws. We further provide a label-free external root execution audit, a marker-candidate resource, and an author-labelled secondary-root adaptation case. In GSE270140/GSM8335426, a LoRA-mode context adapter achieves 83.97% fine accuracy and 84.47% macro-F1 on 2,352 locked test cells, while a pre-registered three-state vascular mapping increases semantic accuracy from 2.02% for the frozen base checkpoint to 90.93% after adaptation. This latter result is explicitly a one-sample supervised adaptation, not a zero-shot or independent validation result. Plant-CellFM therefore provides a reproducible route for separating strict transfer, target-context adaptation and deployment annotation in plant atlas analysis.

## Introduction

Plant atlases now span organs, genotypes, developmental stages and phylogenetic lineages at cell resolution. Their value depends on whether cell identities can be transferred and compared without silently changing the meaning of a label. In practice, species differ in gene identifiers and orthology, organs differ in state composition, and target datasets often contain labels that are absent from a source vocabulary. A model can also be scored under fundamentally different information boundaries: strict transfer excludes target labels, few-shot adaptation uses a labelled support set, and a deployed head may already contain a fixed output vocabulary. These are distinct questions and should not be compressed into a single accuracy statement.

Plant-CellFM addresses this problem with a protocol-aware design. The framework records the provenance of input matrices, aligns genes through exact identifiers or an explicit orthology map, resolves species adapters, emits hierarchical annotations and marker candidates, and attaches the evaluation protocol to the reported result. The scope is plant-general: *Saussurea involucrata* is a future target-species use case rather than a model boundary. The current package does not claim a completed Snow Lotus single-cell atlas because no reusable Snow Lotus single-cell matrix is included.

Here we establish a submission-scale evidence package with a frozen corpus profile, an 8-species nested strict-transfer benchmark, a label-integrity companion analysis, repeat-sampled target-species adaptation, matched internal checkpoint comparisons, a label-free external root execution case, a literature-anchored root candidate resource and a fully audited secondary-root context adapter. Each quantitative result is paired with source data, a declared denominator and a record of what information entered fitting or selection.

## Results

### A frozen corpus profile and explicit input contract separate scope from performance

The frozen Plant-CellFM profile comprises 272,732 cells and 209,405 genes from five profiled species, nine public datasets and 31 samples (Fig. 1). The profile is deliberately distinct from the strict evaluation panel, which contains 3,964 aligned cells drawn from eight held-out species. This separation prevents historical catalogues, evaluation-only species or registered adapter names from being misrepresented as cells in the frozen corpus.

The encoder uses four layers and a 256-dimensional cell representation. Inputs first pass through an exact gene-identifier contract; when genome versions or species require it, an orthology map is supplied as a visible artifact. The model exposes cell embeddings, hierarchical labels, ranked marker candidates and adapter-resolution metadata. This interface is a reusable method component, not a claim that every named plant has already received empirical validation.

### Nested leave-species transfer retains the open-set denominator

The primary cross-species experiment is the v17 nested metadata gate. For every outer held-out species, the decoding rule is selected only with inner leave-species evaluation on source species. Target labels do not enter encoder fitting, rule selection, threshold calibration or post-hoc error correction (Fig. 2 and Extended Data Fig. 2). The resulting all-cell accuracy is 39.96% over all 3,964 test cells. Source-label coverage is 55.90%; the accuracy and macro-F1 restricted to the covered-label subset are 71.48% and 0.2817, respectively.

These quantities describe complementary, rather than competing, aspects of transfer. All-cell accuracy counts cells carrying target labels absent from the source label vocabulary as errors. The conditional measures describe recognition among labels that the source could in principle express. Both are shown because presenting only conditional accuracy would remove the central open-set challenge from the denominator.

The v18 label-integrity companion analysis evaluates a second, pre-specified question. Labels beginning `unknown`, `unknow` or `unannotated` are retained as audit records but do not enter identity fitting or identity scoring. This yields 2,324 explicit-identity cells and 1,640 audit-only labels. The companion analysis is not a replacement for v17; it makes the influence of non-identity public labels inspectable rather than allowing them to create a misleadingly clean or misleadingly poor score.

### Target-species support produces a repeatable adaptation response

Strict zero-shot transfer asks what can be predicted without target labels. Atlas construction frequently offers a different route: a small set of target cells can be labelled before the remaining cells are annotated. We therefore sampled 8, 16, 32 or 64 labelled support cells per target species, excluded them from query scoring, and repeated each support budget across ten independent draws (Fig. 3).

Mean query all-cell accuracy increased monotonically from 59.21% at 8 support cells to 67.34%, 72.30% and 75.89% at 16, 32 and 64 support cells. Query macro-F1 increased from 0.2195 to 0.4619. The panel retains the raw draws and species-by-budget values, making both variability and species heterogeneity visible. These are labelled adaptation results and are never substituted for the strict v17 zero-shot score.

### Matched internal comparisons quantify checkpoint gains without imposing an invalid external rank

Frozen v3 and Plant-CellFM v9 checkpoints are compared only on shared datasets, splits, gene contracts and label coverage. All-cell accuracy rises from 20.21% to 44.90% in leave-dataset evaluation and from 41.55% to 62.00% in leave-sample evaluation. In the recorded label-normalized leave-species comparison, it rises from 19.12% to 23.54% (Extended Data Fig. 3). These are matched internal checkpoint results, not a ranking against unrelated external tools.

Seurat label transfer and a cosine-centroid baseline have separate recorded executions. The official scPlantLLM checkpoint has been loaded on CUDA with zero missing or unexpected state keys and evaluated through a frozen-encoder centroid probe on its own processed chunks. That result verifies executable official software, but it does not share the v17 raw input, ontology, split or open-set denominator. scPlantAnnotate requires authenticated execution or an official prediction export. The manuscript therefore records these routes as benchmark-closure assets rather than constructing an attractive but incomparable league table.

### External root execution and literature-fixed markers provide a biological audit layer

We applied the frozen root checkpoint to the label-free *Arabidopsis* root matrix GSE152766/GSM4626007. The input contains 6,566 cells and 25,171 TAIR10 gene identifiers, is not listed in the frozen v4 profile, and contains no expert cell-identity field. The execution is consequently a blind inference audit, not an external accuracy experiment. The model returns 13 predicted states, confidence values and 256-dimensional embeddings (Fig. 4 and Extended Data Fig. 5).

Before analysing the matrix, we fixed six canonical root marker-identity expectations from the primary literature. Five markers, `COBL9`, `GL2`, `CASP1`, `APL` and `MYB46`, have the highest mean expression and detection rate in their expected predicted group; `WER` remains a positive but non-top signal. The phloem prediction group has four cells and that denominator is retained in the source data. Separately, the root candidate resource covers ten identities with top-20 candidates per identity, for 200 rows. Three of six literature-fixed anchors are recovered in their matching top-20 programs. These analyses support biological coherence and experimental prioritization, not external accuracy or wet-lab validation.

### A secondary-root context adapter resolves author-defined states on locked cells

GSE270140/GSM8335426 is a public *Arabidopsis* secondary-root study that combines single-cell sequencing with lineage tracing. We used its author object only for a labelled, within-sample adaptation study. The preparation chain preserves raw feature names, cell identifiers and author annotations while canonicalizing TAIR identifiers. The resulting matrix contains 11,760 cells and 14 author-defined states.

The frozen SRP169576 root checkpoint initialized a LoRA-mode context adapter. Unique cell identifiers were assigned to a fixed seed 80/10/20 split comprising 8,232 training cells, 1,176 validation cells and 2,352 locked test cells. The best checkpoint was selected at epoch 7 using validation fine macro-F1 only. The primary held-out evaluator reports 83.97% fine accuracy and 84.47% macro-F1; a separate full-precision recheck reports 84.18% and 84.64% (Extended Data Fig. 6).

We also froze, before inference, a semantic map from compatible author labels to Phloem, Xylem and Root stele. On the same 1,885 compatible held-out cells, semantic accuracy increases from 2.02% for the frozen base checkpoint to 90.93% after adaptation, with macro-F1 0.9159. The figure retains the split, validation trajectory, all 14 classes, rare-state F1 values, source data and 3,000 fixed-seed bootstrap intervals. Because all adaptation labels originate from the same author-labelled sample, this result is a context-specific supervised adaptation. It is not used as evidence of zero-shot transfer, leave-species generalization, independent external validation or superiority over a third-party model.

## Methods

### Data contracts, corpus profile and label handling

The corpus profile is generated directly from the frozen H5AD structure and records cells, genes, species, datasets, samples, tissues and raw labels. Strict evaluation records are frozen separately. Exact gene identifiers are aligned to the checkpoint vocabulary; where direct identifiers are insufficient, orthology mappings are supplied as explicit input artifacts. The v18 identity companion rule is fixed before scoring and treats `unknown`, `unknow` and `unannotated` labels as audit-only records.

### Strict transfer and adaptation protocols

The v17 protocol uses nested source-species selection. Each outer held-out species is evaluated once, after candidate rules are ranked only using source-species inner folds. All-cell accuracy uses every held-out cell as the denominator. Source-label coverage, known-label accuracy and known-label macro-F1 are calculated and reported separately. Few-shot adaptation samples labelled support cells by species, keeps support and query cells non-overlapping, and aggregates ten independent draws per support budget.

### Secondary-root adapter

The GSE270140 adapter uses `configs/gse270140_secondary_root_lora_adapter_4070.yaml`: a 256-dimensional, four-layer encoder initialized from `SnowLotus_CellFM_SRP169576_annotation_1024_best.pt`, LoRA rank 8, class-balanced supervised loss, a maximum of ten epochs and a fixed group-random split by unique cell ID. The run was executed with CUDA on an NVIDIA GeForce RTX 4070 Laptop GPU. The released adapter checkpoint is byte-checked against the checkpoint used for the audit. Configuration, source acquisition, archive inventory, label map, test predictions, per-class scores and semantic recovery tables are versioned in the release tree.

### Statistics, figures and release audit

The strict-transfer and secondary-root figures use fixed-seed nonparametric bootstrap resampling only to visualize uncertainty conditional on their frozen test populations. Every quantitative visual panel has a TSV source-data file. All main and Extended Data figures are exported as editable SVG and PDF, PNG preview and 600-dpi TIFF. The v5 audit checks file presence, editable SVG text, source-table presence, raster resolution, frozen strict metrics, secondary-root checkpoint checksum and supplementary-table paths. It reports technical readiness but does not substitute a subjective readiness score for editorial or peer review.

## Data and Code Availability

The repository, source code, v5 manuscript, model card, evidence ledger, figures, source data and reproducibility records are available at https://github.com/ahvsjags/SnowLotus-CellFM on branch `agent/remote-pipeline-20260728`. The v5 GSE270140 adapter is tracked through Git LFS and has SHA256 `1a306c4a5e21630a75a5a63d2867e86712b2da78eea3805eb5dc00b957134fd7`. Reproduce the context-adaptation evidence with:

```bash
python scripts/download_gse270140_external_validation.py
python scripts/extract_gse270140_external_assets.py
python scripts/prepare_gse270140_external_validation.py
python -m snowcell.cli train --config configs/gse270140_secondary_root_lora_adapter_4070.yaml --device cuda
python scripts/audit_gse270140_secondary_root_adapter.py
python scripts/render_v5_secondary_root_adapter_figure.py
python scripts/audit_v5_submission_figure_suite.py
```

## Figure Legends

**Figure 1 | Plant-cell corpus contract and shared representation.** A shared UMAP of 3,964 strict-evaluation cells is coloured by held-out species and ontology state. Corpus profile panels report the profiled five-species training record, strict-panel organ coverage and the gene-to-output annotation contract.

**Figure 2 | Nested strict transfer retains open-set cells.** The reference and strict output views use the same held-out cells. The denominator panel exposes all test cells, source-label-covered cells and open-set or unavailable labels. Species-level all-cell accuracy, conditional accuracy and coverage are shown with a nested-selection firewall.

**Figure 3 | Target-species adaptation dose response.** Disjoint support and query cells are used at four labelled support budgets. Points are individual draws, bars are standard deviations, macro-F1 is reported separately and species-level values remain visible.

**Figure 4 | Label-free external root execution and fixed-marker coherence.** GSE152766/GSM4626007 is shown only with model outputs. The marker panel tests six literature-fixed root anchors against predicted groups. This figure is not an external accuracy or model-ranking result.

**Extended Data Figure 6 | Author-labelled secondary-root LoRA-mode adaptation.** The frozen root checkpoint is adapted on the GSE270140/GSM8335426 train partition and selected on validation cells. The matched semantic recovery, 14-class held-out confusion matrix, per-class F1, validation history and locked-test metrics are shown. The protocol is supervised one-sample adaptation, not zero-shot or independent validation.

## References

1. Chen, H. et al. scPlantDB: a comprehensive database for exploring cell types and markers of plant cell atlases. *Nucleic Acids Research* 52, D1629-D1638 (2024).
2. Zhai, J. et al. scPlant: a versatile framework for single-cell transcriptomic data analysis in plants. *Plant Communications* (2023).
3. Cui, H. et al. scGPT: toward building a foundation model for single-cell multi-omics. *Nature Methods* 21, 1470-1480 (2024).
4. Hao, M. et al. Large-scale foundation model on single-cell transcriptomics. *Nature Methods* 21, 1481-1491 (2024).
5. Rosen, Y. et al. Toward universal cell embeddings: integrating single-cell RNA-seq datasets across species with SATURN. *Nature Methods* 21, 1492-1500 (2024).
6. Theodoris, C. V. et al. Universal cell embedding provides a foundation model for cell biology. *Nature* (2026).
7. Lotfollahi, M. et al. Nicheformer: a foundation model for single-cell and spatial omics. *Nature Methods* 22, 2525-2538 (2025).
8. Jean-Baptiste, K. et al. Dynamics of gene expression in single root cells of *Arabidopsis thaliana*. *Plant Cell* 31, 993-1011 (2019).
9. Shahan, R. et al. A single-cell *Arabidopsis* root atlas reveals developmental trajectories in wild-type and cell identity mutants. *Developmental Cell* 57, 543-560.e9 (2022).
10. NCBI Gene Expression Omnibus. *Arabidopsis thaliana* GSE152766, sample GSM4626007.
11. Lyu, M. et al. The dynamic and diverse nature of parenchyma cells in the *Arabidopsis* root during secondary growth. *Nature Plants* (2025). https://doi.org/10.1038/s41477-025-01938-6
