$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
& ./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt -r requirements-cpu.txt
if ($LASTEXITCODE -ne 0) { throw 'Development dependency installation failed.' }
& ./.venv/Scripts/python.exe -m scripts.setup_models
if ($LASTEXITCODE -ne 0) { throw 'Model acquisition failed.' }
Write-Output 'Launch: ./.venv/Scripts/python.exe -m app.core.server'
