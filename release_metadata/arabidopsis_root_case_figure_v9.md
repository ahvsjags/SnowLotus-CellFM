# Plant-CellFM v9 Arabidopsis Root Case Figure

Generated: 2026-07-30 Asia/Shanghai

This figure package converts the Arabidopsis root computational case into a figure-ready biological result with source data, vector graphics and high-resolution raster exports.

## Figure Claim

Plant-CellFM v9 resolves an Arabidopsis-specific adapter from the plant-general registry and produces marker-candidate evidence for major root cell identities from public single-cell data.

## Figure Files

| Asset | Path |
| --- | --- |
| SVG master | `figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.svg` |
| PDF master | `figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.pdf` |
| PNG preview | `figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.png` |
| TIFF raster | `figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case.tiff` |
| Metadata | `figures/plant_cellfm_v9_arabidopsis_root_case/plant_cellfm_v9_arabidopsis_root_case_figure_metadata.json` |
| Rendering script | `scripts/render_arabidopsis_root_case_figure_v9.py` |

## Source Data

| Source-data file | Description |
| --- | --- |
| `figures/plant_cellfm_v9_arabidopsis_root_case/source_data/arabidopsis_root_marker_candidates_figure_source_v9.tsv` | All 260 marker-candidate rows used in the scatter panel. |
| `figures/plant_cellfm_v9_arabidopsis_root_case/source_data/arabidopsis_root_top_marker_matrix_source_v9.tsv` | Root-identity top-marker rows used in the matrix panel. |
| `figures/plant_cellfm_v9_arabidopsis_root_case/source_data/arabidopsis_root_identity_summary_source_v9.tsv` | Per-root-identity summary values used in the horizontal bar panel. |

## Panel Legend

**a,** Figure workflow. Public Arabidopsis root matrices are routed through the Plant-CellFM v9 Arabidopsis adapter and used for annotation and marker-candidate mining. The case records 24 known adapters, 10 root identity categories, 260 marker-candidate rows and 256-dimensional embeddings.

**b,** Top five marker candidates per root identity. Rows represent major Arabidopsis root identities and columns show candidate rank. Tile colour encodes log2 fold-change for the candidate marker.

**c,** Marker effect-size distribution across all candidate states. Each point is a marker candidate. The x-axis reports log2 fold-change and the y-axis reports detection-rate separation between the focal state and other cells. Green points are root-identity markers; grey points are cell-cycle or other states.

**d,** Identity-level marker strength summary. Bars show median marker score for each root identity. Colour encodes median detection-rate separation and text labels report median log2 fold-change.

## Claim Boundary

The figure supports a computational biology case study: adapter resolution, marker-candidate discovery and root cell-identity interpretation from public data. It does not claim wet-lab validation of the marker candidates.
