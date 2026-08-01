# Plant-CellFM Top-Journal Figure Audit

- State: `VISUAL_REBUILD_REQUIRED`
- Overall score: `35.00/100`
- Technical / metadata readiness: `93.50/100`
- Visual review: `35.0/100` (needs_revision)
- Visual review summary: Technical exports are complete, but final-size visual QA found clipped wide tables, severe long-label collisions in heatmaps, and local panel/text crowding; the suite is not visually approved.
- Verified reference anchors: `8`

## Package Coverage

| Component | Planned | Required |
|---|---:|---:|
| Main figures | 6 | 6 |
| Extended Data figures | 9 | 9 |
| Supplementary figures | 13 | 13 |
| Supplementary tables | 13 | 13 |
| Source-data groups | 6 | 6 |
| Supplementary notes | 5 | 5 |

## Score Components

| Component | Score |
|---|---:|
| blueprint_completeness | 25.00 |
| evidence_integrity | 15.00 |
| supporting_package | 20.00 |
| rendered_asset_coverage | 20.00 |
| technical_export_quality | 10.00 |
| visual_review | 3.50 |

## Hard Blockers

- Visual quality is not approved: status=needs_revision, score=35.0/100. Technical export checks cannot substitute for editorial visual review.

## Next Actions

1. Export the canonical Supplementary Tables before drawing quantitative panels.
1. Create final assets with the figure-asset manifest stems and SVG/PDF/TIFF/PNG exports.
1. Run this audit after every figure batch and record visual QA only after inspecting final-size exports.
