# specs/plans/

Rendered, point-in-time plan artifacts — HTML pages generated from the markdown specs, kept here so
the artifact and its images stay versioned with the repo.

**The markdown specs are authoritative.** Everything in this directory is derived: a snapshot of the
specs at the commit recorded in each artifact's own metadata block. On any conflict, trust the
specs. Do not cite these files as sources, and do not edit them to change the plan — change the
specs and re-render (`/agent-harness:planf3`, Update Plan workflow).

These artifacts are outside the repo's verification machinery: `just link-check` only walks `*.md`,
and nothing in an HTML page is backed by the claims ledger.

| Artifact | Rendered from | Pinned at |
|---|---|---|
| [macos-ci.html](macos-ci.html) (images in `macos-ci/`) | [specs/macos-ci.md](../macos-ci.md) + [specs/macos-ci/*](../macos-ci/00-overview.md) | `f0b434a` |
