$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sshDir = Join-Path $env:USERPROFILE ".ssh"
$path = Join-Path $sshDir "config"
$sourcePrivate = Join-Path $repoRoot "snowcell_matpool_px1_27683_ed25519"
$sourcePublic = "$sourcePrivate.pub"
$targetPrivate = Join-Path $sshDir "snowcell_matpool_px1_27683_ed25519"
$targetPublic = "$targetPrivate.pub"

if (!(Test-Path -LiteralPath $sourcePrivate) -or !(Test-Path -LiteralPath $sourcePublic)) {
  throw "Project SSH key not found: $sourcePrivate"
}

New-Item -ItemType Directory -Force -Path $sshDir | Out-Null
Copy-Item -LiteralPath $sourcePrivate -Destination $targetPrivate -Force
Copy-Item -LiteralPath $sourcePublic -Destination $targetPublic -Force
icacls $targetPrivate /inheritance:r /grant:r "$($env:USERNAME):F" | Out-Null

$backup = "{0}.bak_snowcell_{1}" -f $path, (Get-Date -Format "yyyyMMdd_HHmmss")

Copy-Item -LiteralPath $path -Destination $backup
$text = Get-Content -Raw -Encoding UTF8 -LiteralPath $path

$replacement = @"
Host matpool-px1-jcy px1-jcy.matpool.com
  HostName px1-jcy.matpool.com
  Port 27683
  User root
  PreferredAuthentications publickey,password,keyboard-interactive
  BatchMode yes
  PubkeyAuthentication yes
  PasswordAuthentication yes
  IdentityFile ~/.ssh/snowcell_matpool_px1_27683_ed25519
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 3
  StrictHostKeyChecking accept-new

"@

$pattern = '(?ms)^Host matpool-px1-jcy[^\r\n]*\r?\n.*?(?=^Host |\z)'
$updated = [regex]::Replace($text, $pattern, $replacement, 1)
if ($updated -eq $text) {
  throw "matpool-px1-jcy block not found or unchanged"
}

Set-Content -LiteralPath $path -Encoding UTF8 -Value $updated
Write-Output $backup
