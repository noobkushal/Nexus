# NEXUS AI - Full System Verification Script
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$PytestExe = Join-Path $BackendDir ".venv\Scripts\pytest.exe"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " NEXUS AI - Complete System Verification" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Step 1: Run Backend Tests
Write-Host ""
Write-Host "[1/2] Running Backend Pytest Test Suite..." -ForegroundColor Yellow
Set-Location $BackendDir
& $PytestExe -v
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend tests failed!"
}

# Step 2: Run Frontend Production Build
Write-Host ""
Write-Host "[2/2] Compiling Frontend Next.js Production Build..." -ForegroundColor Yellow
Set-Location $FrontendDir
& npm.cmd run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Frontend build failed!"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host " ALL SYSTEMS OPERATIONAL AND VERIFIED" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
