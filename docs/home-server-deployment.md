# Omarchy/Tailscale deployment and device acceptance

Prepared and approved November 7, 2026; **API, push and backup services are installed. Private Tailscale HTTPS is verified**. This supersedes deployment proposals only where confirmed below. Existing historical documentation remains intact; earlier authentication-pending notes are superseded by the final verification record.

## Confirmed and proposed choices

Confirmed: installed iPhone/Safari PWA and desktop Chrome; use the existing Tailscale host `pigpen.example.com`; real financial storage stays outside Git; retain seven daily and four weekly full backups at `/home/pigpen/.local/share/pigpen-backups` (user confirmed November 7).

Prepared implementation choices: loopback API port 8017, separate tailnet HTTPS port 8445, user services under the existing `pigpen` account. These ports are available at preparation time. Existing Serve routes must remain: 443 → 3210, 8443 → 4312, 8444 → 3000. No public Funnel. Profile selection provides attribution rather than authentication; access follows the existing trusted tailnet policy.

## Reviewed installation scope — approved November 7

- Copy the verified frontend build to a versioned directory under `/home/pigpen/.local/share/pigpen-static/`, with `current` pointing to that release. Tests and Vite builds cannot change this deployed copy.
- Create the empty production database and uploads in `/home/pigpen/.local/share/pigpen-production`, registered explicitly as production. Do not copy synthetic development records into it.
- Create `/home/pigpen/.config/pigpen/pigpen.env` and a new mode-0600 `vapid.pem`. Environment values are reviewed in [pigpen.env.example](../deploy/omarchy/pigpen.env.example). Only the derived public key reaches browsers. The HTTPS application URL is the VAPID contact URI.
- Copy the five reviewed units in [deploy/omarchy](../deploy/omarchy) to `/home/pigpen/.config/systemd/user/`: API service, push service/timer, backup service/timer. Reload the user manager; enable API and timers. Existing user linger is already enabled, so no login policy change is required. No new system packages or login-policy changes are needed. This machine requires administrator authentication for the Tailscale Serve addition; the user separately approved that exact command. No ongoing operator privileges are granted.
- Create and validate the initial daily/weekly backups, restore one into a new temporary directory, check database readiness and remove only that temporary restore.
- Add only `tailscale serve --bg --https=8445 http://127.0.0.1:8017`. Verify HTTPS health, manifest and shell; compare the other Serve routes before/after.

Refuse to overwrite an existing PigPen production/configuration directory, release or unit. Recheck port and route availability immediately before installation. Installation is a machine-level change; the user provided approval under AGENTS.md before these paths and units were created.

## Runtime and recovery

The API serves built static files and JSON under one HTTPS origin. Static directories cannot overlap private data. SQLite remains local; browsers use the API. API processes never run migrations automatically. The push timer processes one due job every five seconds, with persisted retries. Provider delivery requires outbound connectivity. No financial content is sent in a push payload.

The backup timer runs daily around 03:15 America/New_York (up to ten minutes of jitter) and catches up after downtime. Each snapshot includes the full transaction-consistent SQLite database and referenced immutable receipt images. The first successful run each day/week publishes that period's snapshot. Subsequent same-period runs verify it. Daily and weekly directories hold separate full copies. Retention runs only after both current snapshots pass checksum, database and reference checks; unknown files or corruption stop pruning for review. Only managed snapshots in this dedicated, environment-registered root are eligible. A lock serializes timer/manual runs.

These backups are on the same machine. **TODO:** choose an independent private off-server copy and a private backup mechanism for the environment/VAPID key. Those secrets are deliberately excluded from financial snapshot manifests. Preserve the VAPID key across upgrades; changing it requires browser resubscription.

After installation, inspect with `systemctl --user status pigpen.service pigpen-push.timer pigpen-backup.timer` and `journalctl --user -u pigpen.service`. Logs must not contain financial request bodies or subscription keys. Use the backup/restore commands in [backend-operations.md](backend-operations.md) for manual recovery; restore always targets a new directory. Stop only PigPen's installed units during maintenance. Back up before migrations, build a new static release, run explicit production migration/check, update `current`, and restart the API. Retain the previous release for rollback. A schema rollback uses a verified restored database, never an automatic downgrade.

## Device acceptance still required

On the iPhone with Tailscale connected, open `https://pigpen.example.com:8445` in Safari. Create the real household/profiles, then use Share → Add to Home Screen (Open as Web App if offered). Launch from the new icon and verify it opens in its own app window. Wait for “Offline access ready” in Profiles & settings.

