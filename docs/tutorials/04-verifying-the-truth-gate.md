# 4. Verifying the Truth Gate

## What you'll learn

This repo has **two entirely different verification systems** that happen to use overlapping words —
"verify," "check," "test." This tutorial covers the one that has nothing to do with VMs at all: a
system for keeping this repo's own *design specs* honest, by pairing every load-bearing claim in them
with evidence a machine can re-run. By the end you'll be able to run it, read its exit codes, and know
exactly which of the three similarly-named commands (`just check`, `just verify`, `just test`) does
what.

## Prerequisites

- [Tutorial 1](01-getting-started.md) completed (or at least skimmed) — no VM needs to be running for
  anything in this tutorial.

## The problem this solves

The `specs/` directory in this repo is a set of markdown design documents (numbered `00`–`13`) recording
*why* this repo is built the way it is — see
[specs/macos-ci/00-overview.md](../../specs/macos-ci/00-overview.md) for the full reading order. Design
docs like this rot: a sentence that was true when written can silently become false later — a doc page
gets restructured, a CLI flag gets renamed, a file moves. Nothing about markdown prose stops that from
happening invisibly.

This repo's answer is a **claims ledger**: `.team/claims.jsonl`. Every load-bearing assertion in
`specs/` gets one line in that file, pairing the claim with a concrete, re-executable piece of evidence.
A tool re-runs every one of those pieces of evidence and reports which claims still hold.

## The claims ledger: `.team/claims.jsonl`

Each line is one JSON claim. Here's a real one, straight from the file:

```json
{"id": "G11-version-manager-outside-interactive", "kind": "file-contains", "file": "specs/macos-ci/09-dotfiles-under-test.md", "target": "/Users/bossjones/dev/bossjones/zsh-dotfiles/home/.chezmoi.yaml.tmpl", "expect": "promptString \"version_manager\"", "claim": "version_manager is reachable non-TTY via promptString"}
```

Read as prose: *the spec file `09-dotfiles-under-test.md` asserts that `version_manager` is reachable
non-interactively via `promptString` — and the evidence for that is that the string
`promptString "version_manager"` literally appears in `zsh-dotfiles`'s `.chezmoi.yaml.tmpl` file.*

Every claim has a `kind`, which determines what evidence gets re-run. The kinds used in this repo (see
`tools/verify_claims.py`'s own module docstring for the authoritative, more detailed description of
each):

| Kind | What it proves | Example use |
|---|---|---|
| `file-contains` | A file (in this repo or another local checkout) contains a given substring. | "this spec's claim about a template's behavior is backed by the template's actual text" |
| `file-line` | A *specific line number* of a file contains a given substring. | Catches a hallucinated `file:line` citation — a plausible-looking but wrong pointer. |
| `absent` | A file does **not** contain a given substring — a negative claim. | "this repo has no macOS asdf installer" |
| `cli-help` | Running a command's `--help` (or similar read-only invocation) emits a given substring. | "`cirrus run` exposes `--artifacts-dir`" |
| `doc-index` | A given page path appears in a doc site's own search index. | Proves a page *exists* — the search index is the authoritative page list. |
| `doc-contains` | A given doc page's indexed text contains a given sentence. | Proves a page *says* something, not just that it exists. |

### Why `cli-help` alone isn't enough, and `doc-contains` is the antidote

A `--help` flag proves an argument parser *accepts* a flag — nothing about whether it actually works.
The canonical example in this repo: `utmctl start --help` happily lists `--disposable`, but UTM's own
docs state disposable mode is QEMU-backend-only, and this repo's guests are Apple-backend. So every
`cli-help` claim in the ledger that could be misread this way is paired with a `doc-contains` claim
that settles the real, backend-specific question — and the claim's own prose names which `cli-help`
claim it's refuting.

### `must_fail`: claims that guard the checker itself

Some claims are deliberately expected to **fail** — they exist to prove the checker's own oracle still
works. For example:

```json
{"id": "CONTROL-utm-settings-apple-devices-is-fabricated", "kind": "doc-index", "must_fail": true, ..., "expect": "/settings-apple/devices/", "claim": "CONTROL: the first research run cited this URL as a real-but-dead page (G10). It never existed. ... if it does [verify], the doc-index oracle has broken and every doc-index claim is worthless."}
```

