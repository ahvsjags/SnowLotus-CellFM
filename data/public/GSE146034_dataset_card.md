# GSE146034 dataset card

## Source and scope

This asset is the processed single-cell RNA-seq matrix from NCBI GEO series
GSE146034, ``Single-cell transcriptomic analysis of rice root tips``. The
series contains two Oryza sativa root-tip samples: 93-11 (Indica) and
Nipponbare (Japonica). The official GEO record reports more than 20,000 cells,
5-mm root tips from 3-day-old seedlings, protoplast preparation, and the
CellRanger-generated MTX/TSV files.

Official records:

- Series: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE146034
- GSM4363200: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4363200
- GSM4363201: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4363201
- Publication PMID: 33352304
- Raw supplementary archive: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE146nnn/GSE146034/suppl/GSE146034_RAW.tar

## Reproducible local assets

The raw archive is stored at
``data/public/GSE146034_raw_tar/GSE146034_RAW.tar`` and has 206,387,200 bytes
with SHA256
``e48d08ddd271c644e4430b62b04b97b26d771da3dba757d0d2edce8c5e82bb8f``.
The two per-sample sparse NPZ files are listed in
``data/corpus_manifest.gse146034_samples.tsv``. The merged corpus is
``data/plant_foundation_corpus_gse146034.npz`` with 23,532 cells, 43,311 genes,
and 63,856,201 non-zero entries before the standard gene-feature truncation
used by the smoke configuration.

Sample-level provenance is in
``data/public/GSE146034_sample_metadata.tsv`` and has been injected into the
merged NPZ as fields such as ``cultivar``, ``stage``, ``geo_accession``,
``sra_accession``, and ``reference_pmid``.

## Model-use contract

This matrix is an unlabeled public pretraining and embedding asset. The
``cell_type`` and ``cell_type_coarse`` fields intentionally remain
``unannotated_root_tip``; the one-epoch local run is a compute and I/O smoke
test, not a cell-type accuracy claim. Supervised annotation metrics must be
computed only after adding independent, cell-type-labeled plant datasets and
using sample- or study-level held-out splits.
