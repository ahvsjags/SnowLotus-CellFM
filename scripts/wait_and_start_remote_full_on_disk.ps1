param(
    [string]$Alias = "matpool-px1-jcy",
    [string]$ProjectDir = "/root/snowlotus-cellfm",
    [int]$IntervalSeconds = 60,
    [int]$MaxAttempts = 240,
    [string]$Root = "",
    [string]$LogPath = "",
    [string]$PortHintPath = "",
    [string]$CandidatePortsPath = "",
    [string]$CandidateProbeReportPath = "",
    [string]$CandidateProbeJsonPath = "",
    [string]$HostName = "",
    [int]$CandidateProbeMaxPorts = 64,
    [double]$CandidateProbeTimeoutSeconds = 5.0
)

$ErrorActionPreference = "Continue"

if (-not $Root) {
    $Root = Split-Path -Parent $PSScriptRoot
}
if (-not $LogPath) {
    $LogPath = Join-Path $Root "logs\wait_and_start_remote_full_on_disk.log"
}
if (-not $PortHintPath) {
    $PortHintPath = Join-Path $Root "config\matpool_px1_next_port.txt"
}
if (-not $CandidatePortsPath) {
    $CandidatePortsPath = Join-Path $Root "config\matpool_px1_candidate_ports.txt"
}
if (-not $CandidateProbeReportPath) {
    $CandidateProbeReportPath = Join-Path $Root "editor_package\current_submit_v0.3\matpool_candidate_port_probe.local.md"
}
if (-not $CandidateProbeJsonPath) {
    $CandidateProbeJsonPath = Join-Path $Root "editor_package\current_submit_v0.3\matpool_candidate_port_probe.local.json"
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

function Get-AliasPort {
    param([string]$AliasName)
    $proc = & ssh -G $AliasName 2>$null
    foreach ($line in $proc) {
        if ($line -match '^port\s+(\d+)$') {
            return [int]$Matches[1]
        }
    }
    return $null
}

function Get-AliasHost {
    param([string]$AliasName)
    $proc = & ssh -G $AliasName 2>$null
    foreach ($line in $proc) {
        if ($line -match '^hostname\s+(.+)$') {
            return $Matches[1]
        }
    }
    return $null
}

function Invoke-Candidate-Port-Probe {
    if (-not (Test-Path -LiteralPath $CandidatePortsPath)) {
        return
    }
    $probeScript = Join-Path $Root "scripts\probe_matpool_candidate_ports.py"
    if (-not (Test-Path -LiteralPath $probeScript)) {
        Write-Log "candidate ports file present but probe script missing: $probeScript"
        return
    }
    $targetHost = $HostName
    if (-not $targetHost) {
        $targetHost = Get-AliasHost -AliasName $Alias
    }
    if (-not $targetHost) {
        Write-Log "candidate port probe skipped because alias host could not be resolved"
        return
    }
    $reportDir = Split-Path -Parent $CandidateProbeReportPath
    if ($reportDir -and -not (Test-Path -LiteralPath $reportDir)) {
        New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
    }
    $jsonDir = Split-Path -Parent $CandidateProbeJsonPath
    if ($jsonDir -and -not (Test-Path -LiteralPath $jsonDir)) {
        New-Item -ItemType Directory -Force -Path $jsonDir | Out-Null
    }
    Write-Log "candidate port probe: host=$targetHost ports=$CandidatePortsPath hint=$PortHintPath"
    $probeArgs = @(
        "-X", "utf8",
        $probeScript,
        "--host", $targetHost,
        "--ports-file", $CandidatePortsPath,
        "--timeout", "$CandidateProbeTimeoutSeconds",
        "--max-ports", "$CandidateProbeMaxPorts",
        "--write-hint-if-open", $PortHintPath,
        "--output-md", $CandidateProbeReportPath,
        "--output-json", $CandidateProbeJsonPath
    )
    $output = & python @probeArgs 2>&1
    $exitCode = $LASTEXITCODE
    foreach ($line in $output) {
        Write-Log "candidate port probe output: $line"
    }
    if ($exitCode -ne 0) {
        Write-Log "candidate port probe failed exit=$exitCode"
    }
}

function Apply-Port-Hint {
    if (-not (Test-Path -LiteralPath $PortHintPath)) {
        return
    }
    $raw = (Get-Content -Raw -LiteralPath $PortHintPath).Trim()
    if (-not $raw) {
        return
    }
    if ($raw -notmatch '^\d{1,5}$') {
        Write-Log "ignoring invalid port hint in ${PortHintPath}: $raw"
        return
    }
    $nextPort = [int]$raw
    if ($nextPort -lt 1 -or $nextPort -gt 65535) {
        Write-Log "ignoring out-of-range port hint in ${PortHintPath}: $raw"
        return
    }
    $validationOptions = @(
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        "-o", "ServerAliveInterval=5",
        "-o", "ServerAliveCountMax=1",
        "-o", "Port=$nextPort"
    )
    $validation = Start-Process -FilePath "ssh" -ArgumentList @($validationOptions + @($Alias, "test -d '$ProjectDir'")) -NoNewWindow -PassThru -Wait
    if ($validation.ExitCode -ne 0) {
        Write-Log "rejecting port hint ${nextPort}: SSH/project validation failed exit=$($validation.ExitCode)"
        return
    }
    $currentPort = Get-AliasPort -AliasName $Alias
    if ($currentPort -eq $nextPort) {
        return
    }
    $updater = Join-Path $Root "scripts\update_matpool_px1_alias.ps1"
    if (-not (Test-Path -LiteralPath $updater)) {
        Write-Log "port hint present but updater missing: $updater"
        return
    }
    Write-Log "applying port hint: $Alias port $currentPort -> $nextPort"
    $proc = Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $updater, "-Alias", $Alias, "-Port", "$nextPort") -NoNewWindow -PassThru -Wait
    if ($proc.ExitCode -ne 0) {
        Write-Log "port hint update failed exit=$($proc.ExitCode)"
    } else {
        Write-Log "port hint update completed for $Alias -> $nextPort"
    }
}

