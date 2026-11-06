# Initial scaffold setup record

Date: November 6, 2026. Scope: setup only; no PigPen features.

The attached guide supplies a staged workflow. The user's explicit request takes precedence over its JavaScript/no-Router defaults. Existing product documentation remains the source for requirements; proposed defaults have not been approved by this setup.

## Stage outcomes

| Stage | Result | Evidence |
| --- | --- | --- |
| 1. Bounded structure | Passed | Created backend/, frontend/, AGENTS.md, .gitignore; appended README without replacing original text; preserved existing docs/. |
| 2. Read-only preflight | Passed; initial readiness partial | Inspection made no changes. Python/Node/npm/Git available; backend environment, manifests, frontend lock and node_modules initially missing. |
| 3. Git tool checkpoint | Passed | Git 2.55.0 at /usr/bin/git. Initially not a repository; .git was an empty protected directory. No repository changes during this checkpoint. |
| 4. Python checkpoint | Passed | Python 3.14.7: /usr/bin/python, /usr/bin/python3, /usr/bin/python3.14 and /bin aliases resolve to /usr/bin/python3.14. These are all Python interpreters discovered on PATH, not an exhaustive scan of the machine. No installation needed. |
| 5. Backend environment | Passed | backend/.venv is isolated; FastAPI 0.162.0 and pytest 9.2.0 import; pip check passes. Direct pins and the full resolved version constraints are recorded. |
| 6. Node/npm checkpoint | Passed | Node v26.8.2 and npm 11.19.1 at /home/pigpen/.local/share/mise/installs/node/26.8.2/bin/{node,npm}; mise shims also available. Satisfies official Vue requirement ^22.18.0 or >=24.12.0. |
| 7. Vue environment | Passed with advisory limitation | Official create-vue 3.24.0 bare TypeScript/Router/ESLint starter. npm install added 307 packages; npm ci --offline rebuilt them successfully from package-lock.json. Generated lint passes. |
| 8. Scaffold verification | Passed for setup/build; dependency audit partial | Direct read-only lint, TypeScript/production build, backend imports/checks, npm dependency-tree validation, documentation preservation and ignore rules verified. See limitation below. |
| 9. Initial Git checkpoint | Approved | User approved the reviewed scaffold commit. Initialized Git at /home/pigpen/Documents/pigpen through the normal sandbox escalation mechanism. Exact commit scope is listed below; no remote, push, or branch switch. |

Computer tools are separate from project-owned environments: backend/.venv and frontend/node_modules. No global dependencies, machine software, system/desktop settings, database, or server processes were installed/configured/started.

## Commands and inspection evidence

Commands ran at the project root unless another working directory is stated. File scaffolding, README append, SHA-256 assertions, PATH interpreter enumeration and this report were performed with Python pathlib scripts. Persistent writes are enumerated below. Tool output is summarized here; this is not a byte-for-byte terminal transcript.

Initial inventory / read-only checkpoints:

```sh
pwd
rg --files -g 'AGENTS.md' -g 'README.md' -g 'docs/**' -g 'package.json' -g 'pyproject.toml' -g '*lock*' -g '.gitignore'
cat /home/pigpen/.codex/attachments/7f0fcd3b-80a6-4920-8579-b84a3a866ba7/setup-prompts.md
ls -la
cat README.md docs/architecture.md docs/functionality.md
find .. -name AGENTS.md -print
cat /etc/os-release
type -a python python3 python3.10 python3.11 python3.12 python3.13 python3.14 node npm git
python --version
python3 --version
node --version
npm --version
git --version
git rev-parse --show-toplevel
git status --short --branch
ls -la .git .agents .codex
printenv PATH
```

Python 3.10–3.13 executable names were absent. PATH enumeration also checked every matching interpreter's version and resolved path. Git's initial rev-parse/status correctly reported no repository. OS: Omarchy 4.0.4, Arch family, Linux x86_64. Existing frontend/ was empty before generation. No FastAPI/pytest manifest or owned environment existed initially.

