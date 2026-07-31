# Plant-CellFM Figure Quality Gap Audit v2

**Review status:** `VISUAL_REBUILD_REQUIRED`

## Honest assessment

The current `figures/plant_cellfm_submission/` package is technically exportable and numerically traceable, but is a **data-audit prototype**, not a top-journal visual package. The earlier static score measured asset existence, editable text and raster DPI; it did not measure scientific visual hierarchy, biological evidence density or editorial impact. It must not be used as a submission-readiness score.

| Dimension | Current v1 | Relevant top-journal standard | Gap |
|---|---:|---:|---|
| One-glance scientific claim | 4/10 | 9/10 | Main figures read as multi-purpose dashboards rather than one discovery each. |
| Biological primary visual | 2/10 | 9/10 | The main suite lacks a genuine cell-atlas / held-out embedding hero panel. |
| Data-first composition | 4/10 | 9/10 | Box-and-arrow schematics dominate where real UMAPs, spatial maps, images or distributions should lead. |
| Quantitative story | 5/10 | 9/10 | Summary points are present, but bootstrap distributions, effect-size annotations and clear sample-level structure are too limited. |
| Typography and density | 5/10 | 9/10 | Several panels require small text, and labels compete with rather than support the conclusion. |
| Visual language consistency | 5/10 | 9/10 | The palette and card-like boxes are too presentation-like; they do not form a restrained data-led visual system. |
| Main / extended-data allocation | 4/10 | 9/10 | Deployment and reproducibility material occupy too much main-figure real estate. |
| **Visual editorial score** | **29/70** | **60+/70** | **Rebuild, not polish.** |

## What the reference figures do that v1 does not

1. **They open with irreplaceable primary evidence.** Nicheformer Fig. 1 combines corpus-scale embedding, real spatial slices and an architecture only after the reader has seen the biological scope. UCE Fig. 1 makes the biological representation and the actual integrated manifold the visual centre. Plant-CellFM v1 begins with abstract bubbles and boxes.
2. **Each main figure has a single visual verb.** UCE Fig. 2 is a zero-shot claim: protocol contrast, manifold evidence and a label-transfer confusion matrix all support that one claim. Current Figure 6 is a deployment dashboard, not a single biological or methodological discovery.
3. **Schematics are compact and subordinate to evidence.** The reference architecture panels use visual metaphors, fine typographic hierarchy and sparse annotation. Current v1 uses repeated bordered rectangles as its primary language.
4. **Real data carry visual weight.** Top-tier figures devote most pixels to embedding topology, images, distributions, heatmaps or spatial patterns. Current v1 has limited actual cell-level geometry, particularly in Figures 1 and 5.
5. **Supplementary material absorbs completeness.** Operational APIs, checkpoint manifests, threshold grids and execution details belong in Extended Data or Supplementary material unless they directly establish the main claim.

## Required v2 redesign

### Main Figure 1: Foundation-model scope and biological space
- Hero: actual Plant-CellFM embedding, rendered in matched coordinates and coloured by species, organ and canonical cell-state in adjacent views.
- Supporting: a single compact corpus/phylogeny coverage band; minimal ortholog-to-token schematic; no row of generic boxes.

### Main Figure 2: Strict leave-species zero-shot
- Hero: held-out species manifold and true-versus-predicted labels in matched coordinates.
- Supporting: an explicit locked-label protocol, bootstrap/effect-size distribution, per-species forest plot and a small open-set error decomposition.
- The headline stays v14 strict; v15 is excluded.

### Main Figure 3: Adaptation is a measurable transition
- Hero: support-budget response curve with uncertainty and a highlighted 8-support operating point.
- Supporting: species-by-budget heatmap; low/high-response species examples; adapter-resolution / mapping-coverage relationship.

### Main Figure 4: Biological case study
- Hero: real Arabidopsis root query-cell embedding and matched annotation panel, using only data with verifiable labels and predictions.
- Supporting: compact marker matrix, feature plots for a limited set of marker candidates and an effect-size landscape.
- If matched query coordinates cannot be generated faithfully, this item remains Extended Data rather than being simulated.

### Main Figure 5: Benchmark and boundary
- Hero: matched method comparison with raw resample distributions and effect sizes, not only bars.
- Supporting: completed comparators only; third-party pending status moved to Supplementary Figure 7.

### Main Figure 6: Remove from main-text slot unless new biological evidence is added
- Runtime rescue, confidence sweeps, CUDA/API, hashes and resource cards move to Extended Data and Supplementary Notes.

## Visual acceptance gate for v2

- No main figure may use more than two bordered-card groups.
- At least 55% of each main figure's canvas must be direct data evidence.
- Every main figure must have one large hero panel with a conclusion readable at 25% zoom.
- All labels must remain legible at a two-column width; no panel may depend on a paragraph inside the artwork.
- Main text must contain at least two genuine cell-level or spatial biological views, not synthetic illustrative stand-ins.
- Visual review must be human-scored separately from technical export checks. The v1 `SUBMISSION_READY` result is invalidated as a visual-quality judgment.
