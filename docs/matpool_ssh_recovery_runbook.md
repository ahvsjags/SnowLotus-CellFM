# Matpool SSH recovery runbook

Generated context: SnowLotus-CellFM is prepared to continue through the `matpool-px1-jcy` SSH alias, currently reassigned to `root@px2-jcy.matpool.com:29153`.

## Current evidence

- Expected endpoint: `root@px2-jcy.matpool.com:29153`
- Expected alias: `matpool-px1-jcy`
- Expected identity: `~/.ssh/snowcell_matpool_px1_27683_ed25519`
- Current observed GPU on the reassigned host: `NVIDIA GeForce RTX 4090, 24564 MiB`.
- Last observed local failure mode: TCP and SSH both return `Connection refused`.
- Interpretation: the local alias and key can be correct while the remote Matpool port is not accepting connections. This is different from an SSH authentication failure.

## Quick checks

```powershell
$ProjectRoot = (Resolve-Path .).Path
ssh -G matpool-px1-jcy | Select-String -Pattern '^(hostname|port|user|identityfile|batchmode) '
Test-NetConnection px2-jcy.matpool.com -Port 29153
Get-Content -Tail 30 (Join-Path $ProjectRoot "logs\wait_and_start_remote_full_on_disk.log")
```

If `ssh -G` shows `hostname px2-jcy.matpool.com`, `port 29153`, and `user root`, but `Test-NetConnection` is false or `ssh` returns `Connection refused`, the immediate blocker is the remote endpoint/port rather than the local alias.

## If Matpool assigns a new port

Run this from the project root, replacing `<NEW_PORT>` with the new Matpool port:

```powershell
$ProjectRoot = (Resolve-Path .).Path
powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\update_matpool_px1_alias.ps1") -Port <NEW_PORT>
```

Alternatively, write the new port to the watcher hint file:

```powershell
$ProjectRoot = (Resolve-Path .).Path
Set-Content -Encoding ascii -Path (Join-Path $ProjectRoot "config\matpool_px1_next_port.txt") -Value "<NEW_PORT>"
```

The local recovery watcher checks this file before every SSH probe. If the value is a valid port and differs from the current alias, it updates `matpool-px1-jcy` automatically before continuing.

If Matpool shows several candidate ports or the UI changed while the server is coming back, write only those explicit candidates to:

```powershell
$ProjectRoot = (Resolve-Path .).Path
Set-Content -Encoding ascii -Path (Join-Path $ProjectRoot "config\matpool_px1_candidate_ports.txt") -Value @(
  "29153",
  "<NEW_PORT>"
)
python -X utf8 (Join-Path $ProjectRoot "scripts\probe_matpool_candidate_ports.py") `
  --host px2-jcy.matpool.com `
  --ports-file (Join-Path $ProjectRoot "config\matpool_px1_candidate_ports.txt") `
  --write-hint-if-open (Join-Path $ProjectRoot "config\matpool_px1_next_port.txt") `
  --output-md (Join-Path $ProjectRoot "editor_package\current_submit_v0.3\matpool_candidate_port_probe.local.md") `
  --output-json (Join-Path $ProjectRoot "editor_package\current_submit_v0.3\matpool_candidate_port_probe.local.json")
```

The probe only checks ports listed in the candidate file. It does not scan ranges unless `--allow-ranges` is explicitly provided.

The local recovery watcher now performs the same candidate-port probe automatically before each SSH attempt if `config\matpool_px1_candidate_ports.txt` exists. When any listed port opens, the probe writes `config\matpool_px1_next_port.txt`; the watcher then updates the `matpool-px1-jcy` alias and continues the remote startup path.

Then restart the local recovery watcher:

```powershell
Get-Process powershell | Where-Object { $_.Path -like '*powershell*' }
powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\wait_and_start_remote_full_on_disk.ps1") -Alias matpool-px1-jcy -ProjectDir /mnt/snowlotus_cellfm
```

The recovery watcher uploads the full on-disk corpus scripts, starts the remote tmux job, runs `scripts/collect_remote_training_state.sh`, and fetches `remote_training_state.after_recovery.md/json` into the submit package.

## Refresh the editor package after a status change

Use this one-shot helper after restarting the watcher, changing a candidate port file, or syncing a new GitHub commit:

```powershell
$ProjectRoot = (Resolve-Path .).Path
python -X utf8 (Join-Path $ProjectRoot "scripts\refresh_editor_submit_package.py") `
  --root $ProjectRoot `
  --watcher-pid <WATCHER_PID> `
  --github-commit <CURRENT_GITHUB_COMMIT>
```

The helper refreshes `ssh_recovery_status.local.md/json`, `ARCHIVE_SHA256SUMS.txt`, `SUBMISSION_STATUS_NOW.md`, and `SnowLotus-CellFM_editor-v0.3_submit-now.zip` with its `.sha256` sidecar.

## Remote job expected after recovery

- tmux session: `snowcell_public_mlm_full_on_disk_corpus`
- remote log: `/mnt/snowlotus_cellfm/logs/public_mlm_full_on_disk_corpus.log`
- remote audit: `/mnt/snowlotus_cellfm/outputs/recovery_audit/remote_training_state_latest.md`
- local fetched audit: `$ProjectRoot\editor_package\current_submit_v0.3\remote_training_state.after_recovery.md`
