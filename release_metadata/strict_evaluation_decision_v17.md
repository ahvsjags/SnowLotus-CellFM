# Plant-CellFM strict cross-species evaluation decision (v17)

## Decision

The primary strict cross-species result is `revision_v17_nested_metadata_gate.json`.
It reports **39.96% all-cell accuracy**, **71.48% known-label accuracy**, **0.2817
known-label macro-F1** and **55.90% train-label coverage** on 3,964 matched cells
from eight canonical species groups.

For every outer held-out species, v17 selects its metadata-conditioned transfer
rule exclusively by leave-one-source-species-out validation within the remaining
training species. Target-cell labels are not used to fit the selector, estimate a
prior, train a classifier or choose an operating point.

## Reporting hierarchy

| Result | Protocol role | All-cell accuracy | Publication use |
| --- | --- | ---: | --- |
| Centroid | matched strict baseline | 23.64% | completed baseline |
| v10 expression STC | matched strict baseline | 30.10% | completed baseline |
| v16 nested learned probe | nested classifier ablation | 35.32% | negative ablation / Supplementary |
| v17 nested metadata gate | strict primary estimator | 39.96% | main text strict result |
| v14 global metadata gate | globally selected sensitivity | 42.36% | exploratory sensitivity only |

The v14 value must not appear in a title, abstract, graphical abstract, main
conclusion or headline strict-comparison bar as the final model score. Its method
class was selected after inspecting the full set of held-out species folds. It
remains useful as an explicitly labelled sensitivity analysis, including in the
source-data package, but not as the final held-out estimator.

## Interpretation boundary

The all-cell denominator includes the 1,748 target cells whose exact labels are
absent from their outer training fold. `Gossypium hirsutum` has zero exact-label
coverage in this matched panel. Accordingly, v17 supports the claim of a
reproducible, metadata-conditioned **open-set transfer framework**, not universal
high-accuracy annotation for every plant species or cell state.

## Immutable inputs

| File | SHA256 |
| --- | --- |
| `figure_data/v2_embeddings/embeddings.npy` | `f1d7df09756da9322a45fb270aa110f92a457ff160e90c002ed5cf2a7c2dd013` |
| `figure_data/v2_embeddings/predictions.csv` | `878b413e372cc07f6cb5d84d628528ed66c3438acd22d5bc99c0f61e16b057bb` |
| `figure_data/v2_embeddings/v16_nested_strict_predictions.csv` | `a5d41d6a1bed41e1cab926e45c65da3bc498d486195d2c8fa2170420290bf8b3` |
| `figure_data/v2_embeddings/v17_nested_strict_predictions.csv` | `d3a6ce08f0f6eef814beaca4fd2125260125be43b7b11d28fa04c6d1e1bdca53d` |
| `release_metadata/revision_v14_context_stc_benchmark.json` | `67876bcf2da596cbbda6411808baf715e19adf0dc76d3df12e4b75635e2e6397` |
| `release_metadata/revision_v16_nested_hierarchical_probe.json` | `fc2bfe1ae7bdcc90c82561c5671f540b6d00d0146c8df3dfa1a4737b423daeff` |
| `release_metadata/revision_v17_nested_metadata_gate.json` | `349161e42cff619b5aed2bba6e73eacf04cc5706549ef60e26b73ea08a46e5bb` |

## Reproduction

```powershell
python scripts/run_revision_v16_nested_hierarchical_probe.py `
  --embeddings figure_data/v2_embeddings/embeddings.npy `
  --obs-tsv release_metadata/species_ontology_obs_labels_with_ids_v9.tsv `
  --predictions-csv figure_data/v2_embeddings/predictions.csv `
  --output-json release_metadata/revision_v16_nested_hierarchical_probe.json `
  --output-md release_metadata/revision_v16_nested_hierarchical_probe.md `
  --predictions-output figure_data/v2_embeddings/v16_nested_strict_predictions.csv

python scripts/run_revision_v17_nested_metadata_gate.py `
  --embeddings figure_data/v2_embeddings/embeddings.npy `
  --obs-tsv release_metadata/species_ontology_obs_labels_with_ids_v9.tsv `
  --predictions-csv figure_data/v2_embeddings/predictions.csv `
  --output-json release_metadata/revision_v17_nested_metadata_gate.json `
  --output-md release_metadata/revision_v17_nested_metadata_gate.md `
  --predictions-output figure_data/v2_embeddings/v17_nested_strict_predictions.csv
```