$scriptFiles = @(
    "scripts/build_public_mlm_corpus_on_disk.py",
    "scripts/build_public_mlm_full_on_disk_corpus.sh",
    "scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh",
    "scripts/start_public_mlm_continuation_training.sh",
    "scripts/watch_public_mlm_continuation.sh",
    "scripts/start_public_mlm_continuation_watchdog.sh",
    "scripts/watch_publication_package_refresh.sh",
    "scripts/start_public_mlm_continuation_package_watchdog.sh",
    "scripts/collect_remote_training_state.sh",
    "tests/test_on_disk_corpus_builder.py"
)

Write-Log "watcher starting alias=$Alias project=$ProjectDir root=$Root portHint=$PortHintPath candidatePorts=$CandidatePortsPath attempts=$MaxAttempts interval=${IntervalSeconds}s"

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Invoke-Candidate-Port-Probe
    Apply-Port-Hint
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

        $remoteCommand = "cd '$ProjectDir' && mkdir -p scripts tests logs outputs/recovery_audit && chmod +x scripts/build_public_mlm_corpus_on_disk.py scripts/build_public_mlm_full_on_disk_corpus.sh scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh scripts/start_public_mlm_continuation_training.sh scripts/watch_public_mlm_continuation.sh scripts/start_public_mlm_continuation_watchdog.sh scripts/watch_publication_package_refresh.sh scripts/start_public_mlm_continuation_package_watchdog.sh scripts/collect_remote_training_state.sh && bash scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh && bash scripts/start_public_mlm_continuation_watchdog.sh && bash scripts/start_public_mlm_continuation_package_watchdog.sh && bash scripts/collect_remote_training_state.sh && tmux ls"
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
