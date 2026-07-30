# Plant-CellFM v9 English Submission Synopsis

Generated: `2026-07-31 01:07 Asia/Shanghai`

Repository: https://github.com/ahvsjags/SnowLotus-CellFM

Branch: `agent/remote-pipeline-20260728`

Release tag: `v0.9.0-plant-general-lora`

## Proposed Title

Plant-CellFM: a reproducible foundation-model and adapter framework for plant single-cell annotation

## Abstract

Plant single-cell and single-nucleus transcriptomic studies increasingly cover diverse species, tissues and assay formats, yet cross-study reuse is limited by heterogeneous matrix formats, non-unified cell-state names and species-specific gene identifiers. We present Plant-CellFM v9, a reproducible plant expression foundation-model and all-plant adapter framework for audited single-cell annotation. The release combines a public plant expression corpus, shared-gene Transformer representations, LoRA-based model freezing, runtime species-adapter resolution, hierarchical annotation outputs and server-side release verification. On the same shared-gene benchmark, Plant-CellFM v9 improves over the frozen v3 extended baseline in leave-dataset-out all-cell accuracy (0.4490 versus 0.2021) and leave-sample-out all-cell accuracy (0.6200 versus 0.4155). Under normalized leave-species-out evaluation, v9 reaches all-cell accuracy 0.2354, coverage 0.5590 and known-label accuracy 0.4210, supporting open-set cross-species transfer analysis rather than a universal high-accuracy claim. A plant cell-state ontology diagnostic covers 2,324 of 3,964 cells (74.44%) after excluding unknown or unannotated states. The API confidence layer reaches 96.64% and 92.81% selective accuracy when accepting the top 30% and 40% confidence cells. The release further includes 24 adapter entries, an Arabidopsis root case with 260 marker-candidate rows across 13 cell states and 10 root-identity states, and a multi-species scPlantDB case with 31,503 cells across 4 species. Plant-CellFM v9 therefore provides a traceable method and resource for plant single-cell annotation, benchmark auditing and target-species adapter transfer.

## Significance Statement

Plant single-cell atlases are expanding faster than their annotation conventions can be harmonized. Plant-CellFM v9 turns this practical bottleneck into a reproducible modelling problem: matrices, labels, adapters, checkpoints, benchmark splits and server health are all exposed as auditable release objects. Its central contribution is a reusable plant-general framework that makes cross-dataset transfer, open-set species transfer and target-species adapter preparation inspectable from the same code path.

## Highlights

- Plant-general foundation model for single-cell and single-nucleus plant expression annotation.
- All-plant adapter framework with 24 adapter entries and universal fallback resolution.
- Strict grouped evaluation, including leave-dataset-out, leave-sample-out and normalized leave-species-out protocols.
- v9 improves over frozen v3 in leave-dataset-out all-cell accuracy (0.4490 versus 0.2021) and leave-sample-out all-cell accuracy (0.6200 versus 0.4155).
- Ontology-actionable benchmark separates 74.44% covered cells from unknown or unannotated states.
- Open-set calibration reaches 96.64%/92.81% selective accuracy at top-30/top-40 confidence acceptance.
- Arabidopsis root case provides 260 marker-candidate rows across 13 cell states.
- Multi-species scPlantDB case adds 31,503 cells across 4 species and 96 marker-candidate records.

## Graphical Abstract Text

Panel 1: Heterogeneous public plant matrices enter an audited corpus layer with accession, species, label and file-integrity records.

Panel 2: Shared-gene expression profiles are encoded by the Plant-CellFM representation model and frozen through a LoRA release checkpoint.

Panel 3: Runtime adapter resolution selects exact species adapters when available and falls back to a plant-universal adapter for new species.

Panel 4: Grouped benchmarks quantify leave-dataset, leave-sample and open-set leave-species transfer against frozen v3, centroid and Seurat comparators.

Panel 5: The Arabidopsis root case links model output to cell-state labels and marker-candidate mining for downstream biological interpretation.

Panel 6: Open-set confidence calibration and the multi-species scPlantDB case show how high-confidence predictions, review routing and public-data biology examples are packaged for reuse.

## Evidence At A Glance

- Completed metric rows in external benchmark panel: 6 / 8.
- Completed formal comparisons in the current package: 5.
- Normalized leave-species-out all-cell accuracy: 0.2354.
- Normalized leave-species-out known-label accuracy: 0.4210.
- Ontology-label actionable all-cell accuracy: 14.97%.
- Ontology-label known-label accuracy: 20.12%.
- Ontology-label macro-F1: 0.1395.
- API confidence top-30 selective accuracy: 96.64%.
- API confidence top-40 selective accuracy: 92.81%.
- Multi-species scPlantDB case: 31,503 cells, 4 species, 96 marker-candidate records.

## Editorial Positioning

The manuscript is positioned as a computational method/resource paper for plant single-cell annotation. The core promise is reproducibility, adapter-based plant generalization and transparent benchmark auditing. The submission reports open-set leave-species performance as diagnostic transfer evidence, adds selective annotation evidence for high-confidence predictions, treats Snow Lotus as one target-species adapter entry point and records scPlantLLM/scPlantAnnotate through official-source benchmark contracts pending official metric closure.

## Submission Checklist

- Use `SUBMISSION_INDEX_v9.md` as the reviewer entry point.
- Use `manuscript/Plant_CellFM_v9_final_submission_zh_v1.docx` as the current full Chinese manuscript.
- Use `manuscript/Plant_CellFM_v9_cover_letter.docx` as the cover letter.
- Use this synopsis for the English abstract, highlights, significance and graphical abstract text.
- Use `release_metadata/data_code_availability_v9.md` for repository, release and server reproducibility statements.
- Verify the final editor package with `scripts/verify_v9_server_release.py` before resubmission.
