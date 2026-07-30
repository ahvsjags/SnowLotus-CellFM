# Plant-CellFM v10 Continuation Status

Generated UTC: `2026-07-30T16:11:29.513102+00:00`

Project root: `/mnt/snowlotus_cellfm`

Continuation state: `waiting_for_disk_budget`

Disk budget OK: `False`

Required free space: `20.00 GB`

Project disk free: `692.00 MB` on `/mnt` (100% used)

Root disk free: `61.47 GB` on `/` (70% used)

Root staging exists: `True` at `/root/snowlotus_cellfm_v10`

Root staging disk free: `61.47 GB` on `/` (70% used)

Root staging scPlantDB manifest rows: `4`

Root staging scPlantDB H5AD files: `4`; total size `170.80 MB`

Root v10 scPlantDB training exists: `True` at `/root/snowlotus_cellfm_v10_scplantdb_lora_4090`

Root v10 scPlantDB training epochs: `2`; best epoch by eval loss `2`

Root v10 scPlantDB test fine accuracy: `0.06689453125`; coarse accuracy `0.021484375`

Health: `ok`; scope `plant_general`; device `cuda`; adapters `24`

GPU: `NVIDIA GeForce RTX 4090, 24564 MiB, 1 MiB, 0 %`

Final package commit: `35857f667bd277777e93373551a1e01707ce2c6d`

Final package SHA256: `f0dbad6f437557e481c5412d3a5dc21639cbe369cc39e200ccc0762ccca65500`

Server verifier status: `pass`

Release gate position: `release_ready_current_gates_pass`

## Active Queue Sessions

- `snowcell_public_queues_when_space`

## All tmux Sessions

- `plant_cellfm_watchdog`
- `snowcell_public_queues_when_space`

## Root Staging scPlantDB Files

- `SRP164771.h5ad`
- `SRP241596.h5ad`
- `SRP285040.h5ad`
- `SRP386976.h5ad`

## Root v10 scPlantDB Training

- Output: `/root/snowlotus_cellfm_v10_scplantdb_lora_4090`
- Epochs recorded: `2`
- Last train loss: `8.935744511894882`
- Last eval loss: `8.71316534280777`
- Last eval fine accuracy: `0.02978515625`
- Last eval coarse accuracy: `0.2626953125`
- Test fine accuracy: `0.06689453125`
- Test coarse accuracy: `0.021484375`
- Best checkpoint exists: `True`; size `139.88 MB`
- Latest checkpoint exists: `True`; size `387.50 MB`

## Interpretation

This report is for post-v9 continuation work. It does not change the frozen v9 editor package. When the project disk has less free space than the configured budget, public data download and GPU retraining queues should remain paused or waiting. Once disk budget is restored, the queue watcher can start `scripts/start_public_queues.sh` to continue public plant data acquisition and v10 training refresh work.
