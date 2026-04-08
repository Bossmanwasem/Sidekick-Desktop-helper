param(
    [string]$Configuration = "Release",
    [string]$Runtime = "win-x64"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

Write-Host "Publishing application..." -ForegroundColor Cyan
dotnet publish .\SidekickHelper.csproj -c $Configuration -r $Runtime --self-contained true -p:PublishSingleFile=true

$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    Write-Warning "Inno Setup compiler (ISCC.exe) was not found on PATH."
    Write-Host "Install Inno Setup from https://jrsoftware.org/isinfo.php and re-run this script." -ForegroundColor Yellow
    exit 0
}

Write-Host "Building installer with Inno Setup..." -ForegroundColor Cyan
& $iscc.Source ".\installer\SimpleFileZipper.iss"

if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed with exit code $LASTEXITCODE."
}

Write-Host "Installer created in .\\dist" -ForegroundColor Green
