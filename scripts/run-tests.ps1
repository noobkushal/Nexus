# NEXUS AI - Execute Backend Test Suite
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$PytestExe = Join-Path $BackendDir ".venv\Scripts\pytest.exe"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " NEXUS AI - Running Automated Tests" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Set-Location $BackendDir
& $PytestExe -v
