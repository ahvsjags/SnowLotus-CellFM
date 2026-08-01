# Plant-CellFM v7 Visual Argument Contract

## Purpose

This contract governs the next submission-facing figure suite. Its purpose is
not to make a higher claim than the evidence supports. Its purpose is to turn
the existing evidence chain into a clear visual argument in which each main
figure answers one reviewer question, each score retains its denominator, and
audit detail moves out of the primary visual path.

The reference composition is the asymmetric, evidence-led pattern used in
recent methods and cross-species single-cell articles, including scGPT,
Nicheformer and plant cross-species integration studies. The relevant visual
lesson is hierarchy rather than imitation: one dominant result, one short
causal or protocol schematic, and a small number of subordinate checks per
page.

## Non-Negotiable Rules

1. A main figure must have one declarative conclusion that can be read from
   its hero panel at journal column width.
2. A main-page hero must occupy at least 40% of the data-bearing area. It
   cannot be a decorative schematic, a legend, or a list of claims.
3. Scores must visibly state the unit, denominator, split, label-availability
   rule and whether target labels are used during fitting or selection.
4. Strict zero-shot, target-label adaptation, same-study external reference
   and blind biology execution are distinct evidence tiers. They may appear in
   the same paper, but never share a headline or a common ranking axis.
5. Negative results and open-set failures remain in Extended Data with their
   denominators. They are not removed, but neither do they consume the visual
   hierarchy of a primary conclusion page.
6. Every displayed numeric value must have a tabular source-data counterpart
   and a script-level provenance path.
7. The figure suite must remain interpretable in grayscale and use a
   colorblind-safe neutral / signal / alert palette. Red is reserved for
   boundary or failure language, not a high-performing method.

## Main Figure Blueprint

| Figure | Reviewer question | One-sentence conclusion | Hero evidence | Supporting evidence | Required state |
| --- | --- | --- | --- | --- | --- |
| Fig. 1 | What is the scientific object and why is it reproducible? | Plant-CellFM treats annotation as a traceable gene-to-cell evidence chain rather than an opaque species label lookup. | Large left-to-right data-to-output system map driven by real corpus, orthology and adapter metadata. | Compact actual corpus phylogeny/tissue occupancy and output contract. | Rebuild v6 Fig. 1; eliminate equal-weight panels and use real quantities only. |
| Fig. 2 | Does the model transfer beyond a random holdout? | Strict nested leave-species evaluation is heterogeneous but quantified on every held-out cell under an explicit open-set denominator. | Per-species all-cell performance with coverage and bootstrap interval on the same scale. | One denominator flow and a compact label-coverage strip. | Rebuild v6 Fig. 2; move context sensitivity, decoder sweeps and detailed failure matrices to Extended Data. |
| Fig. 3 | What changes when a new plant obtains a small labelled support set? | Small, disjoint target support creates a repeatable dose-response improvement rather than relabelling the evaluation query. | Support-size response with every fixed draw, mean, uncertainty and all-cell denominator. | Split schematic and a species-level gain matrix. | Rebuild v6 Fig. 3 with a stronger vertical hierarchy and direct draw-to-query provenance. |
| Fig. 4 | Can the frozen model execute a biologically interpretable analysis outside the benchmark? | A label-free external root matrix produces a transparent predicted partition with prespecified marker coherence, not an external accuracy claim. | High-density embedding/annotation field with a selected marker-coherence overlay. | Predicted-state composition and a fixed-marker effect plot. | Rebuild v6 Fig. 4 with fewer labels, selected overlays and clear blind-input boundary. |
| Fig. 5 | Can an author-labelled external plant atlas expose open-set failure and validate a practical recovery path? | In a species-absent Sorghum root atlas, the frozen screen exposes open-set mismatch while a library-held-out LoRA adapter restores 27-state annotations. | Matched frozen-to-adapter recovery on one sealed Sorghum library, with bootstrap intervals. | Paired author/prediction topology, all 27 states and an orthology coverage audit. | Completed for GSE297576 Sorghum bicolor. It is a within-atlas target-species adaptation result, not an independent zero-shot ranking. |

## Extended Data and Supplementary Layout

