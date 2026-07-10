# 1. Getting Started

## What you'll learn

By the end of this tutorial you'll understand what `macos-ci` is for, have every required tool
installed and verified, and have run one complete, disposable test cycle end to end.

## Prerequisites

None, beyond a terminal and an Apple Silicon Mac. This tutorial assumes you have never touched
[Tart](https://tart.run), [Packer](https://developer.hashicorp.com/packer), or
[UTM](https://getutm.app) before, and explains each the first time it comes up.

**Time estimate**: 10 minutes to read and run `just doctor`; the first full `just run` walkthrough
at the end takes longer (see the callout in that section) because it depends on a one-time image
build covered in [tutorial 3](03-building-the-golden-image.md).

## What this repo is

`macos-ci` is a local, disposable-VM CI harness. Its whole reason to exist is one gap: the
[`zsh-dotfiles`](https://github.com/bossjones/zsh-dotfiles) repo (managed by
[chezmoi](https://www.chezmoi.io/), a dotfiles manager that renders templated config files into your
home directory) has Linux CI coverage but no macOS equivalent — Docker can't run a macOS guest, and
GitHub's hosted macOS runners are remote, queued CI, not a fast local iteration loop. This repo closes
that gap: it clones a clean macOS virtual machine, installs `zsh-dotfiles` into it exactly the way a
real user would, asserts the install worked, and throws the VM away — repeatably, in a loop tight
enough to run while you're editing a dotfiles template.

Two docs cover this in more depth than this tutorial will:

- [README.md](../../README.md) — the one-paragraph pitch, the stack, and the licensing sign-off.
- [specs/macos-ci/00-overview.md](../../specs/macos-ci/00-overview.md) — the full design orientation
  and reading order through the rest of the specs.

You do not need to read either before continuing — they're there for when you want the "why," not the
"how."

### The stack, briefly

The harness is built on:

- **[Tart](https://tart.run)** — a CLI and virtualization framework for running macOS/Linux VMs on
  Apple Silicon, on top of Apple's own Virtualization.framework. This is the tool that actually creates,
  clones, runs, and deletes the VMs.
- **[Packer](https://developer.hashicorp.com/packer)** — HashiCorp's machine-image build tool. Here it
  drives a one-time build of a "golden" Tart VM image with all the prerequisites (Xcode Command Line
  Tools, Homebrew, chezmoi) already installed, so every test run starts from a known-good baseline
  instead of provisioning from scratch every time. See [tutorial 3](03-building-the-golden-image.md).
- **UTM** — a separate macOS/Linux virtualization app, present in this stack only as a manual escape
  hatch for interactive/GUI work. It is not part of the automated harness. The full decision record for
  why Tart is primary and UTM is not is in
  [specs/macos-ci/10-tart-vs-utm-adr.md](../../specs/macos-ci/10-tart-vs-utm-adr.md) — worth reading if
  you're wondering "why not just use UTM," but not required to follow this tutorial.

You'll also see [just](https://github.com/casey/just) (a command runner, like `make` without make's
syntax baggage) and [uv](https://docs.astral.sh/uv/) (a fast Python package/project manager) throughout
— `just <recipe>` is how you'll invoke almost everything in this repo, and `uv run` is how the Justfile
invokes the repo's own Python CLI, `macos-ci`.

For the full top-level directory map (what `specs/`, `harness/`, `packer/`, `src/macos_ci/`, `tests/`,
and `artifacts/` each are), see [docs/architecture/repo-structure.md](../architecture/repo-structure.md).

## Step 1: Check your prerequisites with `just doctor`

Before anything else, this repo wants to tell you what's missing rather than let you discover it
halfway through a VM build. That's `doctor` — read `src/macos_ci/_doctor_core.py`'s `REQUIRED_TOOLS`
tuple and you'll find the authoritative list is exactly:

| Tool | Version floor | What it's for |
|---|---|---|
| `tart` | `>= 2.0.0` | The VM engine itself |
| `packer` | `>= 1.10.0` | Golden-image builds |
| `just` | present | The command runner driving every recipe in this tutorial |
| `uv` | present | Runs the Python CLI (`uv run macos-ci ...`) |
| `cirrus` | present | The [Cirrus CLI](https://tart.run), used for local/CI parity (`just ci`) |
| `sshpass` | present | Feeds a password to the one-time SSH bootstrap connection (see [tutorial 2](02-running-the-harness.md)) |

`doctor` checks more than tools, too — it also verifies you're on Apple Silicon (`arm64`), your macOS
version is `>= 13.0` (Tart's floor), your login keychain is unlocked (a first-boot codesigning
requirement), that the `ZSH_DOTFILES` path you'll be testing against actually exists on disk, and that
you have at least 60GB of free disk space. All of that lives in `src/macos_ci/_doctor_core.py`'s
`check()` function — read it directly if you want the exact logic, rather than trusting this summary.

Run it:

```bash
just doctor
```

### A clean pass looks like this

```
[     OK] tart                     required=>=2.0.0    found=2.1.0
[     OK] packer                   required=>=1.10.0   found=1.11.2
[     OK] just                     required=present     found=1.34.0
[     OK] uv                       required=present     found=0.5.11
[     OK] cirrus                   required=present     found=0.1.3
[     OK] sshpass                  required=present     found=1.10
[     OK] apple-silicon            required=arm64       found=arm64
[     OK] macos-version            required=>=13.0      found=15.1
[     OK] login-keychain-unlocked  required=unlocked    found=unlocked
[     OK] ZSH_DOTFILES             required=exists      found=/Users/you/dev/zsh-dotfiles
[     OK] free-disk-space          required=>=60GB      found=412.7GB
[     OK] fleet-ceiling            required=report-only found=≤03 hosts / ≤100 combined CPU cores (G4 accepted-risk, see README.md)
```

`doctor` exits `0` here — every row is `OK`.

### A failure looks like this

Say `sshpass` isn't installed and your dotfiles path doesn't exist yet:

```
[     OK] tart                     required=>=2.0.0    found=2.1.0
[     OK] packer                   required=>=1.10.0   found=1.11.2
[     OK] just                     required=present     found=1.34.0
[     OK] uv                       required=present     found=0.5.11
[     OK] cirrus                   required=present     found=0.1.3
[MISSING] sshpass                  required=present     found=None
[     OK] apple-silicon            required=arm64       found=arm64
[     OK] macos-version            required=>=13.0      found=15.1
[     OK] login-keychain-unlocked  required=unlocked    found=unlocked
[MISSING] ZSH_DOTFILES             required=exists      found=None
[     OK] free-disk-space          required=>=60GB      found=412.7GB
[     OK] fleet-ceiling            required=report-only found=≤03 hosts / ≤100 combined CPU cores (G4 accepted-risk, see README.md)
```

```bash
$ echo $?
2
```

Any `MISSING` row makes the whole command exit `2`. Fix the row (`brew install sshpass`, clone
`zsh-dotfiles` next to this repo or set `ZSH_DOTFILES` to point at it — see
[tutorial 2](02-running-the-harness.md#override-variables)) and re-run `just doctor` until every row
is `OK`.

There's also a machine-readable form for scripts and agents:

```bash
just doctor --json
```

which prints the same rows as a JSON array and writes it to `artifacts/<run-id>/doctor.json` either
way — `doctor` always writes this artifact, whether or not you asked for `--json` on stdout.

### The fleet-ceiling row is informational, not a gate

Notice the `fleet-ceiling` row above is always `OK` — that's deliberate. Tart is
[Fair Source](https://fair.io), not open source, and its free tier is capped. This repo's accepted risk
posture (signed off 2026-07-10, see [README.md](../../README.md#licensing-accepted-risk-sign-off-g4))
is **at most 3 hosts, at most 100 combined CPU cores**. `doctor` reports that ceiling on every run so
it stays visible, but it deliberately never turns it into a pass/fail check — nothing in this repo
counts your hosts or cores for you. That's a human judgment call, not a machine one.

## Step 2: Run the full cycle with `just run`

Once `doctor` passes, the single command that exercises the entire harness is:

```bash
just run
```

`run` is a Justfile recipe that depends on `doctor` (so it always preflights first), then chains four
phases inside the `macos-ci` CLI: **up → apply → verify → destroy**. In outline:

1. **`up`** — clones a "golden" VM image (see [tutorial 3](03-building-the-golden-image.md) for how
   that image gets built the first time), boots it headless, waits for it to get a network address,
   and bootstraps SSH access into it.
2. **`apply`** — runs `chezmoi apply` inside the guest, installing `zsh-dotfiles` for real.
3. **verify** — the install gets asserted against (in the full `just run` cycle this is folded into
   the harness's own pass/fail check; the separate `just verify` recipe, covered in
   [tutorial 4](04-verifying-the-truth-gate.md), runs a fuller pytest suite against a VM you keep
   running yourself).
4. **`destroy`** — the clone is deleted, whether the run passed or failed.

> [!NOTE]
> **This first run has a one-time cost you should expect.** `up` clones from a golden image that
> doesn't exist until you build it once with `just build-golden` — and that build pulls a ~23.7GB base
> macOS image over the network. [Tutorial 3](03-building-the-golden-image.md) walks through that build
> step by step. If you haven't built the golden image yet, `just run` will fail at the `up` phase
> looking for a VM named `dotfiles-golden` that doesn't exist. Build it first, then come back here.

Once the golden image exists, `just run` looks like this on success:

```
[     OK] tart                     required=>=2.0.0    found=2.1.0
...
run: {'ok': True, 'phase': 'done', 'cause': None, 'evidence': [], 'next_action': None}
```

and exits `0`. On failure, it prints which phase broke and exits `2`:

```
run FAILED at phase=wait-for-ip: tart ip dotfiles-test-20260710-142301-004821 did not resolve within 120.0s
```

Either way, a `verdict.json` gets written to `artifacts/<run-id>/verdict.json` — this is the
authoritative pass/fail record for the run, and it's written even if the process crashes partway
through. [Tutorial 5](05-debugging-a-failed-run.md) covers reading that file and everything else you
need when a run fails.

## Checkpoint

At this point you should be able to:

- Explain in one sentence what Tart, Packer, and this repo's harness each do.
- Run `just doctor` and read a clean pass vs. a failure.
- Know that `just run` chains doctor → up → apply → verify → destroy, and that its first invocation
  depends on a golden image existing.

## Next steps

- [Tutorial 2 — Running the Harness](02-running-the-harness.md): the VM lifecycle in detail — what
  each of `up`/`down`/`destroy`/`apply`/`recreate`/`prune`/`matrix` actually does, and a fast
  iteration loop for editing dotfiles.
- [Tutorial 3 — Building the Golden Image](03-building-the-golden-image.md): if you haven't built one
  yet, do this next.
- [docs/architecture/build-pipeline.md](../architecture/build-pipeline.md) and
  [docs/architecture/cli-reference.md](../architecture/cli-reference.md) for the full field-by-field
  reference behind everything summarized above.
