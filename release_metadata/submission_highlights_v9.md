# Plant-CellFM v9 Submission Highlights

Generated: `2026-07-31 02:05 Asia/Shanghai`

## Proposed Title

Plant-CellFM: a reproducible foundation-model and adapter framework for plant single-cell annotation

## Highlights

- Plant-general foundation model for single-cell and single-nucleus plant expression annotation.
- All-plant adapter framework with 24 adapter entries and universal fallback resolution.
- Strict grouped evaluation separates leave-dataset, leave-sample and open-set leave-species transfer.
- Frozen v9 improves over frozen v3 on the shared-gene benchmark in leave-dataset-out and leave-sample-out protocols.
- Plant cell-state ontology diagnostics separate actionable labels from unknown or unannotated states.
- Context-aware zero-shot STC raises strict leave-species all-cell accuracy above 40% without held-out species labels.
- v11 target-species adapter calibration moves the revision cross-species query all-cell metric above 40% with only small labeled support sets.
- Full-vocabulary runtime annotation reaches 66.25% all-cell accuracy on the same aligned cross-species cells.
- Open-set calibration provides a confidence-aware accept/review protocol for high-confidence annotations.
- Arabidopsis root case links adapter resolution, hierarchical annotation and marker-candidate mining.
- Multi-species scPlantDB case broadens the public-data biology demonstration beyond Arabidopsis.

## Headline Numbers

- Leave-dataset-out all-cell accuracy: v9 0.4490; v3 0.2021.
- Leave-sample-out all-cell accuracy: v9 0.6200; v3 0.4155.
- Normalized leave-species-out all-cell accuracy: 0.2354.
- Normalized leave-species-out coverage: 0.5590.
- Normalized leave-species-out known-label accuracy: 0.4210.
- STC leave-species all-cell accuracy: 0.3010.
- v14 context-aware zero-shot STC all-cell accuracy: 0.4236.
- v14 context-aware zero-shot STC known-label accuracy: 0.7577.
- v11 few-shot adapter with 8 random support cells/species: 0.5921 mean query all-cell accuracy.
- v11 few-shot adapter with 16 random support cells/species: 0.6734 mean query all-cell accuracy.
- v11 full-vocabulary runtime-head all-cell accuracy: 0.6625.
- Ontology-actionable coverage: 74.44%.
- Ontology-actionable all-cell accuracy: 14.97%.
- Ontology-label known-label accuracy: 20.12%.
- Ontology-label macro-F1: 0.1395.
- Adapter entries: 24.
- Arabidopsis root marker-candidate rows: 260.
- Arabidopsis root cell states: 13.
- Arabidopsis root identity states: 10.

## Claim-Safe Position

Use Plant-CellFM v9 as a plant-general reproducible method and resource. Report v14 as a context-aware strict zero-shot STC extension at 42.36% all-cell accuracy, while keeping the 55.90% coverage and open-set boundary explicit.
