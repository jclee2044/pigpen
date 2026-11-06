# Backend JSON contract

Implementation contract, November 6, 2026. The backend is a single-household service. Profile selection provides attribution, not authentication. Only expose it to trusted household devices; public Internet access is not configured.

## Confirmed decisions

The user confirmed USD, America/New_York, copying the previous month's allocations without carrying unused money forward, allocations only on Personal parents, and approval by **every other active profile**. These supersede earlier proposals where inconsistent. Production financial databases, attachments, secrets, and backups must be outside the Git checkout. Source, migrations, dependency locks and synthetic fixtures belong in Git.

Other implemented working choices remain revisable: distinct profile names; archival preserves history; positive purchases; monthly recurring bills clamped to month end; JPEG/PNG/WebP uploads up to 10 MiB; seven-day retry backoff cap; comments on requests/wish lists. Backup destination/retention, remote access, hostname and certificates require deployment decisions. No OCR, AI, bank integration or authentication is implemented.

## Wire conventions

- Base path `/api/v1`; JSON fields use snake_case.
- Money is an integer in minor units (100 = USD 1.00); floats, booleans and negative purchase amounts are rejected.
- UUID strings identify records and operations; clients generate IDs before offline creation. Dates are ISO `YYYY-MM-DD`, months `YYYY-MM`, event times timezone-aware ISO timestamps normalized to UTC.
- Mutable records expose integer `revision`, timestamps, and `deleted` tombstones. Archived records remain readable but cannot receive new entries.
- Errors: `{ "error": { "code": "...", "message": "...", "details": ... } }`. Invalid input is 422; unknown ID 404; stale revision/idempotency conflict 409. Conflict details contain the current record. Errors and logs never echo financial request bodies or subscription secrets.

## Writes: one operation executor

`POST /operations` accepts `{ "operation_id": UUID, "entity_id": UUID, "actor_id": UUID|null, "client_time": timestamp, "kind": string, "data": object }` and returns `{ "operation_id": UUID, "result": object }`. Pydantic/OpenAPI provides the exact discriminated union for each kind. Repeating an identical operation returns its original response. Reusing an ID with different content returns 409. Deduplication records are retained, including after deletions.

Kinds: `household.initialize`, `user.create`, `user.update`, `category.create`, `category.update`, `budget.set`, `purchase.create`, `purchase.update`, `purchase.delete`, `income.create`, `income.update`, `income.delete`, `savings.create`, `savings.delete`, `bill.create`, `bill.update`, `bill.pay`, `wishlist.create`, `wishlist.update`, `request.create`, `request.update`, `request.cancel`, `vote.set`, `comment.create`, `notification.read`, `installation.select`, `subscription.set`, `subscription.disable`.

Only household initialization and profile creation permit a null actor. Other commands require an active actor. Initializing the household explicitly precedes profile creation. Profile creation atomically creates its Personal category. The server records each write, deduplication outcome, audit event, change-log entries, and any notification/outbox records in one transaction. A failed command changes none of them.

Updates/deletes require `expected_revision`. Votes additionally require `request_revision`; votes use explicit `approved: true|false`. Each reviewer has an independent vote revision (0 before the first vote). Substantive request changes invalidate previous approvals. A linked purchase requires the current request revision, confirmed approval from all other active profiles, and an unlinked open request. Approval does not reserve money. Offline guarantees cover purchase/request creation and vote changes; remaining writes are online-only at `/operations`.

## Reads

`GET /health` reports process/database readiness without household data. GET `/household`, `/avatar-options`, `/users`, `/categories`, `/purchases`, `/income`, `/savings`, `/recurring-bills`, `/wishlist-items`, `/approval-requests`, `/comments`, `/notifications` expose household records. Collections accept `limit` (1–100), `offset`, and documented optional month/category/owner/target/recipient filters. Responses are `{ "items": [...], "limit": n, "offset": n }`. Tombstones are omitted from ordinary lists. `GET /records/{resource}/{id}` returns one record from a fixed allowlist, never arbitrary database tables. Request detail includes current approval status and reviewer votes.

`GET /budget-months/{month}` returns allocations, spending, Personal rollups, income, savings contributions, savings balance, planned unallocated income, and totals. A purchase's transaction date determines its month. Parent/child purchases are counted once. GET `/bill-occurrences?month=...` derives upcoming monthly occurrences; only recorded payments count as purchases.

## Synchronization

`POST /sync/push` accepts `{ "operations": [...] }` (up to 100) for purchase/request creation and votes, in client dependency order. Each operation commits independently; responses preserve order with either the original result or an actionable error. Retrying a previously accepted operation always checks deduplication before current entity state.

`GET /sync/pull?cursor=0&limit=100` returns `{ "changes": [{ "cursor", "resource", "record" }], "next_cursor", "has_more" }`. Records are snapshots at the recorded revision, including tombstones. The cursor advances only through returned changes. No change-log pruning in v1. `GET /sync/snapshot` reads all synchronized records and its cursor from the same read transaction. Household data and active-profile attribution remain separate on the client.

## Attachments and notifications

`POST /purchases/{id}/attachments` is multipart (`operation_id`, `actor_id`, timezone-aware `client_time`, `file`). The server validates decoded image format/size, generates the storage name and checksum, and returns metadata. GET `/purchases/{id}/attachments`, GET `/attachments/{id}/content`, and DELETE `/attachments/{id}?operation_id=...&actor_id=...&expected_revision=...&client_time=...` manage attachment metadata. No offline upload guarantee. Filenames are never used as paths. Deleted/orphaned files are retained until an explicit future cleanup policy so backups cannot lose referenced objects.

Notifications are created from committed changes. The outbox stores recipient IDs; delivery rechecks the current installation/profile binding. Minimal push payloads contain only a notification ID and app link. The worker retries transient failures, disables expired subscriptions and persists attempts; HTTP push is at-least-once, and clients should replace displayed notifications using the stable notification ID as a tag.

## Runtime configuration and recovery

`PIGPEN_ENV=development|production|test`, `PIGPEN_DATA_DIR=/absolute/path`, optional `PIGPEN_VAPID_PRIVATE_KEY` and `PIGPEN_VAPID_SUBJECT`. Production rejects data directories inside the source tree. No implicit production path, no production fallback for tests, and no database creation/migration on import or application startup. Run migrations explicitly before serving. Development uses synthetic data in a distinct configured directory. Tests explicitly configure temporary storage.

The CLI provides migration, snapshot backup, restore into a new directory, and one-shot outbox delivery. Backup combines SQLite's online backup with referenced attachment objects and a checksum manifest. Restore refuses an existing target; VAPID/private configuration is managed separately and never added to a repository or backup manifest. Backup retention and service/HTTPS installation remain operator decisions.
