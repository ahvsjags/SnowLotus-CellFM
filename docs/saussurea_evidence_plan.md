# Saussurea Evidence Plan

## 2026-07-23 status

No public `Saussurea involucrata` scRNA-seq or snRNA-seq matrix has been found in the current GEO/SRA/NCBI-oriented data pass. Therefore, SnowLotus-CellFM is developed as:

1. a plant single-cell foundation annotation model trained on public cross-species plant scRNA/snRNA data;
2. a Snow Lotus-ready transfer model that can ingest `data/saussurea_involucrata.h5ad` as soon as real Snow Lotus single-cell data are available;
3. a Snow Lotus biological evidence framework that uses genome, bulk transcriptome, stress transcriptome, and medicinal/secretory-cell single-cell comparators to prioritize markers and regulators.

## 2026-07-24 broader web sanity check

Additional web-level searches for `Saussurea involucrata single-cell RNA`, `Saussurea involucrata scRNA-seq`, `Saussurea involucrata h5ad`, and Chinese terms such as `天山雪莲 单细胞 转录组` still did not identify a public Snow Lotus scRNA/snRNA matrix, h5ad object, or GEO-style single-cell atlas.

The key update is a 2026 Advanced Healthcare Materials paper (PMID:41668397, DOI:10.1002/adhm.202504623) reporting single-cell transcriptomics in `Saussurea involucrata` multicellular spheroids. The publisher page states that data are available from the corresponding author upon reasonable request, while specific cultivation parameters require an NDA. Therefore, this paper is useful as literature evidence and a data-request target, but it is not yet a reusable public matrix for SnowLotus-CellFM training, benchmarking, or claim-freezing.

The broader evidence remains useful but secondary: low-pressure/cold-response RNA-seq, de novo transcriptome, chloroplast/genome resources, suspension-cell engineering, multicellular-spheroid medicinal-plant work, and close-genus sequence resources can support gene vocabulary, stress biology, and validation design, but cannot substitute for primary single-cell labels.

Manuscript wording should therefore distinguish three claims:

1. `Supported now`: a cross-species plant single-cell foundation annotator and Snow Lotus-ready transfer pipeline.
2. `Supported by secondary evidence`: Snow Lotus stress/adaptation and secondary-metabolism hypotheses grounded in genome/bulk/stress resources.
3. `Not yet supported`: a definitive Snow Lotus cell atlas, tissue-specific cell type discoveries, or Snow Lotus fine-tuning benchmarks until `data/saussurea_involucrata.h5ad` is supplied.

## Snow Lotus evidence layers

| Layer | Identifier | Role in SnowLotus-CellFM |
| --- | --- | --- |
| Required primary data | `data/saussurea_involucrata.h5ad` | LoRA/full fine-tuning, Snow Lotus cell map, model discovery, final biological claims |
| Request-only single-cell literature | PMID:41668397 / DOI:10.1002/adhm.202504623 | reported multicellular-spheroid single-cell transcriptomics; useful for data request and biological framing, not current model training |
| Genome reference | `PRJNA991078` | gene vocabulary normalization, ortholog mapping, genome-backed marker naming |
| Bulk transcriptome | `PRJNA169171 / SRR516284` | Snow Lotus expressed-gene vocabulary and transcript support |
| Low-pressure response | `PRJNA1218246` | high-altitude/low-pressure adaptation evidence |
| Low-temperature response | `PRJNA1033840` | cold-response/dehydrin transcript evidence for alpine marker prioritization |
| Raw sequence read archive | `PRJNA387384` | secondary public accession evidence after runinfo validation |
| Plant scRNA foundation data | GEO/public plant atlases | transferable cell-type priors across root, leaf, stress, monocot, Brassicaceae, and secondary-metabolism contexts |

## Minimum top-journal-ready Snow Lotus data package

The manuscript-level primary dataset should include:

- tissues: root, leaf, stem, flower/inflorescence or meristem;
- conditions: normal, low temperature, low pressure/hypoxia, strong UV or combined alpine stress;
- replication: at least 2-3 biological replicates per tissue/condition;
- target scale: 5k-20k cells or nuclei per sample;
- required `obs` fields: `cell_type`, `cell_type_coarse`, `sample_id`, `species`, `tissue`, `batch`, `cell_id`;
- repository deposition: raw FASTQ plus processed AnnData/matrix files in GEO/SRA/ENA/NGDC GSA before submission.

## How supporting data are used

1. Genome and transcriptome resources define Snow Lotus gene symbols, aliases, and ortholog groups.
2. Public plant scRNA atlases pretrain the model and benchmark cross-species transfer.
3. Medicinal or secretory-cell comparators such as `cotton_glandular_terpenoid_atlas` help rank secondary-metabolism markers.
4. When `data/saussurea_involucrata.h5ad` arrives, `configs/saussurea_lora_finetune.yaml` turns the public foundation model into a Snow Lotus-specific annotator.
5. Final claims should require agreement among model markers, differential expression, ortholog evidence, and at least 3-5 independent wet-lab validations.
