# Plant-CellFM v9 Submission Highlights

Generated: `2026-07-30 21:53 Asia/Shanghai`

## Proposed Title

Plant-CellFM: a reproducible foundation-model and adapter framework for plant single-cell annotation

## Highlights

- Plant-general foundation model for single-cell and single-nucleus plant expression annotation.
- All-plant adapter framework with 24 adapter entries and universal fallback resolution.
- Strict grouped evaluation separates leave-dataset, leave-sample and open-set leave-species transfer.
- Frozen v9 improves over frozen v3 on the shared-gene benchmark in leave-dataset-out and leave-sample-out protocols.
- Plant cell-state ontology diagnostics separate actionable labels from unknown or unannotated states.
- Arabidopsis root case links adapter resolution, hierarchical annotation and marker-candidate mining.

## Headline Numbers

- Leave-dataset-out all-cell accuracy: v9 0.4490; v3 0.2021.
- Leave-sample-out all-cell accuracy: v9 0.6200; v3 0.4155.
- Normalized leave-species-out all-cell accuracy: 0.2354.
- Normalized leave-species-out coverage: 0.5590.
- Normalized leave-species-out known-label accuracy: 0.4210.
- Ontology-actionable coverage: 74.44%.
- Ontology-actionable all-cell accuracy: 14.97%.
- Ontology-label known-label accuracy: 20.12%.
- Ontology-label macro-F1: 0.1395.
- Adapter entries: 24.
- Arabidopsis root marker-candidate rows: 260.
- Arabidopsis root cell states: 13.
- Arabidopsis root identity states: 10.

## Claim-Safe Position

Use Plant-CellFM v9 as a plant-general reproducible method and resource. State leave-species-out performance as open-set transfer evidence, not universal high-accuracy annotation.
