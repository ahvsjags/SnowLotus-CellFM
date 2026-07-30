# Plant-CellFM v9 Server Sustainability Status

Generated: 2026-07-30 16:57 Asia/Shanghai

## Git And Repository State

- Local branch: `agent/remote-pipeline-20260728`
- Local HEAD: `3a6273e7b871cb4265e55c3300d59242a1d29e48`
- GitHub branch head: `3a6273e7b871cb4265e55c3300d59242a1d29e48`
- GitHub branch URL: `https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728`
- GitHub TLS fix: repository-local `http.sslBackend=openssl`

The earlier Windows Git blocker was caused by the default Schannel TLS backend returning `SEC_E_NO_CREDENTIALS`. Fetch and push now work when the repository uses OpenSSL as the Git HTTPS backend.

## Remote Service State

Latest server health check:

```json
{
  "status": "ok",
  "service": "Plant-CellFM",
  "model_scope": "plant_general",
  "adapter_count": 24,
  "known_adapter_count": 24,
  "adapter_resolution": "dynamic_all_plants",
  "device": "cuda"
}
```

GPU state:

```text
NVIDIA GeForce RTX 4090, 24564 MiB, 1 MiB used, 0% utilization
```

The GPU is available but idle. This is acceptable for the frozen v9 submission package because the current task is release stabilization rather than continuing an unbounded v10 expansion run.

## Server Package

- Main package: `/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090`
- Addendum package: `/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090/addendum_methods_panel`
- Addendum checksum file: `addendum_sha256sums.txt`
- Latest addendum checksum verification: `OK`

The addendum package now contains `SUBMISSION_INDEX_v9.md`, the updated `README.md`, the v9 development plan, publication readiness audit, integrated Chinese manuscript, model card, external benchmark panel, Arabidopsis root case, Seurat benchmark JSON, v9/v3 benchmark JSON and generation scripts.

## Current Publishable Scope

The stable submission scope is:

1. Plant-CellFM v9 as a general plant single-cell expression foundation model.
2. A dynamic all-plant adapter framework with 24 known adapters plus runtime adapter materialization.
3. A frozen v9 LoRA checkpoint trained on audited public plant matrices on RTX 4090.
4. Strict leave-dataset, leave-sample and normalized leave-species benchmark reporting.
5. Completed v3, centroid and Seurat comparators.
6. Audited scPlantLLM and scPlantAnnotate execution interfaces, without claiming final metrics.
7. Arabidopsis root marker-candidate case as the current computational biology demonstration.
8. Snow Lotus as a target-species adapter entry point, not as a completed single-cell atlas.

## Remaining Non-Blocking Gaps

- scPlantLLM final metric is still gated by an executable official checkout and weights in the release environment.
- scPlantAnnotate final metric is still gated by authenticated or author-supported batch execution.
- Wet-lab or independent biological validation would strengthen a higher-tier revision but is not required for the current computational-method/resource submission package.
- The current frozen v9 run should not be presented as universal high-accuracy annotation for every plant species; the normalized leave-species open-set result is the correct cross-species headline.
