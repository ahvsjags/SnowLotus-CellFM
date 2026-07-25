# SnowLotus-CellFM scPlantLLM Input Readiness

- Status: `reference_preprocess_ready`
- Input HDF5/meta ready: `True`
- Reference metadata ready: `True`
- Reference preprocess chunks ready: `True`
- Selected cells: `1000`
- Retained genes: `24392`
- scPlantLLM gene-vocabulary overlap rate: `1.0`

## Required Input Checks

- HDF5 path: `outputs/external_benchmarks/scplantllm_preprocess_probe_input/snowcell_public_sprint.h5`
- HDF5 required keys present: `True`
- HDF5 matrix shape: `[1000, 24392]`
- Metadata CSV: `outputs/external_benchmarks/scplantllm_preprocess_probe_input/snowcell_public_sprint.meta.csv`
- Metadata required columns present: `True`

## Reference Checkout

- scPlantLLM checkout exists: `True`
- scPlantLLM gene vocab exists: `True`

## Reference Outputs

| File | Exists | Bytes |
| --- | --- | --- |
| `outputs/external_benchmarks/scplantllm_preprocess_probe_input/reference_preprocess/batch_effect.meta` | `True` | `73016` |
| `outputs/external_benchmarks/scplantllm_preprocess_probe_input/reference_preprocess/batch_effect_vocab.meta.json` | `True` | `19` |
| `outputs/external_benchmarks/scplantllm_preprocess_probe_input/reference_preprocess/cell_type.meta` | `True` | `76959` |
| `outputs/external_benchmarks/scplantllm_preprocess_probe_input/reference_preprocess/cell_type_vocab.meta.json` | `True` | `278` |

- Reference chunk count: `3`