Official workflow references read: [Vue Quick Start](https://vuejs.org/guide/quick-start.html), [create-vue](https://github.com/vuejs/create-vue). Current command-line options were checked using the pinned generator's --help output.

Backend preparation and verification:

```sh
python -m venv backend/.venv
backend/.venv/bin/python -m pip --version
backend/.venv/bin/python -m pip index versions fastapi
backend/.venv/bin/python -m pip index versions pytest
backend/.venv/bin/python -m pip --no-cache-dir index versions fastapi
backend/.venv/bin/python -m pip --no-cache-dir index versions pytest
backend/.venv/bin/python -m pip --no-cache-dir install -r backend/requirements.txt
backend/.venv/bin/python -m pip freeze > backend/requirements.lock
backend/.venv/bin/python -m pip check
backend/.venv/bin/python -m pip --no-cache-dir install --dry-run --no-index -r backend/requirements.txt -c backend/requirements.lock
```

Import assertions used backend/.venv/bin/python, checked sys.prefix against the absolute backend/.venv path and sys.base_prefix, and printed interpreter /home/pigpen/Documents/pigpen/backend/.venv/bin/python and both direct versions. The full lock was compared with the installed distributions. The dry run found all constraints satisfied without network or dependency changes. pip 26.2.1 came from venv creation; it was not upgraded. Portability beyond the verified Python/Linux environment and hash-based artifact integrity were not verified.

The first sandboxed PyPI/npm queries failed DNS resolution. Normal network escalation allowed subsequent dependency resolution/install commands. pip initially warned that the default user cache was unwritable; --no-cache-dir was used for network installation, and no global cache permissions were changed. npm used npm_config_cache=/tmp/pigpen-npm-cache throughout download/install operations.

Frontend setup:

```sh
npm_config_cache=/tmp/pigpen-npm-cache npm view create-vue version
npm_config_cache=/tmp/pigpen-npm-cache npm exec --yes --package=create-vue@3.24.0 -- create-vue --help
npm_config_cache=/tmp/pigpen-npm-cache npm exec --yes --package=create-vue@3.24.0 -- create-vue frontend --ts --router --eslint --bare
# Following commands ran in frontend/:
npm_config_cache=/tmp/pigpen-npm-cache npm install
npm_config_cache=/tmp/pigpen-npm-cache npm ci --offline --no-audit --no-fund
npm_config_cache=/tmp/pigpen-npm-cache npm audit --json > /tmp/pigpen-npm-audit.json
npm_config_cache=/tmp/pigpen-npm-cache npm run lint
npm_config_cache=/tmp/pigpen-npm-cache npm exec -- oxlint .
npm_config_cache=/tmp/pigpen-npm-cache npm exec -- eslint .
npm run build
npm ls --all --json > /tmp/pigpen-npm-tree.json
node --version
npm --version
command -v node npm git
```

The generated lint command may apply fixes; the final direct lint checks omit --fix. Build includes vue-tsc TypeScript checking. It generated frontend/dist/index.html, favicon.ico and bundled assets. No browser/device runtime, backend test, deployment, HTTPS, PWA or feature checks apply yet. The starter has a generic Vue welcome message, Router registration with an empty routes array, and no backend request code.

npm audit exited 1 and reported 11 moderate findings (zero high/critical), rooted in [minimatch globparts amplification](https://github.com/advisories/GHSA-g3hv-75wg-m249) and propagated through the lint dependency chain. The installed minimatch 10.2.6 is a development dependency. npm suggests changes outside generated dependency ranges, including ESLint 9.39.5 and earlier Vue lint configurations. No forced audit fix or toolchain replacement was performed. TODO: review a compatible lint-toolchain fix before processing untrusted projects; this setup does not claim a clean dependency audit.

Other inspection/verification commands: cat of generated package.json, README, router, App.vue, eslint config, Vite config, main.ts and .gitignore; rg --files --hidden of frontend; ls/tail of task npm logs; du -sh frontend/node_modules; process inspection limited to investigating this task's npm install; ls -la frontend/dist; git config --get user.name and user.email; test -w .git. No unrelated process was stopped.

Ignore verification first used temporary Git metadata at /tmp/pigpen-ignore-review.git to avoid changing the project repository before stage 9:

```sh
git init --bare --quiet /tmp/pigpen-ignore-review.git
git --git-dir=/tmp/pigpen-ignore-review.git --work-tree=/home/pigpen/Documents/pigpen -c core.excludesFile=/dev/null check-ignore --no-index backend/.venv/bin/python backend/__pycache__/example.pyc frontend/node_modules/example/index.js frontend/dist/index.html .env .env.production .idea/workspace.xml sample.sqlite3-wal uploads/example.png
git --git-dir=/tmp/pigpen-ignore-review.git --work-tree=/home/pigpen/Documents/pigpen -c core.excludesFile=/dev/null ls-files --others --exclude-standard
```

All sampled generated/secret paths were ignored; manifests and locks remain visible. Files under output/pigpen-animation-previews appeared concurrently during setup; they were not created, modified, or selected by this task.

## Documentation preservation

Original README SHA-256: d02f40eb50a83aa832389f0ef2ae1bdd35d0959d84a4c9ca09755ed1383ca4a2. Its original bytes remain the prefix of the extended README (verified against a temporary snapshot).

Existing docs remain byte-for-byte unchanged:

- docs/architecture.md: 683ba610322e12988d18bf4a9eb84fa87c07522bd36b6d38d64423ebf1870b04
- docs/functionality.md: be90ce356037a97a00a0893f1e4fd474cd2e28ce362131f14ce8e25b0f5b9fbd

## File scope and Git approval

Created backend/ and frontend/; docs/ already existed. README.md was appended. Existing architecture/functionality docs were preserved. AGENTS.md, .gitignore, backend requirements/lock, docs/setup.md and all listed frontend files are new. Generated ignored directories: backend/.venv/, frontend/node_modules/, frontend/dist/. Generated .eslintcache/TypeScript build metadata may also exist. Temporary npm cache, audit/tree reports, README snapshot and ignore-review repository live under /tmp, outside the deliverable.

Approved commit message: `chore: scaffold PigPen development environments`.

Approved file scope (existing product docs included, output/ excluded):

- `.gitignore`
- `AGENTS.md`
- `README.md`
- `backend/requirements.txt`
- `backend/requirements.lock`
- `docs/architecture.md`
- `docs/functionality.md`
- `docs/setup.md`
- `frontend/.editorconfig`
- `frontend/.gitattributes`
- `frontend/.gitignore`
- `frontend/.oxlintrc.json`
- `frontend/README.md`
- `frontend/env.d.ts`
- `frontend/eslint.config.ts`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/public/favicon.ico`
- `frontend/src/App.vue`
- `frontend/src/main.ts`
- `frontend/src/router/index.ts`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.json`
- `frontend/tsconfig.node.json`
- `frontend/vite.config.ts`

Final Git review commands: `git init` (normal sandbox escalation), `git status --short --branch`, `git rev-parse --show-toplevel`, explicit-path `git add` for the list above, `git diff --cached --check`, `git diff --cached --stat`, and `git diff --cached --name-only`. No generated environments/dependencies/build output/secrets are in this scope. Git identity was present; no identity or remote configuration was changed. The user approved this scope and message under stage 9 of the supplied guide. Commit execution: `git add -- docs/setup.md`, `git diff --cached --check`, `git commit -m "chore: scaffold PigPen development environments"`; verify with `git log -1 --format='%h %s'`, `git status --short --branch`, and `git show --format= --name-only HEAD`. This initial commit records the approved checkpoint; retrieve its identifier with the log command.
