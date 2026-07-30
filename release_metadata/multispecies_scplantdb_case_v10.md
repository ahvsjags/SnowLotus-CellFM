# Plant-CellFM v10 Multi-Species scPlantDB Biology Case

This report adds an independent, non-Arabidopsis-only public-data biology case to the Plant-CellFM package. It is used as public-data biological evidence and does not replace the frozen v9 performance claims.

## Corpus

| Item | Value |
| --- | ---: |
| Cells | 31503 |
| Genes | 210485 |
| Species | 4 |
| Tissues | 4 |
| Samples | 15 |
| Datasets | 4 |
| Fine cell-type labels | 27 |

## Species And Tissue Coverage

| Species | Cells | Tissues | Cell-type labels | Dominant tissue | Dominant label |
| --- | ---: | ---: | ---: | --- | --- |
| Arabidopsis thaliana | 1206 | 1 | 8 | Root tip | Non-hair |
| Gossypium hirsutum | 18463 | 1 | 4 | Ovule outer integument | Outer pigment layer |
| Oryza sativa | 11443 | 1 | 13 | Pistil | Style |
| Zea mays | 391 | 1 | 5 | Pollen | Unknow |

## Marker-Candidate Examples

| Species | Cell type | n | Top genes | Median score | Median log2FC | Median detection delta |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| Arabidopsis thaliana | G2/M phase | 233 | AT5G37247, AT1G16630, AT1G03780, AT1G49870, AT3G15550 | 16.266 | 16.155 | 0.073 |
| Arabidopsis thaliana | Non-hair | 254 | AT1G36622, AT1G53970, AT1G18020, AT1G74590, AT3G09220 | 14.154 | 13.824 | 0.087 |
| Arabidopsis thaliana | Root endodermis | 218 | AT4G16270, AT5G20270, AthLNC008721, AT1G71740, AT5G51680 | 12.522 | 12.384 | 0.064 |
| Gossypium hirsutum | Epidermis | 5928 | Ghir-A12G002590, Ghir-A10G010670, Ghir-A07G022690, Ghir-A10G024690, Ghir-D10G002610 | 5.884 | 5.700 | 0.082 |
| Gossypium hirsutum | Fiber cell | 1920 | Ghir-D12G017670, Ghir-D12G017660, Ghir-A12G017450, Ghir-A09G012070, Ghir-A05G016240 | 4.805 | 4.469 | 0.257 |
| Gossypium hirsutum | Outer pigment layer | 9183 | Ghir-A04G014810, Ghir-A05G024890, Ghir-A05G007360, Ghir-D12G019530, Ghir-A07G023810 | 4.084 | 3.870 | 0.108 |
| Oryza sativa | Nucellus | 936 | Os01g0205900, Os05g0556800, Os02g0288600, Os07g0578300, Os02g0134700 | 5.359 | 4.886 | 0.166 |
| Oryza sativa | Outer ovary wall | 2295 | Os03g0739700, Os03g0574900, Os12g0132800, LNC-Os11g68360, Os04g0689000 | 5.245 | 5.047 | 0.100 |
| Oryza sativa | Style | 2367 | Os11g0454300, Os05g0408900, Os03g0141200, Os07g0558400, LOC-Os11g41870 | 3.976 | 3.734 | 0.086 |
| Zea mays | G1/S phase | 97 | Zm00001d012015, Zm00001d031732, Zm00001d036977, Zm00001d031526, Zm00001d024004 | 10.549 | 10.405 | 0.067 |
| Zea mays | S phase | 77 | Zm00001d008222, Zm00001d038060, Zm00001d025414, Zm00001d051817, Zm00001d025319 | 16.769 | 16.665 | 0.065 |
| Zea mays | Unknow | 105 | Zm00001d018579, Zm00001d017647, Zm00001d017735, Zm00001d044585, Zm00001d026961 | 11.466 | 11.212 | 0.076 |

## Interpretation

The case broadens the biological demonstration beyond the Arabidopsis root figure. It shows that the same continuation machinery can organize public data from several plant species, recover species/tissue/cell-type structure and produce marker-candidate tables. The results are computational candidates and should be used as a second public-data biology case, not as wet-lab validation.
