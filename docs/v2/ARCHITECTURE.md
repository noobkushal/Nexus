# NEXUS V2 Architecture

Status: approved implementation blueprint  
Branch: `nexus-v2-development`  
Baseline: `main` at the commit from which this branch was created

## Product objective

NEXUS is a private, user-operated AI workspace reachable from an authenticated mobile client and a Windows PC. It coordinates specialized agents for personal assistance, research, coding, workflows, and career operations.

"Full autonomy" means agents may independently perform explicitly authorized, reversible, low-risk work. It does **not** mean unrestricted access. Every tool call is checked by a policy enforcement point. High-impact actions remain approval-gated.

## System topology

```text
Android / Web client
        |
        | HTTPS + device authentication
        v
Private access gateway (Tailscale; no public PC ports)
        |
        v
FastAPI control plane
  - Authentication / device sessions
  - Intent router and agent orchestrator
  - Policy enforcement point (RBAC + risk policy)
  - Durable approvals and audit events
  - Provider-neutral model router
        |
        +---- PostgreSQL (users, jobs, approvals, audit, workflow state)
        +---- Redis (optional queue/cache; never source of authorization truth)
        +---- Object/file storage (encrypted, scoped workspaces)
        +---- n8n (allow-listed workflow bridge)
        |
        +---- Windows companion agent (outbound authenticated connection)
        |       - scoped file search
        |       - approved app/browser automation
        |       - local development and test execution
        |       - media controls
        |
        +---- External adapters
                Gmail / Calendar / messaging / GitHub / job sources
```

The cloud control plane must never expose an unrestricted shell or filesystem endpoint. The Windows agent initiates an outbound connection to the gateway; do not expose SMB, RDP, PowerShell remoting, or arbitrary local ports to the public internet.

## Existing agent roles

- **Aura:** conversation, task intake, calendar and personal workflows.
- **Scout:** web and document research; source provenance required.
- **Forge:** code analysis, edits in explicitly registered workspaces, tests, and Git checkpoints.
- **Conduit:** allow-listed workflow orchestration and n8n integration.
- **Apex:** job discovery, evidence-based job fit, resume tailoring, and outreach drafts.

Agents are untrusted planners, not authorities. They cannot grant themselves permissions, alter policy, or approve their own actions.

## Provider-neutral model gateway

Define a common provider interface for chat, structured output, tool calling, streaming, and health checks. Provider adapters are configured independently (for example, OpenAI-compatible endpoints and supported hosted/local providers). Routing policy should support per-task model selection, fallback, timeout, token/cost budgets, and redacted telemetry.

No feature may require Ollama to be installed. Local models are optional adapters. Secrets are server-side only and must never be sent to browser clients or committed to Git.

## Authorization and autonomy

Use deny-by-default authorization. Each tool declares:
- stable tool ID and version;
- required permission scopes;
- allowed agent identities;
- risk tier;
- whether human approval is mandatory;
- input schema and resource constraints;
- timeout and execution budget.

Suggested risk tiers:
- **T0 read:** read an explicitly authorized resource.
- **T1 reversible local write:** create or edit inside a registered workspace with version history.
- **T2 external side effect:** send a message, email, create an event, submit a job application, publish, or contact a person. Approval required.
- **T3 high impact:** production deployment, destructive deletion, permission changes, financial/legal commitments, credential changes. Explicit, fresh approval required; sensitive classes may remain disallowed.

Approval is bound to a canonical action payload (recipient, content, destination, environment, and resource), expires, is single-use, and is revalidated immediately before execution. Any material payload change invalidates approval. Never interpret a general "full autonomy" preference as approval for a specific external action.

## Career intelligence workflow

1. Collect the user's verified baseline profile and evidence (education, skills, certifications, projects, experience).
2. Discover opportunities only through permitted APIs, feeds, public pages, or user-authorized integrations; respect site terms, robots policies, rate limits, and anti-spam rules.
3. Normalize job descriptions and deduplicate by source URL/company/role.
4. Score explainably: required-skill evidence, preferred-skill evidence, seniority, location/work mode, eligibility, and freshness. Show missing requirements and uncertainty; do not invent a probability of getting hired.
5. Tailor a resume using only verified profile facts. Mark unsupported requirements as gaps, never fabricate experience, titles, metrics, or certifications.
6. Save a versioned draft and run consistency checks.
7. Prepare outreach drafts with source and recipient provenance. Human approval is required before sending messages, emails, connection requests, or applications.
8. Track follow-ups and enforce per-recipient contact limits and opt-out/suppression lists.

## Data and memory

PostgreSQL is the durable source of truth for users, devices, permissions, approvals, job records, and audit events. Store minimal personal data, encrypt secrets, isolate user data by owner ID, and support export/deletion. Memory retrieval must be scoped to the authenticated owner and carry source/provenance metadata.

## Deployment model

Start with a private single-user deployment. Use Docker Compose for development, a private overlay network for device connectivity, TLS at the gateway, encrypted backups, health checks, and a documented restore drill. Separate development, staging, and production credentials. Production deployment is an approval-gated operation.

## Delivery principle

Implement vertical slices, not a speculative rewrite. Each slice must include schema validation, authorization tests, audit coverage, failure handling, documentation, and CI. Keep the existing application operational while V2 work lands on its own branch.
