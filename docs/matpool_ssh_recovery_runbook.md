# Matpool SSH recovery runbook

Generated context: SnowLotus-CellFM is prepared to continue on the RTX 5090 host through the `matpool-px1-jcy` SSH alias.

## Current evidence

- Expected endpoint: `root@px1-jcy.matpool.com:27683`
- Expected alias: `matpool-px1-jcy`
- Expected identity: `~/.ssh/snowcell_matpool_px1_27683_ed25519`
- Last observed local failure mode: TCP and SSH both return `Connection refused`.
- Interpretation: the local alias and key can be correct while the remote Matpool port is not accepting connections. This is different from an SSH authentication failure.

## Quick checks

```powershell
$ProjectRoot = (Resolve-Path .).Path
ssh -G matpool-px1-jcy | Select-String -Pattern '^(hostname|port|user|identityfile|batchmode) '
Test-NetConnection px1-jcy.matpool.com -Port 27683
Get-Content -Tail 30 (Join-Path $ProjectRoot "logs\wait_and_start_remote_full_on_disk.log")
```

If `ssh -G` shows `hostname px1-jcy.matpool.com`, `port 27683`, and `user root`, but `Test-NetConnection` is false or `ssh` returns `Connection refused`, the immediate blocker is the remote endpoint/port rather than the local alias.

## If Matpool assigns a new port

Run this from the project root, replacing `<NEW_PORT>` with the new Matpool port:

```powershell
$ProjectRoot = (Resolve-Path .).Path
powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\update_matpool_px1_alias.ps1") -Port <NEW_PORT>
```

Then restart the local recovery watcher:

```powershell
Get-Process powershell | Where-Object { $_.Path -like '*powershell*' }
powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\wait_and_start_remote_full_on_disk.ps1") -Alias matpool-px1-jcy -ProjectDir /root/snowlotus-cellfm
```

The recovery watcher uploads the full on-disk corpus scripts, starts the remote tmux job, runs `scripts/collect_remote_training_state.sh`, and fetches `remote_training_state.after_recovery.md/json` into the submit package.

## Remote job expected after recovery

- tmux session: `snowcell_public_mlm_full_on_disk_corpus`
- remote log: `/root/snowlotus-cellfm/logs/public_mlm_full_on_disk_corpus.log`
- remote audit: `/root/snowlotus-cellfm/outputs/recovery_audit/remote_training_state_latest.md`
- local fetched audit: `$ProjectRoot\editor_package\current_submit_v0.3\remote_training_state.after_recovery.md`
