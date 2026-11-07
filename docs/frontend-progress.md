# Frontend implementation gates

November 7, 2026. Authorized execution of the frontend-to-release plan.

1. API connection and testing: passed (4 unit tests, TypeScript/production build and non-mutating lint). Request types are generated from the backend contract; tests use pinned Vitest, Playwright and fake-indexeddb. Native fetch/Vue/Router remain the application stack.
2. Responsive shell: passed (Chromium desktop/mobile routing and overflow checks, TypeScript build and lint). Accepted visual direction and layered avatar assets are reused.
3. Profiles and identity: passed (5 unit tests, real FastAPI/SQLite onboarding, remembered selection/avatar, responsive routing, build and lint). All test data is disposable outside the checkout.
4. First budget/purchase workflow: passed (real-browser allocations, purchase creation, lost-response retry, single purchase, reload persistence, and parity with backend budget totals).
5. Financial management and attachments: passed (real-browser income, starting savings, short-month bill payment, receipt upload and purchase correction; backend totals checked). Category and income/bill forms share typed mutation services.
6. Wish lists/approvals/comments: passed (browser wish creation/comment/prefill, self-approval exclusion, reviewer voting, unanimous approval and linked purchase).
7. Notification inbox: passed (browser read-state persistence, recipient filtering, notification deep links; notifications work independently of push permission).
8. Durable offline records and synchronization: passed (10 unit tests and 4 browser workflows). Offline purchase entry, original-actor preservation after switching, reconnect deduplication, monotonic cursor commits, storage-abort handling, and the background profile-selection race are verified.
9. PWA shell/offline reopening: passed in production Chromium (manifest/standalone configuration, service-worker control, offline reload and closed-page reopening, durable queued purchase and exactly-once reconnect). Desktop/mobile screenshots reviewed. Real iPhone home-screen installation remains device acceptance. Native service worker/manifest use no new runtime dependency. FastAPI serves the built app under the same origin; two backend tests verify API routing, cache headers, traversal/symlink protection and private/static separation.
10. Browser push integration: passed synthetic production-browser checks (permission only on click, denied permission recovery, subscription registration/disable, inbox deep link); public-key API/private-key creation tested, service-worker payload privacy/link origin unit tested. 11 frontend unit tests pass. Real iPhone permission and encrypted provider delivery remain device/production acceptance; no real push sent.
11. Automated release acceptance: passed (63 backend tests; 12 frontend unit tests; six browser workflows and two production PWA/push workflows; generated-contract check, compilation, dependency consistency, TypeScript build and non-mutating lint). Stale offline votes are visibly rejected without approving a revised price; archived allocations survive plan edits; all seven destinations fit a 390px viewport. Native dialogs support Escape/focus behavior. Intended-device acceptance remains open.
12. Production deployment: approved API/push/backup services installed and healthy, external production data/config and separate deployed assets created, initial backup restore verified. [HTTPS and device acceptance](home-server-deployment.md) await local administrator authentication for Tailscale port 8445 and real-device checks. Existing Serve routes are preserved. No synthetic records seeded into production.

Confirmed deployment target: installed PWA on iPhone/Safari and desktop Chrome, reached through the existing Tailscale host pigpen.example.com. Existing HTTPS ports 443, 8443 and 8444 serve other applications and must be preserved.

## Reproduction and dependency record

From the project root: `backend/.venv/bin/python -m pytest -q backend/tests`, `backend/.venv/bin/python tools/generate_api_types.py --check`, `backend/.venv/bin/python -m compileall -q backend/pigpen tools`, and `backend/.venv/bin/python -m pip check`. From frontend/: `npm ci`, `npm test`, `npm run lint:check`, `npm run build`, `npm run test:e2e`, `npm run test:pwa`, `npm ls --all`, and `npm audit`. Browser tests start only their own disposable API/database and local frontend, using the existing Chromium binary. No global package or browser installation. Tests may need ordinary execution outside the restricted sandbox for TestClient threads and local sockets.

The development dependency audit's 11 moderate reports all traced to minimatch 10.2.6. The [maintainer advisory](https://github.com/advisories/GHSA-g3hv-75wg-m249) lists 11.0.1 as patched. An explicit `minimatch: 11.0.1` override updates only that transitive resolution and its dependencies; the locked toolchain remains. Linters, builds and tests verify this override with the existing Node 26 environment. The resulting npm audit reports zero vulnerabilities. Revisit the override when upstream lint dependencies accept the patched major version.

Financial runtime records, backups, uploads, environment files and keys stay outside Git. The existing design/ output/ and UI-reference documentation supplied separately are preserved and excluded from these implementation commits. No remote, push or branch changes were made.

## UI review update — November 7

Confirmed visual feedback: header background matches the supplied swatch exactly (`#F2DDE4`); remove the header tagline and the marked profile-page eyebrow, subtitle and attribution paragraph; move Profiles & settings from the sidebar footer into the Our household dropdown. The dropdown keeps selected-profile attribution visible and supports keyboard entry, Escape, outside clicks and route changes.

Changed presentation files: `frontend/src/App.vue`, `frontend/src/style.css`, `frontend/src/views/ProfilesView.vue`, and new `frontend/src/components/HouseholdMenu.vue`. Existing browser helpers/selectors and shell/offline workflows were adjusted for the new navigation. No dependencies or API/domain rules changed.

