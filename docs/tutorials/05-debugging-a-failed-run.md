# 5. Debugging a Failed Run

## What you'll learn

What to check, in order, when `just run` fails or a VM won't come up: the quick status glance, the log
sweep, the automated triage sweep, and the one artifact file that's always the ground truth for
pass/fail — plus which commands in this area are known-broken so you don't waste time on them.

## Prerequisites

- [Tutorials 1](01-getting-started.md) and [2](02-running-the-harness.md) completed.
- A run that failed, or a VM that's stuck. (If everything's passing for you right now, this tutorial
  is still worth skimming so you know where to look when something eventually does fail.)

## Start here: `just status`

```bash
just status
```

This runs `tart list` (every Tart VM Tart itself knows about, running or not) followed by a
pretty-printed dump of `artifacts/latest/state.json` (the most recent run's VM name, IP, image, and
run-id — see [tutorial 2](02-running-the-harness.md) for how that file gets written). This is the
fastest way to answer "is there even a VM right now, and what does the harness think its state is."

```
Name              State      Started
dotfiles-test     running    2026-07-10T14:23:01Z

{
  "image": "sequoia",
  "ip": "192.168.64.12",
  "mount_point": "/Volumes/My Shared Files/dotfiles",
  "phase": "up",
  "run_id": "20260710-142301-004821",
  "started_at": "2026-07-10T14:23:01Z",
  "vm": "dotfiles-test"
}
```

If `artifacts/latest/state.json` doesn't exist yet, you'll see "no state.json yet" instead — meaning
`up` has never successfully completed.

## Sweep the guest's logs: `just logs`

> [!WARNING]
> **As of this writing, `just logs` does not work.** The Justfile recipe calls
> `uv run macos-ci logs --vm {{vm}}` — a top-level `macos-ci logs` command. But the real CLI mounts
> this command under the `harness` sub-app (`src/macos_ci/cli.py: app.add_typer(harness.app,
> name="harness")`), so the actual, working invocation is:
>
> ```bash
> uv run macos-ci harness logs --vm dotfiles-test
> ```
>
> If you run `just logs` verbatim, it will fail because `macos-ci logs` isn't a real top-level command.
> Use the `uv run macos-ci harness logs --vm <vm>` form directly until the Justfile recipe is fixed.

What this command does (once invoked correctly) is sweep the guest's log sources over SSH and write
each into `artifacts/<run-id>/logs/<label>.log`:

- `install.log` — `/var/log/install.log`, the system installation log.
- `brew.log` — `brew config` output, the Homebrew environment.
- `unified.log` — `log show --predicate 'eventMessage contains "chezmoi"' --last 30m`, macOS's unified
  logging system filtered to chezmoi-related events from the last 30 minutes.
- `chezmoi.log` — a copy of the apply log written earlier by `just apply`, if one exists.

## Automated triage: `just debug`

```bash
just debug
```

This runs `uv run macos-ci vm-debug sweep --json` — a sub-app mounted at `vm-debug` in `cli.py`
(read `src/macos_ci/vm_debug.py` directly for the full mechanics). It collects the same log sources
`just logs` does, plus the apply log, concatenates every line, and matches them against a table of
known failure signatures (`src/macos_ci/_triage_core.py`) grown from real failures seen while building
this harness — not invented speculatively. As of this writing, the signature table covers:

| Signature | What it means |
|---|---|
| `tart-ip-never-returns` | The guest never got a DHCP address — check the networking mode. |
| `clt-gui-prompt-non-interactive` | Xcode Command Line Tools' GUI install prompt fired inside a non-TTY run — the golden image must install CLT via `softwareupdate`, never `xcode-select --install`. |
| `rosetta-homebrew-path-mismatch` | Homebrew ended up under `/usr/local` (Intel/Rosetta convention) instead of `/opt/homebrew` (Apple Silicon). |
| `login-keychain-locked` | The login keychain is locked — this is the G8 issue documented in [specs/macos-ci/01-tart-core.md](../../specs/macos-ci/01-tart-core.md). |
| `chezmoi-template-render-error` | A chezmoi template failed to render — the run should fail here, before `apply` even runs. |
| `asdf-shims-precede-mise` | `asdf`'s shim directory is ahead of `mise`'s on `PATH` — see [specs/macos-ci/09-dotfiles-under-test.md](../../specs/macos-ci/09-dotfiles-under-test.md). |

If nothing matches, you'll see:

```
no known failure signatures matched
```

