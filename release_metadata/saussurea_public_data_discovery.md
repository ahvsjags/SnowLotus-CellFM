# Saussurea Public Data Discovery

- Databases searched: `5`
- Query executions: `25`
- Unique hits: `192`
- Primary `Saussurea involucrata` single-cell hits: `0`
- Public Snow Lotus scRNA/snRNA found: `False`
- Literature reports of Snow Lotus single-cell transcriptomics: `1`
- Public downloadable Snow Lotus single-cell matrix found: `False`
- Low-confidence/noisy query executions: `10`
- Query errors: `0`

This automated NCBI pass searches SRA, BioProject, GEO DataSets, PubMed, and PMC for Saussurea/Saussurea involucrata single-cell evidence. It also tracks a 2026 Advanced Healthcare Materials report of single-cell transcriptomics in Saussurea involucrata multicellular spheroids. A zero primary-data hit count plus no public manual matrix means the project should not claim a reusable public Snow Lotus single-cell atlas or train on it yet; genome, bulk transcriptome, literature, and close-genus evidence remain supporting data only.

## Manual Literature Reports

| ID | Evidence | DOI/PMID | Public matrix | Data availability | Use |
| --- | --- | --- | --- | --- | --- |
| saussurea_multicellular_spheroid_single_cell_report | reported single-cell transcriptomics in multicellular spheroids | 10.1002/adhm.202504623 / PMID:41668397 | False | Data are available from the corresponding author upon reasonable request; specific cultivation parameters require an NDA according to the publisher page. | Use as literature evidence and a data-request target only; do not train or benchmark SnowLotus-CellFM on this study until a reusable matrix is obtained. |

## Low-Confidence Query Guard

- `sra` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`7293164`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `sra` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`7293164`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `bioproject` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`98581`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `bioproject` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`98581`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `gds` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`461538`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `gds` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`461538`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `pubmed` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`98078`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `pubmed` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`98078`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `pmc` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`564793`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `pmc` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`564793`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.

## Primary Single-Cell Hits

- None detected in this pass.

## All Hits

