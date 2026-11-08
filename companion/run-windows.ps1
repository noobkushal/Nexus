$ErrorActionPreference = "Stop"
$CompanionDir = $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $CompanionDir "..")).Path
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { throw "Python 3.11+ is required. Install Python and reopen PowerShell." }

$StateDir = Join-Path $env:LOCALAPPDATA "Nexus"
$TokenFile = Join-Path $StateDir "companion.token"
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
if (-not (Test-Path $TokenFile)) {
    $Bytes = New-Object byte[] 48
    [Security.Cryptography.RandomNumberGenerator]::Fill($Bytes)
    $Token = [Convert]::ToBase64String($Bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
    [IO.File]::WriteAllText($TokenFile, $Token, [Text.Encoding]::ASCII)
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    & icacls $TokenFile /inheritance:r /grant:r "$($Identity):(R,W)" | Out-Null
    Write-Host "Created private companion token at $TokenFile"
    Write-Host "Keep this token private. Never commit or share it."
}
$env:NEXUS_COMPANION_TOKEN = (Get-Content -Raw $TokenFile).Trim()
$env:NEXUS_WORKSPACE_ROOT = $RepoRoot
$env:NEXUS_COMPANION_PORT = "8765"
Write-Host "Starting NEXUS companion for $RepoRoot"
Write-Host "Local endpoint: http://127.0.0.1:8765"
Write-Host "Press Ctrl+C to stop."
& $Python.Source (Join-Path $CompanionDir "nexus_companion.py")
