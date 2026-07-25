# External Benchmark and Snow Lotus Primary-Data Blockers

Status date: 2026-07-24

## scPlantAnnotate

`scPlantAnnotate` is a relevant external comparator because the PubMed record
describes a transformer-based plant cell-type annotation model trained for
Arabidopsis, maize, rice, and soybean, including random-split and
leave-one-dataset-out evaluation. The record also states that a freely accessible
web server exists for pretrained-model annotation.

Current blocker: the official web server is reachable and its React front end
exposes scriptable API routes, including `/api/jobs/api/job_annotate_and_plot/`,
`/api/organisms/api/organism_query/`, and
`/api/predictors/api/predictor_query_public/`. However, anonymous probes of the
organism, predictor, and job endpoints return HTTP 403 with authentication
required. No downloadable pretrained weights or unauthenticated batch endpoint
has been located. SnowLotus-CellFM therefore keeps
`scplantannotate_comparison` as `MISSING` until authorized credentials or an
author-provided batch route is available.

Prepared action: `scripts/run_scplantannotate_authenticated_benchmark.py` now
contains the authenticated login, h5ad upload, and annotation-job request
templates reverse-engineered from the official front end. With an authorized
account in `SCPLANTANNOTATE_USERNAME` and `SCPLANTANNOTATE_PASSWORD`, it can be
run with `--execute`; otherwise it writes a dry-run plan only. A dry-run plan is
not counted as a completed comparison by `write_benchmark_gap_audit.py`.

Source checked:

- PubMed PMID 41554477, DOI 10.1016/j.jare.2026.01.035:
  https://pubmed.ncbi.nlm.nih.gov/41554477/
- Official web server and front-end API probe:
  https://scplantannotate.missouri.edu/

## Saussurea involucrata primary scRNA-seq

No public `Saussurea involucrata` scRNA-seq/snRNA-seq matrix or AnnData object
has been located in the current public-data pass. A 2026 Advanced Healthcare
Materials paper reports single-cell transcriptomics in Snow Lotus multicellular
spheroids, but the publisher data statement makes the data request-only rather
than publicly downloadable. The available public evidence therefore supports
genome, bulk transcriptome, stress-gene, and literature context, but not a
reusable primary cell atlas.

Current blocker: `data/saussurea_involucrata.h5ad` is absent. The
`snow_lotus_finetune_benchmark` requirement remains `MISSING` because final
Snow Lotus-specific fine-tuning and holdout claims require real labelled
single-cell/nucleus data.

Required action: generate or obtain a primary Snow Lotus single-cell dataset with
raw FASTQ, processed matrix, cell labels, sample metadata, and repository
accession. Minimum expected fields are listed in
`docs/saussurea_evidence_plan.md`.

Supporting public sources checked:

- Genome and assembly, BioProject PRJNA991078:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10599237/
- Bulk transcriptome / gene expression, BioProject PRJNA169171:
  https://www.ncbi.nlm.nih.gov/bioproject/PRJNA169171
- SRA experiment SRX156202 / run SRR516284:
  https://www.ncbi.nlm.nih.gov/sra/SRX156202%5Baccn%5D
- CHS atmospheric-pressure stress study using PRJNA991078:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12673789/
- Snow Lotus multicellular spheroid single-cell transcriptomics report,
  PMID 41668397 / DOI 10.1002/adhm.202504623:
  https://advanced.onlinelibrary.wiley.com/doi/10.1002/adhm.202504623
