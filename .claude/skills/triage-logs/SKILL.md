---
name: triage-logs
description: Use when a macos-ci harness run failed, hung, or is behaving oddly and the user wants to know WHY by investigating the tart VM's logs. Trigger on any ask to figure out what broke after `just run` / `just up` / `just apply`, why the VM never came up, why `chezmoi diff`/apply failed, or why the golden image looks unhealthy — and especially any request to sweep multiple macOS log sources at once or run a parallel investigation across sources. Handles casual, vague, or misspelled phrasings ("the vm never booted", "why did chezmoi blow up", "check the logs", "dig into the failed run"). It fans out cheap haiku log-researcher subagents to investigate every suspect log source in parallel and returns one distilled root cause plus a minimal fix, instead of dumping raw logs into the conversation. Prefer this over the single-shot `/vm-debug` command when several sources are suspect; for interpreting a *single* log line or judging "is this signal or noise", use the `triage-patterns` reference skill instead.
capabilities: ["parallel-log-triage", "root-cause-synthesis", "remediation"]
---

# triage-logs — parallel macOS log triage

Diagnose a misbehaving tart VM / harness run fast by fanning out **haiku** researcher subagents
(one per suspect log source) that read the logs in parallel, and keeping the verbose output *in
their contexts* — only distilled, cited findings return to you. You (the main agent, opus) verify
those citations, name the root cause, and drive the fix.

Follow the **systematic-debugging** discipline throughout: gather evidence → name the root cause
→ propose the *minimal* fix → verify. Never guess a fix before you have the smoking-gun line.

`$ARGUMENTS` is `[run-id]` — the run-id (or VM name) to investigate; omit to use `artifacts/latest`.

## Why this shape (subagent discipline — standing rules)

Subagents start with **zero** context from this conversation and can't coordinate mid-task, so a
few rules are load-bearing, not optional:

- **Partition up front, delegate explicitly.** Each researcher gets ONE log source and a
  self-contained prompt naming the exact run-id and source. Don't say "check the logs" — say
  "run `dotfiles-test-20260710-1a2b`, source `chezmoi-diff`."
- **Summaries, never dumps.** The whole point is to keep raw logs out of your context. The
  `log-researcher` agent already enforces a distilled output contract — respect it; don't ask it
  to paste full logs back.
- **Verify before you fix.** The findings are the *only* evidence you see, and a haiku summarizer
  can misread. Before proposing any fix, re-check that the cited lines actually support the
  diagnosis (Phase 3). This is where a subtle misread would otherwise propagate into a wrong fix.
- **Reuse the tested engine.** Both you and the researchers reach the VM only through
  `uv run macos-ci vm-debug` — never hand-rolled `ssh`. It shells out to `ssh`/`tart` (never opens
  a Python socket — dodges the macOS "Local Network" errno-65 block), handles retries/backoff and
  signature matching, and (being `uv run`) is allowlisted, so parallel researchers don't each
  trigger a permission prompt.

## Phase 0 — Preflight

Prefer `artifacts/<run-id>/verdict.json` (or `artifacts/latest/verdict.json`) if it already exists
— it names the failing `phase` and cites `evidence` without a fresh sweep. If there's no verdict
yet, or the VM is still live and you want a fresher read, proceed to Phase 1.

If the run-id can't be resolved and no `tart list` entry matches, stop and tell the user — offer
`just up`. Nothing to triage on a VM that was never launched.

## Phase 1 — Triage map (main, background)

Run the sweeper once across **all** sources to see the lay of the land. Run it **in the
background** (Bash tool with `run_in_background: true`) so its retry loop doesn't block you;
you'll be re-invoked when it finishes.

```bash
uv run macos-ci vm-debug --json
```

It prints a human report to **stderr** and a JSON summary to **stdout**. Per source the JSON has
`source`, `vm`, `ip`, `reachable`, `signature_hits` (`{source, line}` list), and `healthy`. Exit
codes: **0** healthy · **2** issues · **3** unreachable · **4** usage/not-up.

Read the JSON and build the suspect list: **which sources are not `healthy`, and which lines
carry `signature_hits`.**

- If exit is **0** (every source healthy): report that the run is clean and **stop — do not fan
  out**. Spawning researchers against a healthy run just burns tokens.
- If **3** (unreachable): the VM may still be booting — say so and offer to re-run.

## Phase 2 — Fan out haiku researchers (parallel)

For each unhealthy source, dispatch a **`log-researcher`** subagent. Send them **in a single
message** (multiple Agent tool calls) so they run concurrently. One source per subagent.

Give each a self-contained prompt, e.g.:

> Investigate source **`chezmoi-diff`** for run **`dotfiles-test-20260710-1a2b`**. Run
> `uv run macos-ci vm-debug --source chezmoi-diff --json` from the repo root. Apply the
> triage-patterns. Return only your distilled output contract — cited lines with timestamps + a
> 2–3 sentence hypothesis. Do not paste raw logs.

The researcher returns a compact block (source, reachability, a handful of cited lines with
timestamps, and a hypothesis). That block — not the raw log — is what enters your context.

## Phase 3 — Verify + synthesize (main, opus)

Before proposing anything: **re-read the exact lines each researcher cited and confirm they
actually support the stated cause.** If a citation is thin or the hypothesis over-reaches, pull
the specific source's log yourself (`uv run macos-ci vm-debug --source <name> --json`, or
`just ssh` then read the file directly) rather than trusting the summary.

Then state the root cause in **plain terms** (not just the log line), citing the exact evidence.
Correlate across sources where relevant (e.g. a `tart-ip` failure explaining why `chezmoi-diff`
never ran at all). Lean on the `triage-patterns` skill and the seed signature table in
`.claude/commands/vm-debug.md` for the known causes (CLT GUI prompt, Rosetta/Homebrew path
mismatch, locked login keychain, chezmoi template errors, asdf-before-mise). If nothing is
conclusive, say so rather than inventing a cause.

## Phase 4 — Remediate (plan mode, opus)

Author fixes as the opus main agent, and **enter plan mode / use AskUserQuestion before changing
anything** — the research is done cheaply on haiku, but the fix is where judgment matters. Confirm
scope:

- **Report only** — stop here; the user drives the fix.
- **Apply a safe live fix now** — patch the guest over SSH (no `-t`) or re-run `just apply`
  against the already-live clone. Then re-verify.
- **Fix and fold back into the source, then recreate** — port the fix into the golden-image
  provisioner (`packer/**`) or the dotfiles under test, then `just recreate` (the golden image is
  never mutated in place; a fresh `tart clone` picks up the fix).

Only act after the user chooses. After any fix, **verify by re-running Phase 1** and confirming
the sweep exits **0** (or that the specific signature is gone) — evidence before claiming it's
fixed.

## Relationship to `/vm-debug`

`/vm-debug` is the quick single-shot sweep (one process, output lands in your context).
`triage-logs` is its parallel sibling: use it when several log sources are suspect and you want
the digging isolated in subagent contexts. Both share the same engine (`macos-ci vm-debug`) and
the same remediation menu, so findings translate 1:1.
