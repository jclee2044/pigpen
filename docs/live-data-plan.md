# Live-data implementation and validation

November 7, 2026. Requested after committing the UI review as `da812e8`.

## Scope and current evidence

Confirmed: use the existing Vue/TypeScript/Router frontend and FastAPI backend, keep real financial records and uploads outside Git, and use the approved private home-server/PWA deployment. The frontend already uses same-origin `/api/v1` requests and a private SQLite database; no mock-data switch exists in application code. Synthetic data is confined to test tooling and static design studies. Real household/profile names and opening balances must be entered by the household, not invented during deployment.

Read-only preparation found the API healthy at `127.0.0.1:8017`, both scheduled timers active, and the private production/backup/static directories present. The old `localhost:53854` preview is unavailable. Tailscale still has only the previously existing 443, 8443 and 8444 routes; PigPen's already approved 8445 route remains to be completed.

The following are implementation choices for this work, not additional business requirements. Keep each gate's verification green before proceeding.

## 1. Identify the connected data source

Document `GET /api/v1/runtime` before implementation. Return only the configured environment (`production`, `development` or `test`), with `Cache-Control: no-store`. Preserve the existing health response and keep private paths, credentials and financial values out of this metadata. Show a compact data-source status beside connection/sync state; cached/offline records remain labeled as saved device data. No placeholder data or production auto-seeding.

Gate: backend response tests for every environment and startup without storage side effects; frontend build/lint and source-status browser checks. Failure to retrieve optional metadata must not prevent existing records or pending actions from working.

## 2. Prove two-client behavior with disposable data

Run the built production frontend against an actual FastAPI process and temporary test SQLite storage. Use separate browser contexts with independent IndexedDB/device identities. Enter profiles, a budget and purchases through the UI. Verify the second client obtains the exact committed values after syncing, edits propagate, reload retains records, and offline entry on one client is delivered once with its original profile. Compare the resulting API totals and record count. Explicitly label the connection as test data.

Gate: the new two-client acceptance test plus the existing offline/conflict/PWA checks pass. Never direct mutation tests at the installed production service.

## 3. Prove persistence and recovery

Exercise an actual server-process restart with a saved budget/purchase and replay the original operation. Verify the recorded amount and idempotent result survive. Back up that disposable database, restore to a new disposable directory, and verify totals through a fresh server. Reuse the existing attachment/checksum and retention tests.

Gate: backend suite, generated-contract consistency, frontend unit suite, and browser acceptance pass. No dependency, schema or financial-rule change is planned.

## 4. Build and publish the verified release

Build immutable public assets, retain the previous installed release, atomically update the public release pointer and restart only PigPen's API. Verify health, runtime environment, manifest, service worker, direct browser routes, served asset version, and first-use household setup without creating financial records. Check private database/config permissions and backup service readiness without printing their contents. Record the deployed build and exact verification results here and in the deployment record.

Gate: installed service reports production and the browser displays the expected live-data status. Preserve private records, keys and other applications' services/routes. Commit the implementation and evidence locally; no push or remote/branch changes.

## 5. Finish the private entry point and device acceptance

Complete only the previously approved Tailscale 8445 → 8017 route if local administrator authentication permits it; retain all other routes. Verify trusted HTTPS health, runtime metadata and PWA assets through the hostname. If authentication is still needed, present the exact local command rather than changing operator privileges or handling a password.

Final manual acceptance: the household enters real names and its first budget, installs the PWA on iPhone/Safari, checks a labeled purchase across two household devices, tests offline reopening/reconnect and real notification delivery. These OS/provider checks require the intended devices and remain explicit until performed. An independent private off-server backup remains a documented TODO rather than an approved deployment change.

## Execution record

Gates 1–4 passed. Added the documented runtime endpoint and optional source status; production displays **Live data**, test servers display **Test data**, and a running client labels offline records **Saved data**. Missing metadata does not interrupt financial reads or pending actions. The original health response and financial contract remain intact.

Verification commands: `backend/.venv/bin/python -m pytest -q backend/tests` (67 passed), `backend/.venv/bin/python tools/generate_api_types.py --check`, `backend/.venv/bin/python -m compileall -q backend/pigpen tools`, and `backend/.venv/bin/python -m pip check` (consistent). From `frontend/`: `npm test` (12 passed), `npm run lint:check`, `npm run build`, `npm run test:e2e` (seven passed), and `npm exec -- playwright test --config playwright.pwa.config.ts` (four passed, including the two new live-data acceptance tests). `git diff --check` passed. No dependency versions changed.

The two independent browser contexts entered profiles, a budget, a purchase and a correction through the UI. Both clients agreed on exact cents. An offline purchase survived a closed page and reached the server once under its original profile; repeated syncs and reload retained the result. A separate test verifies optional metadata failure leaves records usable. Initial acceptance-test assumptions about post-edit navigation and shared test data were corrected before the passing run. A sandbox-blocked foundation check was stopped and rerun with ordinary local test transport; all test servers use disposable external storage.

The real-process recovery test saved a budget/purchase, stopped and restarted its own API process, replayed the original operation without duplication, backed up the test database, restored into a fresh test directory, and checked totals/idempotency through another server. Existing attachment/checksum/retention tests also passed.

Installed public release: `4079b2b5d51f6019`; previous `528c3f90ee18968c` retained. The approved installation refresh atomically switched public assets and restarted only PigPen's API. Production health/runtime, no-store metadata, direct routes, standalone manifest, service-worker version and served bundle were verified. Private data/config/key permissions passed, API/push/backup timers were active, and the installed backup service completed successfully. Before/after snapshot counts and cursor were identical. A read-only Chromium check verified **Live data** and the first-use form at 1440px and 390px, with no API mutation requests or page overflow; screenshots were reviewed. The production household is still uninitialized so the household can enter its real names and balances.

Gate 5 remains pending local authentication/device acceptance. Retrying only the previously approved noninteractive sudo command returned **a password is required**; existing Tailscale routes were verified unchanged. The local operator was asked to run the exact approved command and reply Done so HTTPS can be checked. No administrator/operator policy change was attempted. Real iPhone installation, encrypted push delivery and off-server backup remain unverified/TODO as described above.

Gate 5 transport verification passed after the operator replied Done on November 7. The live address is `https://pigpen.example.com:8445`. Read-only `tailscale serve status --json` and Python urllib requests verified all four expected routes, normal certificate/hostname trust, production health/runtime, no-store metadata, manifest/icons, worker scope/cache policy, direct routes, immutable assets and the deployed build. Public push configuration is enabled; private credentials were not exposed.

A read-only Chromium session through that HTTPS origin verified secure context, service-worker control, offline reload, closed-page offline reopening, reconnect to Live data, absence of API responses from the public shell cache and a fitting 390px layout. The session blocked mutations and attempted none. No implementation rebuild or additional privileged operation was needed. Real iPhone installation, physical-device workflows, actual encrypted push delivery and the independent off-server backup TODO remain open. Implementation is committed as `bcb8b03`; UI review is `da812e8`.
