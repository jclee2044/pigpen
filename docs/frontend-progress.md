# Frontend implementation gates

November 7, 2026. Authorized execution of the frontend-to-release plan.

1. API connection and testing: passed (4 unit tests, TypeScript/production build and non-mutating lint). Request types are generated from the backend contract; tests use pinned Vitest, Playwright and fake-indexeddb. Native fetch/Vue/Router remain the application stack.
2. Responsive shell: passed (Chromium desktop/mobile routing and overflow checks, TypeScript build and lint). Accepted visual direction and layered avatar assets are reused.
3. Profiles and identity: passed (5 unit tests, real FastAPI/SQLite onboarding, remembered selection/avatar, responsive routing, build and lint). All test data is disposable outside the checkout.
4. First budget/purchase workflow: passed (real-browser allocations, purchase creation, lost-response retry, single purchase, reload persistence, and parity with backend budget totals).
5. Financial management and attachments: passed (real-browser income, starting savings, short-month bill payment, receipt upload and purchase correction; backend totals checked). Category and income/bill forms share typed mutation services.
6. Wish lists/approvals/comments: pending.
7. Notification inbox: pending.
8. Durable offline records and synchronization: pending.
9. PWA installation/offline reopening: pending.
10. Browser push: pending real-device/credential acceptance.
11. Release acceptance: pending.
12. Production deployment: requires hostname, HTTPS, private storage and machine-level approval after a concrete configuration is prepared. No real financial data is used during development.

Confirmed deployment target: installed PWA on iPhone/Safari and desktop Chrome, reached through the existing Tailscale host pigpen.example.com. Existing HTTPS ports 443, 8443 and 8444 serve other applications and must be preserved.
