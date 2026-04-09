param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

Write-Host "Building EXE with PyInstaller..." -ForegroundColor Cyan

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    throw "Python was not found on PATH. Install Python 3.10+ and re-run this script."
}

$arguments = @("scripts/build-installer.py")
if ($Clean) {
    $arguments += "--clean"
}

& $pythonCmd.Source @arguments

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE."
}

Write-Host "Executable created in .\\dist" -ForegroundColor Green
