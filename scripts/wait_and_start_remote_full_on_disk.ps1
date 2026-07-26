param(
    [string]$Alias = "matpool-px1-jcy",
    [string]$ProjectDir = "/root/snowlotus-cellfm",
    [int]$IntervalSeconds = 60,
    [int]$MaxAttempts = 240,
    [string]$Root = "",
    [string]$LogPath = ""
)

$ErrorActionPreference = "Continue"

if (-not $Root) {
    $Root = Split-Path -Parent $PSScriptRoot
}
if (-not $LogPath) {
    $LogPath = Join-Path $Root "logs\wait_and_start_remote_full_on_disk.log"
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
    $line = "[$timestamp] $Message"
    $logDir = Split-Path -Parent $LogPath
    if ($logDir -and -not (Test-Path -LiteralPath $logDir)) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    }
    Add-Content -Encoding utf8 -Path $LogPath -Value $line
    Write-Output $line
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$Label
    )
    Write-Log "$Label :: $FilePath $($Arguments -join ' ')"
    $proc = Start-Process -FilePath $FilePath -ArgumentList $Arguments -NoNewWindow -PassThru -Wait
    if ($proc.ExitCode -ne 0) {
        throw "$Label failed with exit code $($proc.ExitCode)"
    }
}

$scriptFiles = @(
    "scripts/build_public_mlm_corpus_on_disk.py",
    "scripts/build_public_mlm_full_on_disk_corpus.sh",
    "scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh",
    "scripts/collect_remote_training_state.sh",
    "tests/test_on_disk_corpus_builder.py"
)

Write-Log "watcher starting alias=$Alias project=$ProjectDir root=$Root attempts=$MaxAttempts interval=${IntervalSeconds}s"

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Write-Log "attempt $attempt/${MaxAttempts}: probing SSH"
    $sshOptions = @("-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=1")
    $probe = Start-Process -FilePath "ssh" -ArgumentList @($sshOptions + @($Alias, "hostname")) -NoNewWindow -PassThru -Wait
    if ($probe.ExitCode -ne 0) {
        Write-Log "SSH probe failed exit=$($probe.ExitCode); sleeping ${IntervalSeconds}s"
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }

    try {
        Write-Log "SSH is up; uploading full on-disk corpus scripts"
        $prepareCommand = "cd '$ProjectDir' && mkdir -p scripts tests logs outputs/recovery_audit"
        Invoke-Checked -FilePath "ssh" -Arguments @($sshOptions + @($Alias, $prepareCommand)) -Label "prepare remote directories"
        foreach ($relative in $scriptFiles) {
            $local = Join-Path $Root $relative
            if (-not (Test-Path -LiteralPath $local)) {
                throw "missing local file: $local"
            }
            $remote = "$Alias`:$ProjectDir/$($relative -replace '\\','/')"
            Invoke-Checked -FilePath "scp" -Arguments @($sshOptions + @($local, $remote)) -Label "scp $relative"
        }

        $remoteCommand = "cd '$ProjectDir' && mkdir -p scripts tests logs outputs/recovery_audit && chmod +x scripts/build_public_mlm_corpus_on_disk.py scripts/build_public_mlm_full_on_disk_corpus.sh scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh scripts/collect_remote_training_state.sh && bash scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh && bash scripts/collect_remote_training_state.sh && tmux ls"
        Invoke-Checked -FilePath "ssh" -Arguments @($sshOptions + @($Alias, $remoteCommand)) -Label "start remote full on-disk corpus tmux job"
        $packageDir = Join-Path $Root "editor_package\current_submit_v0.3"
        if (-not (Test-Path -LiteralPath $packageDir)) {
            New-Item -ItemType Directory -Force -Path $packageDir | Out-Null
        }
        try {
            Invoke-Checked -FilePath "scp" -Arguments @($sshOptions + @("$Alias`:$ProjectDir/outputs/recovery_audit/remote_training_state_latest.json", (Join-Path $packageDir "remote_training_state.after_recovery.json"))) -Label "fetch remote training state json"
            Invoke-Checked -FilePath "scp" -Arguments @($sshOptions + @("$Alias`:$ProjectDir/outputs/recovery_audit/remote_training_state_latest.md", (Join-Path $packageDir "remote_training_state.after_recovery.md"))) -Label "fetch remote training state md"
        }
        catch {
            Write-Log "remote audit fetch failed after startup: $($_.Exception.Message)"
        }
        Write-Log "remote full on-disk corpus watcher started successfully"
        exit 0
    }
    catch {
        Write-Log "startup attempt failed: $($_.Exception.Message)"
        Start-Sleep -Seconds $IntervalSeconds
    }
}

Write-Log "watcher exhausted attempts without successful remote startup"
exit 2
