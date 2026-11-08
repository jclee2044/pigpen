# Running and recovering the backend

The implemented backend is a single-household FastAPI service. The frontend remains the scaffold; no UI/API connection is made by this work. The API contract and confirmed business decisions are in [backend-api.md](backend-api.md). Historical scaffold instructions in README/setup.md describe the initial state; the commands here describe the implemented backend.

## Private storage is separate from GitHub

Confirmed requirement: actual financial records never belong in the source checkout or a GitHub repository. Configuration rejects all runtime directories inside this checkout, including paths resolving there through symlinks. The application does not create databases on import or startup.

| Location | Contents |
| --- | --- |
| Source checkout | Python/Vue source, Alembic migrations, dependency pins/locks, docs, synthetic tests, avatar artwork, placeholder configuration |
| Explicit external development directory | Disposable synthetic development database and uploads |
| Explicit external production directory | Real SQLite database, WAL/SHM/journal files, receipt/bank images |
| Private configuration outside checkout | Production environment file and VAPID private key |
| Separate backup destination | Private database snapshots, attachment objects and checksum manifest |
| pytest temporary directory | Synthetic isolated databases, deleted by ordinary test cleanup |

Migration/restore registers each directory with an environment marker. Development/test processes refuse a directory registered for production, and existing unregistered databases are not automatically adopted. Use distinct development and production directories, owned by the service account with access restricted to that account. The server-local SQLite file is accessed only on this host, never via an SMB/NFS mount or directly by browsers. The browser communicates through JSON. Keep logs and diagnostic exports private too. `.gitignore` covers database files/sidecars, uploads, backups, environment files and private keys as a second safeguard; it is not the primary separation mechanism. Do not force-add runtime data.

## Install and verify

From the project root, using the project-owned interpreter:

```sh
/usr/bin/python3.14 -m venv backend/.venv
backend/.venv/bin/python -m pip --no-cache-dir install -r backend/requirements.txt -c backend/requirements.lock
backend/.venv/bin/python -m pip --no-cache-dir check
backend/.venv/bin/python -m pytest -q backend/tests
```

Direct dependencies: FastAPI standard tooling and pytest from the scaffold; SQLAlchemy 2.1.8 for persistence; Alembic 1.20.1 for migrations; Pillow 13.0.0 for decoding/validating uploaded images; pywebpush 2.5.0 for standards-compliant encrypted Web Push. All transitive versions are retained in requirements.lock. No global project dependencies or additional database/queue server are needed. Lock verification is for the existing Python 3.14.7/Linux environment; other platforms require their own verification. Build isolation for the http-ece source distribution may also download its build tooling during a fresh install; the runtime dependency lock is version-based, not an artifact-hash/build-tool lock.

## Start an empty development household

Choose a disposable data location **outside** this repository. Commands below are examples for the operator; they have not created this directory on your machine.

```sh
cd backend
export PIGPEN_ENV=development
export PIGPEN_DATA_DIR="$HOME/.local/share/pigpen-development"
.venv/bin/python -m pigpen migrate
.venv/bin/python -m pigpen check
.venv/bin/python -m pigpen serve
```

The API binds to 127.0.0.1:8000 by default. Health: `http://127.0.0.1:8000/api/v1/health`; interactive contract: `http://127.0.0.1:8000/docs`. Initialize the household with `household.initialize`, then create profiles using `user.create`. The executor takes UUIDs for both operations and records, and timezone-aware client timestamps. Subsequent commands specify the acting profile UUID. The operation schema and example below use synthetic data only:

```json
{
  "operation_id": "a3ca571b-ce86-48fa-b7c5-c6b69cb55565",
  "entity_id": "8b6f3f6c-f60e-442b-8f90-1c1799197d44",
  "actor_id": null,
  "client_time": "2026-11-06T12:00:00-05:00",
  "kind": "household.initialize",
  "data": { "name": "Synthetic household", "currency": "USD", "timezone": "America/New_York" }
}
```

POST this JSON to `/api/v1/operations`. Use fresh UUIDs for each new operation and record, and preserve the original payload/IDs on retry. APIs do not seed sample financial transactions automatically. No production financial database was created during implementation.

## Migrations and restart

Before upgrading a populated production database, create and verify a backup. Stop API/worker processes through their supervisor, run `python -m pigpen migrate` with the **production** environment selected explicitly, run `check`, then restart. Migration SQL is frozen in versioned files; normal startup does not run migrations. Automatic destructive downgrades are intentionally unavailable. Recovery uses a tested backup restored to a new location.

Health returns 503 for an absent or outdated schema and does not expose household data. The CLI refuses to serve an unready database. One API process and short SQLite transactions are the initial deployment choice; writes serialize with BEGIN IMMEDIATE, a five-second busy timeout, and atomic audit/change/outbox records. Transient storage errors are retryable; clients retain the original operation ID.

## Backup and restore

These examples require explicitly configured source storage. Choose a new absolute backup destination separate from runtime data and outside Git:

```sh
cd backend
.venv/bin/python -m pigpen backup /absolute/private/backup/pigpen-snapshot-001
.venv/bin/python -m pigpen restore /absolute/private/backup/pigpen-snapshot-001 /absolute/private/pigpen-restore-check --environment development
```

