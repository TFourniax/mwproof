# Security Policy — ProofMW V0.6

ProofMW is an evidence/underwriting research product. V0.6 adds a minimal deployment boundary, but it is **not** a full enterprise IAM stack.

## Supported deployment boundary

Set a long random secret in `PROOFMW_API_KEY` for any non-local deployment.

```bash
export PROOFMW_API_KEY='...'
uvicorn proofmw.api:app --host 0.0.0.0 --port 8080
```

When configured:

- `/health` remains unauthenticated for container/orchestrator liveness;
- `/ready` and all `/v1/*` endpoints require `X-API-Key`;
- comparisons use `secrets.compare_digest`;
- the browser cockpit keeps the entered key in `sessionStorage`, not persistent `localStorage`.

Use TLS at the reverse proxy / ingress. Never send the API key over plaintext internet transport.

## Filesystem boundary

`POST /v1/underwrite` does **not** accept arbitrary server paths. A requested fixture must resolve below the repository `fixtures/` directory. Absolute paths and `..` traversal are rejected.

The API should not be used as a generic file reader.

## Evidence boundary

Canonical evidence is the append-only JSON ledger under `data/europe-public-events-v2/`. SQLite files and CI exports are rebuildable artifacts, not sources of truth.

Do not auto-promote a changed watched webpage into canonical evidence. Source-watch hashes are discovery signals only; evidence must still be normalized, deduplicated, dated and validated.

## Secrets

Do not commit:

- `PROOFMW_API_KEY`;
- lender / customer data-room credentials;
- private document URLs or tokens;
- personal access tokens;
- private project data unless its storage/licensing perimeter has been explicitly approved.

`.env` is ignored by Git.

## Known gaps before enterprise production

V0.6 intentionally does not claim to provide:

- OIDC/SAML/SSO;
- per-user RBAC;
- tenant isolation;
- audit-log persistence for user actions;
- rate limiting / abuse protection;
- managed secret rotation;
- encrypted private-document storage;
- formal penetration testing;
- a reviewed regulatory perimeter for credit/insurance decisions.

These become mandatory if ProofMW moves from a protected research pilot to a multi-tenant production service.

## Reporting

Until a dedicated security contact is configured, report suspected vulnerabilities privately to the repository owner rather than opening a public issue containing exploit details or secrets.
