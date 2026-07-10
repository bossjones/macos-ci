# 🔬 ledger — YOUR BRIEF

**You are `ledger`.** Surface `A6FE02F9-4DD6-4ADA-8938-28B4F4292CC9` (`pane:43`).
**Read [`_RULES.md`](_RULES.md) in full first.** Then this.

**You start immediately. You unblock everyone.**

## You own — and you are the ONLY agent who may edit these

- `.team/claims.jsonl`
- `tools/verify_claims.py`

## Your job

1. **Read `tools/verify_claims.py` first.** It works and passes **50/50**. Extend it **only** if a new
   evidence *kind* is genuinely needed — and justify that in the backlog before you write a line.

2. **Merge `.team/proposed/*.jsonl` → `.team/claims.jsonl`.**
   - Dedupe by `id`.
   - **Reject malformed records** — every record needs a `file` field. (All 50 current ones have it; I
     checked.)
   - **Reject claims whose evidence does not reproduce.** A proposed claim that fails is a **finding**,
     not a bug to silence: route it back to its owning agent as a **CONFLICT** in the backlog.
   - Keep `just verify-claims` exiting **0**. That is your contract with the lead.

3. **`.team/proposed/lead.jsonl` is already waiting for you**, dry-run green at `4/4`:
   - `oq02-vnc-marker-pinned-at-12-340` — `file-line`, pins the marker OQ-02 cites.
   - `CONTROL-12-line-607-does-not-exist` — `file-line` + **`must_fail`**. The prior lead pass
     hallucinated a citation to `12-tooling-and-agent-loop.md:607`; the file is **535 lines**. This
     control records that permanently. **If it ever starts PASSING, the file grew past 607 lines and a
     fabricated citation became accidentally valid — re-audit, do not celebrate.**
   - `oq01-asif-marker-pinned-at-13-54` — `file-line`.
   - `g15-hdiutil-caveat-marker-pinned-at-13-51` — `file-line`.

   Scrutinise `CONTROL-12-line-607-does-not-exist` especially. It relies on `check_line` returning a
   **plain** `False` for an out-of-range line (`"line 607 out of range (file has 535)"`) — **not** an
   `UNREACHABLE:`/`STRUCTURE:`-prefixed failure, which `must_fail` would refuse to invert. Confirm that
   in `verify_claims.py` yourself. If the prefix semantics make this control unsound, **say so and reject
   it** — I would rather lose my own claim than ship a control that lies.

## ENFORCE THE TWO INVARIANTS — this is the part nobody else can do

**(a) NEVER delete or weaken any of the six `must_fail` claims.**
`CONTROL-utm-settings-apple-devices-is-fabricated`, `CONTROL-disposable-is-not-apple-backend`,
`CONTROL-tart-doc-index-oracle`, `CONTROL-tart-cirrus-page-has-no-sshpass`,
`packer-sensitive-hides-secret`, `packer-sensitive-hides-secret-under-debug-log`.
If **any** of them starts *passing*, an oracle has silently broken and **every claim of its kind is
worthless** — the run must fail loudly rather than go green on a dead check.

**(b) EVERY negative `must_fail` probe over a `cli-help` command MUST ship a positive control** running
the same `argv` **and** `env`, asserting a non-sensitive literal **is** present. **Reject a bare negative
probe as unfalsifiable** — *"the secret is absent from the output"* is equally satisfied by **no output at
all**. Verify that each existing control asserts a literal the **same** `argv`+`env` genuinely prints.
**A pair whose control is vacuous is a green check that means nothing. Say so out loud.**

## Then: CROSS-AUDIT 📚 synth's files

`00-overview.md`, `10-tart-vs-utm-adr.md`, `11-sources.md`, `specs/macos-ci.md`.
Red-team posture, **default to refuted**, except the G19 carve-out (§3 of `_RULES.md`).
**Do not edit them** — file CONFLICTs in the backlog under `### 🔬 ledger`.

## Report

- The **claims delta**: added / rejected / refuted, with reasons.
- Whether the six `must_fail` claims are all still intact and still *failing* (i.e. passing their
  inverted verdict).
- Whether any control is **vacuous**.

Keep the pill current, notify on transitions and on your first OQ, and end with exactly:

```
TASK-DONE: ledger | <one-line summary> | claims+N refuted-M unverified-K open-questions-J
```
