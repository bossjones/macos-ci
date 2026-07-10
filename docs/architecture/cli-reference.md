# CLI Reference

Complete reference for the `macos-ci` Typer CLI.

## Quick Reference

The CLI is organized into sub-apps mounted from `src/macos_ci/cli.py`:

| Command | Purpose |
|---------|---------|
| `macos-ci doctor` | Preflight checks — verify all requirements are met |
| `macos-ci harness up` | Clone golden image, start headless VM, bootstrap SSH |
| `macos-ci harness down` | Stop the VM (leave clone on disk) |
| `macos-ci harness destroy` | Delete the VM clone entirely |
| `macos-ci harness apply` | Run chezmoi apply against a live VM (fast iteration) |
| `macos-ci harness run` | Full integration: up → diff → apply → destroy |
| `macos-ci harness prune` | Delete orphan clones not tracked in `artifacts/` |
| `macos-ci harness logs` | Sweep guest logs into `artifacts/<run-id>/logs/` |
| `macos-ci harness matrix` | Cross-product test: image × version-manager |
| `macos-ci gui shot` | Capture framebuffer screenshot (not yet implemented) |
| `macos-ci vm-debug sweep` | Triage: match guest log signatures against failure patterns |

## Top-Level Commands

### doctor

**Invocation**: `macos-ci doctor [OPTIONS]`

**Description**: Preflight every requirement. Exit 2 if anything is missing.

**Options**:
- `--json` — Emit machine-readable JSON output; writes to `artifacts/<run-id>/doctor.json` (boolean, default: `False`)
- `--help` — Show this message and exit

**Exit Codes**:
- `0` — All checks passed
- `2` — One or more checks failed

**Implementation**: `src/macos_ci/doctor.py:doctor_command()`

---

## Harness Sub-App

The `harness` sub-app implements the core VM lifecycle and testing workflow. All harness commands are mounted as `macos-ci harness <command>`.

**Sub-app module**: `src/macos_ci/harness.py`  
**Mounted as**: `macos-ci harness`

### up

**Invocation**: `macos-ci harness up [OPTIONS]`

**Description**: Clone the golden image, start a headless Tart VM, poll for IP, bootstrap key-based SSH, and configure shell environment.

Writes `artifacts/<run-id>/state.json` with VM details (name, IP, image, run-id, mount point, phase, timestamp).

**Options**:
- `--vm TEXT` — VM name to create (default: `dotfiles-test`)
- `--image TEXT` — Base image name to clone from, resolved from `macos-versions.toml` (default: `sequoia`)
- `--dotfiles TEXT` — Path to zsh-dotfiles repo; defaults to `../zsh-dotfiles` relative to cwd
- `--help` — Show this message and exit

**Implementation**: `src/macos_ci/harness.py:up()` → `up_impl()`

**Phases** (in order):
1. `tart clone` from golden image (`dotfiles-golden` for default image)
2. `tart run` headless with `--dir` mount of dotfiles (read-only)
3. Poll `tart ip` until VM has an IP (timeout: 120s)
4. Bootstrap SSH key trust via `sshpass` (one password-authenticated connection)
5. Wait for key-based SSH readiness (timeout: 60s)
6. Append Homebrew/mise/zsh-dotfiles bin directories to `~/.zshenv`
7. Symlink dotfiles mount point to `~/.local/share/chezmoi` (conventional location)

---

### down

**Invocation**: `macos-ci harness down [OPTIONS]`

**Description**: Stop the VM without deleting it. The clone persists on disk for re-use or inspection.

**Options**:
- `--vm TEXT` — VM name (default: `dotfiles-test`)
- `--help` — Show this message and exit

**Implementation**: `src/macos_ci/harness.py:down()` → `down_impl()`

**Note**: Calls `tart stop` directly; does not use SSH.

---

### destroy

**Invocation**: `macos-ci harness destroy [OPTIONS]`

