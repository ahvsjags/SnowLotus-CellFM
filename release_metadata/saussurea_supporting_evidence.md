# Saussurea Supporting Evidence

- Supporting Saussurea evidence layers: `9`
- Layers with SRA runinfo: `6`
- Source pages archived: `9`
- SRA runs indexed: `51`
- Total indexed SRA size: `527756.000 MB`

This file documents public Snow Lotus and close-genus evidence used for gene-vocabulary, orthology, stress-response, and secondary-metabolism context. It does not replace the required primary `data/saussurea_involucrata.h5ad` single-cell dataset.

| Dataset | Species | Scope | Type | Accession | Runinfo runs | Strategies | Sources | Source page | Role |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| saussurea_bulk_transcriptome | Saussurea involucrata | whole sample | bulk RNA-seq | PRJNA169171 / SRR516284 | 3 | RNA-Seq | TRANSCRIPTOMIC | True | Snow lotus gene vocabulary, ortholog mapping, and secondary-metabolism context when no public scRNA exists. |
| saussurea_genome_reference | Saussurea involucrata | genome and gene annotation | reference genome | PRJNA991078 | 0 |  |  | True | Genome-backed Snow Lotus gene vocabulary, ortholog mapping, and marker naming reference. |
| saussurea_low_pressure | Saussurea involucrata | leaf low-pressure treatment | bulk RNA-seq | PRJNA1218246 | 6 | RNA-Seq | TRANSCRIPTOMIC | True | High-altitude/low-pressure adaptation evidence for top-journal biological validation. |
| saussurea_low_temperature | Saussurea involucrata | seedlings under 20C, 4C, and 4C/0C day-night treatments | bulk RNA-seq | PRJNA1033840 | 9 | RNA-Seq | TRANSCRIPTOMIC | True | Low-temperature stress transcriptome evidence for dehydrins, cold response genes, and Snow Lotus alpine adaptation marker prioritization. |
| saussurea_raw_sequence_reads | Saussurea involucrata | raw sequence read archive | raw sequence reads | PRJNA387384 | 0 |  |  | True | Additional public Snow Lotus sequence archive discovered in NCBI/ENA aggregation; keep as secondary accession evidence after runinfo validation. |
| saussurea_medusa_wgs | Saussurea medusa | whole genome sequencing | reference genome | PRJNA1278884 | 14 | RNA-Seq;WGS | GENOMIC;TRANSCRIPTOMIC | True | Discovered NCBI/SRA Saussurea medusa HiFi genome sequencing; close-genus evidence for ortholog and alpine adaptation context. |
| saussurea_hypsipeta_leaf_rna | Saussurea hypsipeta | leaf RNA-seq | transcriptome | PRJNA1293189 | 16 | Hi-C;RNA-Seq;WGS | GENOMIC;TRANSCRIPTOMIC | True | Discovered NCBI/SRA Saussurea hypsipeta leaf RNA-seq; close-genus expression evidence for vocabulary and stress/metabolism context. |
| saussurea_lyrata_hic | Saussurea lyrata | genome Hi-C | reference genome | PRJNA1355060 | 3 | Hi-C;RNA-Seq;WGS | GENOMIC;TRANSCRIPTOMIC | True | Discovered NCBI/SRA Saussurea lyrata Hi-C genome data; close-genus genome-structure support for ortholog mapping context. |
| saussurea_multicellular_spheroid_single_cell_report | Saussurea involucrata | multicellular spheroids | single-cell transcriptomics/metabolomics literature | PMID:41668397 / DOI:10.1002/adhm.202504623 | 0 |  |  | True | Reports Snow Lotus multicellular spheroid single-cell transcriptomics and bioactive-metabolite evidence; data are request-only, so use as literature evidence and a data-acquisition target rather than a training corpus. |
