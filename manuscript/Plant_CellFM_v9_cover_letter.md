# Cover Letter

Generated: `2026-07-30 21:35 Asia/Shanghai`

Dear Editor,

We submit **Plant-CellFM v9**, a plant-general foundation-model and all-plant adapter framework for single-cell and single-nucleus expression annotation. Plant single-cell studies now span multiple species, tissues and assay formats, but public reuse remains constrained by fragmented matrix formats, inconsistent cell-type names, uneven metadata and species-specific gene identifiers. Plant-CellFM v9 addresses this practical bottleneck by combining an audited public-plant expression corpus, a shared-gene Transformer representation model, hierarchical cell-state annotation, LoRA-based model freezing, runtime species-adapter resolution and a reproducible server-side release package.

The current submission is framed as a computational method and resource. It is not a Snow Lotus-only model: Snow Lotus is treated as one target-species adapter entry point under the same h5ad and ortholog-map contract. The submitted evidence focuses on the plant-general annotation framework, reproducible model assets and a callable CUDA service.

The release includes several reviewer-facing safeguards. First, all headline metrics are reported under strict grouped protocols rather than random cell splits. On the same shared-gene benchmark, Plant-CellFM v9 improves over the frozen v3 extended baseline in leave-dataset-out all-cell accuracy (0.4490 versus 0.2021) and leave-sample-out all-cell accuracy (0.6200 versus 0.4155). Under normalized leave-species-out evaluation, v9 reaches all-cell accuracy 0.2354, coverage 0.5590 and known-label accuracy 0.4210; these values are deliberately interpreted as open-set cross-species transfer evidence, not as universal high-accuracy annotation for every plant species.

Second, the strict species-holdout result is accompanied by a failure audit, a 106-label plant cell-state ontology mapping and an ontology-label benchmark on the frozen runtime embeddings. After excluding unknown or unannotated labels, the ontology-actionable protocol covers 2,324 / 3,964 cells (74.44%), with actionable all-cell accuracy 14.97%, known-label accuracy 20.12% and macro-F1 0.1395. This diagnostic makes the remaining cross-species transfer problem explicit rather than hiding it behind label harmonization.

Third, the submission includes a completed Seurat label-transfer comparator, classical centroid baselines and a v3 comparison. scPlantLLM and scPlantAnnotate are disclosed at their auditable execution boundaries because official executable weights or authenticated batch access are not yet fully closed in the release environment. We therefore do not claim final numerical superiority over those tools.

Fourth, the Arabidopsis root case demonstrates biological use of the model output. The case contains 260 marker-candidate rows across 13 cell states and 10 root-identity states, linking adapter resolution, hierarchical annotation and marker-candidate mining in a public-data plant root setting.

The release package is designed for direct inspection. The repository branch, model card, final manuscript, benchmark JSON files, server release verifier, release gate audit, watchdog recovery evidence and GitHub recovery note are included in the editor package. The frozen checkpoint is available from the GitHub release and is SHA256-pinned.

We believe Plant-CellFM v9 will be useful to plant single-cell researchers who need a reproducible starting point for cross-dataset annotation, adapter-based target-species transfer and transparent benchmark auditing across heterogeneous public plant matrices.

Sincerely,

The Plant-CellFM / SnowLotus-CellFM authors
