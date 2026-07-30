# Cover Letter

Generated: `2026-07-31 02:04 Asia/Shanghai`

Dear Editor,

We submit **Plant-CellFM v9**, a plant-general foundation-model and all-plant adapter framework for single-cell and single-nucleus expression annotation. Plant single-cell studies now span multiple species, tissues and assay formats, but public reuse remains constrained by fragmented matrix formats, inconsistent cell-type names, uneven metadata and species-specific gene identifiers. Plant-CellFM v9 addresses this practical bottleneck by combining an audited public-plant expression corpus, a shared-gene Transformer representation model, hierarchical cell-state annotation, LoRA-based model freezing, runtime species-adapter resolution and a reproducible server-side release package.

The current submission is framed as a computational method and resource. It is not a Snow Lotus-only model: Snow Lotus is treated as one target-species adapter entry point under the same h5ad and ortholog-map contract. The submitted evidence focuses on the plant-general annotation framework, reproducible model assets and a callable CUDA service.

The release includes several reviewer-facing safeguards. First, all headline metrics are reported under strict grouped protocols rather than random cell splits. On the same shared-gene benchmark, Plant-CellFM v9 improves over the frozen v3 extended baseline in leave-dataset-out all-cell accuracy (0.4490 versus 0.2021) and leave-sample-out all-cell accuracy (0.6200 versus 0.4155). Under normalized leave-species-out evaluation, v9 reaches all-cell accuracy 0.2354, coverage 0.5590 and known-label accuracy 0.4210; these values are deliberately interpreted as open-set cross-species transfer evidence, not as universal high-accuracy annotation for every plant species.

Second, the strict species-holdout result is accompanied by a failure audit, a 106-label plant cell-state ontology mapping and an ontology-label benchmark on the frozen runtime embeddings. After excluding unknown or unannotated labels, the ontology-actionable protocol covers 2,324 / 3,964 cells (74.44%), with actionable all-cell accuracy 14.97%, known-label accuracy 20.12% and macro-F1 0.1395. This diagnostic makes the remaining cross-species transfer problem explicit rather than hiding it behind label harmonization.

Third, the new Species-Transfer Calibration layer adds an explicit algorithmic improvement on the same frozen embeddings and leave-species split. Without training on held-out species labels, the calibrated `knn_cosine_k9` layer improves exact-label all-cell accuracy from 23.64% to 30.10%, known-label accuracy from 42.28% to 53.84%, and known-label macro-F1 from 0.1922 to 0.2663. Coverage remains 55.90%, so the gain reflects classifier calibration rather than changing the denominator.

Fourth, the open-set calibration audit adds a practical use layer for this strict benchmark. The deployed API annotation head reaches 96.64% selective accuracy when automatically accepting the top 30% fine-confidence cells and 92.81% at the top 40% acceptance level. Lower-confidence and open-set-like cells are routed to manual review, ontology harmonization or species-adapter calibration rather than being converted directly into biological claims.

Fifth, the submission includes a completed Seurat label-transfer comparator, classical centroid baselines and a v3 comparison. scPlantLLM and scPlantAnnotate are disclosed through official-source benchmark contracts with input packages, runner commands, missing artifacts and metric-closure rules. We therefore do not claim final numerical superiority over those tools until executable official metrics are frozen.

Sixth, the Arabidopsis root and multi-species scPlantDB cases demonstrate biological use of the model output. The Arabidopsis case contains 260 marker-candidate rows across 13 cell states and 10 root-identity states, linking adapter resolution, hierarchical annotation and marker-candidate mining in a public-data plant root setting.
 The multi-species scPlantDB case adds 31,503 cells, 4 species, 4 tissues and 96 marker-candidate records as a second public-data biology demonstration.

The release package is designed for direct inspection. The repository branch, model card, final manuscript, benchmark JSON files, server release verifier, release gate audit, watchdog recovery evidence and GitHub recovery note are included in the editor package. The frozen checkpoint is available from the GitHub release and is SHA256-pinned.

We believe Plant-CellFM v9 will be useful to plant single-cell researchers who need a reproducible starting point for cross-dataset annotation, adapter-based target-species transfer and transparent benchmark auditing across heterogeneous public plant matrices.

Sincerely,

The Plant-CellFM / SnowLotus-CellFM authors
