# NEXUS V2 Delivery Roadmap

Branch: `nexus-v2-development`  
Main branch: preserved; no direct commits planned.

## Phase 0 — Baseline and engineering guardrails

- [x] Create isolated V2 branch from main.
- [x] Record architecture and security invariants.
- [ ] Add CI for backend tests and frontend build.
- [ ] Capture baseline test/build results in CI.
- [ ] Add branch protection after confirming repository policy and required checks.

## Phase 1 — Identity, policy, approvals, and audit

Initial authentication slice added: scrypt password hashing, one-time owner bootstrap, short-lived signed access tokens, logout revocation, login throttling, authenticated API routing, and owner-only settings/approval decisions. See [Authentication Setup](AUTHENTICATION_SETUP.md). Phase 1 remains open until resource-level RBAC, durable device/session inventory, centralized tool policy, durable approvals, and audit coverage are implemented and verified.

- [ ] Persistent owner identity and device/session model.
- [ ] Owner-scoped resource authorization on every API route.
- [ ] Central policy enforcement point for all tool invocations.
- [ ] Durable, expiring, single-use, payload-bound approvals.
- [ ] Append-only audit events with redaction.
- [ ] Tests: deny by default, IDOR, privilege escalation, approval replay, payload mutation, expiry, revoked sessions.

Exit criteria: no consequential tool can execute without passing the same centralized policy and approval checks.

## Phase 2 — Provider-neutral AI runtime

- [ ] Provider protocol and adapter contract.
- [ ] OpenAI-compatible adapter with configurable base URL.
- [ ] Additional provider adapters selected by configuration.
- [ ] Per-task routing, timeout, retry, budget, and fallback policy.
- [ ] Structured tool-call validation and streaming.
- [ ] Tests with deterministic fake providers; no live API key required in CI.

Exit criteria: application works with no Ollama installation and can switch providers without changing agent code.

## Phase 3 — Windows companion and private mobile access

- [ ] Device enrollment and revocation.
- [ ] Outbound authenticated PC-agent connection over private overlay.
- [ ] Capability registry instead of arbitrary shell access.
- [ ] Workspace-scoped search/read/write and Git checkpoints.
- [ ] Browser/app automation with explicit allow-lists.
- [ ] Media controls and notification bridge.
- [ ] Android-friendly responsive/PWA interface and approval inbox.
- [ ] Tests for device authentication, workspace escapes, command allow-list, disconnect/revoke.

Exit criteria: phone can securely request scoped PC tasks without exposing the PC to the public internet.

## Phase 4 — Personal assistant integrations

- [ ] Calendar provider adapter and event drafts.
- [ ] Email provider adapter; draft-first behavior.
- [ ] Messaging adapter only where supported by official APIs and user authorization.
- [ ] Reminder scheduler and notification delivery.
- [ ] Music playback through supported local/official integrations.
- [ ] Approval and audit tests for all outbound actions.

Exit criteria: external communication and invitations require exact, fresh approval.

## Phase 5 — Career intelligence

- [ ] Verified candidate profile with evidence and provenance.
- [ ] Job source adapters (official APIs/feeds and permitted public listings).
- [ ] Deduplication, freshness, eligibility and location filters.
- [ ] Explainable skill/requirement match score and gap analysis.
- [ ] Resume tailoring grounded only in verified profile facts.
- [ ] ATS-friendly DOCX/PDF export and consistency validation.
- [ ] Company and recruiter research from public/professional sources.
- [ ] Outreach drafts, suppression list, contact limits, and follow-up scheduler.
- [ ] Approval required for every outbound message and application submission.

Exit criteria: no fabricated credentials or experience; score explanations and source links are visible.

## Phase 6 — Deployment and operations

- [ ] Reproducible development/staging/production environments.
- [ ] Secret management and key rotation.
- [ ] Health checks, metrics, structured redacted logs.
- [ ] Encrypted backups and tested restore.
- [ ] Staging deployment automation.
- [ ] Production deployment approval and rollback.
- [ ] Operational runbook and emergency stop.

Exit criteria: tested recovery and owner-approved production releases.

## Delivery rules

1. Work only on `nexus-v2-development` until a reviewed pull request is ready.
2. Do not rewrite existing modules wholesale; make small, reviewable vertical slices.
3. Every code slice includes tests and documentation.
4. Do not claim a feature works until integration tests exercise the real adapter.
5. Do not commit secrets, real personal data, generated resumes, tokens, or local database files.
6. Keep `main` unchanged. Open a draft PR only after a meaningful tested milestone.
