# PigPen

PigPen is a shared household budget and spending PWA for mobile and desktop. It starts with two people and supports adding more profiles. The application will run on a home server with a Python/FastAPI backend, a server-local SQLite database, and a Vue frontend.

## Project documentation

- [Functionality and release scope](docs/functionality.md): profiles, monthly allocations, purchases, wish lists, approvals, notifications, and offline behavior.
- [Architecture](docs/architecture.md): application boundaries, proposed data model, API, synchronization, deployment, and verification.

These documents capture the decisions made on November 6, 2026. Items explicitly labeled **proposed defaults** remain open to revision; they are not confirmed requirements. This repository currently contains documentation, not an implemented application.

Receipt and bank screenshot extraction, and LLM spending advice, are deferred. Manual uploads, push notifications, and offline purchase/approval entry are part of the first release.

## Initial scaffold

Setup follows the staged guide. The original README above and existing `docs/architecture.md` and `docs/functionality.md` are preserved.

Confirmed stack: Python/FastAPI backend, home-server-local SQLite persistence, and Vue with TypeScript and Vue Router. Node.js/npm provide frontend tooling, not a separate application server. Framework-free domain services will be separate from API routes; frontend presentation will be separate from backend requests. Communication will use a documented JSON contract before integration.

The backend virtual environment and frontend dependencies are project-owned. This scaffold includes only dependency setup and the generated Vue starter. SQLite integration, migrations, PWA support, offline queues, push notifications, domain logic, API routes, and project-specific screens are not implemented.

Proposed defaults remain proposals in the existing docs: SQLAlchemy/Alembic, `/api/v1` routes and schemas, currency/timezone, approval aggregation, attachment limits, hosting/access, and backup policy. TODO: resolve these before their respective features; select deployment hostname/HTTPS and the eventual API entry point during implementation.

### Verified toolchain and dependency choices

Setup date: November 6, 2026. Verified on Omarchy 4.0.4 (Arch Linux), Python 3.14.7 (`/usr/bin/python3.14`), Node.js 26.8.2 and npm 11.19.1 (existing mise installation), Git 2.55.0 (`/usr/bin/git`). These are computer-level tools; no machine-level installation was needed. Python 3.10+ is the guide's baseline, but the resolved lock is verified specifically on Python 3.14.7/Linux x86_64; other interpreters/platforms require verification.

[Vue Quick Start](https://vuejs.org/guide/quick-start.html) currently requires Node `^22.18.0 || >=24.12.0`; the installed Node satisfies this and the generated `package.json` engines field. The official `create-vue@3.24.0` generator was used with `--ts --router --eslint --bare`. TypeScript and Router follow the user's request and architecture docs, overriding the guide's JavaScript-only choices. The current generator bundles Oxlint with ESLint; Vue DevTools and TypeScript/build helpers also come from that starter. No Pinia, JSX, unit/E2E tests, experimental choices, or optional formatter was selected.

`backend/requirements.txt` pins the only direct backend dependencies: `fastapi[standard]==0.162.0` (API framework and its standard tooling) and `pytest==9.2.0` (future backend verification). `backend/requirements.lock` records every resolved transitive version, including tooling pulled in by FastAPI's standard extra; these are dependency closure, not chosen PigPen services. The lock is a pip constraints file produced from this clean environment, not a cross-platform or hash-verified lock. Review dependency changes and regenerate it deliberately. `frontend/package-lock.json` records the exact npm dependency resolution and integrity values. Retain both locks.

### Reproducible setup

Run from the project root with the verified Python and Node toolchain available. Do not regenerate the frontend with `create-vue` on an existing checkout.

```sh
/usr/bin/python3.14 -m venv backend/.venv
backend/.venv/bin/python -m pip --no-cache-dir install -r backend/requirements.txt -c backend/requirements.lock
npm --prefix frontend ci
```

For an intentional backend dependency update only, explain the change, update the direct pins, resolve in a clean project environment, and record all resolved versions with `backend/.venv/bin/python -m pip freeze > backend/requirements.lock`. Ordinary setup uses the existing lock.

### Verification

```sh
backend/.venv/bin/python -c "import pathlib, sys, fastapi, pytest; assert pathlib.Path(sys.prefix) == pathlib.Path('backend/.venv').absolute(); assert sys.prefix != sys.base_prefix; print(sys.executable, fastapi.__version__, pytest.__version__)"
backend/.venv/bin/python -m pip --no-cache-dir check
backend/.venv/bin/python -m pip --no-cache-dir install --dry-run --no-index -r backend/requirements.txt -c backend/requirements.lock
npm --prefix frontend ls --all
```

Run the frontend quality and build commands from its own directory so local configuration is discovered:

```sh
cd frontend
npm exec -- oxlint .
npm exec -- eslint .
npm run build
```

These lint commands check without modifying files. The generated `npm run lint` is also available, but applies automatic fixes. `npm run build` includes TypeScript checking and emits production assets into ignored `frontend/dist/`. No backend tests exist yet; a pytest run would collect no tests, not demonstrate application correctness.

### Local development

```sh
cd frontend
npm run dev
# Optional local preview after npm run build:
npm run preview
```

No FastAPI application entry point or route exists yet, so there is no backend development server command to run. TODO: document the actual entry point and JSON contract when backend implementation is authorized. Node runs the Vite development tool only; deployment will serve built static assets.

See [the staged setup record](docs/setup.md) for outcomes, command evidence, created files, and remaining Git work.
