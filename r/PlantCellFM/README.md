# PlantCellFM

`PlantCellFM` is the R interface to [Plant-CellFM](https://github.com/ahvsjags/SnowLotus-CellFM) and its evidence-aware `PlantCell-Agent` workflow.

It supports:

- local annotation through the repository's Python CLI;
- `.h5ad` files, `SingleCellExperiment` objects and Seurat objects;
- server-side annotation through the Plant-CellFM HTTP service;
- direct predictions, accepted/review partitions, marker evidence and JSONL traces.

## Installation

Install the R package from a local clone:

```r
install.packages(c("httr2", "jsonlite"))
remotes::install_local("r/PlantCellFM")
```

Install the Python runtime from the repository root:

```bash
python -m pip install -e ".[singlecell]"
```

Model checkpoints are stored in the repository's `models/` directory and are
tracked with Git LFS.

## Local Agent annotation

```r
library(PlantCellFM)

result <- plantcellfm_annotate_h5ad(
  data = "input.h5ad",
  checkpoint = "models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt",
  output_dir = "outputs/my_plant_run",
  species = "Arabidopsis thaliana",
  project_root = ".",
  device = "cuda"
)

head(result$predictions)
head(result$review)
head(result$markers)
result$report
```

The returned list contains `predictions`, `predictions_direct`, `review`,
`markers`, `route`, `verification`, `report`, `trace` and `output_dir`.

## R object annotation

For a `SingleCellExperiment`, `zellkonverter` is used only to create a
temporary H5AD input. The returned object receives `predicted_label`,
`prediction_confidence`, `review_required` and `coarse_label` in `colData`.

```r
result <- plantcellfm_annotate_sce(
  sce,
  checkpoint = "models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt",
  output_dir = "outputs/sce_run",
  project_root = "."
)
sce_with_labels <- result$object
```

For Seurat, install `SeuratDisk` and use `plantcellfm_annotate_seurat()` in the
same way.

## Server use

Start the service from the repository root:

```bash
python scripts/serve_snowlotus.py \
  --backbone-checkpoint models/SnowLotus_CellFM_GSE146034_pretrain_8e_512_best.pt \
  --annotation-checkpoint models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt \
  --project-root . --data-root /data/plant_inputs --device cuda --port 8000
```

Then call it from R:

```r
plantcellfm_health("http://127.0.0.1:8000")
plantcellfm_capabilities("http://127.0.0.1:8000")

job <- plantcellfm_service_annotate(
  base_url = "http://127.0.0.1:8000",
  data_path = "/data/plant_inputs/sample.h5ad",
  output_dir = "/data/plant_outputs/sample",
  species = "Arabidopsis thaliana"
)
```

The HTTP service accepts server-side paths by design. The local Agent CLI is
the preferred route when full specialist routing, evidence verification and
the review queue are required.
