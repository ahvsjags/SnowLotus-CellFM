# Plant-CellFM v6 Editorial Figure Contract

## Editorial Objective

Build a five-figure, evidence-first visual narrative for a plant single-cell methods/resource paper. The visual target is a high-impact methods article: one dominant claim per page, a clear hierarchy between primary evidence and support, direct presentation of denominators and evaluation boundaries, vector-editable text, source-data tables and no unstated performance comparison.

This is an editorial and technical contract. It does not elevate the current evidence tier by itself.

## Reference Pattern

The v6 composition follows the page-level pattern used in current high-impact foundation-model articles: a schematic-led opening figure, a benchmark page with one dominant quantitative panel, an adaptation page with a dose-response hero, a biological execution page, and a stress-test/adaptation page. These patterns are visible in the figure sequences of [scGPT](https://www.nature.com/articles/s41592-024-02201-0), [Nicheformer](https://www.nature.com/articles/s41592-025-02814-z) and the plant cross-species integration study [Coexpression enhances cross-species integration](https://www.nature.com/articles/s41477-024-01738-4). Nature Methods currently encourages up to six display items for a full Article, so the main story is kept to five figures with Extended Data carrying audits and sensitivity analyses.

## v5 Gap Audit

| Dimension | v5 state | v6 decision |
| --- | --- | --- |
| Visual hierarchy | Five well-exported pages, but Figures 1–3 distribute attention too evenly. | Use asymmetric grids and a single hero evidence panel on every main page. |
| Scientific density | Panels expose definitions but Figure 2 has unused canvas and Figure 3 contains an uninformative saturated heatmap. | Replace low-information area with compact denominators, raw replicate points and direct effect displays. |
| Benchmark logic | Strict transfer is transparent but has no matched official third-party panel. | Keep strict score primary; reserve a labelled comparator slot and do not fabricate it. |
| Biological payoff | Label-free root execution has marker coherence but no external labels or orthogonal assay. | Make it a biological plausibility page, not an accuracy claim. |
| Adaptation story | Two same-study supervised adapters have useful locked tests but are separated from their provenance limits. | Pair each accuracy claim with its split, mapping and scope in the same page. |
| Typography and palette | Technically passable, but title/subtitle density competes with data in several panels. | Use a dark neutral baseline, teal only for measured Plant-CellFM results, orange for coverage/support, violet for adaptation and red only for boundary callouts. |

## Figure-Level Contract

### Figure 1 | Plant-aware representation and audit trail

**Core conclusion:** Plant-CellFM couples a traceable gene/orthology input contract to a shared cell representation and a species-adaptation output path.

**Archetype:** schematic-led composite.

| Panel | Role | Evidence | Design requirement |
| --- | --- | --- | --- |
| a | Hero workflow | Gene-ID input, deterministic orthology map, 256-dimensional encoder, evidence gate and output record. | Occupy about 45% of the page; use the same color semantics as later figures. |
| b | Corpus landscape | 272,732 frozen-profile cells across five profiled species and tissues. | Use a compact species-by-tissue composition view; do not imply all-plant coverage. |
| c | Shared representation | 3,964 strict-panel cells across eight held-out species. | Use one large embedding with direct species callouts rather than a detached legend. |
| d | State abstraction | The same embedding colored by the frozen ontology. | Visually subordinate to panel c; show that ontology is not species identity. |
| e | Reproducibility strip | Frozen profile, split, adapter registry and evidence ledger pointers. | A narrow bottom strip, never a dashboard card grid. |

**Review risk:** the frozen profile contains five profiled species and nine datasets, not all plants. This sentence stays in the legend and source-data record.

### Figure 2 | Strict cross-species transfer is measurable and heterogeneous

**Core conclusion:** Under a locked leave-species protocol, Plant-CellFM reaches 39.96% all-cell accuracy on 3,964 held-out cells while explicit coverage exposes strong interspecies heterogeneity.

**Archetype:** asymmetric quantitative grid.

| Panel | Role | Evidence | Design requirement |
| --- | --- | --- | --- |
| a | Hero forest/dumbbell | Per-species all-cell accuracy, covered-label accuracy and source-label coverage across eight species. | Occupy the full left column; one shared x-axis and direct per-species denominator labels. |
| b | Primary metric strip | 3,964 all cells, 2,216 covered labels, 1,748 open/unavailable cells, fixed-bootstrap interval. | Make the denominator visual, not prose. |
| c | Failure anatomy | Compact coverage-by-label-state view with Gossypium hirsutum and open-set labels retained. | No deletion of zero-coverage labels. |
| d | Matched historical checkpoint trajectory | v3 to v9 matched internal changes on a fixed historical protocol. | Label it `internal matched historical protocol`; do not visually merge it with v17. |
| e | Context sensitivity | Frozen v14 context-gate sensitivity result. | Use a grey boundary band and state that it is not the nested primary result. |

**Review risk:** do not present the 42.36% global sensitivity result as the v17 primary score, and do not create a third-party comparison without a shared input, label, split and open-set protocol.

### Figure 3 | Small labelled support produces a repeatable adaptation dose response

**Core conclusion:** When target labels are permitted, performance rises monotonically from 8 to 64 support cells per held-out species and reaches 75.89% mean query all-cell accuracy.

**Archetype:** quantitative grid with a dominant dose-response hero.

| Panel | Role | Evidence | Design requirement |
| --- | --- | --- | --- |
| a | Protocol diagram | Physical separation of support and query cells. | Small upper-left schematic with no decorative framing. |
| b | Hero dose-response | Ten fixed support draws at each budget, raw points, mean and s.d. | Use the largest area; direct-label the 64-cell endpoint. |
| c | Fine-label recovery | Macro-F1 dose response and raw draws. | Share x positions with b; avoid redundant legend. |
| d | Species consistency | Species-by-budget outcome matrix with single-label/unknown-only rows visibly marked. | Treat 1.00 rows as low-information records rather than high-confidence wins. |
| e | Adaptation boundary | One sentence: labelled support is not zero-shot transfer. | Small bottom boundary line in red. |

**Review risk:** the support set is a target-label adaptation experiment. It cannot repair the zero-shot claim.

### Figure 4 | Frozen external execution produces a biologically inspectable root partition

**Core conclusion:** On a label-free external Arabidopsis root matrix, the frozen model yields a structured 13-state partition and five of six prespecified marker anchors peak in their expected predicted group.

**Archetype:** asymmetric mixed-modality figure.

| Panel | Role | Evidence | Design requirement |
| --- | --- | --- |
| a | Hero embedding | 6,566 label-free cells colored only by model output. | Large left panel; all state colors match the support panels. |
| b | Output distribution and confidence | All 13 predicted states, cell counts and mean confidence. | Preserve rare phloem cells. |
| c | Marker coherence | Six prespecified marker anchors with direct rank/readout labels. | State explicitly that this is plausibility, not accuracy. |
| d | Audit footer | Input provenance, label-free status and fixed-marker protocol. | Keep to a thin footer. |

**Review risk:** there is no external expert annotation and no wet-lab validation. No accuracy, ranking or validation language appears in the figure title.

### Figure 5 | Allopolyploid wheat stress test and supervised rescue

**Core conclusion:** Provenance-controlled orthogroup mapping retains most input UMI counts, exposes weak frozen direct-root transfer and supports a supervised wheat-specific adapter with a locked 13-class test.

**Archetype:** asymmetric quantitative grid.

| Panel | Role | Evidence | Design requirement |
| --- | --- | --- |
| a | Provenance and exclusion | 7,388 author cells, 224 historical barcodes removed and fixed 5,014/717/1,433 split. | Use a narrow traceability path rather than a large workflow. |
| b | Orthogroup coverage | Feature and UMI retention plus first/mean frozen sensitivity. | Make mapping assumptions immediately visible. |
| c | Hero paired effect | Frozen direct-root projection versus wheat LoRA on the same 964-cell direct subset, 95% intervals. | Use measured point-and-interval geometry, never giant percentage typography. |
| d | Complete locked test | 13-class row-normalized confusion matrix. | Preserve all author states. |
| e | Per-class recovery | Per-class F1 versus support. | Encode support by point area only when the legend is explicit. |
| f | Selection isolation | Validation trajectory and fixed selected epoch. | Keep validation and locked test visually separate. |

**Review risk:** this is one author-labelled study with cell-level splitting. It is supervised adaptation, not independent external validation.

## Extended Data and Supporting Tables

| Asset | Required purpose |
| --- | --- |
| Extended Data 1 | Identity-label denominator, aliases and uninformative-label audit. |
| Extended Data 2 | Nested candidate-selection trace and leakage gate. |
| Extended Data 3 | Matched v3/v9 checkpoint comparison on its original historical protocol. |
| Extended Data 4 | Literature-fixed marker concordance and the 200-row candidate resource. |
| Extended Data 5 | Full 13-state label-free external-root audit. |
| Extended Data 6 | GSE270140 secondary-root supervised adapter and its full 14-class locked test. |
| Extended Data 7 | Source-only Arabidopsis-to-wheat three-state transfer audit, including the negative source-adapter result. |
| Extended Data 8 | Matched GSE270342 scPlantLLM frozen and partial-adaptation references on the identical locked test; explicitly not a full-backbone or compute-matched ranking. |
| Table S1–S20 | Existing corpus, ontology, split, adapter and per-class contracts. |
| Table S21 | GSE270140-to-GSE270342 zero-target-label transfer results, retaining all tested kNN decoders. |
| Table S22 | Per-class results for the matched GSE270342 frozen scPlantLLM representation reference. |
| Table S23 | Per-class results for the matched GSE270342 scPlantLLM final-block-plus-head partial adaptation reference. |

## Visual System

| Semantic role | Color | Rule |
| --- | --- | --- |
| Plant-CellFM measured result | `#007C83` teal | Use only for actual model estimates. |
| Conditional/structural quantity | `#2E6FAD` blue | Do not confuse with all-cell primary performance. |
| Coverage or labelled support | `#D97524` orange | Use for quantities that alter the evaluable denominator. |
| Target adaptation | `#8064A7` violet | Confined to labelled adaptation and adapter modules. |
| Audit-only/open-set state | `#9CAAB2` grey | Keep visible but visually quiet. |
| Claim boundary | `#B34D5B` red | Textual boundary/callout only; never an outcome color. |

Typography uses Arial/Helvetica-compatible editable SVG text. Quantitative pages are 184.15 mm wide. A lower-case panel label, short declarative title and one muted subtitle are allowed; titles should never repeat the caption.

## Acceptance Gate

1. Every main figure has one one-sentence conclusion and one dominant evidence panel.
2. Every quantitative page shows the denominator, repeat structure or test set where it changes interpretation.
3. Every export has SVG, PDF, PNG and 600-dpi TIFF outputs, editable SVG text and panel-level tidy source data.
4. No main figure claims matched third-party superiority, independent external accuracy or wet-lab validation without the corresponding evidence asset.
5. No label-free or open-set cells are removed merely to improve a display metric.
6. At final journal width, no text is below the five-point floor; a manual raster inspection remains mandatory.