and the command exits `0`. If one or more signatures matched:

```
[tart-ip-never-returns] line 42: tart ip dotfiles-test-20260710-142301-004821 timed out
```

exiting `2`. It exits `3` if the VM is unreachable entirely, and `4` on a usage error (e.g. no
`artifacts/latest/state.json` to read from — you need at least one prior `up`).

Either way, this also (re)writes `artifacts/<run-id>/verdict.json` with its findings — see below.

## The ground truth: `artifacts/<run-id>/verdict.json`

No matter which of the above you run, or in what order, **`verdict.json` is the one artifact that's
authoritative for "did this run pass or fail, and why."** It's written by `just run` (via
`run_impl()` in `harness.py`) in a `finally` block, so it gets written **even if the harness process
crashes mid-phase** — you are never left without a verdict just because something threw an exception
partway through.

Its shape:

```json
{
  "ok": false,
  "phase": "wait-for-ip",
  "cause": "tart ip dotfiles-test-20260710-142301-004821 did not resolve within 120.0s",
  "evidence": [],
  "next_action": "run `just debug` to triage"
}
```

- **`ok`** — the bottom-line pass/fail.
- **`phase`** — which stage of `up`/`apply` it failed at (or `"done"` on success).
- **`cause`** — the specific error.
- **`evidence`** — populated when `vm-debug sweep` writes this file instead, listing matched log lines.
- **`next_action`** — a hint for what to do next (usually pointing you back at `just debug`).

`artifacts/latest/verdict.json` — via the `artifacts/latest` symlink — always points at the most recent
one.

## Other known-broken or stubbed commands in this area

Two more commands live in the same neighborhood as `just logs` and are worth knowing about *before* you
try them, not after:

- **`just vnc`** — calls `uv run macos-ci gui vnc --vm <vm>`. **This command does not exist.**
  `src/macos_ci/gui.py` defines only a `shot` command under the `gui` sub-app; there is no `vnc`
  command anywhere in the CLI. Running `just vnc` will fail outright.
- **`just shot LABEL`** — calls `uv run macos-ci gui shot <label> --vm <vm>`, which *does* exist as a
  real CLI command, but its implementation is a stub: `gui.py`'s `shot()` unconditionally raises
  `NotImplementedError`. It will fail every time it's invoked, by design, until someone implements it.

Neither of these is part of the debugging workflow this tutorial covers — they'd be screenshot/VNC
tooling if they worked, not log or verdict inspection — but if you're poking around the Justfile
looking for more options, know going in that both are non-functional as of this writing.

## For Claude Code users: two skills that automate this workflow

If you're working in this repo through Claude Code, two project skills exist specifically for this
kind of investigation:

- **`triage-logs`** — for "why did this run fail" investigations spanning multiple log sources. It fans
  out cheap subagents in parallel, one per suspect log source (install log, Homebrew, chezmoi
  apply/diff, unified log, launchd), and returns one distilled root cause plus a minimal fix instead of
  dumping raw logs into the conversation.
- **`triage-patterns`** — a reference skill for interpreting one specific log line or signature (e.g.
  "is this Rosetta/Homebrew path thing expected or a real failure") without a full parallel sweep. This
  is the same knowledge preloaded into `triage-logs`'s subagents.

This tutorial doesn't need to explain either skill fully — they're pointers for contributors already
working in Claude Code, and both explain their own trigger conditions if invoked.

## Checkpoint

You should now be able to:

- Get a quick VM/run overview with `just status`.
- Correctly sweep guest logs with `uv run macos-ci harness logs --vm <vm>` (knowing `just logs` itself
  is currently broken).
- Run `just debug` and interpret a matched signature.
- Find and read `artifacts/<run-id>/verdict.json` as the authoritative pass/fail record, even after a
  crash.
- Recognize `just vnc` and `just shot` as non-functional, rather than losing time debugging them as if
  they were real failures in your own setup.

## Next steps

- [Tutorial 4 — Verifying the Truth Gate](04-verifying-the-truth-gate.md): if the thing that's "failing"
  is actually a *spec* claim rather than a VM run, that's the other verification system in this repo.
- [docs/architecture/cli-reference.md](../architecture/cli-reference.md) for the complete, verified list
  of which CLI commands exist, which are stubs, and which the Justfile calls incorrectly.
- [specs/macos-ci/12-tooling-and-agent-loop.md](../../specs/macos-ci/12-tooling-and-agent-loop.md) for
  the full design of the artifacts contract and the seed failure-signature table.
