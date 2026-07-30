# Plant-CellFM v9 Final Editor Submission Package Recipe

Generated: 2026-07-30 17:49 Asia/Shanghai

This file records how to regenerate the final editor-facing Plant-CellFM v9 submission package from the repository. The generated archive itself is kept under `outputs/` and on the Matpool server rather than committed to the source tree.

## Command

```bash
python scripts/package_v9_editor_submission.py
```

## Default Outputs

- Package directory: `outputs/editor_submission_v9`
- Zip package: `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.zip`
- SHA256 sidecar: `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.zip.sha256`
- Package status JSON: `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.status.json`
- Package status Markdown: `outputs/editor_submission_v9/Plant_CellFM_v9_editor_submission_final.status.md`
- Peer-review preflight: `release_metadata/publication_peer_review_preflight_v9.md`

## Package Scope

The package contains the current v9 submission index, final Chinese Word manuscript with ASCII file path, README, publication readiness audit, model card, data card, release notes, editor issue closure, stability audit, server sustainability audit, live API smoke evidence, watchdog recovery evidence, external benchmark panel, Seurat baseline result, centroid baselines, v9-v3 benchmark JSON, Arabidopsis root case, Arabidopsis root literature anchor, adapter registry, scPlantLLM/scPlantAnnotate audit files and model asset pointer.

The package intentionally does not duplicate the large checkpoint. It records the GitHub release asset and SHA256:

- Release asset: `https://github.com/ahvsjags/SnowLotus-CellFM/releases/download/v0.9.0-plant-general-lora/SnowLotus-CellFM-v9-lora-4090-best.pt`
- SHA256: `9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`

## Claim Boundary

The package supports a computational method/resource submission. It does not claim universal high-accuracy zero-shot annotation for every plant species, a completed Snow Lotus single-cell atlas, or final scPlantLLM/scPlantAnnotate numeric superiority without executable third-party metric evidence.