If a `must_fail` claim ever starts *passing*, that's not good news — it means the oracle checking it
has broken, and every other claim of that kind is now unreliable. A verifier nobody verifies is just a
second thing to trust.

`must_fail` also does double duty as the only way to express a **negative assertion** over a `cli-help`
probe (since `absent` only works against a file). And per the ledger's own rule: every negative claim
must be paired with a **positive control** proving the same probe *would* have shown a positive result
if there had been one — otherwise "the secret didn't appear" is equally well explained by "nothing
appeared at all." You'll find `packer-sensitive-masks-value` and its paired control
`CONTROL-packer-inspect-prints-plain-literals` right next to each other in the ledger for exactly this
reason.

## Running it

```bash
just verify-claims
```

runs `uv run tools/verify_claims.py`, re-executing the evidence behind every claim in
`.team/claims.jsonl` and printing a pass/fail per claim.

For machine consumption (an agent, a script) instead of prose:

```bash
just verify-claims-json
```

runs the same tool with `--json`.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Every claim verified. |
| `2` | At least one claim failed. |
| `3` | Evidence was unreachable — network down, a binary missing, a target file absent. This is distinct from a claim being *false*; it's "we couldn't even check." |
| `4` | Usage error. |

Two failure prefixes you may see in output are never inverted by `must_fail`, because neither is
evidence *about* the claim itself:

- `UNREACHABLE:` — network down, binary missing, or the target file doesn't exist.
- `STRUCTURE:` — a `doc-contains` claim's page isn't even in the search index. This distinguishes "the
  page vanished" from "the sentence on the page vanished," so an upstream page rename doesn't get
  misread as a fabricated sentence.

## `<!-- UNVERIFIED -->` markers and the honesty budget

Not every sentence in `specs/` can be reduced to a machine-checkable claim — some are reasonable
inference rather than something quotable from a source. Those get an explicit
`<!-- UNVERIFIED -->` marker inline, so nobody mistakes inference for fact.

```bash
just unverified-count
```

counts these markers across every spec file. Read it as an **honesty budget**: the count should fall
over time only because a marked claim got promoted into the ledger with real evidence — never because
someone quietly deleted the marker without doing that work.

## `just check` — the full truth gate

```bash
just check
```

runs, in sequence: `link-check` (every markdown link resolves — see
[CLAUDE.md](../../CLAUDE.md#link-hygiene) for the lychee-based tooling behind this) → `verify-claims` →
`unverified-count`. This is, by this repo's own convention, **the only definition of "this spec is
trustworthy."** If you're contributing a spec change, this is the command to run before you consider it
done.

## Disambiguation: three different things named "verify" / "test" / "check"

This is genuinely confusing on first read, so here it is as a table:

| Command | What it checks | Needs a VM? |
|---|---|---|
| `just check` | This repo's own **specs** are internally honest — links resolve, every claim's evidence still holds, unverified markers are tracked. | No. |
| `just verify` | `pytest -m vm` — testinfra assertions run from the host, over SSH, against a **live Tart VM**, asserting the dotfiles install actually worked in the guest. | Yes — a VM `up` already started. |
| `just test` | `uv run pytest` — the hermetic unit-test tier (no marker), fakes `tart`/`ssh` via `pytest-subprocess`. What you run while developing this repo's own Python code, with no VM at all. | No. |

If someone says "run verify" in this repo, ask (or check context) which of these two entirely different
things they mean — one checks markdown prose against reality, the other checks a running virtual
machine against an installed dotfiles config.

## Checkpoint

You should now be able to:

- Explain what `.team/claims.jsonl` is for and name at least three evidence `kind`s.
- Explain why a `must_fail` claim passing is bad news, not good news.
- Run `just check` and read its three constituent steps.
- Tell `just check`, `just verify`, and `just test` apart without hesitating.

## Next steps

- [Tutorial 5 — Debugging a Failed Run](05-debugging-a-failed-run.md): what to do when the *VM-side*
  verification fails, as opposed to the spec-side truth gate covered here.
- `tools/verify_claims.py`'s own module docstring is the most complete reference for every evidence
  kind — read it directly if this tutorial's summary leaves a question unanswered.
- [specs/macos-ci/11-sources.md](../../specs/macos-ci/11-sources.md) for the retraction log this whole
  system was built in response to.
