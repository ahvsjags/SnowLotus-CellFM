# Saussurea Public Data Discovery

- Databases searched: `5`
- Query executions: `25`
- Unique hits: `779`
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

- `sra` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`7293626`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `sra` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`7293626`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `bioproject` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`98593`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `bioproject` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`98593`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `gds` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`461688`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `gds` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`461688`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `pubmed` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`98108`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `pubmed` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`98108`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `pmc` `"天山雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`565318`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.
- `pmc` `"雪莲" AND (单细胞 OR 单核 OR 转录组 OR "10x" OR RNA-seq)` count=`565318`: NCBI returned an implausibly broad count for a Chinese-language query; treat this search as a sanity check only, not as accession-level evidence.

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
| sra | `SRR39835773` | False | False | lncRNA-Seq of Tinospora sinensis: leaf tissue | https://www.ncbi.nlm.nih.gov/sra/SRR39835773 |
| sra | `SRR39835759` | False | False | GB1275+Lip@V treatment group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835759 |
| sra | `SRR39835760` | False | False | GB1275+Lip@V treatment group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835760 |
| sra | `SRR39835761` | False | False | GB1275+Lip@V treatment group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835761 |
| sra | `SRR39835762` | False | False | GB1275+Lip@V treatment group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835762 |
| sra | `SRR39835763` | False | False | GB1275+Lip@V treatment group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835763 |
| sra | `SRR39835764` | False | False | Blank group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835764 |
| sra | `SRR39835765` | False | False | Blank group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835765 |
| sra | `SRR39835766` | False | False | Blank group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835766 |
| sra | `SRR39835767` | False | False | Blank group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835767 |
| sra | `SRR39835768` | False | False | Blank group mouse Panc02 pancreatic tumor RNA-seq transcriptome | https://www.ncbi.nlm.nih.gov/sra/SRR39835768 |
| sra | `DRR977557` | False | False | zmed3-Trans-1 (CRX1773645) | https://www.ncbi.nlm.nih.gov/sra/DRR977557 |
| sra | `SRR39834754` | False | False | Liver RNA-seq of high-fat diet, biological replicate 5 | https://www.ncbi.nlm.nih.gov/sra/SRR39834754 |
| sra | `SRR39834755` | False | False | Liver RNA-seq of high-fat diet, biological replicate 4 | https://www.ncbi.nlm.nih.gov/sra/SRR39834755 |
| sra | `SRR39834756` | False | False | Liver RNA-seq of high-fat diet, biological replicate 3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834756 |
| sra | `SRR39834757` | False | False | Liver RNA-seq of high-fat diet, biological replicate 2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834757 |
| sra | `SRR39834758` | False | False | Liver RNA-seq of high-fat diet, biological replicate 1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834758 |
| sra | `SRR39834759` | False | False | Liver RNA-seq of low-fat diet, biological replicate 5 | https://www.ncbi.nlm.nih.gov/sra/SRR39834759 |
| sra | `SRR39834760` | False | False | Liver RNA-seq of low-fat diet, biological replicate 4 | https://www.ncbi.nlm.nih.gov/sra/SRR39834760 |
| sra | `SRR39834761` | False | False | Liver RNA-seq of low-fat diet, biological replicate 3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834761 |
| sra | `SRR39834762` | False | False | Liver RNA-seq of high-fat diet with wheat resistant starch, biological replicate 5 | https://www.ncbi.nlm.nih.gov/sra/SRR39834762 |
| sra | `SRR39834763` | False | False | Liver RNA-seq of high-fat diet with wheat resistant starch, biological replicate 4 | https://www.ncbi.nlm.nih.gov/sra/SRR39834763 |
| sra | `SRR39834764` | False | False | Liver RNA-seq of high-fat diet with wheat resistant starch, biological replicate 3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834764 |
| sra | `SRR39834765` | False | False | Liver RNA-seq of high-fat diet with wheat resistant starch, biological replicate 2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834765 |
| sra | `SRR39834766` | False | False | Liver RNA-seq of high-fat diet with wheat resistant starch, biological replicate 1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834766 |
| sra | `SRR39834767` | False | False | Liver RNA-seq of high-fat diet with maize resistant starch, biological replicate 5 | https://www.ncbi.nlm.nih.gov/sra/SRR39834767 |
| sra | `SRR39834768` | False | False | Liver RNA-seq of high-fat diet with maize resistant starch, biological replicate 4 | https://www.ncbi.nlm.nih.gov/sra/SRR39834768 |
| sra | `SRR39834769` | False | False | Liver RNA-seq of high-fat diet with maize resistant starch, biological replicate 3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834769 |
| sra | `SRR39834770` | False | False | Liver RNA-seq of high-fat diet with maize resistant starch, biological replicate 2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834770 |
| sra | `SRR39834771` | False | False | Liver RNA-seq of high-fat diet with maize resistant starch, biological replicate 1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834771 |
| sra | `SRR39834772` | False | False | Liver RNA-seq of low-fat diet, biological replicate 2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834772 |
| sra | `SRR39834773` | False | False | Liver RNA-seq of low-fat diet, biological replicate 1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834773 |
| sra | `SRR39834747` | False | False | Transcriptome sequencing of Escherichia coli | https://www.ncbi.nlm.nih.gov/sra/SRR39834747 |
| sra | `SRR39834748` | False | False | Transcriptome sequencing of Escherichia coli | https://www.ncbi.nlm.nih.gov/sra/SRR39834748 |
| sra | `SRR39834749` | False | False | Transcriptome sequencing of Escherichia coli | https://www.ncbi.nlm.nih.gov/sra/SRR39834749 |
| sra | `SRR39834750` | False | False | Transcriptome sequencing of Escherichia coli | https://www.ncbi.nlm.nih.gov/sra/SRR39834750 |
| sra | `SRR39834751` | False | False | Transcriptome sequencing of Escherichia coli | https://www.ncbi.nlm.nih.gov/sra/SRR39834751 |
| sra | `SRR39834752` | False | False | Transcriptome sequencing of Escherichia coli | https://www.ncbi.nlm.nih.gov/sra/SRR39834752 |
| sra | `SRR39834741` | True | False | RNA-seq of mus musculus:sample 6 | https://www.ncbi.nlm.nih.gov/sra/SRR39834741 |
| sra | `SRR39834742` | True | False | RNA-seq of mus musculus:sample 5 | https://www.ncbi.nlm.nih.gov/sra/SRR39834742 |
| sra | `SRR39834743` | True | False | RNA-seq of mus musculus:sample 4 | https://www.ncbi.nlm.nih.gov/sra/SRR39834743 |
| sra | `SRR39834744` | True | False | RNA-seq of mus musculus:sample 3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834744 |
| sra | `SRR39834745` | True | False | RNA-seq of mus musculus:sample 2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834745 |
| sra | `SRR39834746` | True | False | RNA-seq of mus musculus:sample 1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834746 |
| sra | `SRR39834721` | False | False | hxk2 ko_TCM+cAMP_Rep3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834721 |
| sra | `SRR39834722` | False | False | hxk2 ko_TCM+cAMP_Rep2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834722 |
| sra | `SRR39834723` | False | False | hxk2 ko_TCM+cAMP_Rep1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834723 |
| sra | `SRR39834724` | False | False | hxk2 ko_TCM_Rep3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834724 |
| sra | `SRR39834725` | False | False | hxk2 ko_TCM_Rep2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834725 |
| sra | `SRR39834726` | False | False | hxk2 ko_TCM_Rep1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834726 |
| sra | `SRR39834727` | False | False | H99_TCM_Rep4 | https://www.ncbi.nlm.nih.gov/sra/SRR39834727 |
| sra | `SRR39834728` | False | False | H99_TCM_Rep3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834728 |
| sra | `SRR39834729` | False | False | H99_TCM_Rep2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834729 |
| sra | `SRR39834730` | False | False | H99_TCM_Rep1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834730 |
| sra | `SRR39834481` | False | False | microbical community | https://www.ncbi.nlm.nih.gov/sra/SRR39834481 |
| sra | `SRR39834482` | False | False | microbical community | https://www.ncbi.nlm.nih.gov/sra/SRR39834482 |
| sra | `SRR39834457` | False | False | KpR33_1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834457 |
| sra | `SRR39834458` | False | False | KpR32_3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834458 |
| sra | `SRR39834459` | False | False | KpR32_2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834459 |
| sra | `SRR39834460` | False | False | KpR32_1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834460 |
| sra | `SRR39834461` | False | False | KpR30_3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834461 |
| sra | `SRR39834462` | False | False | KpR30_2 | https://www.ncbi.nlm.nih.gov/sra/SRR39834462 |
| sra | `SRR39834463` | False | False | KpR30_1 | https://www.ncbi.nlm.nih.gov/sra/SRR39834463 |
| sra | `SRR39834464` | False | False | Kp30457_3 | https://www.ncbi.nlm.nih.gov/sra/SRR39834464 |
