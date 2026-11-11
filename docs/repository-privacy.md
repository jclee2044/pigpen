# Public repository privacy

The public repository contains application source, synthetic tests, design artwork,
and documentation. Production databases, uploaded receipts, secrets, and backups
belong outside this checkout.

`output/` is private local verification scratch and is ignored. It can contain
screenshots of real budgets, household names, receipt photographs, browser traces,
and diagnostic responses. Never force-add it. Use synthetic data for anything
intended for publication. Historical verification links into `output/` are retained
as records of local checks; those artifacts are intentionally absent from Git.

Deployment files use `/home/pigpen` and `pigpen.example.com` as illustrative
placeholders. Adapt them privately to the installation; do not commit local paths,
private hostnames, credentials, or household financial records.

The publication cleanup removed output artifacts from every retained branch and
anonymized identifying text and commit author/committer metadata. Commit IDs changed.
Old clones and copies must not be merged or pushed back into this history. Git's
ignore rules prevent ordinary additions, but cannot identify personal information
inside new screenshots, documents, or source files; review staged changes before
publishing.