**Description**: Delete the VM clone entirely (calls `tart delete`).

Internally stops the VM first if running (tolerates already-stopped state).

**Options**:
- `--vm TEXT` — VM name (default: `dotfiles-test`)
- `--help` — Show this message and exit

**Implementation**: `src/macos_ci/harness.py:destroy()` → `destroy_impl()`

---

### apply

**Invocation**: `macos-ci harness apply [OPTIONS]`

**Description**: Run chezmoi apply against an already-live VM (fast iteration path).

Assumes a prior `up` has populated `artifacts/latest/state.json` with IP and run-id. Logs to `artifacts/<run-id>/apply.log`.

**Options**:
- `--vm TEXT` — VM name (must match the name tracked in latest state) (default: `dotfiles-test`)
- `--version-manager TEXT` — Version manager to configure for chezmoi (default: `mise`)
- `--help` — Show this message and exit

**Execution Steps**:
1. Read `artifacts/latest/state.json`
2. Verify VM name matches
3. Run `chezmoi init` (non-apply) to seed config
4. Run `chezmoi diff` and save output
5. Run `chezmoi apply` (with 4 retries on transient failure)

**Implementation**: `src/macos_ci/harness.py:apply()` → `apply_impl()`

---

### run

**Invocation**: `macos-ci harness run [OPTIONS]`

**Description**: Full integration run: up → chezmoi diff → apply → destroy. Always writes `verdict.json`, even on failure.

**Options**:
- `--vm TEXT` — VM name (optional; auto-generated if omitted) (default: `dotfiles-test`)
- `--image TEXT` — Base image name (default: `sequoia`)
- `--version-manager TEXT` — Version manager to configure (default: `mise`)
- `--dotfiles TEXT` — Path to zsh-dotfiles repo
- `--help` — Show this message and exit

**Exit Codes**:
- `0` — Integration succeeded
- `2` — Integration failed (phase, cause, and evidence written to `verdict.json`)

**Artifact Output**:
- `artifacts/<run-id>/state.json` — VM details after `up`
- `artifacts/<run-id>/apply.log` — chezmoi output
- `artifacts/<run-id>/verdict.json` — final success/failure verdict

**Implementation**: `src/macos_ci/harness.py:run()` → `run_impl()`

**Guarantee**: VM is destroyed on exit (even on crash), but `verdict.json` is always written.

---

### prune

**Invocation**: `macos-ci harness prune [OPTIONS]`

**Description**: Delete orphan VM clones not tracked in `artifacts/*/state.json`.

Cross-references every `tart list` entry against every `artifacts/*/state.json`'s `vm` field. Clones starting with `dotfiles-test-` but not listed in any state file are deleted.

**Options**:
- `--help` — Show this message and exit

**Implementation**: `src/macos_ci/harness.py:prune()` → `prune_impl()`

---

### logs

**Invocation**: `macos-ci harness logs [OPTIONS]`

**Description**: Sweep guest log sources over SSH and save them to `artifacts/<run-id>/logs/`.

Reads from `artifacts/latest/state.json` to find IP and run-id, then SSHes into the guest and collects:
- `/var/log/install.log` (system installation log)
- `brew config` output (Homebrew environment)
- `log show` output (macOS unified log, filtered for chezmoi events in last 30m)
- `<run-id>/apply.log` if it exists (chezmoi apply log)

Saves each as `artifacts/<run-id>/logs/<label>.log`.

**Options**:
- `--vm TEXT` — VM name (must match the name tracked in latest state) (default: `dotfiles-test`)
- `--help` — Show this message and exit

**Implementation**: `src/macos_ci/harness.py:logs()` → `logs_impl()`

---

### matrix

**Invocation**: `macos-ci harness matrix [OPTIONS]`

**Description**: Cross-product integration test: every image × every version-manager combination.

Each leg gets its own VM name (`dotfiles-matrix-<image>-<version-manager>`) and runs independently. One leg's failure does not abort others.

