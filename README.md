# Plant-CellFM / SnowLotus-CellFM

Plant-CellFM is the general-plant branch of SnowLotus-CellFM for plant single-cell and single-nucleus expression annotation. The active release is the Plant Methods v1 submission package with v12 main figures.

## Current Plant Methods v1 Submission Package

The reviewer-facing package frames Plant-CellFM as a coverage-aware plant single-cell annotation method that separates frozen-encoder downstream decoder transfer, source-context routing and target-supervised sparse adaptation. The primary transfer result is 39.96% all-cell accuracy on a 3,964-cell complete denominator with 55.90% source-label coverage and 71.48% covered-label accuracy. The context-gate 42.36% result is retained as a global sensitivity analysis, while wheat and Sorghum results are reported as target-supervised adaptation.

- **Main manuscript**: [`Plant_CellFM_Plant_Methods_manuscript_v1.md`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_manuscript_v1.md) and [`Word version`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_manuscript_v1.docx).
- **Supporting Information**: [`Plant_CellFM_Plant_Methods_supporting_information_v1.md`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_supporting_information_v1.md) and [`Word version`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_supporting_information_v1.docx).
- **Cover letter and QA**: [`cover letter`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_cover_letter_v1.md), [`claim map`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_claim_figure_map_v1.md) and [`QA report`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_QA_report_v1.md).
- **Main figures**: seven upload-ready PDFs in [`submission_files/main_figures`](manuscript/plant_methods_submission_v1/submission_files/main_figures), with editable SVG/PDF/PNG source exports, 600-dpi local TIFF exports and panel-level TSV source data in [`figures/plant_cellfm_submission_v12`](figures/plant_cellfm_submission_v12).
- **Submission zip**: [`Plant_CellFM_Plant_Methods_submission_v1.zip`](manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_submission_v1.zip), SHA256 `c7240194f5d6be1a1a9827420e6055db640cd60ecbaaab006d49609a140929a8`.
- **Figure policy**: v12 main figures use table-driven quantitative panels and scripted vector schematics; no generative-image assets are included in the active package.

## Build And Audit

Rebuild the active figure suite and Word files with:

```bash
python scripts/render_v12_system_figure.py
python scripts/render_v12_strict_transfer_figure.py
python scripts/render_v12_context_stc_hero.py
python scripts/render_v12_target_adaptation_figure.py
python scripts/render_v12_root_biology_figure.py
python scripts/render_v12_wheat_benchmark_figure.py
python scripts/render_v12_sorghum_recovery_figure.py
python scripts/assemble_v12_main_figure_suite.py
python scripts/audit_v12_main_figure_suite.py
node scripts/build_plant_methods_submission_docs.js
```

The exact upload bundle is:

```text
manuscript/plant_methods_submission_v1/Plant_CellFM_Plant_Methods_submission_v1.zip
```

Public repository tag:

```text
plant-methods-submission-v1-20260803
```

## PlantCell-Agent Upgrade

The checkpoint-preserving upgrade is a central-model plus specialist-agent
architecture. Plant-CellFM remains the shared expression encoder and direct
prediction service; PlantCell-Agent orchestrates capability-scoped species,
organ-context, orthology, support-prototype, open-set and evidence specialists.
Each specialist declares its contract and fallback chain, while low-confidence,
open-set or failed-contract cells are routed to Review Agent. Direct predictions
and all evidence traces remain visible.

```bash
snowcell agent-annotate \
  --checkpoint models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt \
  --data input.h5ad \
  --output-dir outputs/plantcell_agent_run \
  --device cuda
```

See [`docs/plantcell_agent.md`](docs/plantcell_agent.md), the
[`Agent model card`](release_metadata/plantcell_agent_model_card_v1.md) and
the vector [`specialist-agent architecture`](figures/plantcell_agent/plantcell_agent_extended_data_fig1_v3.svg).

## R Package

An R wrapper is provided in [`r/PlantCellFM`](r/PlantCellFM). It lets R users
run the local PlantCell-Agent on an H5AD/NPZ file, SingleCellExperiment or
Seurat object, or call the Plant-CellFM HTTP service. The wrapper returns the
prediction table together with the review queue, marker evidence, route
decision, verification report and JSONL trace.

Install the Python runtime from the repository root and then install the R
package locally:

```bash
python -m pip install -e ".[singlecell]"
```

```r
install.packages(c("httr2", "jsonlite"))
remotes::install_local("r/PlantCellFM")

library(PlantCellFM)
result <- plantcellfm_annotate_h5ad(
  data = "input.h5ad",
  checkpoint = "models/SnowLotus_CellFM_SRP169576_annotation_1024_best.pt",
  output_dir = "outputs/r_agent_run",
  species = "Arabidopsis thaliana",
  project_root = ".",
  device = "cuda"
)
head(result$predictions)
head(result$review)
```

For R-native objects, use `plantcellfm_annotate_sce()` with `zellkonverter`
or `plantcellfm_annotate_seurat()` with `SeuratDisk`. Full details and the
server client are in [`r/PlantCellFM/README.md`](r/PlantCellFM/README.md).
