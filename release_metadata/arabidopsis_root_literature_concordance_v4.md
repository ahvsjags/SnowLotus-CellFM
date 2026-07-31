# Arabidopsis Root Literature Concordance Audit

- Predefined canonical anchors: **6**
- Candidate-list cutoff per identity: top **20**
- Matching-identity recovery: **3/6** (50.0%)
- Recovered canonical markers: CASP1, APL, MYB46

## Evidence Boundary

- Canonical loci and cell-identity assignments were fixed from primary literature before inspecting Plant-CellFM candidate ranks.
- A recovered locus demonstrates concordance of a computational candidate program with an established identity marker; an unrecovered locus is not a negative biological result because this audit is limited to the stored top-20 ranking.
- This analysis does not use a new expression matrix, does not test causal function, and does not replace reporter-line or perturbation validation.

## Anchor Lookup

| Plant-CellFM identity | Canonical marker | Locus | Candidate rank | log2 fold-change | Detection delta | Source |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Root hair | COBL9 | AT5G49270 | not in top 20 | - | - | jean_baptiste_2019 |
| Non-hair | WER | AT5G14750 | not in top 20 | - | - | jean_baptiste_2019 |
| Non-hair | GL2 | AT1G79840 | not in top 20 | - | - | jean_baptiste_2019 |
| Root endodermis | CASP1 | AT2G36100 | 7 | 4.256 | 0.563 | shahan_2022 |
| Phloem | APL | AT1G79430 | 4 | 7.071 | 0.360 | jean_baptiste_2019 |
| Xylem | MYB46 | AT5G12870 | 12 | 7.206 | 0.228 | jean_baptiste_2019 |

## Primary Sources

- `jean_baptiste_2019`: Jean-Baptiste et al. Dynamics of Gene Expression in Single Root Cells of Arabidopsis thaliana. Plant Cell (2019). https://pmc.ncbi.nlm.nih.gov/articles/PMC8516002/
- `shahan_2022`: Shahan et al. A single cell Arabidopsis root atlas reveals developmental trajectories in wild-type and cell identity mutants. Developmental Cell (2022). https://pmc.ncbi.nlm.nih.gov/articles/PMC9014886/
