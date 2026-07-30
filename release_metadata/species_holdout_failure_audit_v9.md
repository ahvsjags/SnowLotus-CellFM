# Plant-CellFM v9 Species-Holdout Failure Audit

This audit decomposes the strict normalized leave-species-out benchmark into per-species coverage, known-label performance and open-set error sources. It is reviewer-facing evidence for why the headline species-holdout score must be interpreted as open-set transfer evidence, not as universal high-accuracy annotation.

## Aggregate Decomposition

| Metric | Value |
| --- | ---: |
| Test cells | 3964 |
| Evaluable known-label cells | 2216 |
| Open-set cells without train-fold label overlap | 1748 |
| Coverage | 55.90% |
| All-cell accuracy | 23.54% |
| Known-label conditional accuracy | 42.10% |
| Known-label conditional macro-F1 | 0.1918 |
| Estimated all-cell errors attributed to open-set label absence | 57.67% |

## Per-Species Diagnostic Table

| Species | Category | n | coverage | v9 all-cell acc. | v9 known-label acc. | v3 all-cell acc. | delta | Main interpretation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Arabidopsis thaliana | label_coverage_bottleneck | 2366 | 43.28% | 18.81% | 43.46% | 19.15% | -0.34% | The all-cell score is dominated by labels absent from the training fold; expand or harmonize the label ontology before claiming species transfer. |
| Brassica rapa | mixed_transfer | 256 | 93.75% | 27.73% | 29.58% | 25.39% | 2.34% | The species is partially supported, but accuracy and macro-F1 should be interpreted as a mixed open-set transfer result. |
| Catharanthus roseus | covered_label_transfer_failure | 256 | 94.14% | 0.39% | 0.41% | 0.00% | 0.39% | Most labels are evaluable, but the transferred representation fails on the covered labels; prioritize species-specific adapter or tissue-context calibration. |
| Eutrema salsugineum | strong_transfer | 62 | 100.00% | 98.39% | 98.39% | 98.39% | 0.00% | The species provides positive evidence that the v9 representation can transfer when label coverage and tissue context are favorable. |
| Fragaria vesca | regression_vs_v3 | 256 | 62.89% | 15.62% | 24.84% | 28.91% | -13.28% | The frozen v9 candidate underperforms v3 on this held-out species; keep it visible as a revision target. |
| Gossypium bickii | mixed_transfer | 256 | 90.62% | 36.33% | 40.09% | 41.02% | -4.69% | The species is partially supported, but accuracy and macro-F1 should be interpreted as a mixed open-set transfer result. |
| Gossypium hirsutum | ontology_gap_no_label_overlap | 256 | 0.00% | 0.00% | - | 0.00% | 0.00% | No test labels are present in the training fold; this species requires label ontology mapping before accuracy is interpretable. |
| Triticum aestivum | strong_transfer | 256 | 100.00% | 86.72% | 86.72% | 0.00% | 86.72% | The species provides positive evidence that the v9 representation can transfer when label coverage and tissue context are favorable. |

## Reviewer-Safe Interpretation

The normalized species-holdout benchmark contains two distinct sources of error. First, 1,748 of 3,964 held-out cells have reference labels absent from the corresponding training fold; these cells are counted as errors in the all-cell open-set metric. Second, among the 2,216 cells whose labels are evaluable, several species remain difficult, especially Catharanthus roseus. This explains why the correct headline is 23.54% all-cell accuracy at 55.90% coverage, while 42.10% is only a conditional known-label value.

## Revision Priorities

- **P1 Catharanthus roseus.** High coverage but near-zero known-label accuracy indicates a genuine transfer failure rather than only open-set label absence. Review tissue/label mapping and add a species- or tissue-aware adapter calibration experiment.
- **P1 Gossypium hirsutum.** No label overlap makes the species unassessable under the current ontology. Map the held-out label into the shared plant cell-state ontology or add a comparable training label.
- **P2 Arabidopsis thaliana.** This species dominates the test set and has low coverage after species holdout. Separate ontology coverage from representation error and report open-set cells explicitly.
- **P2 Fragaria vesca and Gossypium bickii.** v9 regresses against v3 on these species despite moderate-to-high coverage. Inspect label harmonization and adapter selection before claiming broad species gains.

## Files

- Source v9 benchmark: `release_metadata/v9_benchmarks/v9_lora_cross_species_benchmark.json`
- Source v3 benchmark: `release_metadata/v9_benchmarks/v3_on_v9_shared_subset_cross_species_benchmark.json`
- Machine-readable audit: `release_metadata/species_holdout_failure_audit_v9.json`
- Per-species table: `release_metadata/species_holdout_failure_audit_v9.tsv`