**Options**:
- `--images TEXT` — Comma-separated image names; default: config default (default: `""`)
- `--version-managers TEXT` — Comma-separated version managers (default: `mise,asdf`)
- `--help` — Show this message and exit

**Implementation**: `src/macos_ci/harness.py:matrix()` → `matrix_impl()`

**Example**: `macos-ci harness matrix --images sequoia,ventura --version-managers mise,asdf` runs 4 legs.

---

## GUI Sub-App

The `gui` sub-app provides VNC-based framebuffer operations. Currently only screenshot capture is referenced (not yet implemented).

**Sub-app module**: `src/macos_ci/gui.py`  
**Mounted as**: `macos-ci gui`

### shot

**Invocation**: `macos-ci gui shot LABEL [OPTIONS]`

**Description**: Capture one framebuffer PNG screenshot into `artifacts/<run-id>/screenshots/`.

**Arguments**:
- `LABEL` — Screenshot label/filename (required)

**Options**:
- `--help` — Show this message and exit

**Status**: ⚠️ Not yet implemented — raises `NotImplementedError`

**Implementation**: `src/macos_ci/gui.py:shot()`

---

## VM-Debug Sub-App

The `vm-debug` sub-app triages guest logs for known failure signatures.

**Sub-app module**: `src/macos_ci/vm_debug.py`  
**Mounted as**: `macos-ci vm-debug`

### sweep

**Invocation**: `macos-ci vm-debug sweep [OPTIONS]`

**Description**: Triage guest logs for known failure signatures (see `_triage_core.match()` for signature patterns).

Reads from `artifacts/latest/state.json` to find IP and run-id. Collects every log source (install, brew, unified, chezmoi apply), feeds combined text to pattern matcher, writes `verdict.json`.

**Options**:
- `--vm TEXT` — VM name (optional; uses state.json default if omitted)
- `--json` — Emit machine-readable JSON output (boolean, default: `False`)
- `--help` — Show this message and exit

**Exit Codes**:
- `0` — No known failure signatures matched
- `2` — One or more signatures matched (evidence in `verdict.json`)
- `3` — VM unreachable (SSH timeout)
- `4` — Usage error

**Log Sources** (per spec 12):
- `/var/log/install.log` — System installation log
- `brew config` — Homebrew environment and configuration
- `log show --predicate 'eventMessage contains "chezmoi"' --last 30m` — macOS unified log for chezmoi events
- `artifacts/<run-id>/apply.log` (if exists) — chezmoi apply output

**Implementation**: `src/macos_ci/vm_debug.py:sweep()` → `sweep_impl()`

**Artifact Output**: `artifacts/<run-id>/verdict.json` with structure:
```json
{
  "ok": bool,
  "phase": "vm-debug",
  "cause": string | null,
  "evidence": [
    {
      "file": "vm-debug",
      "line": int,
      "text": string
    }
  ],
  "next_action": string | null
}
```

---

## SSH Transport

All commands that interact with the guest (apply, logs, vm-debug sweep) use two-phase SSH:

1. **Bootstrap phase** (one-time, password-authenticated via `sshpass`):
   - Seed SSH public key (`id_ed25519_harness.pub`) into guest
   - Runs during `up`

2. **Steady-state phase** (all subsequent commands):
   - Key-based authentication via `id_ed25519_harness`
   - Flags: `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=8 -o BatchMode=yes`
   - Guest user: `admin`
   - Key path: `harness/ssh/id_ed25519_harness`

**Note**: SSH key permissions are enforced to `0600` before use (OpenSSH refuses more-permissive keys).

---

## Artifacts Contract

Every run produces an `artifacts/<run-id>/` directory with structured outputs:

