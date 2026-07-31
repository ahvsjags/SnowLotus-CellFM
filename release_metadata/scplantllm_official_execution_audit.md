# scPlantLLM Official Execution Audit

- Audit status: **passed**
- Execution state: `official_encoder_executed_on_official_chunks_not_matched_to_plant_cellfm_v17`
- Probe record: `release_metadata/scplantllm_official_data_embedding_probe_256.json`

## Verified execution facts

- CUDA execution: `True`
- Checkpoint bytes: `431801156`
- Missing/unexpected state keys: `0` / `0`
- Stratified official train/test cells: `256` / `256`
- Probe accuracy / macro-F1: `0.839844` / `0.840813`

## Interpretation boundary

- The official scPlantLLM checkpoint was loaded and executed on CUDA after documented FlashMHA-to-PyTorch attention-key conversion.
- The recorded metric is a frozen-encoder cosine-nearest-centroid representation probe on scPlantLLM's own 256-cell stratified train and test subsets.
- This is not the scPlantLLM classifier head, not a matched input to Plant-CellFM v17, and not evidence of numerical superiority by either method.

## Requirement before a formal external ranking

- Acquire a frozen Plant-CellFM v17-compatible raw matrix and run both methods under a shared gene, label, split and open-set scoring contract.
