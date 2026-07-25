# scPlantAnnotate Benchmark Input Package

- Status: `input_ready_waiting_for_authorized_scplantannotate_run`
- Counts as completed metric: `False`
- Input h5ad: `outputs/external_benchmarks/scplantannotate_public_sprint_input/scplantannotate_input.h5ad`
- Truth CSV: `outputs/external_benchmarks/scplantannotate_public_sprint_input/truth_labels.csv`
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
| `Columella root cap` | 417 |
| `G1/G0 phase` | 417 |
| `Lateral root cap` | 417 |
| `Non-hair` | 417 |
| `Phloem` | 417 |
| `Root cap` | 417 |
| `Root cortex` | 417 |
| `Root endodermis` | 417 |
| `Root hair` | 416 |
| `Root stele` | 416 |
| `S phase` | 416 |
| `Xylem` | 416 |

This package is an input/readiness artifact only. It is intentionally excluded from completed external metric counts until scPlantAnnotate predictions are exported and scored against the truth CSV.
