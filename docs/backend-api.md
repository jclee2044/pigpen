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

Kinds: `household.initialize`, `user.create`, `user.update`, `category.create`, `category.update`, `budget.set`, `purchase.create`, `purchase.update`, `purchase.delete`, `income.create`, `income.update`, `income.delete`, `savings.create`, `savings.delete`, `bill.create`, `bill.update`, `bill.pay`, `wishlist.create`, `wishlist.update`, `wishlist.delete`, `request.create`, `request.update`, `request.cancel`, `vote.set`, `comment.create`, `notification.read`, `installation.select`, `subscription.set`, `subscription.disable`.

Only household initialization and profile creation permit a null actor. Other commands require an active actor. Initializing the household explicitly precedes profile creation. Profile creation atomically creates its Personal category. The server records each write, deduplication outcome, audit event, change-log entries, and any notification/outbox records in one transaction. A failed command changes none of them.

Updates/deletes require `expected_revision`. Votes additionally require `request_revision`; votes use explicit `approved: true|false`. Each reviewer has an independent vote revision (0 before the first vote). Substantive request changes invalidate previous approvals. A linked purchase requires the current request revision, confirmed approval from all other active profiles, and an unlinked open request. Approval does not reserve money. Offline guarantees cover purchase/request creation and vote changes; remaining writes are online-only at `/operations`.

## Reads

`GET /runtime` returns `{ "environment": "production"|"development"|"test" }` from the server's validated configuration, with `Cache-Control: no-store`. It identifies the connected data source without exposing private paths, credentials or household values. It does not initialize storage or replace `/health`; clients may omit its optional source label if unavailable and continue using the existing data/sync contract. Production UI labels this source **Live data**, with connection/offline state shown separately.

`GET /health` reports process/database readiness without household data. GET `/household`, `/avatar-options`, `/users`, `/categories`, `/purchases`, `/income`, `/savings`, `/recurring-bills`, `/wishlist-items`, `/approval-requests`, `/comments`, `/notifications` expose household records. Collections accept `limit` (1–100), `offset`, and documented optional month/category/owner/target/recipient filters. Responses are `{ "items": [...], "limit": n, "offset": n }`. Tombstones are omitted from ordinary lists. `GET /records/{resource}/{id}` returns one record from a fixed allowlist, never arbitrary database tables. Request detail includes current approval status and reviewer votes.

`GET /budget-months/{month}` returns allocations, spending, Personal rollups, income, savings contributions, savings balance, planned unallocated income, and totals. A purchase's transaction date determines its month. Parent/child purchases are counted once. GET `/bill-occurrences?month=...` derives upcoming monthly occurrences; only recorded payments count as purchases.

## Synchronization

`POST /sync/push` accepts `{ "operations": [...] }` (up to 100) for purchase/request creation and votes, in client dependency order. Each operation commits independently; responses preserve order with either the original result or an actionable error. Retrying a previously accepted operation always checks deduplication before current entity state.

`GET /sync/pull?cursor=0&limit=100` returns `{ "changes": [{ "cursor", "resource", "record" }], "next_cursor", "has_more" }`. Records are snapshots at the recorded revision, including tombstones. The cursor advances only through returned changes. No change-log pruning in v1. `GET /sync/snapshot` reads all synchronized records and its cursor from the same read transaction. Household data and active-profile attribution remain separate on the client.

## Attachments and notifications

`POST /purchases/{id}/attachments` is multipart (`operation_id`, `actor_id`, timezone-aware `client_time`, `file`). The server validates decoded image format/size, generates the storage name and checksum, and returns metadata. GET `/purchases/{id}/attachments`, GET `/attachments/{id}/content`, and DELETE `/attachments/{id}?operation_id=...&actor_id=...&expected_revision=...&client_time=...` manage attachment metadata. No offline upload guarantee. Filenames are never used as paths. Deleted/orphaned files are retained until an explicit future cleanup policy so backups cannot lose referenced objects.

Notifications are created from committed changes. The outbox stores recipient IDs; delivery rechecks the current installation/profile binding. Minimal push payloads contain only a notification ID and app link. The worker retries transient failures, disables expired subscriptions and persists attempts; HTTP push is at-least-once, and clients should replace displayed notifications using the stable notification ID as a tag.

`GET /push-config` returns `{ "enabled": boolean, "public_key": string|null }`. The public key is URL-safe base64 of the uncompressed P-256 public point; private credentials are never returned. Missing key/contact disables browser registration; invalid configured keys return a generic 503. Clients explicitly request permission on a user gesture, subscribe through the service worker, then send `subscription.set` with the existing installation/subscription revision. Disable the server subscription before unsubscribing the browser. Push links resolve only notifications belonging to the currently selected profile; selecting another profile rebinds future delivery.

