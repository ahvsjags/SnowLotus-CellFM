param(
    [string]$Alias = "matpool-px1-jcy",
    [string]$ProjectDir = "/root/snowlotus-cellfm",
    [int]$IntervalSeconds = 60,
    [int]$MaxAttempts = 240,
    [string]$LogPath = "D:\天山雪莲\logs\wait_and_start_remote_full_on_disk.log"
)

$ErrorActionPreference = "Continue"

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

$root = "D:\天山雪莲"
$scriptFiles = @(
    "scripts/build_public_mlm_corpus_on_disk.py",
    "scripts/build_public_mlm_full_on_disk_corpus.sh",
    "scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh",
    "tests/test_on_disk_corpus_builder.py"
)

Write-Log "watcher starting alias=$Alias project=$ProjectDir attempts=$MaxAttempts interval=${IntervalSeconds}s"

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Write-Log "attempt $attempt/${MaxAttempts}: probing SSH"
    $probe = Start-Process -FilePath "ssh" -ArgumentList @($Alias, "hostname") -NoNewWindow -PassThru -Wait
    if ($probe.ExitCode -ne 0) {
        Write-Log "SSH probe failed exit=$($probe.ExitCode); sleeping ${IntervalSeconds}s"
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }

    try {
        Write-Log "SSH is up; uploading full on-disk corpus scripts"
        foreach ($relative in $scriptFiles) {
            $local = Join-Path $root $relative
            if (-not (Test-Path -LiteralPath $local)) {
                throw "missing local file: $local"
            }
            $remote = "$Alias`:$ProjectDir/$($relative -replace '\\','/')"
            Invoke-Checked -FilePath "scp" -Arguments @($local, $remote) -Label "scp $relative"
        }

        $remoteCommand = "cd '$ProjectDir' && chmod +x scripts/build_public_mlm_corpus_on_disk.py scripts/build_public_mlm_full_on_disk_corpus.sh scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh && bash scripts/start_public_mlm_full_on_disk_corpus_watchdog.sh && tmux ls"
        Invoke-Checked -FilePath "ssh" -Arguments @($Alias, $remoteCommand) -Label "start remote full on-disk corpus tmux job"
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
