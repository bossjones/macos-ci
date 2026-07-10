---
description: Triage a tart VM / harness run by reading the macOS log sources that matter, and surface the root cause fast.
argument-hint: [source]
allowed-tools: Bash, Read, AskUserQuestion
---

# /vm-debug — fast macOS harness triage

Diagnose a failed or stuck `macos-ci` run by reading the logs that matter — the way a `permission
denied` or a locked login keychain is obvious the moment you see it. Follow the
**systematic-debugging** discipline: gather evidence → name the root cause → propose the
*minimal* fix → verify. Do not guess a fix before you have the smoking-gun line.

`$ARGUMENTS` is `[source]` — one of `tart-ip`, `install-log`, `brew-log`, `chezmoi-diff`,
`unified-log`, `launchd` — or omitted to sweep every source.

## Phase 1 — Collect evidence, artifacts first

**Check the artifacts before re-running anything.** If `artifacts/latest/verdict.json` exists and
is from the run being debugged, read it first — `{ok, phase, cause, evidence: [{file, line,
text}], next_action}` already names the failing phase and cites its evidence. A run that already
failed and wrote a verdict needs no fresh sweep to reach the same conclusion.

Only invoke a live sweep when there's no usable verdict yet, or the VM is still up and you need a
fresher read. Run it **in the background** (Bash tool with `run_in_background: true`) so its
retry loop (up to 3 attempts with exponential backoff) doesn't block. You'll be re-invoked when it
finishes; then read its output.

```bash
uv run macos-ci vm-debug --source $ARGUMENTS --json    # one source
uv run macos-ci vm-debug --json                        # every source
```

The command resolves the VM via `tart ip <run-id>`, SSHes in as `admin@`, sweeps the log sources
in the table below, and **highlights** lines matching known failure signatures. It prints a human
report (stderr) plus a JSON summary (stdout), and writes `artifacts/<run-id>/verdict.json`. Exit
codes: **0** healthy · **2** issues found · **3** VM unreachable · **4** usage/resolve error.

If exit is **4**: the run-id/VM likely doesn't exist or `tart` can't resolve it — tell the user and
stop (offer `just up`). If **3** (unreachable): the VM may still be booting; mention it and offer
to re-run.

| Source | What it reads |
|---|---|
| `tart-ip` | `tart ip <vm>` resolution (DHCP/bridged/agent) |
| `install-log` | `/var/log/install.log` (OS install, Xcode CLT) |
| `brew-log` | `brew config`, `~/Library/Logs/Homebrew/` |
| `chezmoi-diff` | `artifacts/<run-id>/apply.log` (captured host-side, pre-apply lint) |
| `unified-log` | `log show --predicate '...' --last 30m` |
| `launchd` | `launchctl print system/<label>` |

## Phase 2 — Name the root cause

From the highlighted `signature_hits`, state the actual root cause in plain terms, not just the
log line. Seed signatures (grow this from real failures, don't invent more):
- `tart ip <vm>` never returns → guest never got DHCP; check the softnet/bridged networking mode.
- `xcode-select: note: install requested` → the CLT GUI prompt fired inside a non-TTY run; the
  golden image must install CLT non-interactively via `softwareupdate --install <label>`.
- `Cannot install under Rosetta 2` / `/usr/local` vs `/opt/homebrew` → architecture mismatch; the
  VM is arm64, Homebrew must live at `/opt/homebrew`.
- Headless boot + `The specified item could not be found in the keychain` → the login keychain is
  locked (G8 — see `specs/macos-ci/01-tart-core.md`).
- `chezmoi: template: ...` on `chezmoi diff` → template render error; the run must fail here,
  before apply.
- `which node` resolves to `~/.asdf/shims/node` under `version_manager=mise` → asdf shims precede
  mise on `PATH`.

Cite the exact line(s). If nothing is conclusive, say so rather than inventing a cause.

## Phase 3 — Ask how far to go, then act

Before changing anything, use **AskUserQuestion** to confirm remediation scope:

- **Report only** — stop here; the user drives the fix.
- **Apply a safe live fix now** — patch the guest over SSH (no `-t`) or re-run `just apply`
  against the already-live clone (the harness's fast iteration loop). Then **re-run this command**
  to verify the signature is gone.
- **Fix and fold back into the source, then recreate** — port the fix into the golden-image
  provisioner (`packer/**`) or the dotfiles under test, then `just recreate` (a fresh `tart clone`
  is needed for image-level or template changes — the golden image itself is never mutated).

Only act after the user chooses. After any fix, verify by re-running the sweep and confirming the
exit code is `0` (or the specific signature is gone) — evidence before claiming it's fixed.
