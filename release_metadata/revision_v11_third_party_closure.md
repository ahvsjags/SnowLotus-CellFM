# Plant-CellFM v11 Third-Party Metric Closure Audit

Generated: 2026-07-31 02:26 Asia/Shanghai

Overall status: `scplantllm_weight_download_in_progress`

## scPlantLLM

- Weight status: `partial_or_in_progress`
- Weight path: `external/scPlantLLM/model_params/scPlantLLM_model.pth`
- Weight bytes: `2636096` / `431801156`
- Expected SHA256 / LFS OID: `baa24dc1e686b94aa08e7e7b08df17e1bb53e479416acf7f50cd032b0fabf416`
- Probe status: `missing_or_incomplete`
- Probe accuracy: `None`
- Probe macro-F1: `None`

Closure command:

```bash
/root/miniconda3/envs/myconda/bin/python scripts/run_scplantllm_embedding_centroid_probe.py --chunks-dir outputs/external_benchmarks/scplantllm_public_sprint_input/reference_preprocess/chunks --scplantllm-dir external/scPlantLLM --weight-path model_params/scPlantLLM_model.pth --device cuda --batch-size 8 --max-train 2048 --max-test 2048 --output outputs/external_benchmarks/scplantllm_embedding_centroid_probe.json
```

## scPlantAnnotate

- Status: `auth_or_export_pending`
- Metrics path: `outputs/external_benchmarks/scplantannotate_final_metrics.json`
- Username env present: `False`
- Password env present: `False`

## Submission Rule

Only completed metric JSON files with accuracy and macro-F1 are reportable as third-party numerical comparators. Official source reachability, input readiness or partial weight downloads are evidence of closure progress, not completed superiority claims.
