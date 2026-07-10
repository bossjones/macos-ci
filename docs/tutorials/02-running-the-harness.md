# 2. Running the Harness

## What you'll learn

The full VM lifecycle this repo drives — what each `just` recipe actually does to a real Tart VM
under the hood — plus the seed-config fixtures and override variables you'll use once you go beyond
the defaults, and a realistic "edit a dotfiles template, see the result" iteration loop.

## Prerequisites

- [Tutorial 1](01-getting-started.md) completed: `just doctor` passes, and you understand what
  Tart/Packer/this-harness each are.
- A golden image already built (`just build-golden` — see
  [tutorial 3](03-building-the-golden-image.md) if you haven't done this yet). Everything in this
  tutorial clones from that image; without it, `just up` has nothing to clone from.

## The mental model: one golden image, many disposable clones

A **Tart VM** is a named virtual machine tracked by the `tart` CLI (`tart list`, `tart clone`,
`tart run`, `tart delete`, ...). This repo never mutates its one golden VM (named `dotfiles-golden`)
directly. Instead, every test run **clones** it into a fresh, disposable VM, does its work against the
clone, and deletes the clone when it's done. That's the whole point of the harness: a broken test run
never corrupts the thing future runs clone from.

Every recipe below is a thin `just` wrapper around `uv run macos-ci harness <command>`, which is Typer
Python code in `src/macos_ci/harness.py`. If you ever want ground truth beyond this tutorial, that file
(and its pure-logic sibling `_harness_core.py`) is the actual implementation.

## The lifecycle recipes

### `just up` — clone, boot, bootstrap SSH

```bash
just up
```

Runs `macos-ci harness up`, which does, in order (read `up_impl()` in `harness.py` for the exact
sequence):

1. **`tart clone`** the golden image (resolved from `macos-versions.toml` — `dotfiles-golden` for the
   default `sequoia` image) into a fresh, uniquely-named clone (e.g.
   `dotfiles-test-20260710-142301-004821`, or just `dotfiles-test` if you didn't override the name).
2. **Mount your dotfiles working tree read-only** into the guest via `tart run --dir`, a Tart feature
   that shares a host directory into the guest's filesystem (surfacing at
   `/Volumes/My Shared Files/dotfiles` inside the VM) — no copying, no git clone inside the guest.
3. **`tart run --no-graphics`** (headless) to boot the clone in the background.
4. **Poll `tart ip`** every 2 seconds, up to 120 seconds, until the VM reports a network address.
5. **Bootstrap SSH key trust** — this is the two-phase part worth understanding: the golden image only
   has password auth configured (`admin`/`admin`), and the harness's steady-state SSH wants
   password-less, key-based auth (`BatchMode=yes`, no interactive prompt possible). So `up` makes
   **one** password-authenticated connection (via `sshpass`, which is exactly why `sshpass` is in
   `doctor`'s required-tools list) whose only job is to seed the harness's own public key
   (`harness/ssh/id_ed25519_harness.pub`) into the guest's `authorized_keys`. Every subsequent SSH
   command in this repo — `apply`, `logs`, `vm-debug sweep`, `just ssh`, `just exec` — uses the private
   key instead, never the password again.
6. **Wait for key-based SSH** to actually work (up to 60 seconds) — the key gets seeded before the
   guest has necessarily finished setting itself up enough to accept it.
7. **Seed `~/.zshenv`** in the guest with Homebrew/mise/zsh-dotfiles bin directories on `PATH`, and
   **symlink** the mounted dotfiles tree to chezmoi's conventional source location
   (`~/.local/share/chezmoi`) — both idempotent, safe to run against a VM that's already been through
   this once.

`up` writes `artifacts/<run-id>/state.json` (VM name, IP, image, run-id, mount point) and every later
command that needs to find "the currently active VM" reads it back via
`artifacts/latest/state.json` — `artifacts/latest` is a symlink to whichever run-id was most recent.

### `just apply` — just the chezmoi install, on a VM that's already up

```bash
just apply
```

This is the fast-iteration recipe: it does **not** clone or boot anything. It assumes `up` already ran
and reads the live VM's IP/run-id straight out of `artifacts/latest/state.json`. Then, over SSH:

1. `chezmoi init` (without `--apply`) to seed a config, because `chezmoi diff` can't render templates
   without one existing first.
2. `chezmoi diff`, saved to `artifacts/<run-id>/chezmoi-diff.log`.
3. `chezmoi apply`, wrapped in a `retry -t 4` (four attempts, to absorb transient network blips during
   Homebrew/mise installs), saved to the apply log.

Because `apply` skips clone/boot entirely, it's dramatically faster than `up` — this is the recipe
you'll run over and over while iterating on a dotfiles change.

### `just down` (alias `just stop`) — stop, keep the clone

```bash
just down
```

Runs `tart stop` on the named VM directly (no SSH involved) and leaves the clone sitting on disk. Use
this when you want to pause without losing the VM's current state.

### `just destroy` — delete the clone

```bash
just destroy
```

Stops the VM first (tolerating "already stopped" — `tart delete` on a *running* clone fails with a
misleading "does not exist" error, so `destroy_impl()` always stops first), then runs `tart delete`.
The clone is gone after this.

### `just recreate` — destroy then up, in one step

```bash
just recreate
```

Exactly `destroy` followed by `up` on the same VM name — a full refresh when you want a byte-identical
clean start without two separate commands.

### `just run` — the whole cycle, one shot

Covered in [tutorial 1](01-getting-started.md#step-2-run-the-full-cycle-with-just-run): doctor → up →
apply → verify → destroy, always writing `verdict.json`.

### `just prune` — clean up orphaned clones

```bash
just prune
```

Cross-references every VM `tart list` knows about against every `artifacts/*/state.json`'s `vm` field.
Anything named `dotfiles-test-*` that isn't tracked by any state file — typically left behind by a
crashed or killed run — gets deleted. Safe to run any time; it never touches a VM that's still
tracked.

### `just matrix` — the cross-product test

```bash
just matrix
```

Runs the full `up → apply → destroy` cycle once per combination of image × version manager (default:
the config's default image against both `mise` and `asdf`). Each leg gets its own uniquely-named VM
(`dotfiles-matrix-<image>-<version-manager>`), so one leg failing never aborts the others — you get one
independent verdict per leg.

## Seed-config fixtures: reaching toggles a non-interactive install can't prompt for

`chezmoi apply` inside this harness runs over an SSH session with no TTY attached — deliberately, per
[specs/macos-ci/09-dotfiles-under-test.md](../../specs/macos-ci/09-dotfiles-under-test.md). That means
any dotfiles template field gated behind an interactive `promptBool` (things like whether to install
Ruby, pyenv, Node.js, Kubernetes CLIs, CUDA, fnm, or OpenCV) silently resolves to its documented
non-interactive default — every one of those seven toggles defaults to `false` in a harness run.

To actually exercise the `true` path for those toggles, this repo ships two pre-seeded chezmoi config
fixtures under `harness/seed-config/` (read `harness/seed-config/README.md` for the complete field
reference and mechanism):

- **`lean-baseline.yaml`** — all seven toggles explicit `false`. Behaviorally identical to no seed file
  at all; it exists to give the toggle matrix an explicit, named baseline instead of relying on
  implicit absence.
- **`all-features.yaml`** — all seven toggles explicit `true`. Exercises every optional install path in
  one (slower) run.

These aren't wired to a `just` flag in this tutorial's default recipes — they're a harness-side
mechanism the CLI consumes by writing the fixture into the guest's
`~/.config/chezmoi/chezmoi.yaml` before `chezmoi init` runs. If you need to drive a specific fixture,
read `harness/seed-config/README.md` for the exact field names and how they map to `.chezmoi.yaml.tmpl`
in `zsh-dotfiles`.

## Override variables

The Justfile's `vm`/`image`/`dotfiles`/`vmgr` variables all read from environment variables first, so
you can override any of them without editing the Justfile:

| Env var | Overrides | Default |
|---|---|---|
| `MACOS_CI_VM` | VM name | `dotfiles-test` |
| `MACOS_CI_IMAGE` | Base image name (from `macos-versions.toml`) | `sequoia` |
| `ZSH_DOTFILES` | Path to the `zsh-dotfiles` checkout under test | `../zsh-dotfiles` (relative to the Justfile) |
| `MACOS_CI_VERSION_MANAGER` | Version manager chezmoi configures (`mise` or `asdf`) | `mise` |

For example, to test against a different dotfiles checkout without touching any file in this repo:

```bash
ZSH_DOTFILES=/path/to/my/zsh-dotfiles just up
```

or to run the whole cycle against the `tahoe` image with `asdf` instead of `mise`:

```bash
MACOS_CI_IMAGE=tahoe MACOS_CI_VERSION_MANAGER=asdf just run
```

See [docs/architecture/cli-reference.md](../architecture/cli-reference.md#environment-variables) for
the full mapping table.

## A realistic fast-iteration loop

This is the loop you'll actually use while editing a `zsh-dotfiles` template and re-testing it:

```bash
# 1. Bring up a VM once — this is the slow step (clone + boot + SSH bootstrap).
just up

# 2. Edit something in your zsh-dotfiles checkout...
#    (in another terminal / editor)

# 3. Re-apply just the chezmoi install — fast, no clone/boot.
just apply

# 4. Poke around inside the guest to see what actually happened.
just ssh

# --- inside the guest ---
$ chezmoi status
$ cat ~/.zshrc
$ exit
# --- back on the host ---

# 5. Not quite right? Edit zsh-dotfiles again, then repeat from step 3.
just apply

# 6. One-shot commands without a full interactive shell:
just exec "chezmoi diff"

# 7. Done for now — stop it (keeps the clone, in case you want to pick back up).
just down

# ...or tear it down entirely if you're done for good:
just destroy
```

Because `apply` skips the clone-and-boot phase entirely, steps 3–6 are the tight loop — you should be
able to run several `apply` cycles in the time a single `up` takes.

`just ssh` and `just exec CMD` both use the same key-based, `BatchMode=yes` SSH connection the harness
itself uses (`tart ip <vm>` to find the address, then `ssh` with the fixed `ssh_opts` in the Justfile) —
they are plain conveniences for a human, not part of the automated pass/fail path.

## Checkpoint

You should now be able to:

- Explain what each of `up`/`down`/`destroy`/`recreate`/`apply`/`prune`/`matrix` does to a real Tart VM.
- Explain why SSH bootstrap is two-phase (password once, key forever after).
- Override the VM name, image, dotfiles path, and version manager via environment variables.
- Run a fast `up` once, `apply` repeatedly loop.

## Next steps

- [Tutorial 3 — Building the Golden Image](03-building-the-golden-image.md): what `up` actually clones
  from, and how to build or rebuild it.
- [Tutorial 4 — Verifying the Truth Gate](04-verifying-the-truth-gate.md): this repo's *other*
  verification system, for its own specs — not to be confused with `just verify` (VM testinfra tests).
- [docs/architecture/build-pipeline.md](../architecture/build-pipeline.md) for the full lifecycle table
  and diagram.
