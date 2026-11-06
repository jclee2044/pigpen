# Backend implementation gates

November 6, 2026. Authorized implementation of the staged backend plan. Existing artwork and uncommitted design work are outside this change.

1. Contract and immediate decisions: documented in backend-api.md; user confirmed currency/timezone/month rules and unanimous approval by other active profiles.
2. Application/configuration: passed (5 tests). TestClient hangs under restricted event-loop/thread execution; the identical suite passes with normal sandbox escalation. No runtime data created on import/startup.
3. SQLite/migrations: passed (6 cumulative tests): explicit migration, repeat migration, foreign keys/WAL/busy timeout, transaction rollback. Recovery follows the attachment stage.
4. Profiles/categories: passed (9 cumulative tests): atomic profile/Personal creation, avatar options, duplicate retries/names, invalid nesting and migration preservation.
5. Allocations/purchases: passed (17 cumulative tests): exact integer money, month boundaries, Personal rollups, allocation copying, simultaneous duplicate retries, tombstones and optimistic revisions.
6. Income/savings/bills: passed (19 cumulative tests): actual/expected income separation, savings without double-counting, month-end bill dates and payment retry/deduplication.
7. Wish lists/approvals/comments: passed (22 cumulative tests): unanimous independent votes, self/stale rejection, request-edit invalidation, atomic purchase links and event-failure rollback. Durable notification creation is in the same transaction.
8. Synchronization: passed (26 cumulative tests): ordered per-operation results, original actor preservation, repeat replay, cursor paging, immutable revision snapshots, tombstones and archived-record recovery.
9. Attachments/notifications/worker: passed (31 cumulative tests): decoded-image checks, immutable content-addressed uploads, idempotent upload/delete, private metadata, profile rebinding, retry persistence and expired subscriptions. Real push delivery still requires credentials and a device.
10. Recovery/deployment readiness: pending; live HTTPS and real-device push require operator configuration.