Backup uses SQLite's online backup API, checks database integrity/foreign keys, reads attachment references from that snapshot, and copies/checks immutable image objects. It does not copy a live SQLite main file blindly. It publishes a checksum manifest only after validation. Deleted/orphaned image objects are retained in live storage pending an explicit future cleanup policy; backups include objects referenced by the snapshot, including tombstoned attachment metadata.

Restore validates paths, checksums, database integrity and attachment completeness. It refuses existing targets, then publishes a new data directory. Select that directory explicitly to run a restore check; never test by overwriting live financials. VAPID credentials and private configuration are separate secrets and must be backed up through an operator-managed private mechanism. Retention/destination/scheduling are not configured by this work.

## Push delivery

The notification inbox works without push credentials. To enable actual delivery, obtain a private VAPID key and configure its path in `PIGPEN_VAPID_PRIVATE_KEY` plus a real `mailto:` or HTTPS contact in `PIGPEN_VAPID_SUBJECT`, outside the source checkout. The frontend must register a service worker and browser push subscription in a secure context; that integration is separate frontend work.

Register an installation with `installation.select`, then `subscription.set`; selecting a new profile revises the installation binding. GET `/api/v1/installations/{id}` returns binding/revision information without endpoint secrets. Supported endpoints are HTTPS browser-provider hosts for FCM, Mozilla, Apple and Windows push; additional providers need explicit review. HTTP redirects are disabled for push requests.

```sh
cd backend
.venv/bin/python -m pigpen deliver-once
```

One invocation handles at most one due job. Schedule repeated calls using the provided example timer or another supervisor. Jobs use leases and persisted retry backoff. Successful devices are recorded so a failure on another device does not resend to them on ordinary retries. Expired endpoints are disabled. Subscription/profile bindings are checked immediately before sending; a push already in flight or displayed by the OS cannot be recalled. Network delivery is at-least-once across a crash after sending but before recording success. The minimal payload supplies a stable notification ID/tag for client deduplication and includes no financial details. No real push notifications were sent during implementation; tests substitute a delivery function.

## Deployment boundary

The files under backend/deploy/ are **examples**, not installed services. Replace all paths, service-user and hostname placeholders before use. Serve built Vue assets and reverse-proxy the API under one HTTPS origin. The API example binds only to loopback. Choose trusted-household network access and certificates before device testing. Profile selection is attribution, not authentication; public exposure requires a separate access-control decision.

No system users, service units, firewall rules, remote access, certificates, production directories, or backup schedules were configured. Installing or changing those machine-level settings requires the operator's approval. Device PWA behavior, push permission prompts, real encrypted delivery and production restore remain deployment acceptance checks.

## Working choices and limitations

The confirmed budget/approval decisions are recorded separately from revisable defaults. The API implements a single shared Savings category; ordinary positive purchases; online edits/deletions; monthly bills; owner-managed wish lists; profile self-edit/archive; and plain-text comments. An archived profile is retained permanently; reactivation is not exposed in v1. Editing a linked purchase preserves approval/bill history; deleting it retains its historical link and prevents accidentally paying the same occurrence again. Correct a linked payment by editing its record; a new unlink/reopen workflow would require a separate product decision.

Pagination/filtering applies to ordinary resource collections. Summary calculation currently reads household records into Python for transparent exact arithmetic; the single-household workload keeps this simple. Measure before introducing aggregation caches or a more complex data pipeline. Sync history and accepted-operation deduplication are retained without pruning in v1. Refunds, split transactions, recurring income, extraction and AI remain outside this implementation.

## Frontend and deployment checkpoint — November 7

The Vue/TypeScript/Router frontend is now integrated through the documented JSON contract. Native IndexedDB stores confirmed snapshots and durable original operation envelopes. A native service worker/manifest provides the installed app shell and offline reopening; no additional PWA runtime dependency was needed. Optional `PIGPEN_STATIC_DIR` serves a verified build from FastAPI under the API origin. See [frontend-progress.md](frontend-progress.md) for acceptance evidence and [home-server-deployment.md](home-server-deployment.md) for the concrete reviewed deployment, confirmed backup policy and remaining device checks.

`cryptography==50.0.2`, previously transitively locked, is now declared directly for public VAPID derivation and explicit private-key generation. No resolved backend version changed. The browser receives only `GET /api/v1/push-config` public configuration. Missing push credentials leave the inbox usable. Permission is requested on the user's Enable action. Real provider delivery remains unverified.

### VAPID contact URI compatibility — November 8, 2026

The pinned py-vapid subject regex rejects HTTPS contact URIs containing ports or paths, including the approved installation URL on port 8445. PigPen now validates the HTTPS/mailto contact itself and passes a configured Vapid signer to pywebpush; audience validation, P-256 signing, encrypted payloads and redirect blocking remain in place. This follows the HTTPS/mailto contact schemes in RFC 8292 section 2.1 (https://www.rfc-editor.org/rfc/rfc8292.html#section-2.1). Invalid contact configuration returns the existing generic push-unavailable response. Pushes use a one-day provider TTL so temporarily disconnected devices can receive them later. No dependency or JSON contract changes.
