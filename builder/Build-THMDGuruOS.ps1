<#
.SYNOPSIS
    THMD-Guru OS Forge -- Windows PowerShell Build Launcher
    Owner: os-forge-devops
.DESCRIPTION
    Builds THMD-Guru Linux (Desktop, Server, ATTT) packages and ISOs from Windows
    using Docker Desktop, WSL2, or the built-in Portable Native Builder (Git Bash + Python ISO-9660).
#>
param(
    [ValidateSet("smoke-test", "stage", "packages", "iso", "all")]
    [string]$Action = "all",

    [ValidateSet("desktop", "server", "attt")]
    [string]$Edition = "desktop"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot

try {
    Write-Host "====================================================================" -ForegroundColor Yellow
    Write-Host "  THMD-GURU OS FORGE -- GLOBAL TECH ACADEMY (Windows Launcher)" -ForegroundColor Cyan
    Write-Host "  Action: $Action | Edition: $Edition" -ForegroundColor Yellow
    Write-Host "====================================================================" -ForegroundColor Yellow

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Host "[OS Forge] Detected Docker Engine. Building container image thmd-guru-forge:bookworm..." -ForegroundColor Green
        docker build -t thmd-guru-forge:bookworm -f "builder/Dockerfile" .
        if ($Action -eq "smoke-test") {
            docker run --rm -v "${RepoRoot}:/workspace" --entrypoint /bin/bash thmd-guru-forge:bookworm tests/smoke-test.sh
        } else {
            docker run --rm --privileged -v "${RepoRoot}:/workspace" thmd-guru-forge:bookworm $Action $Edition
        }
        exit $LASTEXITCODE
    }

    Write-Host "[OS Forge] Running Portable Native Builder (Git Bash + Python ISO-9660)..." -ForegroundColor Green
    $gitBash = "C:\Program Files\Git\bin\bash.exe"
    $pyExe = "C:\Python314\python.exe"
    if (-not (Test-Path $pyExe)) { $pyExe = "python" }

    if ($Action -eq "smoke-test") {
        & $gitBash "tests/smoke-test.sh"
        exit $LASTEXITCODE
    }

    if ($Action -eq "stage") {
        & $gitBash "builder/forge.sh" "stage" $Edition
        exit $LASTEXITCODE
    }

    & $gitBash "builder/build-debs-portable.sh"
    & $gitBash "builder/setup-signing-keys.sh"

    if ($Action -in @("iso", "all")) {
        & $pyExe "builder/build-iso-portable.py"
    }
    & $gitBash "tests/smoke-test.sh"
} finally {
    Pop-Location
}
