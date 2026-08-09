# PlantCell-Agent replay v1

The report separates frozen direct inference from Agent acceptance and review. Missing local inputs are not assigned metrics.

| Case | Status | Route | Primary specialist | Contract | Direct accuracy | Agent accuracy | Agent coverage | Review fraction | Repeatability |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Strict held-out species | NOT_REPLAYED_INPUT_MISSING | - | - | - | - | - | - | - | - |
| Arabidopsis secondary root | auto_annotation_pass | registered_adapter | specialist.adapter.plant_arabidopsis_thaliana | passed | 0.8664 | 0.8664 | 0.8417 | 0.1583 | exact_match |
| Wheat non-overlap benchmark | manual_review_required | registered_adapter | specialist.adapter.plant_triticum_aestivum | passed | 0.6471 | 0.6471 | 0.4136 | 0.5864 | exact_match |
| Sorghum root atlas | manual_review_required | ortholog_stc | specialist.orthology_transfer | passed | 0.8219 | 0.8219 | 0.7758 | 0.2242 | exact_match |

## Locked interpretation

- `all_cell_accuracy` uses the complete matched denominator.
- `coverage` is the fraction accepted by the Agent confidence/open-set policy.
- `accepted_cell_accuracy` is reported separately and is never substituted for all-cell accuracy.
- A route mismatch or species metadata mismatch remains visible in the JSON output.
- The strict case is labelled `raw_h5ad_end_to_end` only when the manifest H5AD exists and is directly passed to the Agent; otherwise it remains `locked_bundle_replay` with no inferred raw-input metrics.
- Specialist contract status is reported per end-to-end case; a failed contract activates Review Agent and preserves direct predictions.
