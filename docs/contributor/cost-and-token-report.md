# macos-ci-build — Cost & Token Report

**Run:** 7-pane cmux BUILD team implementing `specs/macos-ci.md` steps 1–14, TDD red-first, including the
real golden-image Packer build.
**Date:** 2026-07-10 · **Wall-clock:** ~3h50m (13:59 → 17:53 local) · **Outcome:** DONE, GATE green
(`just check` 311/311 + `uv run pytest` 76 passed).

> ⚠️ **The dollar figures are API-equivalent (pay-as-you-go) estimates, not an invoice.** All seven agents
> ran under the existing Claude Code login/subscription, so the actual out-of-pocket cost is most likely
> **$0 (included in the plan)** or governed by usage limits — not the numbers below. Use these for *tuning
> the workflow*, which is what they're good for.

---

## Headline

| Metric | Value |
|---|---:|
| **Total tokens (all types)** | **1,159,112,870** (~1.16 B) |
| &nbsp;&nbsp;— cache-read | 1,137,911,708 (**98.2%**) |
| &nbsp;&nbsp;— cache-write | 17,996,329 (1.6%) |
| &nbsp;&nbsp;— output | 2,470,997 (0.2%) |
| &nbsp;&nbsp;— uncached input | 733,836 (0.06%) |
| **API-equiv cost @ standard rates** | **$490.18** |
| API-equiv cost @ Sonnet intro rates ($2/$10, thru 2026-08-31) | $361.84 |

The single most important fact for tuning: **98.2% of all tokens are cache reads.** Long agentic sessions
re-read their entire cached context on every turn; the token *volume* is dominated by that re-read, and so
is the cost — even though cache reads are the cheapest token class ($0.30–$0.50/MTok).

---

## Per-agent breakdown

Standard rates — Opus 4.8 `$5 / $25 / $6.25cw / $0.50cr`; Sonnet 5 `$3 / $15 / $3.75cw / $0.30cr` per MTok
(cache-write = 1.25× input, cache-read = 0.1× input; 5-min TTL).

| Agent | Model | Turns¹ | Uncached in | Output | Cache read | Cache write | Cost |
|---|---|---:|---:|---:|---:|---:|---:|
| 🛠 **harness-builder** | Sonnet 5 | 1,349 | 158,952 | 731,203 | **713,593,434** | 7,805,877 | **$254.79** |
| 👑 **ORCHESTRATOR** (me) | **Opus 4.8** | 549 | 145,111 | 765,723 | 142,786,692 | 2,221,448 | **$105.15** |
| 👑 lead | Sonnet 5 | 491 | 169,295 | 374,981 | 131,957,832 | 1,523,033 | $51.43 |
| ✅ validator | Sonnet 5 | 299 | 75,231 | 239,466 | 58,052,936 | 2,408,090 | $30.26 |
| 🐍 core-builder | Sonnet 5 | 302 | 98,547 | 176,482 | 51,397,492 | 3,029,152 | $29.72 |
| 📦 packer-builder | Sonnet 5 | 216 | 61,350 | 165,894 | 38,902,819 | 881,372 | $17.65 |
| 📡 log-watcher | Sonnet 5 | 18 | 25,350 | 17,248 | 1,220,503 | 127,357 | $1.18 |
| | | | | | | **TOTAL** | **$490.18** |

¹ assistant turns carrying a usage record. The 🏗 build pane is a plain shell (no agent, no tokens).

**Two agents are 73% of the cost:**
- **harness-builder ($255, 52%)** — 713 M cache reads over 1,349 turns. It drove every live run (clone →
  apply → assert), and each poll re-read a context bloated by large tool outputs (font-install logs,
  `apply.log`, testinfra output). Unbounded context growth × many turns = the run's biggest cost sink.
- **orchestrator ($105, 21%)** — the only **Opus** agent (5× Sonnet input price), running a ~2-min
  heartbeat for ~4 hours. 142 M cache reads at Opus's $0.50/MTok. Most of those polls happened during the
  known-slow 2-hour build, where nothing was actionable.

The three fastest-finishing agents (core, packer, watcher) are the cheapest — cost tracks **session
lifetime × context size**, not usefulness.

---

## Biggest loops / inefficiencies

Ranked by impact. Each is a real, fixable pattern from this run.

1. **The base-image OCI pull dominated wall-clock (~90%).** The golden build was 2h 0m 24s; nearly all of
   it was pulling the immutable ~23.7 GB `ghcr.io/cirruslabs/macos-sequoia-vanilla` disk over a
   blip-throttled network (~1%/min). The team finished *all* hermetic + shadow work in ~25 min and then
   waited. → **Cache the base image once** (`just images-cache` / `tart pull …`); future builds clone
   locally in seconds. Already documented in `CLAUDE.md` and `specs/macos-ci/02`.

2. **Cache-read token explosion (98.2% of tokens, and the cost).** harness-builder's 713 M cache reads
   came from a long-lived session whose context kept growing as it polled live runs with big tool outputs.
   → Stream large tool outputs to files and read summaries; `/compact` or spin fresh sub-sessions for
   repetitive polling loops; don't let one agent both *drive* and *poll* a long job in the same context.

