# Run from repo root: .\backend\start.ps1
# Or from anywhere: & ".\backend\start.ps1" (from repo root)
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$env:PYTHONPATH = Join-Path $RepoRoot "py"
python -m uvicorn backend.main:app --reload --port 8000
