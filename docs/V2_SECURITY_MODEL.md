# NEXUS V2 — Authentication, RBAC & Approval Security Contract

Status: implementation contract for Phase 1. This document is not evidence that runtime enforcement is complete.

## Security invariants

1. Deny by default. Every protected API route must authenticate and authorize on the server.
2. Identity, role, permissions, approval decisions, and audit records are server-owned. An agent or model cannot modify them.
3. An agent may propose an action; it cannot approve its own proposal or execute an approval-gated action by changing request payloads.
4. Approval is bound to an immutable action type, canonical payload digest, requester, target resource, and expiry. Any payload change invalidates the approval.
5. Approval is single-use and state transitions are atomic: pending -> approved/rejected/expired -> executed/failed. No replay.
6. External messaging, job applications/submissions, and production deployment always require explicit operator approval immediately before dispatch.
7. Development branch changes may be committed and tested autonomously. Production deployment is a separate protected action.
8. Secrets are never returned by API responses or written to logs. Passwords use a slow password hash; tokens are signed, short-lived, and revocable.

## Identity and credential lifecycle

- Persist users in the existing SQLAlchemy users table; add password hash, active state, token version, and timestamps through a versioned migration.
- Bootstrap the first administrator through a one-time setup secret supplied out-of-band. Never ship a default username/password or public self-registration.
- Store only salted password hashes using a modern password-hashing implementation. Enforce minimum password length and rate-limit login/bootstrap attempts.
- Use short-lived signed access tokens with issuer, subject, issued-at, expiry, and token-version claims. Validate signature and expiry on every request.
- Keep signing/bootstrap secrets in environment variables; fail closed in production if required secrets are absent or weak.
- Logout/revocation increments token version. Deactivated users cannot authenticate or use existing tokens.

## RBAC baseline

| Role | Allowed scope |
|---|---|
| administrator | User and role administration, policy configuration, approvals, all non-production operations |
| operator | Normal assistant operations, task/workspace management, approve eligible requests |
| auditor | Read-only access to permitted operational and audit records |

Permissions are explicit scopes, not role-name checks scattered through handlers. Initial scope families:

- `identity:read`, `identity:manage`
- `tasks:read`, `tasks:write`
- `agents:read`, `agents:operate`
- `storage:read`, `storage:write`, `storage:delete`
- `approvals:read`, `approvals:decide`
- `communications:draft`, `communications:send`
- `career:read`, `career:prepare_application`, `career:submit_application`
- `deployment:prepare`, `deployment:production`
- `integrations:manage`, `audit:read`

Agents receive separate service identities and narrowly scoped grants. User roles must never be inferred from client-supplied fields.

## Approval engine contract

An approval request stores: request ID, requester identity/type, action type, resource, canonical payload hash, human-readable summary, requested scopes, created/expiry timestamps, status, reviewer identity, decision timestamp, execution timestamp, and immutable audit correlation ID.

- Only authenticated human operators with `approvals:decide` may decide eligible requests.
- Requester and reviewer must be different principals for high-impact operations.
- Approval is valid only for the exact payload digest and resource.
- Execution re-checks actor status, permissions, approval state, expiry, payload digest, and policy immediately before the side effect.
- A database transaction claims the approval exactly once before dispatch. Failures are recorded; automatic replay is forbidden.
- No approval endpoint may directly trust an `approved` boolean supplied by an agent or browser.

## Delivery sequence

1. Add password hashing, token signing/validation, bootstrap flow, and auth tests.
2. Add permission registry and FastAPI dependencies; protect routes and test anonymous/unauthorized/authorized access.
3. Migrate approval records to persistent storage and implement atomic, payload-bound, expiring decisions.
4. Add audit events for login, denied access, role changes, approval decisions, and execution attempts.
5. Add frontend login/session handling and approval review UI. Do not store long-lived credentials in localStorage.
6. Run backend tests, frontend production build, migration tests, and security regression tests before merging.

## Mandatory regression tests

- No default credentials; bootstrap is one-time and secret-protected.
- Invalid, expired, malformed, revoked, or wrong-signature tokens are rejected.
- Disabled users and stale token versions are rejected.
- Anonymous requests cannot access protected endpoints.
- Lower-privilege roles cannot call administrative or approval endpoints.
- Agents cannot grant permissions, change roles, approve requests, or bypass policy.
- Approval cannot be replayed, transferred to another payload/resource, or used after expiry.
- Concurrent execution attempts produce at most one dispatch.
- Outbound message, application submission, and production deployment remain blocked without a valid human approval.
- Secrets and password hashes never appear in API output or logs.

## Release gates

Do not merge Phase 1 until all security regression tests pass and the frontend production build succeeds. Do not enable external integrations or production deployment merely because the authentication layer is present; each integration must enforce the same server-side policy at its execution boundary.