3. **Orchestrator on Opus, polling every 2 min for 4 hours = $105.** Two-thirds of those polls covered the
   known-slow build, which the watcher already tracked. → Run the orchestrator on **Sonnet** (≈5× cheaper
   input) and use **adaptive polling** — 5–10 min cadence during a known-slow phase, tight only during
   active agent work. Estimated saving: **~$80–90**.

4. **Redundant full re-apply during INTEGRATE.** The first live `-m vm` run failed 5/10 (a `KeyError`
   test bug cascading). harness-builder started a *second full ~20-min apply* to re-validate when the
   fixes were assertion-layer. I caught it and redirected to an **assertions-only re-run** (`pytest -m vm`
   against the already-applied VM) — 3m23s instead of 20 min. → For assertion-layer fixes, never re-apply;
   re-run the assertions against the live clone.

5. **Stranded composers (recurring).** The lead and packer repeatedly had un-submitted text sitting in
   their composers (a `send` that missed its `enter`), silently stalling — it cost several probe/flush
   cycles. Compounded by the user typing into panes directly (legitimate, but indistinguishable from a
   strand). → Enforce the `send` → `send-key enter` → `read-screen` confirm discipline on every dispatch;
   treat visible composer text above the `❯` as a stall signal.

6. **Log-watcher didn't auto-arm.** It idled waiting for the lead to hand it the log path, so the build
   ran unwatched for ~5 min until the orchestrator nudged. → The watcher should poll for
   `logs/packer-build-*.log` itself and arm the instant one appears.

7. **Board state-line lag.** The lead kept the board's top state line on `IMAGE-READY → dispatch` for ~1
   hour while work progressed, making status opaque and prompting a manual probe. → Require the state line
   to advance on every FSM transition.

8. **Cirrus parity iteration.** packer-builder spent a ~12-min turn and spawned three short-lived cirrus
   VMs working through `.cirrus.yml` before the parity run stabilized. Fiddly, not fatal. → Get the
   `cirrus run` invocation right against a cached image before the real acceptance pass.

9. **One false-alarm escalation (cheap, but noted).** I escalated a possible scope violation — the lead
   retired 6 ledger claims tagged "human sign-off" that didn't route through me — which turned out to be
   user-authorized directly in-pane. Correct diligence, but a round-trip. → When the human is watching
   cmux, "human-authorized" claims can be legit; confirm, don't accuse.

---

## Learnings to pay forward

**Cost/token tuning (biggest levers first):**
- **Cache the base image** — turns the hour-scale build (and the idle-wait tokens around it) into minutes.
- **Run the orchestrator on Sonnet, not Opus** — it's a coordinator, not a reasoner; ~5× cheaper input,
  and it's the 2nd-most-expensive agent purely because of the model tier.
- **Adaptive polling** — the anti-silence heartbeat is right, but 2-min Opus polls through a 2-hour build
  is the wrong cadence. Widen to 5–10 min when a watcher already covers the long pole; go tight only
  during active agent phases. (The cache TTL is 5 min, so polls >5 min apart also pay a cache-miss —
  factor that in, but the win from fewer Opus turns dominates.)
- **Keep worker context lean** — harness-builder's 713 M cache reads are the proof that unbounded context
  growth, not output, drives agentic cost. Offload big tool outputs to files; compact long polling loops.

**Process (no corners cut):**
- **Assertions-only re-runs** for assertion-layer fixes — don't re-apply a 20-min image to re-check tests.
- **Watcher auto-arms** on log-file presence (removes an orchestrator round-trip).
- **Flag claim-tripping spec steps up front** — a step that renames a recipe (`build`↔`build-golden`)
  predictably trips guard/`must_fail` ledger claims; decide the alias direction *before* the first
  `just check`, not after a red.
- **State line advances every FSM transition** — durable status the orchestrator can read without probing.

**What NOT to cut** (these are the correctness guarantees, and they held): the smoke test, the
`verify-no-secrets` **fired** token canary, the `-m vm` assertion tier, and a real end-to-end `just run`
that writes `verdict.json`. None of these are where the time or money went.

---

## Provenance & method

Token counts are summed from each agent session's transcript JSONL under
`~/.claude/projects/-Users-bossjones-dev-bossjones-macos-ci/*.jsonl`, over the `message.usage` fields
(`input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`). The seven
build-run sessions were isolated by start time (≥ 17:59 UTC / 13:59 local) and mapped to roles by the
kickoff prompt (`You are <role> on team macos-ci-build`). Earlier haiku/fable/opus sessions from the same
day are this morning's specs work and are excluded. Pricing per the Anthropic model catalog: Opus 4.8
`$5/$25` per MTok, Sonnet 5 `$3/$15` standard (`$2/$10` intro through 2026-08-31); cache-write = 1.25×
input, cache-read = 0.1× input (5-min TTL).
