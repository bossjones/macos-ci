# 3. Building the Golden Image

## What you'll learn

How to build the "golden" Tart VM image that every test-run clone in
[tutorial 2](02-running-the-harness.md) is cloned from, what that build actually does, what it costs
in time and bandwidth, and how to check afterward that no build secret leaked into the image.

## Prerequisites

- [Tutorial 1](01-getting-started.md) completed: `just doctor` passes.
- Comfortable with the terms *Tart VM*, *clone*, and *headless* from
  [tutorial 2](02-running-the-harness.md) — this tutorial doesn't re-explain them.

## Why a separate "golden image" build exists at all

[Tutorial 2](02-running-the-harness.md) explained that every test run clones a VM rather than mutating
one directly. But clone *from what*? Cloning a bare, freshly-downloaded macOS image would mean every
single test run has to install Xcode Command Line Tools, Homebrew, and chezmoi from scratch before it
can even attempt the `zsh-dotfiles` install it's actually trying to test — turning a fast iteration loop
into a slow provisioning loop, every time.

The golden image solves that by doing all of that provisioning **once**, producing a VM
(`dotfiles-golden`) with those prerequisites already baked in. Every `tart clone` after that is a
byte-identical copy in seconds, not a from-scratch install.

This tutorial is deliberately task-oriented — "how do I build one." For the full pipeline diagram, the
exact provisioner steps, and the design rationale for why the golden image and the per-test clone are
split this way, see [docs/architecture/build-pipeline.md](../architecture/build-pipeline.md) and
[specs/macos-ci/08-dotfiles-test-harness.md §"(a) Golden image vs. from-scratch per test"](../../specs/macos-ci/08-dotfiles-test-harness.md).

## What Packer is doing here