## Runtime configuration and recovery

`PIGPEN_ENV=development|production|test`, `PIGPEN_DATA_DIR=/absolute/path`, optional `PIGPEN_VAPID_PRIVATE_KEY` and `PIGPEN_VAPID_SUBJECT`. Production rejects data directories inside the source tree. No implicit production path, no production fallback for tests, and no database creation/migration on import or application startup. Run migrations explicitly before serving. Development uses synthetic data in a distinct configured directory. Tests explicitly configure temporary storage.

The CLI provides migration, snapshot backup, restore into a new directory, and one-shot outbox delivery. Backup combines SQLite's online backup with referenced attachment objects and a checksum manifest. Restore refuses an existing target; VAPID/private configuration is managed separately and never added to a repository or backup manifest. Backup retention and service/HTTPS installation remain operator decisions.

November 7 confirmation: seven daily and four weekly full backups at the private external destination are now approved as policy. `backup-scheduled DESTINATION` implements that policy in a new, dedicated environment-registered root. It verifies current snapshots before pruning only its recognized expired snapshots. Service installation remains a separate approval; see [home-server-deployment.md](home-server-deployment.md). `vapid-keygen /absolute/private/new.pem` explicitly creates a private P-256 key outside the checkout and refuses an existing file.

Plan edits may retain an existing archived category allocation unchanged, preserving historical plans. New or changed amounts on archived categories remain invalid; new-month copying includes only active categories.

## Built frontend serving

Optional `PIGPEN_STATIC_DIR=/absolute/path/to/frontend/dist` mounts the built Vue app after API routes. Static and private data directories must not overlap. Browser routes fall back to index.html; unknown API routes and missing assets remain 404. HTML/service worker require revalidation; hashed assets are immutable. The service worker caches only the built public shell, never API responses. Household records and pending operations use the separate IndexedDB transaction layer.

## Recurring budget defaults — November 7, 2026

Confirmed: assume the same plan across months; no manual copy action. A month without a saved plan uses the latest earlier saved plan (including expected income), even across skipped months. Only active categories inherit allocations. Months before the first plan remain unbudgeted. An explicit monthly plan, including an empty plan, overrides inheritance; edits preserve other saved months. Spending, income receipts and savings movements stay dated to their actual month; unused funds never roll forward.

`GET /budget-months/{month}` calculates effective inherited totals without writing a plan. Its `budget` remains null until that month has its own saved record. Snapshot clients derive the same fallback from budget-month and allocation records. `budget.set` with omitted/null allocations initializes from the latest earlier plan; explicit allocations override this fallback. The UI pre-fills effective expected income and allocations when editing. JSON shapes and revision rules are unchanged.

Avatar eyewear extension, November 7, 2026: `avatar.glasses` remains a manifest-listed string ID (for example `rounded-tortoiseshell`). Existing IDs remain valid and unchanged. `/avatar-options` glasses entries add `shape` and `frameColor` metadata for separate presentation controls; these fields are not profile fields. Shape/color variants are explicit allowed IDs, with `none` omitting the layer and `original` preserving each style’s original color. No schema migration or additional profile field is required.

Shared category order — November 7, 2026: `category.reorder` targets the household ID with `{ "expected_revision": <household revision>, "category_ids": [<top-level category UUID>, ...] }`. IDs must be unique, existing nondeleted top-level categories (up to 500). The supplied subset comes first; omitted categories retain their prior order and new categories follow the stored order. It atomically updates `household.category_order` (a UUID string array), advances the household revision, and emits the ordinary household sync record. Active household members can reorder any top-level category, including Personal parents. Standard revision conflict and operation-id deduplication apply. Archiving, amounts and category ownership are unaffected. Pointer drop and keyboard movement save this shared preference independently of unsaved budget amounts. Migration 0007 adds an empty order for existing households.

## Allocation amount/percentage editor — November 8, 2026

Confirmed request: the budget editor has Dollars and Percentages tabs directly below expected income, and persists both equivalent values. Implementation contract: Each allocation persists `amount_minor` and nullable `percentage_basis_points` (100 = 1.00% of expected income). `budget.set` continues accepting dollar amounts; the domain service derives and stores percentages on every save, including income-only edits and inherited plans. Snapshot allocation records include the new field. Existing records are backfilled by migration 0008. No new dependencies or request fields are needed.