Checks run: `npm run build`, `npm run lint:check`, `npm run test:e2e` (six passed), `npm exec -- playwright test --config playwright.pwa.config.ts` (two passed), and `git diff --check`. Built desktop/mobile screenshots were visually reviewed. The previous browser preview at localhost:53854 was unreachable from the workspace; the installed app at 127.0.0.1:8017 was updated and its health and served header color verified. Real iPhone checks remain outside this UI verification.

Deployed public asset release: `b9ec050e10817949`; previous release retained. Financial storage and existing service configuration are unchanged.

## Functional copy and dashboard review — November 7

Confirmed feedback: use direct screen/action names and budget terminology, show approval review as a compact status, show purchaser avatars instead of category initials, and remove the decorative sidebar note. Decorative headings, empty-state slogans and invented wish descriptions were removed across the Vue screens, forms, comments, installation/push settings and inbox labels. Essential guidance about approvals, savings, offline actions and device data is retained.

Research references: [Copilot dashboard overview](https://help.copilot.money/en/articles/6045480-dashboard-tab-overview) separates review items and budget summaries; [Monarch budget guide](https://help.monarchmoney.com/hc/en-us/articles/360048883631-Budgets) presents monthly category budgets and spending directly. These informed the compact review status and labels Budgeted, Spent and Budget remaining. Existing financial calculations and JSON field names remain unchanged.

Presentation changes are in DashboardView, BudgetView, PurchaseRows, App/sidebar, the remaining view headings and related form/settings components, plus lib/notifications.ts. Browser interactions were updated for the direct labels. A browser workflow verifies that approval status increases for a new request, decreases only after the selected reviewer's vote, opens Approvals, and displays two different purchasers' avatars.

Commands: `npm run build`, `npm run lint:check`, `npm run test:e2e` (seven passed), `npm exec -- playwright test --config playwright.pwa.config.ts` (two passed), `git diff --check`. Desktop/mobile screenshots with synthetic purchases were reviewed. No new dependencies. The original localhost:53854 preview is unavailable to the browser tools; the installed app at 127.0.0.1:8017 serves the verified update. Real iPhone acceptance remains unverified.

Current deployed public release: `74f4b1fbb105e7a3`.

## Purchase empty state and table readability — November 7

Confirmed review feedback: empty purchases say **Nothing here yet**, accompanied by the existing pig mascot looking toward the viewer; larger financial table text; retain direct labels and remove decorative subtitles throughout the app. The previously implemented **Unbudgeted income** wording remains in place. These presentation choices do not alter the API contract or financial rules.

Added `frontend/src/components/PurchaseEmptyState.vue`, composing the existing SVG pig into a playful peeking illustration. `PurchaseRows.vue` shares this state between Purchases and the dashboard. `frontend/src/style.css` now uses 16px table body text, 14px headers/secondary notes, tabular numerals and unbroken money values. Tables retain their own overflow container on narrow screens. No dependencies or original avatar assets changed.

Commands/checks: `npm run build`, `npm run lint:check`, `npm exec -- playwright test --config playwright.pwa.config.ts` (two passed), and `git diff --check`. A one-off Playwright review used `tools/run_test_api.py --port 8767 --static --demo` and a disposable synthetic database: filtered Purchases displayed the mascot and exact empty-state text, Budget used the intended computed font sizes, and both views fit 1440px/390px viewports without page overflow or browser errors. Desktop/mobile screenshots were visually reviewed. The first review attempt used an incorrect profile-button selector; the corrected review passed and its temporary server was stopped. The full domain/browser suites were not repeated for these presentation-only changes; real iPhone acceptance remains open.

Deployed public release: `528c3f90ee18968c`; previous release retained. PigPen API health, the served empty-state bundle, budget wording, table styles and service-worker build were checked after the approved installation refresh. The older localhost:53854 preview remains unavailable; the updated installed app is at http://127.0.0.1:8017/purchases.

## Live-data acceptance — November 7

UI review was committed as `da812e8`. The requested [live-data plan and execution record](live-data-plan.md) was written before implementation. The existing frontend already used FastAPI/SQLite; the new optional `/api/v1/runtime` metadata makes the connected source visible without exposing financial records or private paths. The app shows Live data for production and Test data for disposable test servers, with saved-device state when offline. Metadata failure leaves the existing data/sync flow available.

Added production-build two-client acceptance: UI-entered profiles/budget/purchase, correction visibility, separate device state, closed-page offline persistence, exactly-once reconnect and API total parity. Added a metadata-unavailable case and actual-process restart/backup/restore verification. Commands/results: backend 67 passed, frontend unit 12 passed, ordinary browser seven passed, production PWA/live-data four passed; generated-contract check, compileall, pip check, TypeScript build, lint and diff check passed. No dependencies or financial rules changed. Exact commands, presentation/test files and remaining deployment/device gates are in the linked execution record.

Current installed release: `4079b2b5d51f6019`. Production health/source metadata, private permissions, backup service success and unchanged record counts/cursor passed verification. The installed first-use form and Live data status were visually checked at desktop/phone sizes with no API mutations. Real setup is intentionally left for the household's own entries. The private HTTPS route still needs local sudo authentication; intended-device checks remain open.

HTTPS completion, November 7: the operator finished the approved route locally. `https://pigpen.example.com:8445` now serves the verified production PWA with trusted HTTPS, preserving all existing routes. A read-only Chromium check through this origin passed service-worker control, offline reload/closed-page reopening, reconnect and mobile overflow checks; API responses were absent from the shell cache and no mutations were attempted. See [the deployment verification](home-server-deployment.md#https-verified--november-7). Real iPhone installation and encrypted provider delivery remain manual acceptance; no code or dependency change was required.
