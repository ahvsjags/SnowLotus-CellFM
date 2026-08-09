# scPlantAnnotate formal benchmark audit v1

Status: **auth_required_not_counted**
Counts as completed metric: **False**

| Item | Value |
| --- | --- |
| Frozen cells | 5,000 |
| Frozen classes | 12 |
| Input SHA256 | `336ae75b77582785ff6328bfdcb28ea62fa63ef41f4fdec61fdf5786ab1cde33` |
| Truth SHA256 | `1d80e4d62c2bd5e6986d97a4a863f4f37b00073b71750c8e68e0e725ec9fbaf1` |
| Official numerical output | not available |

This packet is a formal comparison contract, not a substitute for the official numerical output. The result is counted only after the authenticated job or an official exported prediction file is scored against the frozen truth CSV.

## Reproduction

```text
SCPLANTANNOTATE_USERNAME=<user> SCPLANTANNOTATE_PASSWORD=<password> python scripts/run_scplantannotate_authenticated_benchmark.py --input-h5ad release_metadata/external_benchmarks/scplantannotate_public_sprint_input_v2/scplantannotate_input.h5ad --dataset-name snowcell_public_sprint_scplantannotate_probe --organism-id 1 --predictor-id 1 --execute --wait --output outputs/external_benchmarks/scplantannotate_authenticated_benchmark_plan.json
```
