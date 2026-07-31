# GSE152766 Blind External Root Inference Audit

## Scope

- GEO input: `GSE152766` / `GSM4626007`; `6566` cells and `25171` TAIR10 genes.
- Frozen-v4 corpus-profile membership: `False`. This is only a statement about the documented frozen v4 dataset list.
- Execution: checkpoint epoch `4`, `256`-dimensional embedding, `cuda (NVIDIA GeForce RTX 4070 Laptop GPU at execution)`.
- Predicted states: `13`; no cell-type labels were present in the downloaded input.

## Evidence Boundary

- This is blinded external inference, not an external accuracy estimate: the input matrix has no expert cell-type labels.
- It is not a numerical comparison with scPlantLLM, scPlantAnnotate or any other tool.
- The marker test is deliberately restricted to six loci fixed from primary literature before external-expression lookup. It tests coherence of model-predicted groups with expression, not causal biology or experimental validation.

## Prediction Distribution

| Predicted state | Cells | Fraction | Mean confidence | Median confidence |
| --- | ---: | ---: | ---: | ---: |
| Lateral root cap | 2177 | 0.332 | 0.860 | 0.956 |
| Root cortex | 1364 | 0.208 | 0.855 | 0.939 |
| Root stele | 605 | 0.092 | 0.885 | 0.951 |
| Unknow | 530 | 0.081 | 0.753 | 0.789 |
| Root cap | 451 | 0.069 | 0.788 | 0.858 |
| Non-hair | 428 | 0.065 | 0.736 | 0.772 |
| Root endodermis | 321 | 0.049 | 0.690 | 0.695 |
| Xylem | 191 | 0.029 | 0.733 | 0.834 |
| S phase | 178 | 0.027 | 0.888 | 0.953 |
| Root hair | 168 | 0.026 | 0.854 | 0.953 |
| Columella root cap | 127 | 0.019 | 0.587 | 0.575 |
| G1/G0 phase | 22 | 0.003 | 0.501 | 0.482 |
| Phloem | 4 | 0.001 | 0.718 | 0.852 |

## Predefined Marker Coherence

- Expected group had highest mean marker expression: **5/6** anchors.
- Expected group had highest marker detection fraction: **5/6** anchors.

| Expected model state | Marker | Locus | n predicted cells | Mean-expression delta | Detection delta | Mean rank | Detection rank |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Root hair | COBL9 | AT5G49270 | 168 | 0.714 | 0.622 | 1 | 1 |
| Non-hair | WER | AT5G14750 | 428 | 0.018 | 0.077 | 4 | 3 |
| Non-hair | GL2 | AT1G79840 | 428 | 0.131 | 0.183 | 1 | 1 |
| Root endodermis | CASP1 | AT2G36100 | 321 | 0.082 | 0.021 | 1 | 1 |
| Phloem | APL | AT1G79430 | 4 | 1.007 | 0.747 | 1 | 1 |
| Xylem | MYB46 | AT5G12870 | 191 | 0.025 | 0.023 | 1 | 1 |

## Primary Sources

- `jean_baptiste_2019`: Jean-Baptiste et al. Dynamics of Gene Expression in Single Root Cells of Arabidopsis thaliana. Plant Cell 31, 993-1011 (2019). https://pmc.ncbi.nlm.nih.gov/articles/PMC8516002/
- `shahan_2022`: Shahan et al. A single cell Arabidopsis root atlas reveals developmental trajectories in wild-type and cell identity mutants. Developmental Cell 57, 543-560.e9 (2022). https://doi.org/10.1016/j.devcel.2022.01.008
