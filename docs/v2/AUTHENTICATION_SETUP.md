# NEXUS V2 Authentication Setup

This milestone adds first-owner bootstrap, password login, signed bearer tokens, logout revocation, and server-side role dependencies.

## 1. Configure secrets

Copy `backend/.env.example` to `backend/.env`. Generate two independent random values (do not reuse either value):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set the generated values:

- `AUTH_SECRET_KEY`: signing key, at least 32 characters.
- `AUTH_BOOTSTRAP_SECRET`: one-time owner-bootstrap secret, at least 24 characters.
- `ACCESS_TOKEN_TTL_MINUTES`: short-lived access token lifetime; default 20 minutes.

Never commit `.env`, share these values in chat, or put them in frontend environment variables.

## 2. Start the backend

Install backend requirements and start FastAPI as described in the project README. On startup, the database creates missing tables and applies additive auth-column migration to an existing `users` table.

## 3. Create the first owner exactly once

Call `POST /api/v1/auth/bootstrap` with the `X-Nexus-Bootstrap-Secret` header and JSON body:

```json
{
  "username": "owner",
  "password": "use-a-unique-password-at-least-12-characters"
}
```

The response contains a short-lived bearer access token. Store it only in a secure client session. The bootstrap endpoint refuses requests without the configured secret and refuses to run after any user record exists. There are no default credentials and no public registration endpoint.

## 4. Login and use protected APIs

- `POST /api/v1/auth/login` accepts username/password and returns a short-lived bearer token while also setting an HttpOnly browser cookie.
- `GET /api/v1/auth/me` returns the authenticated user's public profile.
- `POST /api/v1/auth/logout` increments the user's token version, clears the HttpOnly cookie, and immediately invalidates previously issued tokens.
- Product API routes require `Authorization: Bearer <access_token>`.
- `/health`, `/`, bootstrap, and login remain public. Settings changes and approval decisions are owner-only.

Do not store access tokens in browser localStorage. The Next.js dashboard now includes an owner sign-in page at `/login`, a route guard, credentialed API requests, and a sign-out control. The browser uses a short-lived HttpOnly cookie rather than storing the bearer token in localStorage or sessionStorage.

## Approval API behavior

- `POST /api/v1/approvals` creates a persistent request owned by the authenticated user. The server canonicalizes the payload and returns its SHA-256 digest.
- `GET /api/v1/approvals` and `GET /api/v1/approvals/{id}` return only requests owned by the authenticated user.
- `POST /api/v1/approvals/{id}/decision` is owner-role-only. The decision must include the exact `payload_hash` shown in the request preview; only `approved` or `rejected` is accepted.
- Requests expire after 15 minutes. Expired, altered, already-decided, or replayed requests cannot be approved again.
- The internal `ApprovalService.consume_approval` method atomically claims an approved request once using the same payload digest. A real executor must call this only after rechecking actor permissions and policy immediately before dispatch. No external side effect is wired to this method yet.
- Approval request and decision events are persisted in the append-only audit event table.

## Current scope and limitations

- Passwords are stored as salted scrypt hashes; plaintext passwords are never persisted.
- Tokens are HS256-signed, short-lived, issuer-checked, expiry-checked, and checked against the database token version on each request.
- Failed login attempts are rate-limited per username in the running backend process. A multi-worker deployment should move this limiter to a shared store.
- Roles currently recognized by the authorization helper are `owner`, `operator`, and `auditor`. Role administration, granular per-resource scopes, MFA/passkeys, refresh-token rotation, durable device inventory, and distributed rate limiting are not yet implemented.
- Existing legacy users without a password hash cannot log in; do not automatically promote them or assign a default password. Plan a controlled owner recovery/migration before enabling a pre-existing multi-user database.
- Approval records and decisions are now durable, expiring, payload-bound, owner-scoped, audited, and have an atomic one-time consumption primitive. The actual tool execution adapters still need to invoke the consumption gate and revalidate policy immediately before any side effect.
