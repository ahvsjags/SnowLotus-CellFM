# Arabidopsis Root Literature Anchor For Plant-CellFM v9

Generated: 2026-07-30 17:36 Asia/Shanghai

This file strengthens the Plant-CellFM v9 Arabidopsis root case by connecting the model-derived cell-identity case to established Arabidopsis root single-cell literature. It is not a wet-lab validation claim. The marker candidates in `release_metadata/plant_biology_case_study_v9.md` remain model-derived candidates; the literature anchors below support the biological plausibility of the reported root identity taxonomy and identify canonical marker genes that can be used in a later manual marker-overlap or reporter-line validation.

## Literature-Supported Cell Identity Taxonomy

| Plant-CellFM case label | Literature-aligned identity | Literature support |
| --- | --- | --- |
| Columella root cap | root cap / columella branch | Shahan et al. report root-cap branches containing lateral root cap and columella cells in an organ-scale Arabidopsis root atlas. |
| Lateral root cap | lateral root cap | Shahan et al. separate lateral root cap and columella cells within the root-cap lineage. |
| Root cap | root cap | Ryu et al. report root-cap cell transcriptomes among major Arabidopsis root tissue types. |
| Root hair | trichoblast / root-hair epidermis | Ryu et al. and Shahan et al. annotate root-hair/trichoblast epidermal populations; Jean-Baptiste et al. use root-hair markers such as COBL9. |
| Non-hair | atrichoblast / non-hair epidermis | Ryu et al. and Shahan et al. annotate non-hair/atrichoblast epidermal populations. |
| Root cortex | cortex / ground tissue | Jean-Baptiste et al. assign cortex cells as a major group; Shahan et al. place cortex together with endodermis in the ground-tissue branch. |
| Root endodermis | endodermis / ground tissue | Jean-Baptiste et al. cite SCARECROW as an endodermis marker; Shahan et al. use SCR, MYB36 and CASP1 profiles for endodermis. |
| Root stele | stele / vascular cylinder | Ryu et al. and Jean-Baptiste et al. annotate stele cells; Shahan et al. further split stele into phloem, xylem, procambium and pericycle. |
| Phloem | phloem within stele | Jean-Baptiste et al. cite APL and SUC2 as phloem-related stele markers; Shahan et al. distinguish phloem subtypes. |
| Xylem | xylem within stele | Jean-Baptiste et al. cite MYB46 as xylem-specific within stele; Shahan et al. distinguish xylem subtypes. |

## Canonical Marker Anchors For Later Manual Validation

| Identity | Canonical literature markers or marker families | Use in the current submission |
| --- | --- | --- |
| Root hair / trichoblast | COBL9; root-hair marker sets | Supports biological naming of `Root hair`, not a claim that every top Plant-CellFM candidate is a canonical marker. |
| Non-hair / atrichoblast | WER, GL2 and non-hair marker sets | Supports the epidermal non-hair identity boundary; known heterogeneous expression is acknowledged in the literature. |
| Endodermis | SCR, MYB36, CASP1 | Supports the `Root endodermis` identity and later marker-overlap validation. |
| Cortex | CORTEX / AT1G09750, NPF6.4 / AT3G21670 | Supports the `Root cortex` identity and ground-tissue interpretation. |
| Stele / xylem | MYB46, VND7 and xylem marker sets | Supports vascular subtyping for `Root stele` and `Xylem`. |
| Stele / phloem | APL, SUC2 and phloem marker sets | Supports vascular subtyping for `Phloem`. |
| Root cap / columella / lateral root cap | lateral root cap and columella marker sets from root atlas studies | Supports the separation of root-cap-related Plant-CellFM labels. |

## Source Notes

- Jean-Baptiste et al., "Dynamics of Gene Expression in Single Root Cells of Arabidopsis thaliana", Plant Cell. Public source: `https://pmc.ncbi.nlm.nih.gov/articles/PMC8516002/`.
- Shahan et al., "A single cell Arabidopsis root atlas reveals developmental trajectories in wild-type and cell identity mutants", Developmental Cell. Public source: `https://pmc.ncbi.nlm.nih.gov/articles/PMC9014886/`; DOI route: `https://doi.org/10.1016/j.devcel.2022.01.008`.
- Ryu et al., "Single-Cell RNA Sequencing Resolves Molecular Relationships Among Individual Plant Cells", Plant Physiology. Public source: `https://pmc.ncbi.nlm.nih.gov/articles/PMC6446759/`; DOI: `10.1104/pp.18.01482`.

## Claim-Safe Manuscript Sentence

The Arabidopsis root case uses cell-identity categories that are consistent with established Arabidopsis root single-cell atlases, including root cap/columella, root-hair and non-hair epidermis, cortex, endodermis, stele, phloem and xylem. Plant-CellFM marker candidates should be interpreted as computational candidates aligned to these literature-supported identities, not as wet-lab-validated markers.
