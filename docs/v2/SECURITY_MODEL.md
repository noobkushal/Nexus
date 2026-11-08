# NEXUS V2 Security and Approval Model

## Security invariants

1. Deny by default: missing identity, permission, policy, or approval means deny.
2. The authenticated owner is the only principal allowed to access personal workspaces and memory.
3. Agents cannot approve actions, edit their own permission grants, or bypass the policy enforcement point.
4. Authorization is enforced server-side for every request and again at execution time.
5. External side effects are never triggered directly by model-generated text.
6. Secrets are never stored in source control, prompts, browser storage, logs, or audit payloads.
7. All consequential actions produce tamper-evident audit events.
8. The Windows companion agent accepts commands only from an authenticated, authorized control plane and only for registered capabilities.

## Identity and device trust

- Use a real authentication mechanism with short-lived access tokens, refresh-token rotation, revocation, and device/session inventory.
- Require MFA or passkey support for account recovery and sensitive settings.
- Bind device sessions to an owner and device record. A private network address alone is not authentication.
- Use Tailscale or an equivalent private overlay to connect phone, cloud host, and PC. Do not publish the PC agent listener to the internet.
- Keep separate service identities for the control plane, worker, and PC companion.

## Permission model

Permissions are explicit scopes, for example:
- `profile:read`
- `jobs:read`
- `workspace:<id>:read`
- `workspace:<id>:write`
- `calendar:read`
- `calendar:draft`
- `communications:draft`
- `communications:send` (approval-gated)
- `applications:submit` (approval-gated)
- `deployment:staging`
- `deployment:production` (approval-gated)
- `policy:admin` (owner-only; never agent-grantable)

An agent receives only the scopes needed for its task. Avoid wildcard scopes. Resource IDs and owner IDs must be checked to prevent IDOR and cross-user access.

## Approval protocol

An approval request contains:
- immutable action ID and idempotency key;
- owner, requesting agent, and tool identity;
- action type and risk tier;
- canonical payload hash plus human-readable preview;
- exact recipient/destination/environment/resource;
- created time, expiry, and one-time nonce;
- status: pending, approved, rejected, expired, or consumed.

Execution sequence:
1. Validate the caller and resource ownership.
2. Validate tool scope and policy.
3. Build a canonical action payload and persist an approval request.
4. Present a clear preview to the owner.
5. On approval, persist the decision with actor, timestamp, and payload hash.
6. Immediately before execution, re-check permission, expiry, status, payload hash, and idempotency.
7. Atomically consume the approval and enqueue/execute the action.
8. Record outcome and sanitized audit event.

Approvals are not reusable. Editing recipient, message body, attachments, deployment target, or other material parameters creates a new approval request.

## Risk policy

| Action | Default policy |
|---|---|
| Search authorized files / read public information | Allow within scope |
| Draft resume, email, message, calendar event | Allow; save as draft |
| Edit registered project files | Allow with checkpoint and bounded workspace |
| Run tests / lint / build | Allow in isolated workspace with limits |
| Send email, SMS, LinkedIn message | Approval required |
| Submit job application / public post | Approval required |
| Create or invite calendar attendees | Approval required before external invitations |
| Install software, change firewall, access credentials | Explicit approval; often disallow |
| Delete user data or change permissions | Explicit owner approval; require recovery path |
| Deploy to staging | Policy-controlled; approval configurable |
| Deploy to production / alter infrastructure | Fresh explicit approval required |

## PC companion constraints

- Run as a standard user, not administrator.
- Use an allow-listed command registry; never expose arbitrary shell execution to an LLM.
- Restrict file operations to registered workspace roots and resolve symlinks before access.
- Require confirmation for destructive operations and maintain recoverable backups.
- Browser automation must use dedicated profiles and never extract or reveal stored passwords, cookies, or session tokens.
- Provide a local emergency stop and remote device revocation.
- Log command metadata, not secrets or full sensitive file contents.

## Web and prompt-injection safety

Treat websites, email, documents, job descriptions, repository text, and tool output as untrusted data. Instructions found in those sources cannot change system policy or authorize actions. Use strict URL validation, DNS/IP checks at connection time, redirect revalidation, response-size limits, timeouts, content-type checks, and egress allow-lists to mitigate SSRF.

## Audit and incident response

Audit records should include actor, agent, tool, resource, decision, policy version, approval ID, timestamps, outcome, and correlation ID. Redact credentials, tokens, private message contents, and unnecessary personal data. Provide owner-visible history, session revocation, key rotation, backup restore, and incident shutdown procedures.

## Release gate

A feature is not production-ready until:
- authorization and cross-owner isolation tests pass;
- approval bypass and replay tests pass;
- secrets scanning and dependency checks pass;
- destructive operations have recovery tests;
- logs are redacted;
- documentation and threat-model notes are updated.


## Phase 1 implementation contract

### Authentication lifecycle
- Persist owner identity and device/session records. Add password hash, active state, token version, and timestamps through a versioned migration.
- Bootstrap the first owner through a one-time setup secret supplied out-of-band. Never ship default credentials or public self-registration.
- Store only salted password hashes using a modern password-hashing implementation. Rate-limit login and bootstrap attempts.
- Use short-lived signed access tokens with issuer, subject, issued-at, expiry, and token-version claims. Validate signature and expiry on every request.
- Keep signing/bootstrap secrets in environment variables; fail closed in production if required secrets are absent or weak.
- Logout/revocation increments token version. Deactivated users cannot authenticate or use existing tokens.

### Initial role and scope baseline
- **owner:** identity and policy administration, approvals, all explicitly permitted non-production operations.
- **operator:** normal assistant operations, task/workspace management, and eligible approval decisions.
- **auditor:** read-only access to permitted operational and audit records.

Initial scope families: `identity:read/manage`, `tasks:read/write`, `agents:read/operate`, `storage:read/write/delete`, `approvals:read/decide`, `communications:draft/send`, `career:read/prepare_application/submit_application`, `deployment:prepare/production`, `integrations:manage`, and `audit:read`. Production deployment, outbound communications, and application submission remain approval-gated regardless of role. Agents use separate service identities and narrowly scoped grants; role names are not accepted from client payloads.

### Approval record and state machine
Persist: request ID, requester identity/type, action type, resource, canonical payload hash, human-readable preview, requested scopes, creation/expiry timestamps, status, reviewer identity, decision timestamp, execution timestamp, and immutable audit correlation ID.

State transitions: `pending -> approved | rejected | expired`; approved requests may transition once to `consumed` or `failed`. Execution re-checks actor status, permissions, approval state, expiry, payload digest, resource ownership, and policy immediately before the side effect. A transaction claims the approval exactly once; automatic replay is forbidden. Any material payload change requires a new approval.

### Required regression tests
- No default credentials; bootstrap is one-time and secret-protected.
- Invalid, expired, malformed, revoked, or wrong-signature tokens are rejected.
- Disabled users and stale token versions are rejected.
- Anonymous requests and lower-privilege roles cannot access protected/admin routes.
- Agents cannot grant permissions, change roles, approve requests, or bypass policy.
- Approval cannot be replayed, transferred to another payload/resource, or used after expiry.
- Concurrent execution attempts produce at most one dispatch.
- Outbound message, application submission, and production deployment remain blocked without valid, fresh human approval.
- Password hashes, signing secrets, and tokens never appear in API output or logs.

### Delivery and release gates
Implement authentication, RBAC, approval persistence, and audit as small vertical slices. Protect every route server-side and enforce policy again at the tool execution boundary. Do not merge until backend tests, frontend production build, migration tests, and security regression tests pass. Enabling an integration does not bypass these gates.
