# GSE270140 Secondary-Root Reference Stress Audit

## Scope and Boundary

- Author-labelled input: `11760` cells, `22506` genes and `14` raw annotations from GSE270140/GSM8335426.
- The frozen mapping is applied before inspecting predictions. It maps compatible vascular states to `Phloem`, `Xylem` or `Root stele`; periderm, myrosin idioblast and lateral-root-primordium states stay explicitly out of the frozen output ontology.
- GSE270140 is present in historical project manifest registration. This is therefore recorded as a provenance-aware stress case, not promoted as an unqualified unseen-data benchmark.

## Diagnostic Result

- Shared-state denominator: `9481` cells (80.6% of the complete input).
- Shared-state accuracy / macro-F1: **0.0160 / 0.0130**.
- Ontology-external states: `2279` cells; `Unknow` rejection rate **79.6%**.
- Mapped shared states also predicted as `Unknow`: **85.2%**.

## Interpretation

- The frozen root checkpoint does not recover secondary-growth vascular labels sufficiently for a positive external-accuracy claim.
- Its partial `Unknow` response demonstrates a detectable open-set signal, but the high unknown rate on compatible vascular states shows that a secondary-root adapter and a broader developmental ontology are required before this dataset can be used as a validation win.
- This audit is retained to prevent accidental promotion of label-free marker coherence into a substitute for expert-labelled accuracy.

## Frozen Mapping and Per-label Audit

| Author annotation | Frozen model state | Tier | Cells | Unknown fraction | Mean confidence | Recall | F1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Mature phloem parenchyma | Phloem | shared_state | 3306 | 0.8339 | 0.8464 | 0.0000 | 0.0000 |
| Periderm | not_in_frozen_ontology | no_direct_model_state | 2156 | 0.8001 | 0.8670 |  |  |
| Vascular cambium | Root stele | shared_state | 1668 | 0.7608 | 0.8303 | 0.0851 | 0.1499 |
| Conductive phloem parenchyma | Phloem | shared_state | 1217 | 0.9326 | 0.9287 | 0.0000 | 0.0000 |
| Maturing xylem parenchyma | Xylem | shared_state | 795 | 0.9044 | 0.8785 | 0.0033 | 0.0063 |
| Young xylem parenchyma | Xylem | shared_state | 735 | 0.9483 | 0.9391 | 0.0033 | 0.0063 |
| Fiber | Xylem | shared_state | 664 | 0.8735 | 0.8482 | 0.0033 | 0.0063 |
| Mature xylem parenchyma | Xylem | shared_state | 661 | 0.9138 | 0.9086 | 0.0033 | 0.0063 |
| Vessel identity cell/expanding vessel | Xylem | shared_state | 147 | 0.7959 | 0.8130 | 0.0033 | 0.0063 |
| Companion cell | Phloem | shared_state | 127 | 0.7874 | 0.8492 | 0.0000 | 0.0000 |
| Sieve element | Phloem | shared_state | 104 | 0.6923 | 0.8717 | 0.0000 | 0.0000 |
| Myrosin idioblasts | not_in_frozen_ontology | no_direct_model_state | 84 | 0.7262 | 0.7741 |  |  |
| Late differentiating vessel | Xylem | shared_state | 57 | 0.5088 | 0.7894 | 0.0033 | 0.0063 |
| Lateral root primordium/meristem | not_in_frozen_ontology | no_direct_model_state | 39 | 0.7179 | 0.7983 |  |  |
