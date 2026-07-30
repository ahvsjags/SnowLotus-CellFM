# Plant-CellFM v9 Server Sustainability Status

Generated: 2026-07-30 20:12 Asia/Shanghai

## Git And Repository State

- Local branch: `agent/remote-pipeline-20260728`
- Current local and GitHub branch heads should be verified with `git rev-parse HEAD origin/agent/remote-pipeline-20260728`.
- GitHub branch URL: `https://github.com/ahvsjags/SnowLotus-CellFM/tree/agent/remote-pipeline-20260728`
- GitHub fetch transport: repository-local `http.sslBackend=openssl`
- Current GitHub push blocker: workstation `gh` token is invalid; latest local/server package may be ahead of the public branch until GitHub authentication is refreshed.

The earlier Windows Git transport blocker was caused by the default Schannel TLS backend returning `SEC_E_NO_CREDENTIALS`. Fetch works when the repository uses OpenSSL as the Git HTTPS backend. Push is currently gated by GitHub authentication, not by SSH access to the Matpool server. The final editor zip therefore includes `GITHUB_SYNC_RECOVERY.md`, and the server keeps bundle/patch/tar recovery artifacts under `/mnt/snowlotus_cellfm/outputs/editor_submission_v9/`.

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

## Runtime Annotation Smoke Test

The live `POST /annotate` route passed an end-to-end smoke test on 2026-07-30. The request used `/root/snowlotus_public_plants_v9/v9_benchmark_subset_256_shared_genes.h5ad`, species `Arabidopsis thaliana`, annotation mode and batch size 64. The service resolved `plant_arabidopsis_thaliana` without fallback and wrote predictions, embeddings, metadata and adapter-selection artifacts to `/mnt/snowlotus_cellfm/outputs/runtime_smoke_v9_annotation_20260730_1659`.

- Cells annotated: `3964`
- Embedding shape: `3964 x 256`
- Prediction rows: `3965`, including header
- Evidence file: `release_metadata/api_runtime_smoke_v9.md`

## Watchdog Recovery Test

The server also passed a controlled process-recovery test. A tmux session named `plant_cellfm_watchdog` is running `scripts/watch_plant_cellfm_service.sh`. During the test, the active service process `648368` was terminated with `SIGTERM`; the watchdog restarted the service as PID `654567` and restored a healthy `/health` response after 30 seconds.

- Watchdog session: `plant_cellfm_watchdog`
- Watchdog script: `scripts/watch_plant_cellfm_service.sh`
- Recovery result: `passed`
- Evidence file: `release_metadata/watchdog_recovery_status_v9.md`

## Server Package

- Main package: `/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090`
- Addendum package: `/mnt/snowlotus_cellfm/outputs/publication_package/v9_lora_shared_4090/addendum_methods_panel`
- Final editor package: `/mnt/snowlotus_cellfm/outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.zip`
- Server release verifier: `scripts/verify_v9_server_release.py`
- Addendum checksum file: `addendum_sha256sums.txt`
- Latest addendum checksum verification: `OK`

The addendum package now contains `SUBMISSION_INDEX_v9.md`, the updated `README.md`, the v9 development plan, publication readiness audit, integrated Chinese manuscript, model card, external benchmark panel, Arabidopsis root case, Seurat benchmark JSON, v9/v3 benchmark JSON, species ontology coverage audit, ontology-label species benchmark and generation scripts.

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