[Packer](https://developer.hashicorp.com/packer) is HashiCorp's image-build tool: you hand it a
template describing a source image and a list of provisioning steps, and it produces a finished,
reusable machine image. Here, the "machine" is a Tart VM, via the
[`packer-plugin-tart`](https://developer.hashicorp.com/packer/integrations/cirruslabs/tart) builder
plugin — the template that drives this is
[`packer/tart-golden-image.pkr.hcl`](../../packer/tart-golden-image.pkr.hcl).

## Step 1: Build it

```bash
just build-golden
```

(`just build` is an alias for the same recipe, matching the name used in
[specs/macos-ci/12-tooling-and-agent-loop.md](../../specs/macos-ci/12-tooling-and-agent-loop.md).)

This Justfile recipe first checks that `packer/tart-golden-image.pkr.hcl` actually exists (failing
loudly with exit `4` and a pointer to the relevant spec if it doesn't, rather than letting `packer`
itself emit a confusing error), then runs:

```bash
packer build packer/tart-golden-image.pkr.hcl
```

Under the hood, the template:

1. **Clones the base image** — `ghcr.io/cirruslabs/macos-sequoia-vanilla:latest` (the `default` entry
   in [`macos-versions.toml`](../../macos-versions.toml)), an unmodified vanilla macOS OCI image Tart
   can pull straight from a container registry.
2. **Shapes the VM** — 4 CPUs, 8GB memory, 60GB disk, headless, named `dotfiles-golden`.
3. **Provisions it**, all in one inline shell script, idempotently:
   - Installs Xcode Command Line Tools non-interactively (`softwareupdate`, not
     `xcode-select --install`, which would pop a GUI prompt that never resolves on a headless VM).
   - Installs Homebrew if not already present.
   - Installs a handful of brew prerequisites (`wget`, `curl`, `retry`, `go`, `openssl@3`, `readline`,
     `libyaml`, `gmp`, `autoconf`, `tmux`).
   - Installs `chezmoi` via Homebrew.

It deliberately does **not** install `zsh-dotfiles-prep` — that stays a separate, optional matrix leg,
not baked into the golden image.

> [!NOTE]
> **Expect this to be slow the first time.** The base image pull is ~23.7GB compressed, and that
> single download dominates the build's wall-clock — it alone can run to the majority of an hour-scale
> build. This was observed directly during a real build in this repo (including several transient
> "network connection was lost" layer retries that Tart's own retry logic absorbed without failing the
> build). The provisioner step itself, by comparison, is fast. Budget for this the first time you run
> `just build-golden` on a given host.

### Planned but not implemented: `just images-cache`

> [!IMPORTANT]
> This repo's [CLAUDE.md](../../CLAUDE.md) describes a planned optimization: pre-pulling the base OCI
> image once per host (`tart pull ghcr.io/cirruslabs/macos-sequoia-vanilla`) so every subsequent
> golden-image build clones from a local cache in seconds instead of re-pulling ~23.7GB every time. **As
> of this writing, no `just images-cache` recipe exists in the checked-in Justfile.** Do not try to run
> it — it isn't there yet. The Justfile does have `just images` (prints `macos-versions.toml` alongside
> `tart list`, for cross-referencing what's declared vs. what's actually present locally) and
> `just pull IMAGE`, but neither is the documented pre-warm-every-lane recipe `CLAUDE.md` describes.
> Treat the caching optimization as a stated design intent, not a shipped command, until a recipe by
> that name actually lands in the Justfile.

## Step 2: Verify no secret leaked into the image

The build can optionally inject `HOMEBREW_GITHUB_API_TOKEN` (pulled from your environment or
`gh auth token` if available) purely as a rate-limit optimization — GitHub's unauthenticated API cap is
60 requests/hour vs. 5,000/hour authenticated. The build succeeds either way; the token is never
required.

That token is passed to the provisioner only as a process environment variable for the life of one SSH
command — never written to a file inside the guest. This matters because, as
[CLAUDE.md](../../CLAUDE.md) explains, **deleting a secret from inside a guest does not erase it**:
`rm` unlinks the filesystem entry but doesn't zero the underlying disk blocks, so a secret that was ever
written to a file would still be recoverable with `strings` against the VM's disk image, even after
being "deleted."

`just verify-no-secrets <vm>` is the canary that proves this held — a distinct recipe, run *after* a
build, not a step Packer itself depends on:

```bash
just verify-no-secrets dotfiles-golden
```

It resolves the same token value from your environment, and if one is present, recursively greps the
entire `~/.tart/vms/dotfiles-golden/` directory (not a single named disk file — Tart documents the
directory, not the specific file inside it, and the disk format may vary) for that literal string.

- If no token was present in your environment to begin with, it exits `0` with "nothing to search for"
  — there's nothing to prove.
- If the token is genuinely absent from the built VM's artifact, it exits `0`, clean.
- If the token turns up anywhere in the artifact, it exits `2` — a real leak, and it prints exactly
  where it found the match.

```
✅ clean: token absent from ~/.tart/vms/dotfiles-golden/
```

vs. a leak:

```
🚨 LEAK: the token is present in the artifact above
```

Run this once per build — it's cheap, and it's the only thing standing between "we believe the token
never touched disk" and "we checked."

## Checkpoint

You should now be able to:

- Explain in one sentence why a separate golden-image build exists, distinct from the per-test clone.
- Run `just build-golden` (or `just build`) and know what to expect from the first, slow run.
- Run `just verify-no-secrets <vm>` and read a clean pass vs. a leak.
- Know that `just images-cache` does not exist yet, despite being described in `CLAUDE.md`.

## Next steps

- [Tutorial 2 — Running the Harness](02-running-the-harness.md): now that a golden image exists, this
  is what `just up` clones from.
- [docs/architecture/build-pipeline.md](../architecture/build-pipeline.md): the full pipeline diagram
  and every provisioner detail this tutorial intentionally skipped.
- [specs/macos-ci/13-build-secrets.md](../../specs/macos-ci/13-build-secrets.md): the full secrets-handling
  design, including why Packer's `sensitive = true` masks *values*, not variables, and why the guest
  SSH credentials (`admin`/`admin`) are deliberately *not* marked sensitive.
