# Monthly analysis — November 22, 2026

## Confirmed scope

Sir Pennysworth reviews the previous calendar month's budget and purchases. A push notification opens the saved analysis. Home shows a deeper pink review card above Ask Sir Pennysworth on days 1–5, whether or not it was opened. There is no reviewed/dismissed state. Past analyses remain accessible from a permanent bubble in the advisor card. Reports contain relevant findings, exact charts, supporting purchases and contextual chat, using the existing app design. Suggestions never mutate financial records.

## Implementation defaults

- Generate at 08:00 on the first in the household timezone, starting with the month in which this feature is installed. No unsolicited historical backfill on installation. A durable job lease/retry recovers downtime; missed months are saved, with only the newest completed month notifying active profiles. One report per household/month; one notification per recipient/report.
- Keep the original report and its source snapshot. Later purchases/edits do not silently rewrite history. The report shows its preparation date and a changed-records notice when applicable; contextual chat distinguishes the saved report from live read-tool results.
- Compare up to six prior calendar months with recorded activity. Missing months are not zeros. Parent/child expense spending rolls up once; savings are separate from purchases. Other grouping uses purchase descriptions/explanations only as untrusted evidence. Limits are disclosed in the report when model evidence is truncated.
- PigPen computes all totals and chart marks. The existing configured OpenAI model selects/ranks structured findings and supplies short interpretations, using store=false. Referenced categories/purchases and grouped totals are validated. Provider failures retry with persisted backoff; no failure push or invented analysis is published.
- Existing API process runs the lightweight scheduler; existing push outbox/timer handles delivery. No new dependency, machine package, service or timer is needed. Report viewing/history require connectivity; chat stays in page memory and is cleared on profile/month changes.

## JSON contract (before client integration)

### Explicit preview operation

An operator may generate a current-month preview on explicit user request. It uses real recorded data, labels the summary as a month-to-date preview, and warns the model that the month is incomplete. Preview rows are readable in history/detail/chat, but never count as completed scheduled reviews. At the user's request, the preview also appears in the homepage card during its own calendar month, labeled as a preview; regular completed reviews retain the days 1–5 rule. The ordinary scheduler replaces the preview with the completed report after month end. Preview notifications have a separate deduplication key and preview wording, so the normal monthly notification still occurs. This is an operator action, not a new public API endpoint; it never changes budgets or purchases.

All paths are under `/api/v1`, responses use `Cache-Control: no-store`.

- `GET /advisor/reviews?before=YYYY-MM&limit=24`: `{items: ReviewSummary[], next_before: string|null, current_month: string, show_home: boolean, latest: ReviewSummary|null, enabled: boolean}`. Month/day use the server's household timezone. `latest` is the previous completed month, except a current-month preview is selected when no completed report is eligible for the homepage. `show_home` is true on days 1–5 for completed reports, or during the preview's own month. Summaries add `is_preview: boolean`; older clients may ignore it. Pagination is descending and excludes `before`.
- `GET /advisor/reviews/{month}`: `Review`, or 404 until ready. `Review` includes `id`, `month`, `created_at`, `summary`, `totals`, `findings`, `coverage`, `data_changed`, `chat_enabled`. `totals` has integer-cent `budgeted_minor` (expenses), `spent_minor` (purchases), `remaining_minor`, `savings_allocated_minor`, `savings_actual_minor`, `income_minor`. `coverage` contains `comparison_months`, `purchase_count`, `included_purchase_count`. Each finding has stable `id`, `kind` (`trend`, `budget`, `category_group`, `observation`), `title`, `explanation`, optional `suggested_category`, `category_id`, exact `chart: {label, amount_minor}[]`, and saved `purchases: {id, item, merchant, transaction_date, amount_minor, category_id, category_explanation}[]`. ReviewSummary has `id`, `month`, `created_at`, `finding_count`, `remaining_minor`.
- Existing `POST /advisor/ask` adds optional `review_month: string|null`, `finding_id: string|null`. A review request must match `month` and reference an existing saved report/finding. The server supplies its snapshot; clients cannot inject report content. Ordinary chat remains compatible. Existing answer/history contract remains unchanged.
- Notification kind `analysis.ready`, resource `monthly-reviews`, target report UUID. Its safe text contains the month name only, never amounts or category findings. Push URL `/analyses/YYYY-MM` is allowlisted by the service worker; inbox links use the report UUID via `/analyses?report=UUID`.

## Release isolation

Monthly reviews use an independent additive migration branch from 0014, joined with the category migration by 0017. During verification the monthly-category release became live at schema 0015; the deployment guard stopped the earlier receipt-based candidate before any mutation. The final snapshot builds on that verified category/receipt release and migrates 0015 → 0017. Existing categories, purchase explanations and receipt behavior are preserved. Review code also accepts older purchase snapshots without the Other explanation field.

## Verification

Deployed `bae0e96c26ae0f81`, schema 0017, preserving the verified category/receipt release. Final validation: 150 backend tests, 46 frontend unit tests, 10 browser tests, build/type/lint/contract checks, a real synthetic-data structured model response, and live read-only verification at mobile/desktop widths. First review: November 2026, generation scheduled for December 1 at 08:00 America/New_York. See [commands, changed files, backup/rollback evidence and limitations](../output/monthly-analysis/verification.md). Physical-device push delivery and the future scheduled event remain acceptance checks.
