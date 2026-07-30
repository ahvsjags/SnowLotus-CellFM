# Plant-CellFM v9 Biology Case Study

## Arabidopsis root cell-identity marker and adapter case

A complete public-plant biological case demonstrating adapter resolution, hierarchical annotation evidence and marker-candidate mining on root cell states.

## Evidence

- Adapter registry scope: `all_plants`
- Dynamic adapter resolution: `True`
- Total adapters: `24`
- Arabidopsis adapter: `plant_arabidopsis_thaliana`
- Arabidopsis evidence: `{'manifest_rows': 12, 'datasets': 10}`
- Marker labels: `13`
- Marker rows: `260`
- Root identity labels: `10`
- Literature anchor: `release_metadata/arabidopsis_root_literature_anchor_v9.md`

## Top Marker Summary

| Cell state | Category | Top genes | Median score | Median log2FC | Median detection delta |
| --- | --- | --- | ---: | ---: | ---: |
| Columella root cap | root_cell_identity | AT5G02380, AT2G04025, AT2G36950, AT3G20840, AT3G45730 | 0.849 | 3.296 | 0.231 |
| G1/G0 phase | cell_cycle_or_other | ATCG00790, ATCG00740, ATCG00170, ATCG00800, ATCG00770 | 1.917 | 3.395 | 0.575 |
| Lateral root cap | root_cell_identity | AT1G26820, AT3G16440, AT1G15385, AT1G06090, AT5G55110 | 2.871 | 4.235 | 0.677 |
| Non-hair | root_cell_identity | AT1G65310, AT4G12545, AT1G70850, AT1G14960, AT4G12550 | 2.023 | 3.742 | 0.607 |
| Phloem | root_cell_identity | AT5G04080, AT1G62380, AT2G46630, AT1G79430, AT5G59090 | 3.051 | 7.071 | 0.495 |
| Root cap | root_cell_identity | AT1G54010, AT5G10130, AT1G28290, AT5G58784, AT2G43610 | 2.634 | 3.634 | 0.730 |
| Root cortex | root_cell_identity | AT1G12090, AT1G13930, AT1G21310, AT5G13930, AT4G30170 | 1.665 | 2.941 | 0.559 |
| Root endodermis | root_cell_identity | AT3G22620, AT3G22600, AT2G32300, AT2G28670, AT5G15290 | 2.863 | 4.341 | 0.593 |
| Root hair | root_cell_identity | AT3G54580, AT1G30870, AT3G09925, AT3G54590, AT3G62680 | 1.602 | 3.700 | 0.427 |
| Root stele | root_cell_identity | AT4G11210, AT2G02130, AT1G12080, AT4G14130, AT3G59370 | 2.043 | 3.840 | 0.541 |
| S phase | cell_cycle_or_other | AT5G15200, AT5G20290, AT3G60245, AT5G16130, AT4G16720 | 1.821 | 3.053 | 0.605 |
| Unknown | cell_cycle_or_other | AT2G43820, AT2G29440, AT2G29450, AT1G43160, AT3G50970 | 0.339 | 1.208 | 0.283 |
| Xylem | root_cell_identity | AT5G03170, AT1G20850, AT5G16490, AT1G08283, AT4G23690 | 2.489 | 6.266 | 0.463 |

## Manuscript-Ready Case Statement

The Arabidopsis root case provides a complete public-data demonstration of Plant-CellFM v9: the same plant-general model resolves a species adapter, produces annotation-ready representations and returns marker candidates for major root cell identities.

The reported root identity categories are aligned with established Arabidopsis root single-cell atlas terminology, including root cap/columella, root-hair and non-hair epidermis, cortex, endodermis, stele, phloem and xylem. The model-derived marker genes remain computational candidates, not wet-lab-validated markers.

## Reproducible Workflow

1. Resolve the input species to the Arabidopsis adapter, with plant_universal as fallback.
2. Run the Plant-CellFM backbone and annotation head to obtain cell embeddings and fine/coarse labels.
3. Mine marker candidates per predicted or reference cell state using expression enrichment, log2 fold-change and detection-rate separation.
4. Review root identity labels such as root cap, cortex, endodermis, stele, phloem, xylem and root hair as a coherent plant biology case.

## Files

- `marker_json`: `release_metadata/strict_benchmarks/public_sprint.marker_candidates.json`
- `marker_tsv`: `release_metadata/strict_benchmarks/public_sprint.marker_candidates.tsv`
- `top_marker_tsv`: `release_metadata/plant_biology_case_study_top_markers_v9.tsv`
- `adapter_registry`: `release_metadata/plant_species_adapters.json`

## Figure-Ready Package

The case has a manuscript-ready four-panel figure package:

- figure record: `release_metadata/arabidopsis_root_case_figure_v9.md`
- SVG/PDF/PNG/TIFF exports: `figures/plant_cellfm_v9_arabidopsis_root_case/`
- source data: `figures/plant_cellfm_v9_arabidopsis_root_case/source_data/`
- rendering script: `scripts/render_arabidopsis_root_case_figure_v9.py`
