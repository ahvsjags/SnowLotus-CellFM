# Plant-CellFM Post-v9 Continuation Operations

This note separates the frozen v9 editor package from post-v9 continuation work.

The frozen v9 package remains the editor-facing release. It is tied to the current GitHub branch, checksum-verified server zip, RTX 4090 service, model card, benchmark panel and release gate audit.

Post-v9 continuation work is allowed to collect additional public plant matrices and launch v10 refresh training, but it must not rewrite the v9 evidence package unless a new release is intentionally frozen.

## Disk-aware queue start

The Matpool `/mnt` volume can become full because it is shared with other projects. Do not start large downloads or retraining when `/mnt` is below the disk budget.

Use:

```bash
cd /mnt/snowlotus_cellfm
SNOWCELL_MIN_FREE_BYTES=21474836480 bash scripts/start_public_queues_when_space.sh
```

This starts a tmux watcher named `snowcell_public_queues_when_space`. The watcher checks `scripts/check_disk_budget.sh` and only launches `scripts/start_public_queues.sh` when the configured free-space budget is met.

## Status report

Use:

```bash
cd /mnt/snowlotus_cellfm
/root/miniconda3/envs/myconda/bin/python scripts/write_server_continuation_status_v10.py
```

The report is written to:

- `release_metadata/server_continuation_status_v10.md`
- `release_metadata/server_continuation_status_v10.json`

The report records disk state, queue tmux sessions, API health, GPU visibility, v9 package commit, v9 package SHA256, server verifier status and release gate position.

## Interpretation

If the report says `waiting_for_disk_budget`, the continuation machinery is ready but intentionally paused. Free space must be restored before public downloads or v10 training can resume safely.
