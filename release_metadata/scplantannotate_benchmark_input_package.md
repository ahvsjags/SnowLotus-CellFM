# scPlantAnnotate Benchmark Input Package

- Status: `input_ready_waiting_for_authorized_scplantannotate_run`
- Counts as completed metric: `False`
- Input h5ad: `release_metadata/external_benchmarks/scplantannotate_public_sprint_input_v2/scplantannotate_input.h5ad` (22,506 genes; SHA256 recorded in `release_metadata/scplantannotate_formal_benchmark_v1.json`)
- Truth CSV: `release_metadata/external_benchmarks/scplantannotate_public_sprint_input_v2/truth_labels.csv`
- Selected cells: `5000`
- Class count: `12`
- Species: `Arabidopsis thaliana`
- Label key: `cell_type`

## Reproducible Commands

Authorized web/API submission:

```bash
SCPLANTANNOTATE_USERNAME=<user> SCPLANTANNOTATE_PASSWORD=<password> python scripts/run_scplantannotate_authenticated_benchmark.py --input-h5ad outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad --dataset-name snowcell_public_sprint_scplantannotate_probe --organism-id 1 --predictor-id 1 --execute --wait --output outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json
```

Author or web-exported predictions to metrics:

```bash
python scripts/run_scplantannotate_authenticated_benchmark.py --prediction-csv <scplantannotate_predictions.csv> --truth-csv outputs/external_benchmarks/scplantannotate_public_sprint_input/truth_labels.csv --metrics-output outputs/external_benchmarks/scplantannotate_final_metrics.json --output outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json
```

## Label Distribution

| Label | Cells |
| --- | ---: |
| `Mature phloem parenchyma` | 1421 |
| `Periderm` | 924 |
| `Vascular cambium` | 715 |
| `Conductive phloem parenchyma` | 521 |
| `Maturing xylem parenchyma` | 340 |
| `Young xylem parenchyma` | 315 |
| `Fiber` | 284 |
| `Mature xylem parenchyma` | 283 |
| `Vessel identity cell/expanding vessel` | 63 |
| `Companion cell` | 54 |
| `Sieve element` | 44 |
| `Myrosin idioblasts` | 36 |

This package is an input/readiness artifact only. It is intentionally excluded from completed external metric counts until scPlantAnnotate predictions are exported and scored against the truth CSV.
