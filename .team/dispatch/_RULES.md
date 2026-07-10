# RULES — every agent obeys. Read this in full.

## 0. Read these first, in this order

1. **[`prompts/macos-ci-verify-team.md`](../../prompts/macos-ci-verify-team.md)** — the 835-line master
   brief. Scope, oracles, FSM, rotation, ground truths **G1–G19**, defects **D1–D5**. Read it **in full**.
2. **[`.team/macos-ci.backlog.md`](../macos-ci.backlog.md)** — what the lead already found. Do not
   rediscover it.
3. **[`.team/macos-ci.board.md`](../macos-ci.board.md)** — the pasted baseline.
4. **[`.team/macos-ci.open-questions.md`](../macos-ci.open-questions.md)** — OQ-01…OQ-07 already exist.

## 1. THE BRIEF IS NOT PRIVILEGED OVER THE EVIDENCE

This is the whole point of the run. If a **GROUND TRUTH**, this file, or the master brief contradicts a
passing ledger claim or a read-only command you just ran, **the brief is RETRACTED**. Report it in the
backlog under your role heading. **Do not reconcile it. Do not soften what you observed.**

**Already retracted, do not rediscover, do not re-litigate:**

| | verdict |
|---|---|
| **G10** | RETRACTED. `settings-apple/devices/` was **fabricated**. A `must_fail` control guards it. NEVER restore. |
| **G14** | RETRACTED. `packer` **is** installed (v1.15.4). No `just doctor` recipe exists. |
| **D5** | RETRACTED → **D5′**. Both halves false; its enumeration was short by one (`specs/macos-ci.md:517`). Baseline is **16**, not 17 and not 22. |
| **OQ-03** | ANSWERED. `notify` emits **both** `notification.created` and `notification.requested`. False dichotomy. |
| **OQ-07** | ANSWERED. Bare `cmux rename-tab "<t>"` **fails** — `$CMUX_TAB_ID` holds a *workspace* UUID. Always pass `--surface "$CMUX_SURFACE_ID"`. |

> **The master brief has now been caught with a false line-number claim (D5) and a false CLI claim
> (rename-tab). Treat every line number in it as a hostile witness.** Re-derive them. `12:200-202`,
> `13:51`, `13:54`, `00:58` — check each with `sed -n 'Np'` before you cite it.

## 2. Scope — hard limits

**Writes allowed:** markdown; `.team/proposed/<your-role>.jsonl`; appends to
`.team/macos-ci.open-questions.md`; your **owned files only**.
**Writes forbidden:** `.team/claims.jsonl` and `tools/verify_claims.py` (🔬 **ledger** alone owns these),
the `Justfile` (👑 **lead** alone), and any file owned by another agent.

**No installs. No VM boots. No host mutation.**

**REQUIRED and encouraged (read-only):**
```
<tool> --help   |  <tool> --version  |  packer version  |  packer inspect <dir>
curl -fsSL <doc-index-url>          |  curl -sS -o /dev/null -w '%{http_code}' <url>
grep / rg / sed over the LOCAL clones            just link-check | verify-claims | check | unverified-count
uv run tools/verify_claims.py [--json] [ledger]  git log | git show | git blame
```
**FORBIDDEN even though the binaries exist:** `packer build`, `packer init`, `just build-golden`,
`just verify-no-secrets <vm>`, `cmux hooks setup`.

> **If you CAN check something with an allowed command and you don't, that is a defect, not caution.**

**Local clones — read them, never WebFetch them:**
`/Users/bossjones/dev/bossjones/zsh-dotfiles` · `/Users/bossjones/dev/bossjones/zsh-dotfiles-prep`
Also present: `/Users/bossjones/dev/cirruslabs/macos-image-templates`, `.../packer-plugin-tart`.

## 3. The oracles — query the index BEFORE you type a URL

