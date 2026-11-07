# NEXUS AI — Start Frontend Dashboard (PowerShell)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " NEXUS AI — Launching Mission Control UI" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Set-Location $FrontendDir
Write-Host "Starting Next.js dev server on http://localhost:3000..." -ForegroundColor Green
& npm.cmd run dev
