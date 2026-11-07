# NEXUS AI - Start Backend Server
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " NEXUS AI - Launching Backend Service" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment not found at $PythonExe. Please set up backend venv first."
}

Set-Location $BackendDir
Write-Host "Starting FastAPI on http://127.0.0.1:8000..." -ForegroundColor Green
& $PythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