| Item | Visual role | Current evidence source | Status |
| --- | --- | --- | --- |
| ED Fig. 1 | Full strict per-species confusion and label-coverage audit | v17 primary strict evidence | Rebuild from v6 Fig. 2 supporting panels. |
| ED Fig. 2 | Context-gate and classifier sensitivity | v10/v13/v14 records | Retain explicit non-nested boundary. |
| ED Fig. 3 | Adapter response by held-out species and support draw | v11 adaptation records | Rebuild from v6 Fig. 3 supporting panels. |
| ED Fig. 4 | Blind root input, preprocessing and fixed-marker audit | GSE152766 audit | Rebuild from v6 Fig. 4 detailed panels. |
| ED Fig. 5 | Wheat same-study target-adaptation protocol and complete confusion matrix | GSE270342 Wheat LoRA audit | Rebuild from v6 Fig. 5; do not call it independent. |
| ED Fig. 6 | Zero-target Arabidopsis-to-wheat stress test | zero-target transfer audit | Preserve negative result and all three target states. |
| ED Fig. 7 | scPlantLLM matched reference, frozen / partial / full backbone variants | locked GSE270342 test and replay audit | Rebuild only after full-backbone replay is confirmed. |
| ED Fig. 8 | GSE297576 external-screen contract, ontology and frozen failure structure | GSE297576 conversion, orthology and frozen audit records | Complete; preserves the full external denominator and `Unknow` composition outside the main adapted-recovery page. |
| Table S1-S14 | corpus, ontology, split, adapter, strict and adaptation source data | existing v6 tables | Verify all table references and row counts. |
| Table S15-S24 | external cases, comparator protocol, predictions and replay hashes | existing and pending comparator tables | Append no table without a source-data script and SHA256 record. |

## Figure-Critic Rubric

The release gate evaluates each main figure independently. A score below 4 in
any hard gate blocks submission export.

| Dimension | Hard-gate question | Score 5 standard |
| --- | --- | --- |
| Claim focus | Can a reader state one conclusion without reading the caption? | The hero panel alone establishes the conclusion and supporting panels answer the next two reviewer questions. |
| Evidence integrity | Are denominator, split and label-use rules visible at point of interpretation? | Every score is traceable to locked source data and its boundary is adjacent, concise and unambiguous. |
| Visual hierarchy | Does one data panel dominate rather than four panels compete? | One hero uses 40-65% of data area; all other panels have an explicitly subordinate role. |
| Information density | Does every mark earn its space? | No decorative panel, repeated legend, unused quadrant or low-information saturated heatmap remains. |
| Typography | Is primary text readable at final width without clipping? | Consistent 6.5-8 pt final type, 0 clipped labels, short direct annotations, and no caption-like paragraph inside a panel. |
| Color semantics | Is color consistent and accessible? | Colors encode stable scientific roles across the entire suite and are never the sole channel for meaning. |
| Export integrity | Can production edit and reproduce it? | Vector text stays editable, raster data panels meet resolution requirements, and PNG/PDF/SVG/TIFF outputs agree. |

## Automated Gate Outputs

The v7 figure audit must produce a JSON record containing, for every export:

- canvas dimensions, format, resolution and file checksum;
- panel labels detected in the vector source and their expected order;
- text bounding-box overflow / clipping check;
- source-data file list and row/column summaries;
- claim-boundary phrases required by the evidence tier;
- a human visual-review checklist result for hierarchy, density and legibility.

The automated audit can detect mechanical failures. A visual reviewer must
still inspect the final PNG at 100% and at the intended one- and two-column
widths before release.

## Evidence Gates Before v7 Submission Claims

1. Replay the full-backbone scPlantLLM GSE270342 run exactly on the locked
   barcode set. This is a same-study adaptation reference, not a universal
   external ranking.
2. Complete: recover an author-labelled GSE297576 Sorghum bicolor Seurat atlas,
   verify the species is outside the frozen five-species corpus, and lock its
   gene-identifier and label-ontology contracts before inference.
3. Complete: run the frozen Plant-CellFM checkpoint, save per-cell predictions
   and recompute every external metric from the saved table. Keep the frozen
   result visually distinct from the subsequent sealed-library adaptation.
4. Run at least one independent external comparator only where its official
   code, weights, preprocessing and compute scope can be verified. A missing
   comparator remains a documented gap, not a synthetic baseline.