Both views represent the same allocation: entering a percentage rounds the corresponding dollar amount to the nearest cent; percentages display to two decimal places with half-up rounding. Switching tabs alone preserves exact cents and never reapplies a rounded percentage. Changing expected income preserves dollar amounts and recalculates percentages. At zero income percentages are undefined (`null`), and percentage entry is disabled with guidance to enter income. Allocations above 100% remain allowed. Archived allocations retain their dollar amounts and stay read-only. The tab choice is editor state, not a change to the household plan.

## Category rename and restore — November 8, 2026

The existing `category.update` command accepts `{ "name": "Category name", "active": true, "expected_revision": 1 }`; `active: true` restores an archived category and `name` renames it without changing its ID, purchase links or saved allocations. The current revision is required. Personal categories remain editable only by their owner; Personal parent availability follows profile management. The Budget page exposes these existing operations through Manage categories. No new endpoint or schema is required.


Category hierarchies — November 8, 2026 (confirmed request): Subscriptions is a shared expense parent that allows subcategories. New shared expense categories offer an optional subcategory capability. One nesting level and parent-only allocations apply to both shared and Personal categories; child purchases roll up exactly once.

Contract before client integration: category records include `allows_subcategories: boolean`. `category.create` adds optional `allows_subcategories` (default false) and accepts expense children with `parent_id` pointing to an active, top-level expense parent with that flag enabled; expense `owner_id` stays null. Children cannot themselves allow children. Personal ownership rules remain in force and Personal parents always allow children. Savings cannot have children. `category.update` accepts optional `allows_subcategories`; omission preserves it for older clients. Disabling is rejected while any nondeleted child exists, including archived children. Parent links/kind/owner are immutable. Archived parents block new child entries and purchases until restored.

Migration 0009 preserves existing categories/references, enables Personal parents, and adds Subscriptions to existing households (or enables an existing shared top-level Subscriptions category). It publishes ordinary category change records so connected clients see these changes. Household initialization includes Subscriptions. This supersedes the earlier Personal-only hierarchy restriction.

Wish deletion — November 8, 2026: `wishlist.delete` uses the standard operation envelope with `entity_id` set to the wish ID and `data: { "expected_revision": number }`. Only the active owner may delete (403 for another profile); stale revisions return 409. The result is the revised wish with `deleted: true`, propagated through sync (including snapshots) and omitted from ordinary lists. Replaying the same operation returns the original outcome. Comments/history and independent approval requests/purchases remain intact. Online-only; no schema change.

Category deletion entry points — November 8, 2026 (confirmed request): Manage categories supports swiping left to reveal Delete, and Edit category offers Delete category. Both require an explicit confirmation. They use the existing `category.update` command with the saved name, `active: false`, and current `expected_revision`, matching deletion from Edit budget. This archives the category; past purchases and saved budgets remain, future months skip it, and Manage categories can restore it. Personal parents cannot be archived here; Personal children remain owner-only. No new API or schema is needed.

### Descriptive notification previews — November 8, 2026

Confirmed update superseding generic-only previews: new notification records expose `message: string` (older records may have an empty/missing message). The server snapshots a plain-text message at event creation using only the acting profile's name, action, and relevant item/category name. It excludes structured amounts, prices, balances, percentages, merchants, descriptions and comment bodies. Digits in names such as “Switch 2” remain intact. Older notifications retain their existing generic labels.

The encrypted Web Push JSON contract is now `{ "notification_id": string, "url": "/notifications", "tag": string, "title": "PigPen", "body": string }`. `body` is the same server-generated notification message, or a generic fallback for legacy records. Clients display only this approved `body` field, never compose a preview from raw financial fields. Existing recipient checks, stable tags, retries and same-origin deep links remain. New `purchase.created` notifications go to other active profiles only after committed purchase creation, including purchases linked to approvals; replaying an operation creates no duplicates. In-app inbox/banner use the persisted message with legacy label fallback. Comment notifications describe who commented and the target, without revealing comment text.

Approval card actions — November 8, 2026: `request.delete` accepts `{ "expected_revision": number }` and tombstones a request owned by the actor; linked/purchased requests cannot be deleted. `request.deny` accepts `{ "expected_revision": number, "reason": string }` (trimmed, 1–4000 characters). An active profile other than the requester can deny an open request. Denial atomically closes it with status `denied`, adds an attributed discussion comment containing the reason, and notifies other profiles without exposing the reason in push previews. Both operations are online-only, revision checked, audited, synchronized, and replay safe. Denied requests cannot be approved, edited or purchased; history remains accessible through All requests. Migration 0011 extends the request status constraint; it preserves existing records and foreign keys. Requester deletion preserves comments and prior audit history.