| File | Created by | Purpose |
|------|------------|---------|
| `state.json` | `up` | VM metadata (name, IP, image, run-id, mount point, phase, timestamp) |
| `apply.log` | `apply` | stdout + stderr from chezmoi init and apply |
| `verdict.json` | `run` or `vm-debug sweep` | Success/failure verdict with phase, cause, evidence, next action |
| `doctor.json` | `doctor` | Tool versions and system facts (always written) |
| `logs/<label>.log` | `logs` | Guest log sources (install, brew, unified, chezmoi) |
| `screenshots/<label>.png` | `gui shot` | Framebuffer screenshot (not yet implemented) |

**Latest Symlink**: `artifacts/latest/` always points to the most recent run's directory (used by `apply`, `logs`, `vm-debug sweep` to find the current IP and run-id).

---

## Environment Variables

The CLI does not directly consume environment variables. The **Justfile** (via `uv run` recipes) maps these to CLI options:

| Justfile Var | CLI Usage | Default |
|--------------|-----------|---------|
| `MACOS_CI_VM` | `--vm` | `dotfiles-test` |
| `MACOS_CI_IMAGE` | `--image` | `sequoia` |
| `ZSH_DOTFILES` | `--dotfiles` | `../zsh-dotfiles` (relative to cwd) |
| `MACOS_CI_VERSION_MANAGER` | `--version-manager` | `mise` |

Override via environment:
```bash
export MACOS_CI_VM=my-test-vm
uv run macos-ci harness up
```

---

## Justfile Integration Notes

The Justfile wraps CLI commands. Where a Justfile recipe exists, it is documented in [`justfile-reference.md`](./justfile-reference.md). Key mappings:

| Justfile Recipe | CLI Command |
|-----------------|-------------|
| `just up` | `macos-ci harness up --vm {{vm}} --image {{image}} --dotfiles {{dotfiles}}` |
| `just down` | `macos-ci harness down --vm {{vm}}` |
| `just destroy` | `macos-ci harness destroy --vm {{vm}}` |
| `just apply` | `macos-ci harness apply --vm {{vm}} --version-manager {{vmgr}}` |
| `just run` | `macos-ci harness run --vm {{vm}} --image {{image}} --version-manager {{vmgr}} --dotfiles {{dotfiles}}` |
| `just prune` | `macos-ci harness prune` |
| `just logs` | **Calls wrong command**: `uv run macos-ci logs --vm {{vm}}` (should be `macos-ci harness logs`) ⚠️ |
| `just matrix` | `macos-ci harness matrix` |
| `just doctor` | `uv run macos-ci doctor` |
| `just debug` | `uv run macos-ci vm-debug sweep --json` |
| `just shot` | **Calls non-existent command**: `uv run macos-ci gui shot {{LABEL}} --vm {{vm}}` ⚠️ |
| `just vnc` | **Calls non-existent command**: `uv run macos-ci gui vnc --vm {{vm}}` ⚠️ |

**⚠️ Discrepancies** (Justfile references CLI commands that don't exist or are incorrectly named):
- `logs` recipe calls `macos-ci logs` but CLI has `macos-ci harness logs`
- `shot` recipe calls `macos-ci gui shot LABEL` but the command is not yet implemented
- `vnc` recipe calls `macos-ci gui vnc` which does not exist in the CLI
- `build-ipsw` recipe references a non-existent CLI command
- `pull` recipe references a non-existent CLI command

Tracked with reproduction evidence and claims-ledger entries in [specs/macos-ci/14-known-discrepancies.md](../../specs/macos-ci/14-known-discrepancies.md) — `just verify-claims` catches these directly.

---

## Sourcing

This reference is extracted directly from:
- `src/macos_ci/cli.py` — entrypoint and sub-app mounting
- `src/macos_ci/harness.py` — harness commands and implementation
- `src/macos_ci/gui.py` — GUI commands (shot only, unimplemented)
- `src/macos_ci/vm_debug.py` — vm-debug commands
- `src/macos_ci/doctor.py` — doctor command

**Last verified**: 2026-07-10 by reading actual `@app.command()` decorators and Typer option signatures.
