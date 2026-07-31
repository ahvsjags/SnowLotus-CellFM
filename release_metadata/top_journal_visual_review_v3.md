# Plant-CellFM v5 Visual And Evidence Review

## Scope

This review covers five main figures and six Extended Data figures in `figures/plant_cellfm_submission_v5`. It is a release-control record, not a self-assigned journal-quality score and not a substitute for editorial production checks.

## Visual Contract

| Gate | Release rule | Verification |
| --- | --- | --- |
| Figure architecture | Main figures follow corpus contract, strict transfer, dose-response adaptation, label-free external execution, and allopolyploid wheat adaptation in that order. | `scripts/audit_v5_submission_figure_suite.py` |
| Information density | Low-cardinality audits use compact horizontal panels; no panel is stretched merely to fill a page. | Manual raster review of Main Figs. 1--5 and Extended Data Figs. 1--6 |
| Typography | SVG text remains editable and no non-empty label is below 5 pt. | Automated SVG text-size gate |
| Reproducible artwork | Each figure has SVG, PDF, PNG, 600 dpi TIFF and one or more tidy TSV source-data tables. | Automated export/source-data gate |
| Figure scale | Full-width artwork is composed at 7.25 in (184.15 mm); the wheat figure is 6.55 in high (166.37 mm). | Renderer source and TIFF metadata |
| Colour use | Teal denotes Plant-CellFM/adaptation results, grey denotes baselines or audit-only states, orange denotes caution or support selection, and red denotes claim boundaries. | Palette constants in renderers and raster review |

## Figure-Level Readout

| Figure | Reviewer-facing question | Evidence boundary carried in the artwork |
| --- | --- | --- |
| Fig. 1 | What corpus, ontology and annotation contract are frozen? | Training corpus composition is descriptive and does not constitute a held-out accuracy claim. |
| Fig. 2 | What remains under strict leave-species evaluation? | The primary all-cell result is 39.96%; the 42.36% context result is explicitly a global sensitivity analysis. |
| Fig. 3 | How much labelled support is needed for target adaptation? | Support and query cells are disjoint; this is labelled adaptation, not zero-shot transfer. |
| Fig. 4 | Can a label-free root matrix yield inspectable model states? | Marker coherence is not external accuracy, model ranking or wet-lab validation. |
| Fig. 5 | Can an allopolyploid wheat input be mapped and adapted without reusing prior strict-transfer cells? | The wheat result is a same-study supervised adapter with barcode exclusion; it is not external validation. |
| ED1--ED3 | Are denominators, model selection and matched checkpoint gains inspectable? | These are audit and matched-protocol analyses, not third-party model rankings. |
| ED4--ED5 | Do root predictions show literature-linked and marker-coherence evidence? | Neither panel replaces independent labels or experiments. |
| ED6 | Does a second root adaptation retain fine state resolution on a locked split? | It is a same-study supervised cell-level split, kept separate from strict transfer. |

## Final Editorial Checks

- Re-open the supplied PDF/SVG in the target journal workflow and verify font embedding, colour conversion and rasterization policy.
- Check every caption against the corresponding source-data TSV before submission.
- Keep third-party scPlantLLM/scPlantAnnotate comparisons labelled as unfinished until a matched official numerical benchmark is available.
- Do not convert same-study supervised adapters, label-free marker coherence, or global sensitivity analyses into zero-shot/external-validation claims.
