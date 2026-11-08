# NEXUS V2 implementation status

## Implemented

- Owner login, protected APIs, logout, and one-time bootstrap.
- Persistent payload-bound approval requests and audit events.
- Owner-scoped persistent task API.
- Real n8n webhook dispatch with honest failure results.
- Provider-neutral provider interface with a mock default.
- Local Windows companion preview with authenticated loopback-only workspace file operations.

## Incomplete

- Workflow executions are now persisted in the database and scoped to the authenticated owner.
- Legacy tasks without an owner remain inaccessible until an explicit migration assigns ownership.
- The Windows companion is not registered with the backend and has no remote relay.
- Android access, browser automation, full desktop control, and device revocation are not implemented.
- Email and messaging transport adapters are not connected; drafts are not sent.
- Job discovery and resume tailoring need real external data/provider integrations.
- Production deployment is not configured or verified.

## Safety invariants

- Keep main separate from development until review and verified CI.
- Do not execute arbitrary shell commands through the companion.
- Do not expose the companion port to the public internet.
- Keep outbound communications, applications, destructive actions, and production deployments behind explicit owner approval.
- Never report an external action as complete without a successful provider response.
