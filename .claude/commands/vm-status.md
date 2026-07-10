---
description: Print the current harness verdict and tart VM inventory. Cheap, read-only orientation.
argument-hint: (none)
allowed-tools: Bash, Read
---

# /vm-status — cheap read-only orientation

Answer "what's the state of things right now" without running anything that touches a VM. This is
the command to reach for before `/vm-debug` — it costs nothing and often makes a deeper triage
unnecessary.

## What to print

1. **The last run's verdict**, if one exists:

   ```bash
   test -f artifacts/latest/verdict.json && cat artifacts/latest/verdict.json
   ```

   `verdict.json` has the shape `{ok, phase, cause, evidence: [{file, line, text}], next_action}`.
   If `ok` is `true`, say so plainly and stop — there's nothing to triage. If `false`, surface
   `phase`, `cause`, and the cited `evidence` lines verbatim; don't paraphrase them away.

   If the file doesn't exist, say so — no run has completed yet, or `artifacts/` was cleaned.

2. **The tart VM inventory**:

   ```bash
   tart list
   ```

   Note any clone whose name doesn't correspond to a run-id under `artifacts/` — that's an orphan
   `just prune` would clean up, not evidence of a live problem.

## Output

A short status block, not a wall of JSON:

```
Last run: <run-id> — <ok/FAILED at phase X>
  cause: <one line, if failed>
Tart VMs: <n> total, <n> orphaned (no matching artifacts/<run-id>)
```

If the verdict shows a failure, offer `/vm-debug` as the next step — don't start triaging inline;
that's a different command with its own evidence-gathering discipline.
