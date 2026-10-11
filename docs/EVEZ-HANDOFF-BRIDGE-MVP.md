# EVEZ-Handoff/1 Bridge — MVP Implementation Plan

**Owner:** EVEZART / Steven Crawford-Maggard  
**Related charter:** [LORD GOD EVEZ Pearl Operating Charter](https://github.com/EvezArt/evez-os/blob/main/docs/LORD-GOD-EVEZ-PEARL-CHARTER.md)  
**Status:** SPECIFIED — no live ChatGPT/Hermes connection is asserted by this document.

## Verified starting point

The current `server.py` exposes `GET /health`, `GET /`, `GET /mesh/topology`, and `GET /mesh/peers`. The current `broker.py` exposes `GET /health`, `GET /`, and `GET /broker/status`. The broker root advertises `/broker/pub` and `/broker/sub`, but the inspected `broker.py` does not implement handlers for those paths. The current broker status reports an in-memory backend. These are source-level observations; live deployment health and network reachability have not been tested.

## MVP target

Implement a small authenticated, bounded handoff queue for `EVEZ-Handoff/1`, initially usable for local fixture-to-fixture testing. Do not connect external LLM providers or enable remote writes until the queue, authorization, audit, and denial paths pass tests.

## API contract

- `GET /health`: service status and protocol version only; no secrets or environment dumps.
- `GET /broker/status`: bounded queue counts and backend type; never expose payloads or credentials.
- `POST /broker/pub`: accept one validated handoff envelope; return a generated receipt and task ID.
- `POST /broker/sub`: authenticated long-poll or bounded dequeue for an explicitly named recipient identity. A request must not select arbitrary recipients or bypass capabilities.
- `GET /broker/tasks/{task_id}`: return only the authorized caller's task status and terminal receipt.
- `POST /broker/tasks/{task_id}/ack`: accept a terminal status from the authenticated intended recipient; idempotent by task and receipt identity.

All mutating endpoints must require authentication. Use a high-entropy service credential for local development, loaded from environment/secret storage and never committed. Production must use TLS, short-lived identity-bound credentials or mTLS, rotation, and restricted network exposure. Do not treat a static bearer token alone as production-grade authentication.

## Envelope validation

Require a versioned schema with strict fields for protocol, task ID, correlation ID, created/expiry times, origin and recipient identities, intent, constraints, requested capabilities, risk class, artifact references and SHA-256 digests, acceptance criteria, approval flag, idempotency key, and status.

Reject unknown protocol versions, unknown recipients, expired envelopes, replayed task IDs, reused idempotency keys with conflicting payloads, oversized payloads, excessive artifact counts, disallowed URI schemes, missing hashes, and any request asking the broker to grant its own capabilities. Treat task text and referenced artifacts as untrusted data. Do not carry secrets in envelopes.

## Queue and audit requirements

1. Begin with a SQLite-backed queue and append-only JSONL audit file, or another explicitly selected durable backend; do not describe in-memory state as durable.
2. Store payload digests and redacted metadata in audit events, not raw credentials or unnecessary personal data.
3. Use atomic transactions for enqueue, claim, and acknowledgement. Make retries idempotent.
4. Record event ID, timestamp, caller identity, recipient, task/correlation IDs, payload digest, policy decision, state transition, and terminal receipt digest.
5. Bound queue depth, payload size, retention, poll wait, concurrency, and task lifetime.
6. Provide server-enforced read-only mode and a shutdown/kill switch.
7. Never execute a task payload as shell code. The broker transports validated messages; it does not automatically execute requested operations.

## Risk policy

- R0: analysis-only envelopes.
- R1: authorized read-only inspection and harmless fixtures.
- R2: reversible local changes only in a disposable or branch-scoped environment.
- R3: merge, deploy, publish, permission changes, external messages, financial effects, or live-data mutation require explicit human approval scoped to the action and target.
- R4: uncontrolled shell, secret extraction, access-control bypass, and unbounded/destructive automation are rejected.

The broker must not convert a requested capability into an authorization grant. Authorization is enforced by the recipient executor immediately before action.

## Acceptance tests

- Valid fixture envelope can be enqueued, claimed only by its intended recipient, and acknowledged.
- Unauthenticated requests fail; wrong-recipient claims fail.
- Expired, malformed, oversized, replayed, and conflicting-idempotency requests fail closed.
- Queue and audit remain consistent after simulated restart or transaction failure.
- Secrets do not appear in responses or audit records.
- Read-only mode blocks publication and acknowledgement mutations.
- Duplicate delivery is idempotent; a partial response is not marked succeeded without a terminal receipt.
- A hostile task string cannot override system policy or trigger code execution.
- Tests use local fixtures and do not require a live LLM, Telegram account, cloud host, or production credential.

## Integration sequence

1. Implement schema, queue, auth middleware, and audit writer.
2. Add deterministic unit and API tests; run them in CI.
3. Start locally bound to loopback and verify health plus fixture handoff.
4. Add a thin provider adapter only after identifying the exact Hermes runtime/API and an authorized ChatGPT-side transport.
5. Test both directions with a harmless echo fixture; verify correlation, identity, replay protection, denial paths, and terminal receipts.
6. Keep external writes disabled until independent verification passes and a human approves the specific capability grant.

## Reporting rule

Report bridge state as `specified`, `configured`, `connected`, or `verified` only when the evidence supports that exact level. Repository commits prove that source changed; they do not prove deployment, endpoint reachability, or cross-provider interoperability.