Use an explicitly labeled test purchase, turn connectivity off, close/reopen the installed app, and verify the action is still waiting. Reconnect and verify a single purchase with its original profile/date. Correct or remove that test record through the UI. Sync saved actions before removing the app or clearing browser data; device storage is not a backup and browser eviction cannot be ruled out.

Tap Enable notifications only in the installed app. Verify permission, switch the selected profile, and trigger a request/comment from another household device. Check that the right profile receives one generic OS notification and that tapping it opens the correct record. Verify denied permission leaves the inbox working and turning notifications off stops future delivery. Real provider delivery, OS installation and iPhone storage behavior cannot be proved by Chromium mocks.

Desktop Chrome must also pass installation, an offline reopening, and a household workflow. Version 1 release acceptance remains open until these intended-device checks and the home-server restore check pass.

## Installed verification record

The API is healthy on 127.0.0.1:8017; production shell, direct routes, manifest, service worker and immutable assets pass HTTP checks. The deployed static release is `098f8b72d27b2d0c`, copied outside the checkout. Private data/config/key permissions are restricted to pigpen. API, push timer and backup timer are active; the push oneshot exits successfully. The initial daily/weekly snapshots were verified and a separate temporary restore passed database readiness. No household or synthetic financial records were seeded into production.

The existing Serve configuration is unchanged. HTTPS port 8445 still needs the already approved administrator command to finish in the local terminal:

```sh
sudo /usr/bin/tailscale serve --bg --yes --https=8445 http://127.0.0.1:8017
```

No password is sent to Codex. Once authorized, verify trusted HTTPS and compare all prior Serve routes, then perform the intended-device checks above.

UI review update, November 7: current public asset release is `b9ec050e10817949`, with the exact requested pink header and household settings dropdown. The initial `098f8b72d27b2d0c` release remains available. Only the public asset pointer and API restart were needed; health and the served stylesheet passed verification. The HTTPS authorization status above is unchanged by this UI update.

Functional copy/dashboard review, November 7: current public release is `74f4b1fbb105e7a3`. Approval review uses a compact status, purchase rows display purchaser avatars, budget labels use the confirmed wording, and decorative copy/sidebar note were removed. Prior public releases remain available. API health and the served UI bundle were verified after restart; private financial storage and Tailscale configuration were unchanged.

Purchase empty-state/table review, November 7: current public release is `528c3f90ee18968c`. Empty purchases show the peeking pig and “Nothing here yet”; financial tables use 16px body text and 14px headers. Build, lint, disposable desktop/mobile visual checks and both production PWA browser checks passed before deployment. The public release pointer was atomically updated, only PigPen's API was restarted, and health, public bundle/styles and service-worker version were verified. Release `74f4b1fbb105e7a3` is retained for rollback. Private records, configuration and existing Tailscale routes were preserved; intended-device acceptance remains open.

Live-data acceptance, November 7: current public release is `4079b2b5d51f6019`, retaining `528c3f90ee18968c`. `GET /api/v1/runtime` identifies this installation as production and the UI displays Live data. All 67 backend, 12 unit and 11 browser checks passed, including independent-client synchronization and real-process restart/backup recovery. The installation's health, private permissions, public PWA assets and backup service completion passed; financial snapshot counts/cursor were preserved. A read-only desktop/mobile browser check displayed Create household without sending mutations. Enter real household/profile names and balances through that form; no demo financials were installed. See [the live-data execution record](live-data-plan.md) for commands and remaining gates. The approved sudo retry still required a password and all prior Tailscale routes remained intact; HTTPS verification awaits local authentication.

## HTTPS verified — November 7

After the operator completed the approved command locally, `https://pigpen.example.com:8445` passed hostname/certificate verification with the normal system/browser trust stores. `tailscale serve status --json` confirms 8445 → 8017 and preservation of 443 → 3210, 8443 → 4312 and 8444 → 3000. No further privileged command or policy change was needed.

Read-only HTTPS checks verified API health, production runtime metadata and its no-store header, the standalone manifest and every icon, service-worker scope/cache headers, direct browser routes, immutable public assets, release `4079b2b5d51f6019`, and enabled public push configuration without printing keys. A Chromium session at 390px verified secure context, service-worker control, offline reload, closed-page offline reopening and reconnect to Live data. API responses were absent from the public shell cache; all mutation requests were blocked and none were attempted. No financial records were created or changed.

Use the HTTPS address in Safari with Tailscale connected, then Share → Add to Home Screen. Real iPhone home-screen/OS behavior, two physical household devices and encrypted push-provider delivery remain manual acceptance checks. Existing automatic-test and backup/restore evidence is unchanged. Implementation commits: `da812e8` (UI review), `bcb8b03` (live-data validation).
