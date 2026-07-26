# Saussurea Data Request Package

- Request candidates: `1`
- Package ready: `True`
- Public downloadable matrix already found: `False`
- Saussurea h5ad contract ready: `False`

This package converts request-only Saussurea involucrata single-cell literature into a concrete acquisition workflow. It is evidence for an active data-request path, not evidence that the data are already available for model training.

## Request Candidates

| Dataset | Species | Evidence | DOI/PMID | Source | Data availability |
| --- | --- | --- | --- | --- | --- |
| saussurea_multicellular_spheroid_single_cell_report | Saussurea involucrata | reported single-cell transcriptomics in multicellular spheroids | 10.1002/adhm.202504623 41668397 | https://advanced.onlinelibrary.wiley.com/doi/10.1002/adhm.202504623 | Data are available from the corresponding author upon reasonable request; specific cultivation parameters require an NDA according to the publisher page. |

## Required Cell Metadata

`cell_id`, `cell_type`, `cell_type_coarse`, `sample_id`, `species`, `tissue`, `batch`

## Requested Files

| File class | Required | Description |
| --- | --- | --- |
| `processed_anndata` | `True` | Processed AnnData .h5ad or equivalent sparse matrix with genes by cells. |
| `raw_or_filtered_matrix` | `True` | 10x H5, MTX+barcodes+features, Loom, or another sparse count matrix export. |
| `cell_metadata` | `True` | Per-cell metadata containing labels, sample identifiers, tissue, condition, batch, and QC fields. |
| `gene_metadata` | `True` | Gene identifiers, aliases, ortholog hints, and genome annotation version. |
| `raw_fastq_or_repository_accession` | `False` | Raw reads or a stable SRA/ENA/GSA/GEO accession for reproducibility. |
| `protocol_and_license` | `True` | Library protocol, preprocessing steps, citation terms, data license, and model-training permission. |

## Validation Commands

```bash
python scripts/validate_saussurea_h5ad_contract.py --input data/saussurea_involucrata.h5ad --output-md outputs/publication_package/saussurea_h5ad_contract.md --output-json outputs/publication_package/saussurea_h5ad_contract.json
```

```bash
bash scripts/generate_publication_package.sh
```

```bash
bash scripts/top_journal_pipeline.sh
```

## Email Template

```text
Subject: Request for Saussurea involucrata single-cell transcriptomics data

Dear Professor / Corresponding Author,

I am developing SnowLotus-CellFM, a plant single-cell foundation model for cross-species cell-type annotation and Snow Lotus transfer analysis. Your study, "Sustainable Cultivation of Rare and Endangered Medicinal Plant Multicellular Spheroids Producing Bioactive Therapeutics for Alcohol-Related Liver Disease Therapy" (10.1002/adhm.202504623), is directly relevant because it reports Saussurea involucrata single-cell transcriptomics.

Could you share, under your preferred data-use terms, the reusable single-cell data needed for reproducible analysis?

Requested materials:
- processed AnnData .h5ad or equivalent sparse matrix;
- raw or filtered count matrix files;
- per-cell metadata with cell type, sample, tissue, condition, batch, and QC fields;
- gene metadata and genome annotation version;
- raw FASTQ files or a repository accession if available;
- citation, license, and model-training/benchmarking permission terms.

We will validate the files with an auditable h5ad contract, cite the study, and keep claims limited to the permissions and evidence available.

Best regards,
SnowLotus-CellFM project team
```
