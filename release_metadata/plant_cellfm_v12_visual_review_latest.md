# Plant-CellFM v12 Main-Figure Visual Review

- Scope: `figures/plant_cellfm_submission_v12/main` (7 main figures)
- Reviewed: 2026-08-09 Asia/Shanghai
- Status: `pass_with_final_size_proof`
- Technical export status: PASS — every canonical figure group has SVG/PDF/PNG/TIFF; the project audit reports editable vector typography/data layers and 600-dpi PNG/TIFF exports. Figures 2–7 were refreshed on 2026-08-08 and Figure 1 on 2026-08-09; all seven were rechecked.
- Manual visual status: PASS — original-resolution review of the refreshed seven-figure contact sheet and Figures 1, 5, and 7 found no blocking clipping, panel overlap, hierarchy failure, or inconsistent color semantics.

## Technical checks

| Check | Result |
|---|---|
| Complete four-format export | 7/7 canonical figure groups |
| SVG/PDF editable typography/data layers | PASS per `figures/plant_cellfm_submission_v12/review/plant_cellfm_v12_main_audit.json` |
| PNG/TIFF raster resolution | 600/600 dpi for all 7 figures |
| Source-table coverage | PASS; 6–9 TSV inputs per figure |

## Visual review

- Figure hierarchy is consistent across the seven-page narrative; panel letters, titles, legends, and footer contracts are visibly separated.
- No visible right-edge clipping or panel/text overlap was found in Figures 1–7 at original PNG resolution.
- Color semantics are coherent across the suite: teal denotes correct/adapted outcomes, orange denotes error or contrast routes, and gray denotes frozen/open/unavailable states.
- Figure 1 has generous lower whitespace but no clipping or hierarchy failure. Figure 4a has locally dense route labels; Figure 5c and Figure 7d contain the densest heatmap labels. They remain readable at original resolution but require a final-size proof at the target journal width.
- The v12 audit reports a 3 pt minimum SVG font size. This is not a current export blocker, but it is the main remaining readability risk after journal-scale reduction.

## Blockers and minimum action

- v12 main-figure package blockers: none identified.
- Minimum action: perform one final-size proof at the target journal column width, focusing on Figure 4a route labels, Figure 5c/7d heatmap labels, and small species/state annotations; revise only if labels become ambiguous.
- Technical note: the v12 audit records embedded-raster layers at 272–620 dpi in SVG and 361–620 dpi in PDF; the canonical external PNG/TIFF exports are 600 dpi. The sub-300-dpi embedded layers are retained as non-blocking preferred-page composition elements and should be checked in the same final-size proof.

## Package scope note

The main audit still targets the older `figures/plant_cellfm_submission` 6+9+13 manifest, so it reports 0/15 rendered groups. This is a manifest/package-scope mismatch, not a missing v12 export.

No model data, metrics, or scientific conclusions were modified.
