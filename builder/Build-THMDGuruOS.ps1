<#
.SYNOPSIS
    THMD-Guru OS Forge — Windows PowerShell Build Launcher (Docker / WSL2)
    Owner: os-forge-devops
.DESCRIPTION
    Builds THMD-Guru Linux (Desktop, Server, ATTT) ISOs from Windows using either
    Docker Desktop ( privileged Debian 12 container ) or WSL2 Debian/Ubuntu.
.PARAMETER Action
    Action to run: smoke-test | stage | packages | iso | all
.PARAMETER Edition
    Target edition: desktop | server | attt (default: desktop)
#>
param(
    [ValidateSet("smoke-test", "stage", "packages", "iso", "all")]
    [string]$Action = "iso",

    [ValidateSet("desktop", "server", "attt")]
    [string]$Edition = "desktop"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host "  THMD-GURU OS FORGE — GLOBAL TECH ACADEMY (Windows Launcher)" -ForegroundColor Cyan
Write-Host "  Action: $Action | Edition: $Edition" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Yellow

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "[OS Forge] Detected Docker Engine. Building container image thmd-guru-forge:bookworm..." -ForegroundColor Green
    docker build -t thmd-guru-forge:bookworm -f "$RepoRoot\builder\Dockerfile" "$RepoRoot"
    if ($Action -eq "smoke-test") {
        docker run --rm -v "${RepoRoot}:/workspace" --entrypoint /bin/bash thmd-guru-forge:bookworm tests/smoke-test.sh
    } else {
        docker run --rm --privileged -v "${RepoRoot}:/workspace" thmd-guru-forge:bookworm $Action $Edition
    }
    exit $LASTEXITCODE
}

$wslDistros = wsl -l -q 2>$null
if ($LASTEXITCODE -eq 0 -and $wslDistros) {
    Write-Host "[OS Forge] Detected WSL2. Running via WSL..." -ForegroundColor Green
    $wslPath = wsl wslpath -a "$RepoRoot"
    if ($Action -eq "smoke-test") {
        wsl bash -lc "cd '$wslPath' && bash tests/smoke-test.sh"
    } else {
        wsl sudo bash -lc "cd '$wslPath' && bash builder/forge.sh $Action $Edition"
    }
    exit $LASTEXITCODE
}

Write-Warning "Chưa phát hiện Docker Desktop hoặc WSL2 trên máy Windows này."
Write-Host "Để biên dịch ra file .iso thực tế, vui lòng cài đặt 1 trong 2 công cụ:" -ForegroundColor Cyan
Write-Host "  1. Docker Desktop: winget install Docker.DockerDesktop"
Write-Host "  2. WSL2 Debian 12: wsl --install -d Debian"
exit 1
