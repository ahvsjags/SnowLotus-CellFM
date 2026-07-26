$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONPATH = Join-Path $root "src"
$log = Join-Path $root "logs\local_gse146034_pretrain_8e_512.log"
$err = Join-Path $root "logs\local_gse146034_pretrain_8e_512.err.log"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $log) | Out-Null
& python -X utf8 -m snowcell.cli train --config configs\local_gse146034_pretrain_8e.yaml --device cuda 1>>$log 2>>$err
exit $LASTEXITCODE