| DB | Accession/UID | Single-cell terms | Snow Lotus terms | Title | URL |
| --- | --- | --- | --- | --- | --- |
| sra | `SRR32195153` | False | True | RNA-seq of Saussurea involucrata:hypobaric hypoxic | https://www.ncbi.nlm.nih.gov/sra/SRR32195153 |
| sra | `SRR32195154` | False | True | RNA-seq of Saussurea involucrata:hypobaric hypoxic | https://www.ncbi.nlm.nih.gov/sra/SRR32195154 |
| sra | `SRR32195155` | False | True | RNA-seq of Saussurea involucrata:hypobaric hypoxic | https://www.ncbi.nlm.nih.gov/sra/SRR32195155 |
| sra | `SRR32195156` | False | True | RNA-seq of Saussurea involucrata:normobaric normoxic | https://www.ncbi.nlm.nih.gov/sra/SRR32195156 |
| sra | `SRR32195157` | False | True | RNA-seq of Saussurea involucrata:normobaric normoxic | https://www.ncbi.nlm.nih.gov/sra/SRR32195157 |
| sra | `SRR32195158` | False | True | RNA-seq of Saussurea involucrata:normobaric normoxic | https://www.ncbi.nlm.nih.gov/sra/SRR32195158 |
| sra | `SRR26779311` | False | True | RNA-seq of Saussurea involucrata treated with freezing temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779311 |
| sra | `SRR26779312` | False | True | RNA-seq of Saussurea involucrata treated with freezing temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779312 |
| sra | `SRR26779313` | False | True | RNA-seq of Saussurea involucrata treated with freezing temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779313 |
| sra | `SRR26779314` | False | True | RNA-seq of Saussurea involucrata treated with cold temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779314 |
| sra | `SRR26779315` | False | True | RNA-seq of Saussurea involucrata treated with cold temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779315 |
| sra | `SRR26779316` | False | True | RNA-seq of Saussurea involucrata treated with cold temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779316 |
| sra | `SRR26779317` | False | True | RNA-seq of Saussurea involucrata in room temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779317 |
| sra | `SRR26779318` | False | True | RNA-seq of Saussurea involucrata in room temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779318 |
| sra | `SRR26779319` | False | True | RNA-seq of Saussurea involucrata in room temperature | https://www.ncbi.nlm.nih.gov/sra/SRR26779319 |
| sra | `SRR516284` | False | True | Saussurea involucrata transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR516284 |
| sra | `SRR39832267` | False | False | MCAO/R | https://www.ncbi.nlm.nih.gov/sra/SRR39832267 |
| sra | `SRR39832268` | False | False | Sham | https://www.ncbi.nlm.nih.gov/sra/SRR39832268 |
| sra | `SRR39831972` | False | False | ABC | https://www.ncbi.nlm.nih.gov/sra/SRR39831972 |
| sra | `SRR39831473` | False | False | RNAseq of apple | https://www.ncbi.nlm.nih.gov/sra/SRR39831473 |
| sra | `SRR39831474` | False | False | RNAseq of apple | https://www.ncbi.nlm.nih.gov/sra/SRR39831474 |
| sra | `SRR39831361` | False | False | RNA-seq of Populus ussuriensis Kom. | https://www.ncbi.nlm.nih.gov/sra/SRR39831361 |
| sra | `SRR39831363` | False | False | RNA-seq of Populus ussuriensis Kom. | https://www.ncbi.nlm.nih.gov/sra/SRR39831363 |
| sra | `SRR39831365` | False | False | RNA-seq of Populus ussuriensis Kom. | https://www.ncbi.nlm.nih.gov/sra/SRR39831365 |
| sra | `SRR39831366` | False | False | RNA-seq of Populus ussuriensis Kom. | https://www.ncbi.nlm.nih.gov/sra/SRR39831366 |
| sra | `SRR39831367` | False | False | RNA-seq of Populus ussuriensis Kom. | https://www.ncbi.nlm.nih.gov/sra/SRR39831367 |
| sra | `SRR39831368` | False | False | RNA-seq of Populus ussuriensis Kom. | https://www.ncbi.nlm.nih.gov/sra/SRR39831368 |
| sra | `SRR39831317` | False | False | mazF_BMB171_12h_1 | https://www.ncbi.nlm.nih.gov/sra/SRR39831317 |
| sra | `SRR39831318` | False | False | BMB171_36h_3 | https://www.ncbi.nlm.nih.gov/sra/SRR39831318 |
| sra | `SRR39831319` | False | False | BMB171_36h_2 | https://www.ncbi.nlm.nih.gov/sra/SRR39831319 |
| sra | `SRR39831320` | False | False | BMB171_36h_1 | https://www.ncbi.nlm.nih.gov/sra/SRR39831320 |
| sra | `SRR39831321` | False | False | BMB171_24h_3 | https://www.ncbi.nlm.nih.gov/sra/SRR39831321 |
| sra | `SRR39831322` | False | False | BMB171_24h_2 | https://www.ncbi.nlm.nih.gov/sra/SRR39831322 |
| sra | `SRR39831323` | False | False | BMB171_24h_1 | https://www.ncbi.nlm.nih.gov/sra/SRR39831323 |
| sra | `SRR39831324` | False | False | BMB171_12h_3 | https://www.ncbi.nlm.nih.gov/sra/SRR39831324 |
| sra | `SRR39831325` | False | False | mazF_BMB171_36h_3 | https://www.ncbi.nlm.nih.gov/sra/SRR39831325 |
| bioproject | `1218246` | False | True | Integrated transcriptome and metabolome analysis revealed the low pressure regulation  in Saussurea involucrata leaves | https://www.ncbi.nlm.nih.gov/bioproject/1218246 |
| bioproject | `1033840` | False | True | Transcriptome on Saussurea involucrata in response to low-temperature stress | https://www.ncbi.nlm.nih.gov/bioproject/1033840 |
| bioproject | `387384` | False | True | Saussurea involucrata Raw sequence reads | https://www.ncbi.nlm.nih.gov/bioproject/387384 |
| bioproject | `169171` | False | True | Saussurea involucrata strain:Maxim Transcriptome or Gene expression | https://www.ncbi.nlm.nih.gov/bioproject/169171 |
| bioproject | `1501715` | False | False | Virus detection in a variegated individual of camellia cultivar 'Kumagai' using RNA-Seq | https://www.ncbi.nlm.nih.gov/bioproject/1501715 |
| bioproject | `1501713` | False | False | RNA-seq analysis of oriental tea tortrix | https://www.ncbi.nlm.nih.gov/bioproject/1501713 |
| bioproject | `1501675` | False | False | A Glycolysis-Calcineurin Regulatory Axis Orchestrates Titan Cell Formation in Cryptococcus neoformans (RNA Sequencing) | https://www.ncbi.nlm.nih.gov/bioproject/1501675 |
| bioproject | `1501668` | False | False | Macrotyloma uniflorum Raw sequence reads | https://www.ncbi.nlm.nih.gov/bioproject/1501668 |
| bioproject | `1501659` | False | False | A Glycolysis-Calcineurin Regulatory Axis Orchestrates Titan Cell Formation in Cryptococcus neoformans (RNA-seq) | https://www.ncbi.nlm.nih.gov/bioproject/1501659 |
| bioproject | `1501645` | False | False | RNASEQ | https://www.ncbi.nlm.nih.gov/bioproject/1501645 |
| bioproject | `1501327` | False | False | transcriptomic data of Humicola insolens | https://www.ncbi.nlm.nih.gov/bioproject/1501327 |
| bioproject | `1501257` | False | False | RNA-seq of hPSCs-derived vascular smooth muscle cells | https://www.ncbi.nlm.nih.gov/bioproject/1501257 |
| bioproject | `1500113` | False | False | RNA-seq analysis of BV-2 microglia infected with Streptococcus pneumoniae | https://www.ncbi.nlm.nih.gov/bioproject/1500113 |
| bioproject | `1500105` | False | False | RNA-seq of Arabidopsis thaliana seeds from WT and DREB2G overexpression (OE) lines | https://www.ncbi.nlm.nih.gov/bioproject/1500105 |
| bioproject | `1500094` | False | False | bulk RNA-seq NOHA | https://www.ncbi.nlm.nih.gov/bioproject/1500094 |
| bioproject | `1500080` | False | False | Bumped kinase inhibitor BKI-1708 | https://www.ncbi.nlm.nih.gov/bioproject/1500080 |
| bioproject | `1500078` | True | False | RNA Seq of hMDMs and BLaER1 cells in response to LPS-priming and Candida albicans infection | https://www.ncbi.nlm.nih.gov/bioproject/1500078 |
| bioproject | `1500067` | False | False | To identify circRNAs associated with translating polyribosomes in proliferating C2C12 myoblasts and differentiated C2C12 myotubes, we performed high-throughput RNA sequencing of po | https://www.ncbi.nlm.nih.gov/bioproject/1500067 |
| bioproject | `1500060` | False | False | Transcriptome study raw reads of W. prolifica IICB1 | https://www.ncbi.nlm.nih.gov/bioproject/1500060 |
| bioproject | `1499967` | False | False | Raphanus sativus var. sativus Raw sequence reads | https://www.ncbi.nlm.nih.gov/bioproject/1499967 |
| bioproject | `1499905` | False | False | Transcriptomic analysis of murine mesenteric lymph nodes following STEC infection | https://www.ncbi.nlm.nih.gov/bioproject/1499905 |
| bioproject | `1499904` | False | False | Study on Attractant Activity and Mechanism of 1,8-Cineole against Bactrocera dorsalis | https://www.ncbi.nlm.nih.gov/bioproject/1499904 |
| bioproject | `1499897` | False | False | Integrated Transcriptomic and Metabolomic Dynamics Reveal Mechanisms of Tobacco Resistance to Phytophthora nicotianae | https://www.ncbi.nlm.nih.gov/bioproject/1499897 |
| bioproject | `1499893` | False | False | Tor tambra RNA-seq | https://www.ncbi.nlm.nih.gov/bioproject/1499893 |
| gds | `GSE341280` | False | False | Systematic identification of age-related microbiome metabolites that impact the brain - mouse brain RNA-seq | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341280 |
| gds | `GSE341091` | False | False | total RNA-seq from HG03129 (ENCSR998MYO) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341091 |
| gds | `GSE341090` | False | False | long read RNA-seq from right lung (ENCSR997XFO) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341090 |
| gds | `GSE341089` | False | False | total RNA-seq from GM19449 (ENCSR997LSS) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341089 |
| gds | `GSE341088` | False | False | total RNA-seq from T-helper 1 cell (ENCSR997HFD) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341088 |
| gds | `GSE341087` | False | False | long read RNA-seq from stomach (ENCSR993RKQ) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341087 |
| gds | `GSE341086` | False | False | long read RNA-seq from large intestine (ENCSR992UMK) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341086 |
| gds | `GSE341085` | False | False | total RNA-seq from CD4-positive, alpha-beta T cell (ENCSR992FYQ) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341085 |
| gds | `GSE341084` | False | False | total RNA-seq from T-cell (ENCSR990GHM) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341084 |
| gds | `GSE341083` | False | False | total RNA-seq from GM21775 (ENCSR989SXC) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341083 |
| gds | `GSE341082` | False | False | long read RNA-seq from muscle of arm (ENCSR989PGQ) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341082 |
| gds | `GSE341077` | False | False | total RNA-seq from GM19020 (ENCSR984PRR) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341077 |
| gds | `GSE341076` | False | False | total RNA-seq from CD4-positive, alpha-beta T cell (ENCSR983YCJ) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341076 |
| gds | `GSE341075` | False | False | total RNA-seq from GM19037 (ENCSR983OGO) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341075 |
| gds | `GSE341074` | False | False | total RNA-seq from CD4-positive, alpha-beta T cell (ENCSR982RIX) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341074 |
| gds | `GSE341073` | False | False | total RNA-seq from GM19437 (ENCSR982AOX) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341073 |
| gds | `GSE341071` | False | False | total RNA-seq from HG03369 (ENCSR981CYF) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341071 |
| gds | `GSE341070` | False | False | long read RNA-seq from muscle of leg (ENCSR979UPD) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341070 |
| gds | `GSE341069` | False | False | total RNA-seq from HG03268 (ENCSR979JWV) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341069 |
| gds | `GSE341068` | False | False | total RNA-seq from CD4-positive, alpha-beta T cell (ENCSR979GPU) | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE341068 |
