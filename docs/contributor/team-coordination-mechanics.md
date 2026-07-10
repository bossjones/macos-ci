# Team Coordination Mechanics — the `.team/` scaffold

This is a reference for the concrete coordination files this repo uses **today** if you run or extend a
boss-cmux team against it. It documents current, live tooling — not a history of past runs. For the
general pattern this scaffold implements (why a dispatch brief, a board, and a ledger exist at all), see
[`boss-cmux-workflow.md`](boss-cmux-workflow.md). For the full verification philosophy behind the ledger
(evidence kinds, the `must_fail` self-check pattern), see this repo's own
[`../../CLAUDE.md`](../../CLAUDE.md) section **"The claims ledger"** — it's covered there in depth and
this document links to it rather than re-explaining it.

> **Scope note:** `.team/` also holds files for unrelated side-projects that happen to share this repo's
> `.team/` folder — `.team/docs-fleet/*` and `.team/centralized_k0s.board.md`. Those are out of scope
> here; this document only covers the macos-ci coordination files.

## Dispatch briefs — what a dispatched agent reads first

[`.team/dispatch/_RULES.md`](../../.team/dispatch/_RULES.md) is the rulebook every dispatched agent
reads in full before anything role-specific. Its key mechanics:

- **A fixed read order**: the master orchestration brief, then the backlog ("what the lead already
  found — do not rediscover it"), then the board (the pasted baseline), then the open-questions file.
- **The brief is not privileged over the evidence.** If a documented "ground truth," the rules file
  itself, or a read-only command you just ran disagree, the brief is retracted on the spot — you report
  the contradiction, you don't reconcile it or soften what you observed.
- **A hard-scoped write allowlist.** Agents may write markdown, their own
  `.team/proposed/<role>.jsonl`, and appends to the open-questions file. `.team/claims.jsonl` and the
  verifier script are owned by exactly one role; the Justfile by exactly one other. No installs, no VM
  boots, no host mutation for read-only roles.
- **Query the doc site's own search index before typing a URL** — the same anti-fabrication technique
  documented in this repo's `CLAUDE.md` under "Verifying a claim against the upstream docs."
- **Red-team posture:** for each non-obvious claim, try to construct the command that would *disprove*
  it. Every claim resolves to one of four states — passing evidence, an explicit unverified marker tied
  to an open question, an open-questions entry, or deletion.
- **Proposing ledger claims**: write to `.team/proposed/<role>.jsonl`, never directly to
  `.team/claims.jsonl` — only one role merges. Dry-run your own proposals first with
  `uv run tools/verify_claims.py .team/proposed/<role>.jsonl` before handing them over; an
  un-dry-run proposal is "a wish," not a proposal.
- **An honesty budget**: a running count of `<!-- UNVERIFIED -->` markers that must only fall because a
  claim got verified — never because a marker got quietly deleted.
- **A fixed status/notification/sentinel protocol**: rename your own tab to
  `<emoji> <role> <n>/<N> [progress-bar] · <one-line log>`, fire a `cmux notify` on every state
  transition, and end your final turn with an exact sentinel line the lead can grep for
  (`TASK-DONE: <role> | <summary> | <counts>`), since the notification event's payload is redacted and
  the sentinel is the only authoritative completion signal.

### Per-role dispatch briefs

[`.team/dispatch/`](../../.team/dispatch/) also holds one brief per role — `harness.md`, `tart-core.md`,
`tart-ci.md`, `utm.md`, `secrets.md`, `ledger.md`. Each follows the same shape:

- Which surface (pane) the role runs on and which spec files it **owns**.
- The specific claims, ground truths, or defects it's responsible for re-verifying, often naming exact
  files and giving a *reason to distrust the line numbers already in the brief* (this repo's briefs
  explicitly warn that a prior pass hallucinated a `file:line` citation past the end of the actual
  file — re-derive every citation with `grep -n` / `sed -n 'Np'` rather than trust it).
  For example, `harness.md` owns `specs/macos-ci/08-dotfiles-test-harness.md`,
  `09-dotfiles-under-test.md`, and `12-tooling-and-agent-loop.md`, and is assigned two specific defects
  (`D2`, `D4`) to independently confirm rather than inherit.
- A **cross-audit** assignment: after finishing its own files, each role audits another role's files
  read-only, filing any disagreement as a `CONFLICT` in the backlog under its own role heading rather
  than editing the other role's spec directly.
- Its own `.team/proposed/<role>.jsonl` target and the same dry-run-before-filing instruction.
- The same exact sentinel format, parameterized by role name.

If you're extending this scaffold with a new role, a new file under `.team/dispatch/` following this
shape — owned files, specific claims to re-derive (not inherit), a cross-audit target, a proposed-claims
file, a sentinel line — is the expected unit of work.

## The board — durable run state

Two board files exist for two different runs:

- [`.team/macos-ci.board.md`](../../.team/macos-ci.board.md) — the **verify** run's board.
- [`.team/macos-ci-build.board.md`](../../.team/macos-ci-build.board.md) — the **build** run's board.

Either one opens with the same instruction: *"Durable state. Any restarted/confused agent: read this
file and resume from the recorded state."* The build board documents its FSM explicitly:

```
SCAFFOLD → PRE-IMAGE → BUILD-LAUNCH → SHADOW-WORK → IMAGE-READY → SMOKE → INTEGRATE → MATRIX → GATE →
  {CLEAN→DONE | DIRTY→FIX→GATE | ERROR→NEEDS-HUMAN}
```

At the time of writing, the recorded state is `DONE` — all 14 spec steps landed, gate clean (`just
check` 311/311, `uv run pytest` 76 passed / 17 deselected), golden image built, no orphaned VMs.

The board is updated by commits, and always with pasted command output rather than a paraphrase of it —
this repo's own commit history shows the pattern directly:

```
efb7bc2 chore(board): DONE -- full a-h report at the top of the board
4866015 chore(board): GATE-clean -- just check 311/311 + uv run pytest 76/17 both exit 0
8f3e0cc chore(board): mark IMAGE-READY -- golden-image build succeeded (2h24s)
```

The verify run's board follows the same evidence-first convention even though its FSM is simpler (it
converges on a single `DONE` state): its gate section is a literal pasted transcript of
`just verify-claims ; echo "EXIT=$?"` and `just check ; echo "EXIT=$?"`, with the full unedited capture
linked (`.team/gate-final-full.txt`) and any elision of the capture explicitly declared (e.g. "lines
1–278 are `link-check` output, exactly 277 `[200]` lines, zero non-200").

## The claims ledger — `.team/claims.jsonl`

[`.team/claims.jsonl`](../../.team/claims.jsonl) is the machine-checkable ledger:
[`tools/verify_claims.py`](../../tools/verify_claims.py) re-executes the evidence behind every record. As
of this writing the ledger holds **311 claim records** (plus header comment lines), of which **36** are
`must_fail` controls. Each record is one JSON object per line; representative shapes actually in the
file:

```json
{"id": "G11-stdinIsATTY-line-2", "kind": "file-line", "file": "specs/macos-ci/09-dotfiles-under-test.md", "target": "/Users/.../zsh-dotfiles/home/.chezmoi.yaml.tmpl", "line": 2, "expect": "stdinIsATTY", "claim": ".chezmoi.yaml.tmpl:2 defines $interactive := stdinIsATTY"}
```

```json
{"id": "CONTROL-utm-settings-apple-devices-is-fabricated", "kind": "doc-index", "must_fail": true, "file": "specs/macos-ci/11-sources.md", "site": "utm", "expect": "/settings-apple/devices/", "claim": "CONTROL: the first research run cited this URL as a real-but-dead page (G10). It never existed. Its evidence must NOT verify; if it does, the doc-index oracle has broken and every doc-index claim is worthless.", "polarity": "negative"}
```

Common fields: `id` (unique, human-legible), `kind` (the evidence type), `file` (the spec the claim
backs), `target`/`line` (for file-scoped evidence), `expect` (the literal or substring evidence must
produce), `claim` (the prose assertion), and optionally `must_fail`/`polarity` for negative/control
claims, or `site`/`page` for doc-site claims. `verify_claims.py` currently implements eight evidence
kinds — `file-contains`, `file-line`, `absent`, `cli-help`, `doc-index`, `doc-contains`, `http-status`,
and `http-contains` — of which `CLAUDE.md` documents the first six in depth (`http-status`/`http-contains`
were added to reach pages outside the two doc-site search indexes, such as `/packer/integrations/**`
pages and pinned GitHub blob URLs). See `CLAUDE.md`'s "The claims ledger" section for the full
philosophy: why `cli-help` is unsound for backend questions and needs a `doc-contains` partner, why every
negative `must_fail` probe needs a positive control proving it isn't vacuous, and why `UNREACHABLE:` and
`STRUCTURE:` failure prefixes are never inverted.

Run it yourself:

```bash
uv run tools/verify_claims.py            # or: just verify-claims
uv run tools/verify_claims.py --json     # machine-readable, for an agent to read
just check                               # link-check + verify-claims + unverified-count — the truth gate
```

## `.team/proposed/*.jsonl` — draft claims per role

[`.team/proposed/`](../../.team/proposed/) holds one JSONL file per role that has proposed claims —
currently `harness.jsonl`, `lead.jsonl`, `ledger.jsonl`, `secrets.jsonl`, `synth.jsonl`, `tart-ci.jsonl`,
`tart-core.jsonl`, and `utm.jsonl`. These are drafts: a role appends claims here (never directly to
`claims.jsonl`) and dry-runs them in isolation, since `verify_claims.py` takes a ledger path
positionally:

```bash
uv run tools/verify_claims.py .team/proposed/<role>.jsonl
```

Only the ledger role reads across all of `.team/proposed/*.jsonl`, dedupes by `id`, rejects malformed or
non-reproducing records (routing a rejection back to its owning role as a backlog `CONFLICT`, not
silencing it), and merges the survivors into `.team/claims.jsonl` — while keeping the two ledger
invariants intact: no `must_fail` claim is ever deleted or weakened, and every negative `must_fail` probe
ships with a positive control proving it isn't vacuously satisfied by *no output at all*.

## Backlog and open questions

[`.team/macos-ci-build.backlog.md`](../../.team/macos-ci-build.backlog.md) is the task-detail file
alongside the board: it names each role's owned files, binding rules (red-first testing, lint/format
gates, the exact sentinel format), and a `CONFLICTS` section where any role can append a disagreement
under its own role heading rather than editing another role's files directly (see the older
[`.team/macos-ci.backlog.md`](../../.team/macos-ci.backlog.md) for worked `CONFLICT L1`…`L6` examples —
only the lead edits this file's overall structure; agents append below their own heading).

[`.team/macos-ci-build.open-questions.md`](../../.team/macos-ci-build.open-questions.md) is strictly
append-only — never rewrite another agent's block. Each entry is an `## OQ-NN · <role> · <question>`
block recording status (`OPEN` / `ANSWERED` / `FLAGGED` / `NEEDS-HUMAN` / `BLOCKED-BY-SCOPE`), the spec
line it concerns, what was tried, why it's stuck, and — labeled explicitly as a guess, never as fact —
a best guess plus the cost of that guess being wrong. Filing one of these the moment you're stuck (rather
than at the end of a run) is treated as a success, not a failure: it's the run correctly refusing to
invent an answer instead of quietly presenting inference as fact.

## Summary — the loop this scaffold implements

Read the dispatch brief (rules, then role) → do read-only or owned-file work → propose claims to your
own `.team/proposed/<role>.jsonl` and dry-run them → file backlog `CONFLICT`s and open-questions `OQ-NN`
entries the moment you're stuck, never at the end → let the board (not your own narration) record run
state, always via pasted command output → converge on the ledger role merging the survivors and `just
check` exiting 0 as the only definition of done.
