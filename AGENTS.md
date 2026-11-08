# PigPen project rules

- Work only inside this project; read AGENTS.md, README.md, and relevant docs before changes.
- Preserve existing documentation. Confirmed requirements and proposed defaults are distinct; do not silently promote proposals into requirements.
- Ask targeted follow-up questions when missing information would materially change the work; otherwise record explicit TODOs.
- Keep framework-free Python domain logic separate from FastAPI routes.
- Keep Vue presentation separate from backend-request code. Use TypeScript and Vue Router.
- Communicate between Vue and FastAPI through a documented JSON contract. Document the contract before connecting clients; no API contract is implemented in this scaffold.
- Backend and frontend environments belong to this project. Never install project Python or JavaScript dependencies globally.
- Explain why before adding, removing, or upgrading dependencies; retain manifests and reproducible lockfiles.
- Ask before machine-level installation, destructive actions, or scope expansion. Never use sudo automatically or bypass managed-computer policies.
- Stop only processes started for the current task.
- Do not implement PigPen features during initial setup. Database tooling, PWA tooling, authentication, notifications, synchronization, OCR, and AI dependencies require later justification.
- Ask for approval before creating the initial scaffold commit. Do not configure remotes, push, rewrite history, or switch branches without explicit instruction.
- Report commands run, files changed, checks performed, and anything not verified.
- Deploy verified application changes to the existing PigPen installation after changes; retain the previous release for rollback and verify the live result. This standing authorization does not cover unrelated machine configuration, dependency installation, or destructive actions.