```bash
# tart.run (MkDocs Material) — entries under .docs[]
curl -fsSL https://tart.run/search/search_index.json

# docs.getutm.app (Just the Docs) — 281 entries / 78 pages. 403s WebFetch; use curl.
curl -fsSL https://docs.getutm.app/assets/js/search-data.json

# developer.hashicorp.com — no search JSON. The sitemap IS the page list, for /packer/docs/** ONLY.
curl -fsSL https://developer.hashicorp.com/server-sitemap.xml | grep -o '<loc>[^<]*packer[^<]*</loc>'
```

An index is authoritative **for the prefixes it covers**. Inside that domain, absence from the index is
proof of fabrication. **Outside it, absence is evidence of nothing — go fetch the URL.**

### ⚠️ THE ONE CARVE-OUT — G19. Read it twice.

`/packer/integrations/**` is **NOT in the HashiCorp sitemap** (0 of 337 `/packer/*` entries) **yet the
Tart builder field reference returns HTTP 200.** HashiCorp renders those pages from
`cirruslabs/packer-plugin-tart`'s own `.web-docs/` directory.

**Refuting one of those URLs by grepping the sitemap is G10 running backwards** — declaring a *real*
page fake, with total confidence. Verify them with
`curl -sS -o /dev/null -w '%{http_code}' <url>` or by reading `.web-docs/`.
**NEVER refute a page you have not fetched.**

## 4. Red-team posture: TRY TO REFUTE, DEFAULT TO REFUTED

For each non-obvious claim, construct the read-only command that would **disprove** it. If you can
neither verify nor disprove it → `<!-- UNVERIFIED -->` **and** an open question. **Do not be charitable.**
The last run was charitable and shipped a fabricated URL. File every refutation in the backlog as a
**CONFLICT**. The only carve-out is §3's G19.

Every non-obvious claim resolves to exactly one of four states — there is no fifth, and *"it sounds
right"* is state (d):
**(a)** a passing ledger entry · **(b)** an explicit `<!-- UNVERIFIED -->` marker citing an OQ number ·
**(c)** an entry in the open-questions file · **(d)** deletion.

## 5. Proposing ledger claims

Write to **`.team/proposed/<your-role>.jsonl`**. Only 🔬 ledger merges. Every record needs `id`, `kind`,
`file`, `claim`, plus its evidence fields.

**Dry-run your own proposals before you hand them over** — `verify_claims.py` takes a ledger path
positionally, so you can test yours in isolation without touching `claims.jsonl`:

```bash
uv run tools/verify_claims.py .team/proposed/<your-role>.jsonl
# exit 0 verified · 2 a claim failed · 3 evidence unreachable · 4 usage
```

**A proposal you have not dry-run is not a proposal, it is a wish.** The lead's four proposals were
dry-run to `4/4` before being filed. Do the same.

Evidence kinds: `file-contains` · `file-line` (kills hallucinated `file:line`) · `absent` ·
`cli-help` (runs `argv` from repo root; optional `env` overlay) · `doc-index` (kills fabricated URLs) ·
`doc-contains` (kills real-URL-invented-sentence). Relative `target` paths resolve against the repo root.

### `cli-help` is UNSOUND for backend questions; `doc-contains` is the antidote
**A flag in `--help` proves the argument parser accepts it. Nothing more.** `utmctl start --help`
advertises `--disposable` on a host that can only run Apple-backend macOS guests, while the docs say
*"Disposable mode is only supported on QEMU backend."* Both are true. Any `cli-help` claim about what a
flag **does** (rather than that it parses) must be **paired** with a `doc-contains` claim, and each
must **name its partner in its `claim` prose**.

### `must_fail` — never weaken it
Six exist: four `CONTROL-*` guard the oracles; two are negative probes. **Never delete, weaken, or
"fix" a control.** A verifier nobody verifies is just a second thing to trust.
**Every negative `must_fail` probe over a `cli-help` command MUST ship a positive control running the
same `argv`+`env` and asserting a non-sensitive literal IS present** — *"no secret in the output"* is
equally satisfied by **no output at all**. A pair whose control is vacuous is a green check that means
nothing.

