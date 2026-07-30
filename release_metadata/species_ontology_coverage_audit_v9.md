# Plant-CellFM v9 Species Ontology Coverage Audit

This audit adds a label-ontology view on top of the frozen normalized leave-species-out benchmark. It uses the server-exported benchmark `obs` labels, aligns them to the frozen per-species test counts, and maps fine labels into a conservative plant cell-state ontology. The ontology table is a coverage and triage audit; it does not change the frozen v9 accuracy, macro-F1 or v9-v3 comparison.

## Aggregate Coverage

| Metric | Value |
| --- | ---: |
| Frozen leave-species test cells | 3964 |
| Frozen exact fine-label evaluable cells | 2216 |
| Frozen exact fine-label coverage | 55.90% |
| Obs-derived exact-label reconstruction | 2246 cells (56.66%) |
| Reconstruction delta vs frozen JSON | 30 cells |
| Ontology-mapped actionable evaluable cells | 1794 |
| Ontology-mapped actionable coverage | 45.26% |
| Ontology delta vs frozen exact coverage | -422 cells (-10.65%) |
| Unknown/unannotated cells excluded from ontology coverage | 1384 (34.91%) |
| Exact-missed but ontology-covered rescue candidates | 420 |

## Per-Species Table

| Species | frozen coverage | obs exact | ontology coverage | ontology delta | unknown/unannotated | rescue candidates | alignment | reconstruction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Arabidopsis thaliana | 43.28% | 1035 (43.74%) | 1013 (42.81%) | -11 (-0.46%) | 663 (28.02%) | 385 | raw_species_exact_count | near_exact |
| Brassica rapa | 93.75% | 240 (93.75%) | 121 (47.27%) | -119 (-46.48%) | 119 (46.48%) | 0 | raw_species_exact_count | near_exact |
| Catharanthus roseus | 94.14% | 241 (94.14%) | 228 (89.06%) | -13 (-5.08%) | 13 (5.08%) | 0 | raw_species_exact_count | near_exact |
| Eutrema salsugineum | 100.00% | 62 (100.00%) | 0 (0.00%) | -62 (-100.00%) | 62 (100.00%) | 0 | raw_species_exact_count | near_exact |
| Fragaria vesca | 62.89% | 161 (62.89%) | 181 (70.70%) | 20 (7.81%) | 15 (5.86%) | 35 | raw_species_exact_count | near_exact |
| Gossypium bickii | 90.62% | 251 (98.05%) | 251 (98.05%) | 19 (7.42%) | 0 (0.00%) | 0 | raw_species_exact_count | near_exact |
| Gossypium hirsutum | 0.00% | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 256 (100.00%) | 0 | raw_species_exact_count | near_exact |
| Triticum aestivum | 100.00% | 256 (100.00%) | 0 (0.00%) | -256 (-100.00%) | 256 (100.00%) | 0 | raw_species_exact_count | near_exact |

## Top Ontology Rescue Signals

- **Arabidopsis thaliana**: rescued ontology groups: meristem_or_stem_cell_niche=251, epidermis=105, vascular_stele=22, guard_or_stomatal_cell=6, phloem=1; unknown/unannotated labels: unannotated_root=318, unannotated=256, Unknow=89.
- **Brassica rapa**: rescued ontology groups: none; unknown/unannotated labels: Unknow=119.
- **Catharanthus roseus**: rescued ontology groups: none; unknown/unannotated labels: Unknow=13.
- **Eutrema salsugineum**: rescued ontology groups: none; unknown/unannotated labels: unannotated_root=62.
- **Fragaria vesca**: rescued ontology groups: epidermis=27, xylem=8; unknown/unannotated labels: Unknow=15.
- **Gossypium hirsutum**: rescued ontology groups: none; unknown/unannotated labels: unannotated_leaf_glandular=256.
- **Triticum aestivum**: rescued ontology groups: none; unknown/unannotated labels: unannotated_root=256.

## Reviewer-Safe Interpretation

The strict benchmark remains the controlling performance claim. The ontology view shows whether low leave-species coverage is caused by genuinely absent biological states, superficial label wording differences, or uninformative labels such as unknown/unannotated classes. Because unknown and unannotated labels are excluded from actionable ontology coverage, this audit is deliberately conservative: it identifies what can be fixed by label harmonization without inflating model accuracy.

The main near-term use is to guide the next frozen benchmark: keep the current all-cell and known-label metrics, add an explicit plant cell-state ontology mapping file, and report exact-label and ontology-label coverage side by side before rerunning species holdout.

## Files

- Frozen benchmark JSON: `release_metadata/v9_benchmarks/v9_lora_cross_species_benchmark.json`
- Server-exported obs labels: `release_metadata/species_ontology_obs_labels_v9.tsv`
- Cell-state ontology mapping table: `release_metadata/plant_cell_state_ontology_mapping_v9.tsv`
- Machine-readable audit: `release_metadata/species_ontology_coverage_audit_v9.json`
- Per-species TSV: `release_metadata/species_ontology_coverage_audit_v9.tsv`
