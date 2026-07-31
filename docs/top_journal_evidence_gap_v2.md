# Plant-CellFM Top-Journal Evidence Gap v2

**Status:** `DATA-FIRST SUBMISSION REBUILD, COMPLETE FIGURE/TABLE DRAFTS`  
**Primary strict record:** `release_metadata/strict_evaluation_decision_v17.md`  
**Scope:** this is an external-methods-readiness assessment, not an internal delivery scorecard.

## 1. Current Evidence Position

| Dimension | Working score | Evidence now frozen | Remaining requirement for a high-tier methods claim |
|---|---:|---|---|
| Importance of the problem | 90/100 | Cross-species, open-set plant single-cell annotation remains a material bottleneck. | The framing is strong and should remain focused on annotation under label shift. |
| Reproducibility and software | 89/100 | Versioned scripts, source data, H5AD profile, checkpoint/runtime records, six main figures, four Extended Data figures and ten v3 tables are locally reproducible. | Commit and push the immutable release; an independent rerun remains desirable. |
| Data traceability | 86/100 | The current frozen H5AD profile measures 272,732 cells, 209,405 genes, 5 species, 9 datasets, 31 samples and 34 labels. Every new quantitative panel exports TSV source data. | Expand only with a separately profiled corpus and clearly distinguish it from this frozen subset. |
| Foundation-model scale | 48/100 | A 256-dimensional, four-layer LoRA-adapted encoder and adapter/runtime stack are implemented. | This evidence supports a reproducible plant annotation framework, not a field-defining million-cell foundation-model scale claim. |
| Methodological novelty | 62/100 | Ortholog-aware data contract, species adapters, nested context-aware transfer selection, explicit open-set accounting, few-shot adaptation and calibrated runtime controls are implemented. | The nested metadata gate is a transparent selection module, not a new learned biological representation method. A learned, ablated hierarchical open-set module would materially strengthen novelty. |
| Strict cross-species generalization | 58/100 | Primary nested v17 strict leave-species result: 39.96% all-cell accuracy, 71.48% known-label accuracy, macro-F1 0.2817 and 55.90% source-label coverage across 3,964 cells. | Add independent species/dataset collections, group-resampling uncertainty and a stronger open-set recognition mechanism. |
| Open-set evaluation | 64/100 | Exact-label denominator, source-label coverage and per-species held-out label-space summaries are now shown directly in Fig. 2 and ED Fig. 3. | Exact recognition of unsupported target labels remains intrinsically low; runtime-head results must remain outside the strict headline. |
| Few-shot adaptation | 76/100 | With 8/16/32/64 random support cells per target species, mean query all-cell accuracy is 59.21%/67.34%/72.30%/75.89% across ten support draws. | Add an independent target-species collection and label-budget matched comparator. |
| External benchmark closure | 44/100 | Matched frozen v3, centroid and Seurat evidence is present; external-method status is audited in Fig. 3 and Table S8. | scPlantLLM official predictions and scPlantAnnotate authenticated/exported predictions remain unclosed and cannot be ranked numerically. |
| Biological utility | 57/100 | The Arabidopsis root case includes 10 identity classes, 50 top marker candidates, effect-size landscapes and literature-aligned taxonomy. | It is a public-data computational case; independent query-cell replication or experimental validation is required for a discovery claim. |
| Main-figure editorial quality | 78/100 | Six data-first main figures replace the dashboard-style v1 suite. They use frozen cells, real corpus composition, explicit protocol boundaries and per-panel source-data files. | Final-size print review, journal-specific typography and an independent biological panel are still needed. |
| Extended Data and tables | 80/100 | Four Extended Data figures and ten v3 supplementary tables are regenerated from source records. | Add third-party numerical outputs and independent data once available. |
| Manuscript spine | 60/100 | An evidence hierarchy and full v3 figure/table map now exist. | Rewrite the main English and Chinese manuscripts from v17/v3 records; legacy v14-first prose must not remain in the final package. |

## 2. Non-Negotiable Reporting Boundary

The manuscript may claim a **reproducible plant expression-modelling and annotation framework** with measured strict cross-species, few-shot target adaptation and runtime protocols. It may not claim universal high-accuracy annotation for all plants, official superiority over an unexecuted third-party model, or completion of a *Saussurea involucrata* single-cell atlas without a reusable Snow Lotus single-cell matrix and independent validation.

The protocols must remain separate.

1. **Primary strict leave-species (v17):** nested source-species selection; no held-out species labels are used for fitting or selection. This is the only strict headline.
2. **Global-context sensitivity (v14):** 42.36% all-cell accuracy. It uses a global choice over outer folds and is exploratory, not primary.
3. **Few-shot target adaptation (v11):** labelled support cells are allowed and excluded from query scoring.
4. **Runtime full-vocabulary head (v11/v15):** deployment evidence only; it is not a zero-shot result.

## 3. v3 Figure and Table Package

### Main figures

| Figure | Central question | Primary evidence |
|---|---|---|
| Fig. 1 | What is the frozen, traceable evidence base? | H5AD corpus profile and an eight-species evaluation atlas. |
| Fig. 2 | Does strict cross-species transfer survive nested selection? | v17 nested evaluation, cell bootstrap, per-species outcomes and coverage. |
| Fig. 3 | Where are numerical comparisons actually matched? | Frozen v3-v9 grouped split comparisons; external-comparator audit is explicitly non-ranking. |
| Fig. 4 | How efficiently can new target species be adapted? | Ten-draw support/query benchmark at 8-64 support cells. |
| Fig. 5 | What biological resource does the model produce? | Arabidopsis root identity taxonomy and marker-candidate programmes. |
| Fig. 6 | How are deployment outputs controlled? | Full-vocabulary runtime confidence/selectivity and species-specific operational outcomes. |

### Extended Data and supplementary tables

| Asset | Central question |
|---|---|
| ED Fig. 1 | Corpus provenance, source imbalance and cell-label abundance. |
| ED Fig. 2 | Outer-species nested candidate selection is auditable. |
| ED Fig. 3 | Exact-label open-set composition and species/organ structure. |
| ED Fig. 4 | Target-species adaptation trajectories and support stability. |
| Tables S1-S10 | Corpus manifest, protocol boundaries, v17 results, nested selection, few-shot results, external audit, marker candidates and SHA256 reproducibility manifest. |

All v3 source tables are emitted beside the figures and under `supplementary_tables/submission_v3/`.

## 4. Submission Gates That Still Require New Evidence

1. Run at least one genuinely independent public plant single-cell collection not used by the present 3,964-cell strict evidence set.
2. Obtain reproducible official outputs for scPlantLLM and scPlantAnnotate, then compare only on an identical frozen input and split.
3. Add either independent Arabidopsis root query-cell replication or experimental validation before making a biological discovery claim.
4. Publish the exact commit, model artefacts, data-manifest checksums and source-data bundle, then perform a clean-environment rerun.

## 5. Current Submission Interpretation

The package is now suitable for a rigorous **methods/resource submission draft**: the central results are traceable, protocol boundaries are explicit, figures no longer disguise heterogeneity and the implementation has a full evidence package. It is not yet appropriate to represent the work as a completed Nature Methods-level universal plant foundation model. The fastest genuine route upward is new independent data plus closed third-party baselines, not cosmetic inflation of the current strict result.