Two failure prefixes are **never** inverted by `must_fail`, because neither is evidence about the claim:
`UNREACHABLE:` (network down, binary missing) and `STRUCTURE:` (a `doc-contains` page absent from the index).

## 6. Open questions — THE HUMAN READS THIS FILE

`.team/macos-ci.open-questions.md` is **append-only**. **Never edit or delete another agent's block.**
To answer one, append a `**Resolution:**` line *inside* its block and flip `**Status:**`.

**OQ-01 … OQ-07 already exist. Take OQ-08 next.** If you race, renumber yours upward.

**Open an OQ the MOMENT you are stuck — not at the end.** An entry costs nothing; guessing costs a
fabricated URL. **If you catch yourself typing *"presumably" / "it appears" / "likely" / "should be"* —
that is an OQ, not a sentence.** An open question is a **success**: it is the run correctly refusing to
invent an answer. An empty open-questions file after 8 agents audit 14 specs is a **red flag**, not a triumph.

Format — one `##` block, appended:
```
## OQ-<NN> · <role> · <question ending in a question mark>
**Status:** OPEN | ANSWERED | BLOCKED-BY-SCOPE | NEEDS-HUMAN
**Spec:** specs/macos-ci/NN-xxx.md:LINE
**What I tried:** the exact read-only commands, and what they returned.
**Why it is stuck:** what would settle it, and why you cannot run that.
**My best guess, explicitly labelled a guess:** …
**Cost of guessing wrong:** what breaks downstream if the guess is inverted.
```
`NEEDS-HUMAN` = only the human can decide. `BLOCKED-BY-SCOPE` = a booted VM would settle it.
Every `<!-- UNVERIFIED -->` marker you **add** must cite an OQ number in its comment text.
Never delete an `<!-- UNVERIFIED -->` marker without adding a **passing** ledger claim.

## 7. The honesty budget

`just unverified-count` → **16** marker lines today. It must fall only because claims got **verified**,
never because markers got **deleted**. The lead diffs it against the baseline and **will reject a silent
drop as a CONFLICT**.

## 8. Status, notifications, sentinel

**Rename your own tab — the `--surface` flag is MANDATORY (OQ-07; the bare form errors):**
```bash
cmux rename-tab --surface "$CMUX_SURFACE_ID" "<emoji> <role> <n>/<N> [####------] · <one-line log>"
```
emoji: 🔵 working · 🟢 done · 🔴 error · 🟡 refuted-a-claim · ❓ blocked-on-an-open-question

**Fire a notify on every FSM transition AND the first time you open an OQ:**
```bash
cmux notify --title "<role>" --body "<state>: <one-line>"
```

**End your final turn with exactly this line, and nothing after it:**
```
TASK-DONE: <role> | <one-line summary> | claims+N refuted-M unverified-K open-questions-J
```
The sentinel is the **authoritative** completion signal. The notification event is only a free early
exit: its payload is **redacted** (`title`/`body` come back `null`), so it tells the lead *who*
finished, never *what* you said. A notification also fires on a turn where you **refused** to do the
work. **Print the sentinel.**

## 9. Environment hazards

- The `pre_tool_use` hook **blocks the substrings** `rm ` (with trailing space), `--rm`, and the literal
  dot-env token. Use `mv` into a scratchpad instead of deleting.
- Lint Python with `uvx ruff check <file>` (`ruff`/`ty` are not on `PATH`).
- `zsh` does **not** word-split unquoted vars — inline lists or use `${=var}`.
- Bash is auto-rewritten through `rtk`.
- **`just check` is the only definition of done. Paste its output; never describe it.**

## 10. Prefer a shorter document that is entirely true

…over a longer one padded with plausible detail. Deleting an unverifiable sentence is a **win**, not a loss.
