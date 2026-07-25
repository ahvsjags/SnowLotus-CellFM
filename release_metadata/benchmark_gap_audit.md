# SnowLotus-CellFM Benchmark Gap Audit

- Requirements audited: `10`
- Ready: `8`
- In progress: `0`
- Missing: `2`
- Top-journal benchmark ready: `False`

| ID | Priority | Status | Evidence | Blocker / next action |
| --- | --- | --- | --- | --- |
| random_split_centroid | A | READY | `outputs/strict_benchmarks/public_sprint_group_random.centroid_baseline.json` | Run scripts/run_strict_benchmark_audits.sh after a labelled corpus is available. |
| leave_dataset_split_audit | A | READY | `outputs/strict_benchmarks/leaveout_brassicaceae_dataset.split_audit.json` | Build the public MLM corpus and run strict benchmark audits. |
| leave_species_split_audit | A | READY | `outputs/strict_benchmarks/leaveout_eutrema_species.split_audit.json` | Build the public MLM corpus and run strict benchmark audits. |
| leaveout_supervised_baseline | A | READY | `outputs/strict_benchmarks/leaveout_*.centroid_baseline.json` | Current leave-out splits need enough labelled train/validation/test cells after filtering. |
| marker_candidate_mining | A | READY | `outputs/strict_benchmarks/public_sprint.marker_candidates.json` | Run snowcell marker-candidates on a labelled benchmark corpus. |
| seurat_label_transfer | A | READY | `outputs/external_benchmarks/*seurat*.json` | Export comparable train/test matrices and run Seurat label transfer in R. |
| scplantllm_comparison | A | READY | `outputs/external_benchmarks/*scplantllm*.json` | Prepare scPlantLLM-compatible input and run its public evaluation code. |
| scplantannotate_comparison | B | MISSING | `outputs/external_benchmarks/*scplantannotate*.json` | Prepare matched Arabidopsis/maize/rice/soybean benchmarks and run scPlantAnnotate. |
| snow_lotus_finetune_benchmark | S | MISSING | `outputs/saussurea_lora_finetune/* and data/saussurea_involucrata.h5ad` | Requires real data/saussurea_involucrata.h5ad with cell labels and sample metadata. |
| public_corpus_scale | A | READY | `15 manifest-ready public targets` | Finish queued GEO downloads/conversions and rebuild the public MLM corpus. |
