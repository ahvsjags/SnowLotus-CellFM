# Plant-CellFM v10 Third-Party Benchmark Contract

Generated: 2026-07-31 01:09 Asia/Shanghai

This contract upgrades third-party comparator handling from an informal pending item to a reproducible execution specification. It does not create completed metrics for tools whose official weights, executable checkout or authenticated API are absent.

## Official Sources

| Tool | Source | Local role |
| --- | --- | --- |
| scPlantLLM | https://github.com/compbioNJU/scPlantLLM; DOI 10.1093/gpbjnl/qzaf024 | official foundation-model comparator with input and execution contract ready |
| scPlantAnnotate | https://scplantannotate.missouri.edu/; DOI 10.1016/j.jare.2026.01.035 | official web/API comparator, authenticated execution required |
| Seurat | https://satijalab.org/seurat/ | completed traditional label-transfer baseline |

## Completed Comparator

- Seurat label transfer: `completed_metric`
- Test cells: `512`
- Fine accuracy: `0.2207`
- Fine macro-F1: `0.0603`
- Evidence: `release_metadata/external_benchmarks/seurat_v9_subset.json`

## Contract Readiness

| Tool | Status | Evidence-readiness score | Metric closure | Reporting rule |
| --- | --- | --- | --- | --- |
| scPlantLLM | execution_contract_ready_metric_pending | 92 | pending_official_weight_and_probe_json | Report input readiness and official-source anchoring now; report numerical comparison only after the official checkpoint/probe JSON exists and is regenerated inside the release tree. |
| scPlantAnnotate | auth_limited_contract_ready | 90 | pending_authenticated_prediction_export | Keep this as access-limited until authenticated predictions or an official export are scored. |

## scPlantLLM Execution Contract

- Input ready: `ready`
- Selected cells: `20000`
- Retained genes: `24392`
- Gene-vocabulary overlap: `1.0000`
- Reference chunks ready: `ready`
- Chunk count: `3`

Required artifacts for metric closure:

- `external/scPlantLLM/model_params/scPlantLLM_model.pth`
- `outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json`
- `command log for scripts/run_scplantllm_embedding_centroid_probe.py`

Runner contract:

```bash
python scripts/run_scplantllm_embedding_centroid_probe.py --chunks-dir outputs/external_benchmarks/scplantllm_public_sprint_input/reference_preprocess/chunks --checkpoint external/scPlantLLM/model_params/scPlantLLM_model.pth --output outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json
```

## scPlantAnnotate Execution Contract

- Web server reachable: `ready`
- Anonymous API accessible: `not_ready`
- Auth-required endpoint count: `3`
- Input h5ad: `outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad`
- Truth CSV: `outputs/external_benchmarks/scplantannotate_public_sprint_input/truth_labels.csv`
- Selected cells: `5000`
- Class count: `12`

Required artifacts for metric closure:

- `authenticated scPlantAnnotate account or author-exported predictions`
- `outputs/external_benchmarks/scplantannotate_final_metrics.json`
- `truth-matched prediction CSV with cell identifiers`

Runner contract:

```bash
SCPLANTANNOTATE_USERNAME=<user> SCPLANTANNOTATE_PASSWORD=<password> python scripts/run_scplantannotate_authenticated_benchmark.py --input-h5ad outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad --dataset-name snowcell_public_sprint_scplantannotate_probe --organism-id 1 --predictor-id 1 --execute --wait --output outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json
```

## Submission Upgrade

- Before: Third-party model comparison needed a clearer separation between completed metrics and official-source metric-pending contracts.
- After: Completed Seurat metrics, scPlantLLM input/runner readiness and scPlantAnnotate auth-limited execution are separated, sourced and assigned closure criteria.
- Safe sentence: Plant-CellFM v9 includes completed v3, centroid and Seurat benchmarks, while scPlantLLM and scPlantAnnotate are disclosed through official-source benchmark contracts pending executable metric closure.
