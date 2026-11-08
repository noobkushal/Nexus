# NEXUS Windows Companion (local preview)

The companion is a narrow local bridge between NEXUS and a Windows workspace.
It is a first implementation milestone, not unrestricted remote desktop control.

## Current capabilities

- Authenticated status endpoint.
- Workspace directory listing and UTF-8 text file reads.
- Text file writes up to 1 MB with an explicit confirmation header.
- Workspace-root enforcement, traversal rejection, and symlink escape checks.
- Random per-install bearer token stored under the current Windows user's LOCALAPPDATA.

It does not expose shell execution, process control, arbitrary application launch,
credential stores, browser sessions, or a public network listener. The service
binds to 127.0.0.1 only. Do not expose port 8765 through router port-forwarding.

## Start on Windows

From the cloned repository root, open PowerShell:

~~~powershell
Set-ExecutionPolicy -Scope Process Bypass
.\companion\run-windows.ps1
~~~

The script creates a random token on first run and restricts its file ACL to
the current Windows identity. It starts the local service on port 8765 and
uses the repository as the allowed workspace.

Open the NEXUS dashboard on the same PC, navigate to **Windows Companion**,
paste the token from LOCALAPPDATA\\Nexus\\companion.token, and select Connect.
The browser may ask permission to access a local network service. The token is
held only in the page's memory. Select a file to read it; saving requires a
separate confirmation dialog.

## API

All endpoints require an Authorization: Bearer header containing the value in
LOCALAPPDATA\Nexus\companion.token.

- GET /v1/status
- GET /v1/files?path=relative/directory
- GET /v1/files/read?path=relative/file.md
- POST /v1/files/write with JSON containing path and content, plus
  X-NEXUS-LOCAL-CONFIRM: true.

Allowed file extensions are source/document formats only. Hidden files,
.env* files, common private-key names, and files outside the workspace are
blocked. Writes replace files atomically; the parent directory must exist.

## Verify

~~~powershell
cd companion
python -m unittest discover -v
~~~

An authenticated status check:

~~~powershell
$Token = (Get-Content "$env:LOCALAPPDATA\Nexus\companion.token" -Raw).Trim()
Invoke-RestMethod -Headers @{ Authorization = "Bearer $Token" } http://127.0.0.1:8765/v1/status
~~~

## Integration boundary

The dashboard can access the companion only from the same PC/browser. This
version is not registered with the NEXUS backend and has no authenticated
relay, Android remote access, Playwright browser control, or full desktop
control. Those require a pairing/revocation protocol and device-identity
lifecycle. Do not expose the local service to the internet as a workaround.
