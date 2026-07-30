# Plant-CellFM v9 Watchdog Recovery Status

Generated: 2026-07-30 17:16 Asia/Shanghai

## Purpose

This audit verifies that the Plant-CellFM v9 service is not merely a one-off process. A tmux watchdog is running on the server and can automatically restart the deployed inference service after the service process exits.

## Watchdog

| Field | Value |
| --- | --- |
| Session | `plant_cellfm_watchdog` |
| Runner | `tmux` |
| Script | `scripts/watch_plant_cellfm_service.sh` |
| Project directory | `/mnt/snowlotus_cellfm` |
| Log file | `/root/snowlotus_cellfm_v9_lora_shared_4090/service_watchdog.log` |
| Status | `running` |

## Controlled Recovery Test

The existing Plant-CellFM service process was terminated with `SIGTERM` in a controlled test. The watchdog detected the missing service and restarted it.

| Field | Value |
| --- | --- |
| Old service PID | `648368` |
| New service PID | `654567` |
| Recovery time | `30 seconds` |
| Recovery result | `passed` |
| Health after recovery | `status=ok`, `model_scope=plant_general`, `adapter_resolution=dynamic_all_plants`, `device=cuda` |

## Post-Recovery Process Evidence

After recovery, the service process is a child of the watchdog shell:

```text
watchdog pid: 654450
service pid: 654567
service parent pid: 654450
```

The restarted service uses the frozen v9 checkpoint and the public v9 data root:

```text
scripts/serve_snowlotus.py
--backbone-checkpoint /root/snowlotus_cellfm_v9_lora_shared_4090/best.pt
--annotation-checkpoint /root/snowlotus_cellfm_v9_lora_shared_4090/best.pt
--data-root /root/snowlotus_public_plants_v9
--adapter-registry /mnt/snowlotus_cellfm/release_metadata/plant_species_adapters.json
--device cuda
```

## Interpretation

The deployed Plant-CellFM v9 server now has verified process-level sustainability evidence: a live tmux watchdog, a controlled restart test, a recovered CUDA service and an OK health response after restart.
